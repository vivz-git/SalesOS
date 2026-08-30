from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.db import get_db_session
from app.main import app
from app.models import ContactModel, DeliveryModel, OutreachDraftModel


def create_mock_session() -> MagicMock:
    session = MagicMock()
    tx_ctx = MagicMock()
    tx_ctx.__aenter__ = AsyncMock(return_value=session)
    tx_ctx.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=tx_ctx)
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_principal() -> Principal:
    return Principal(
        user_id=uuid4(),
        email="sender@example.com",
        workspace_id=uuid4(),
        role="admin",
    )


def test_delivery_approval_gate_enforcement(mock_principal: Principal) -> None:
    draft_id = uuid4()
    # 1. Test unapproved draft rejected
    mock_draft = OutreachDraftModel(
        id=draft_id,
        workspace_id=mock_principal.workspace_id,
        campaign_id=uuid4(),
        contact_id=uuid4(),
        current_version_id=uuid4(),
        current_version_number=1,
        current_subject="Draft Subj",
        current_body="Draft Body",
        status="ready_for_review",  # NOT approved
        created_by=mock_principal.user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_session = create_mock_session()
    mock_session.get.return_value = mock_draft

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        client = TestClient(app)
        res = client.post("/v1/deliveries", json={"draft_id": str(draft_id)})
        assert res.status_code == 400
        assert "cannot_deliver_unapproved_draft_in_ready_for_review_state" in res.text
    finally:
        app.dependency_overrides.clear()


def test_delivery_idempotency_returns_existing(mock_principal: Principal) -> None:
    draft_id = uuid4()
    contact_id = uuid4()
    delivery_id = uuid4()
    version_id = uuid4()

    mock_draft = OutreachDraftModel(
        id=draft_id,
        workspace_id=mock_principal.workspace_id,
        campaign_id=uuid4(),
        contact_id=contact_id,
        current_version_id=version_id,
        current_version_number=1,
        current_subject="Approved Subject",
        current_body="Approved Body",
        status="approved",
        created_by=mock_principal.user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_contact = ContactModel(
        id=contact_id,
        workspace_id=mock_principal.workspace_id,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    idemp_key = f"{mock_principal.workspace_id}:{draft_id}:1"
    existing_delivery = DeliveryModel(
        id=delivery_id,
        workspace_id=mock_principal.workspace_id,
        draft_id=draft_id,
        version_id=version_id,
        version_number=1,
        contact_id=contact_id,
        recipient_email="jane@example.com",
        subject="Approved Subject",
        body="Approved Body",
        provider="resend",
        provider_message_id="msg_12345",
        status="sent",
        idempotency_key=idemp_key,
        created_by=mock_principal.user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_session = create_mock_session()
    # mock_session.get handles draft, contact, delivery
    mock_session.get.side_effect = lambda model, id_val: (
        mock_draft
        if model == OutreachDraftModel
        else (mock_contact if model == ContactModel else existing_delivery)
    )
    # scalar returns existing delivery for idempotency check
    mock_session.scalar.return_value = existing_delivery

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        client = TestClient(app)
        res = client.post("/v1/deliveries", json={"draft_id": str(draft_id)})
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == str(delivery_id)
        assert data["status"] == "sent"
        assert data["idempotency_key"] == idemp_key
    finally:
        app.dependency_overrides.clear()


def test_resend_webhook_updates_delivery_status() -> None:
    delivery_id = uuid4()
    workspace_id = uuid4()
    msg_id = "msg_resend_123"

    mock_delivery = DeliveryModel(
        id=delivery_id,
        workspace_id=workspace_id,
        provider_message_id=msg_id,
        status="sent",
        draft_id=uuid4(),
        version_id=uuid4(),
        version_number=1,
        contact_id=uuid4(),
        recipient_email="test@example.com",
        subject="sub",
        body="body",
        provider="resend",
        idempotency_key="test",
        created_by=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_session = create_mock_session()
    mock_session.scalar.return_value = mock_delivery

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    from app.core.config import Settings

    def _override_settings() -> Settings:
        return Settings(resend_webhook_secret=None)

    app.dependency_overrides[get_db_session] = _override_session
    from app.core.config import get_settings

    app.dependency_overrides[get_settings] = _override_settings

    from unittest.mock import patch

    with patch("app.auth._clients") as mock_clients:
        mock_admin = MagicMock()
        mock_clients.return_value = (None, mock_admin)

        mock_execute = MagicMock()
        mock_execute.execute.return_value.data = [
            {"id": str(delivery_id), "workspace_id": str(workspace_id)}
        ]
        mock_limit = MagicMock()
        mock_limit.limit.return_value = mock_execute
        mock_eq = MagicMock()
        mock_eq.eq.return_value = mock_limit
        mock_select = MagicMock()
        mock_select.select.return_value = mock_eq
        mock_table = MagicMock()
        mock_table.table.return_value = mock_select
        mock_admin.table = mock_table.table

        try:
            client = TestClient(app)
            payload = {"type": "email.delivered", "data": {"email_id": msg_id}}
            res = client.post("/v1/deliveries/webhooks/resend", json=payload)
            assert res.status_code == 200
            assert res.json()["status"] == "processed"

            assert mock_delivery.status == "delivered"
            mock_session.commit.assert_awaited()
        finally:
            app.dependency_overrides.clear()
