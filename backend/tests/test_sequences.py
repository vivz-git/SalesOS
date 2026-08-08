from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.main import app


def test_create_or_update_sequence_definition() -> None:
    user_id = uuid4()
    ws_id = uuid4()
    campaign_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_campaign: dict[str, Any] = {
        "id": str(campaign_id),
        "workspace_id": str(ws_id),
        "name": "Target Campaign",
        "target_segment": "Tech",
        "value_proposition": "Value",
        "offer": "Offer",
        "tone": "professional",
        "status": "draft",
        "owner_id": str(user_id),
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_campaign]

    with patch("app.api.campaigns._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        # 1. Fetch sequence (creates default)
        get_resp = client.get(f"/v1/campaigns/{campaign_id}/sequences")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["campaign_id"] == str(campaign_id)
        assert len(data["steps"]) == 2

        # 2. Update sequence definition
        update_payload = {
            "name": "Custom Sequence",
            "steps": [
                {
                    "step_number": 1,
                    "delay_days": 0,
                    "channel": "email",
                    "step_type": "first_touch",
                    "template_subject": "Step 1 Subject",
                    "template_body": "Step 1 Body",
                },
                {
                    "step_number": 2,
                    "delay_days": 4,
                    "channel": "email",
                    "step_type": "follow_up",
                    "template_subject": "Step 2 Subject",
                    "template_body": "Step 2 Body",
                },
            ],
        }
        post_resp = client.post(f"/v1/campaigns/{campaign_id}/sequences", json=update_payload)
        assert post_resp.status_code == 200
        updated_data = post_resp.json()
        assert updated_data["name"] == "Custom Sequence"
        assert updated_data["version_number"] == 2
        assert len(updated_data["steps"]) == 2

    app.dependency_overrides.clear()


def test_enroll_contact_in_sequence_creates_draft() -> None:
    user_id = uuid4()
    ws_id = uuid4()
    campaign_id = uuid4()
    contact_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_campaign: dict[str, Any] = {
        "id": str(campaign_id),
        "workspace_id": str(ws_id),
        "name": "Outreach Campaign",
        "target_segment": "SaaS",
        "value_proposition": "Value",
        "offer": "Offer",
        "tone": "professional",
        "status": "active",
        "owner_id": str(user_id),
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_campaign]

    with patch("app.api.campaigns._clients", return_value=(MagicMock(), mock_admin)):
        with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
            client = TestClient(app)
            enroll_resp = client.post(
                "/v1/sequence-enrollments",
                json={
                    "campaign_id": str(campaign_id),
                    "contact_id": str(contact_id),
                },
            )
            assert enroll_resp.status_code == 200
            enr_data = enroll_resp.json()
            assert enr_data["status"] == "pending_approval"
            assert enr_data["current_step_number"] == 1

            enrollment_id = enr_data["id"]

            # Pause enrollment
            pause_resp = client.post(f"/v1/sequence-enrollments/{enrollment_id}/actions/pause")
            assert pause_resp.status_code == 200
            assert pause_resp.json()["status"] == "paused"

            # Resume enrollment
            resume_resp = client.post(f"/v1/sequence-enrollments/{enrollment_id}/actions/resume")
            assert resume_resp.status_code == 200
            assert resume_resp.json()["status"] == "active"

            # Stop enrollment
            stop_resp = client.post(
                f"/v1/sequence-enrollments/{enrollment_id}/actions/stop",
                json={"reason": "manual_stop"},
            )
            assert stop_resp.status_code == 200
            assert stop_resp.json()["status"] == "stopped"

    app.dependency_overrides.clear()


def test_inbound_reply_automatically_halts_sequence() -> None:
    user_id = uuid4()
    ws_id = uuid4()
    campaign_id = uuid4()
    contact_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_campaign: dict[str, Any] = {
        "id": str(campaign_id),
        "workspace_id": str(ws_id),
        "name": "Campaign",
        "target_segment": "Tech",
        "value_proposition": "V",
        "offer": "O",
        "tone": "prof",
        "status": "active",
        "owner_id": str(user_id),
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_campaign]

    with patch("app.api.campaigns._clients", return_value=(MagicMock(), mock_admin)):
        with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
            client = TestClient(app)
            # 1. Enroll contact
            enroll_resp = client.post(
                "/v1/sequence-enrollments",
                json={"campaign_id": str(campaign_id), "contact_id": str(contact_id)},
            )
            enr_id = enroll_resp.json()["id"]

            # 2. Ingest inbound reply from prospect
            client.post(
                "/v1/conversations/inbound",
                json={
                    "workspace_id": str(ws_id),
                    "sender_email": "prospect@example.com",
                    "recipient_email": "rep@company.com",
                    "subject": "Re: Touchpoint",
                    "body": "Thanks for reaching out, let's connect!",
                },
            )

            # 3. Verify sequence enrollment is automatically stopped
            enr_detail = client.get(f"/v1/sequence-enrollments/{enr_id}")
            assert enr_detail.status_code == 200
            assert enr_detail.json()["status"] == "stopped"
            assert enr_detail.json()["stop_reason"] == "prospect_replied"

    app.dependency_overrides.clear()
