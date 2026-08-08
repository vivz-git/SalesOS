from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.adapters.email_provider import (
    EmailDeliverySendRequest,
    EmailDeliverySendResult,
    EmailProviderInterface,
)
from app.api.deliveries import get_email_provider
from app.auth import Principal, get_current_principal
from app.main import app


class MockEmailProvider(EmailProviderInterface):
    def send_email(self, request: EmailDeliverySendRequest) -> EmailDeliverySendResult:
        return EmailDeliverySendResult(
            provider="resend",
            provider_message_id=f"msg_mock_{uuid4().hex[:8]}",
            status="sent",
            idempotency_key=request.idempotency_key,
            duration_ms=120,
            raw_response={"id": "msg_mock_123"},
        )


class FailingEmailProvider(EmailProviderInterface):
    def send_email(self, request: EmailDeliverySendRequest) -> EmailDeliverySendResult:
        raise ValueError("Provider API connection timeout")


def test_create_delivery_for_approved_draft_success() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()
    contact_id = uuid4()
    version_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="sender@example.com",
        workspace_id=workspace_id,
        role="admin",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_email_provider] = lambda: MockEmailProvider()

    approved_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(contact_id),
        "current_version_id": str(version_id),
        "current_version_number": 2,
        "current_subject": "Approved Subject",
        "current_body": "Approved Body Text",
        "status": "approved",
        "created_by": str(user_id),
    }

    sample_contact: dict[str, Any] = {
        "id": str(contact_id),
        "workspace_id": str(workspace_id),
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value

    # Side effects:
    # 1. get_outreach_draft lookup
    # 2. contacts lookup
    mock_select.eq.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[approved_draft]),
        MagicMock(data=[sample_contact]),
    ]
    mock_select.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {
            "id": str(version_id),
            "workspace_id": str(workspace_id),
            "draft_id": str(draft_id),
            "version_number": 2,
            "subject": "Approved Subject",
            "body": "Approved Body Text",
        }
    ]

    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []
    mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        with patch("app.api.deliveries._clients", return_value=(MagicMock(), mock_admin)):
            client = TestClient(app)
            response = client.post(
                "/v1/deliveries",
                json={"draft_id": str(draft_id)},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "sent"
            assert data["recipient_email"] == "john.doe@example.com"
            assert data["provider"] == "resend"
            assert data["provider_message_id"] is not None
            assert str(workspace_id) in data["idempotency_key"]

    app.dependency_overrides.clear()


def test_cannot_create_delivery_for_unapproved_draft() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="sender@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    ready_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "current_version_id": str(uuid4()),
        "current_version_number": 1,
        "status": "ready_for_review",
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [ready_draft]

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            "/v1/deliveries",
            json={"draft_id": str(draft_id)},
        )
        assert response.status_code == 400
        assert "cannot_deliver_unapproved_draft" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_resend_webhook_handler_status_updates() -> None:
    from app.api.deliveries import _DELIVERIES_STORE

    delivery_id = uuid4()
    workspace_id = uuid4()
    msg_id = f"msg_{uuid4().hex[:8]}"

    _DELIVERIES_STORE.append({
        "id": str(delivery_id),
        "workspace_id": str(workspace_id),
        "draft_id": str(uuid4()),
        "version_id": str(uuid4()),
        "version_number": 1,
        "contact_id": str(uuid4()),
        "recipient_email": "test@example.com",
        "subject": "Subject",
        "body": "Body",
        "provider": "resend",
        "provider_message_id": msg_id,
        "status": "sent",
        "idempotency_key": "key123",
        "created_by": str(uuid4()),
        "created_at": "2026-08-08T10:00:00+00:00",
        "updated_at": "2026-08-08T10:00:00+00:00",
    })

    client = TestClient(app)
    webhook_payload = {
        "type": "email.delivered",
        "data": {
            "email_id": msg_id,
            "created_at": "2026-08-08T10:01:00Z",
        },
    }

    response = client.post("/v1/deliveries/webhooks/resend", json=webhook_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    # Verify status was updated to delivered
    updated_rec = next(d for d in _DELIVERIES_STORE if d["id"] == str(delivery_id))
    assert updated_rec["status"] == "delivered"
