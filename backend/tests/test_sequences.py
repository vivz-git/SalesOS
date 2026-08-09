import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.auth import Principal, get_current_principal

pytestmark = pytest.mark.asyncio

async def test_create_or_update_sequence_definition(seeded_workspace) -> None:
    workspace_id, user_id = seeded_workspace

    mock_principal = Principal(
        user_id=user_id,
        email="test@example.com",
        workspace_id=workspace_id,
        role="owner"
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a campaign
            camp_resp = await client.post("/v1/campaigns", json={
                "name": "Target Campaign",
                "target_segment": "Tech",
                "value_proposition": "Value",
                "offer": "Offer",
                "tone": "professional"
            })
            assert camp_resp.status_code == 201
            campaign_id = camp_resp.json()["id"]

            # 1. Fetch sequence (creates default)
            get_resp = await client.get(f"/v1/campaigns/{campaign_id}/sequences")
            assert get_resp.status_code == 200
            data = get_resp.json()
            assert data["campaign_id"] == campaign_id
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
            post_resp = await client.post(f"/v1/campaigns/{campaign_id}/sequences", json=update_payload)
            assert post_resp.status_code == 200
            updated_data = post_resp.json()
            assert updated_data["name"] == "Custom Sequence"
            assert updated_data["version_number"] == 2
            assert len(updated_data["steps"]) == 2
            
    finally:
        app.dependency_overrides.clear()


async def test_enroll_contact_in_sequence_creates_draft(seeded_workspace) -> None:
    workspace_id, user_id = seeded_workspace
    
    mock_principal = Principal(
        user_id=user_id,
        email="test@example.com",
        workspace_id=workspace_id,
        role="owner"
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            camp_resp = await client.post("/v1/campaigns", json={"name": "Outreach Campaign", "status": "active"})
            assert camp_resp.status_code == 201
            campaign_id = camp_resp.json()["id"]
            
            contact_resp = await client.post("/v1/contacts", json={"email": "prospect@example.com", "first_name": "Test", "last_name": "User"})
            assert contact_resp.status_code == 201
            contact_id = contact_resp.json()["id"]

            enroll_resp = await client.post(
                "/v1/sequence-enrollments",
                json={
                    "campaign_id": campaign_id,
                    "contact_id": contact_id,
                },
            )
            assert enroll_resp.status_code == 200
            enr_data = enroll_resp.json()
            assert enr_data["status"] == "pending_approval"
            assert enr_data["current_step_number"] == 1

            enrollment_id = enr_data["id"]

            # Pause enrollment
            pause_resp = await client.post(f"/v1/sequence-enrollments/{enrollment_id}/actions/pause")
            assert pause_resp.status_code == 200
            assert pause_resp.json()["status"] == "paused"

            # Resume enrollment
            resume_resp = await client.post(f"/v1/sequence-enrollments/{enrollment_id}/actions/resume")
            assert resume_resp.status_code == 200
            assert resume_resp.json()["status"] == "active"

            # Stop enrollment
            stop_resp = await client.post(
                f"/v1/sequence-enrollments/{enrollment_id}/actions/stop",
                json={"reason": "manual_stop"},
            )
            assert stop_resp.status_code == 200
            assert stop_resp.json()["status"] == "stopped"

    finally:
        app.dependency_overrides.clear()


async def test_inbound_reply_automatically_halts_sequence(seeded_workspace) -> None:
    workspace_id, user_id = seeded_workspace
    
    mock_principal = Principal(
        user_id=user_id,
        email="test@example.com",
        workspace_id=workspace_id,
        role="owner"
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            camp_resp = await client.post("/v1/campaigns", json={"name": "Outreach Campaign", "status": "active"})
            assert camp_resp.status_code == 201
            campaign_id = camp_resp.json()["id"]
            
            contact_resp = await client.post("/v1/contacts", json={"email": "prospect@example.com", "first_name": "Test", "last_name": "User"})
            assert contact_resp.status_code == 201
            contact_id = contact_resp.json()["id"]
            
            enroll_resp = await client.post(
                "/v1/sequence-enrollments",
                json={"campaign_id": campaign_id, "contact_id": contact_id},
            )
            assert enroll_resp.status_code == 200
            enr_id = enroll_resp.json()["id"]

            await client.post(
                "/v1/sequence-enrollments/{enr_id}/actions/resume"
            ) # force active

            # Ingest inbound reply from prospect
            reply_resp = await client.post(
                "/v1/conversations/inbound",
                json={
                    "workspace_id": str(workspace_id),
                    "sender_email": "prospect@example.com",
                    "recipient_email": "rep@company.com",
                    "subject": "Re: Touchpoint",
                    "body": "Thanks for reaching out, let's connect!",
                },
            )
            assert reply_resp.status_code == 200

            # Verify sequence enrollment is automatically stopped
            enr_detail = await client.get(f"/v1/sequence-enrollments/{enr_id}")
            assert enr_detail.status_code == 200
            assert enr_detail.json()["status"] == "stopped"
            assert enr_detail.json()["stop_reason"] == "prospect_replied"

    finally:
        app.dependency_overrides.clear()
