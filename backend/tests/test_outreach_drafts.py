from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.main import app


def test_create_outreach_draft() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    campaign_id = uuid4()
    contact_id = uuid4()
    research_brief_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="contributor@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    mock_admin = MagicMock()
    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            "/v1/outreach/drafts",
            json={
                "campaign_id": str(campaign_id),
                "contact_id": str(contact_id),
                "research_brief_id": str(research_brief_id),
                "subject": "Initial Intro Subject",
                "body": "Hello prospect, checking in based on recent research.",
                "generation_source": "human",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["campaign_id"] == str(campaign_id)
        assert data["contact_id"] == str(contact_id)
        assert data["research_brief_id"] == str(research_brief_id)
        assert data["status"] == "draft"
        assert data["current_version_number"] == 1
        assert data["current_subject"] == "Initial Intro Subject"
        assert data["current_body"] == "Hello prospect, checking in based on recent research."
        assert len(data["versions"]) == 1
        assert data["versions"][0]["version_number"] == 1

    app.dependency_overrides.clear()


def test_list_and_get_outreach_drafts() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()
    campaign_id = uuid4()
    contact_id = uuid4()
    version_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="manager@example.com",
        workspace_id=workspace_id,
        role="manager",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_version: dict[str, Any] = {
        "id": str(version_id),
        "workspace_id": str(workspace_id),
        "draft_id": str(draft_id),
        "version_number": 1,
        "subject": "Draft Subject",
        "body": "Draft Body",
        "generation_source": "human",
        "created_by": str(user_id),
        "created_at": "2026-08-08T10:00:00+00:00",
    }

    sample_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(campaign_id),
        "contact_id": str(contact_id),
        "research_brief_id": None,
        "current_version_id": str(version_id),
        "current_version_number": 1,
        "current_subject": "Draft Subject",
        "current_body": "Draft Body",
        "status": "draft",
        "created_by": str(user_id),
        "created_at": "2026-08-08T10:00:00+00:00",
        "updated_at": "2026-08-08T10:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    # For list_outreach_drafts
    mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_draft]

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        list_res = client.get("/v1/outreach/drafts", headers={"Authorization": "Bearer fake-token"})
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) == 1
        assert items[0]["id"] == str(draft_id)

    # For get_outreach_draft
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_draft]
    mock_select.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = [sample_version]

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        get_res = client.get(f"/v1/outreach/drafts/{draft_id}", headers={"Authorization": "Bearer fake-token"})
        assert get_res.status_code == 200
        detail = get_res.json()
        assert detail["id"] == str(draft_id)
        assert len(detail["versions"]) == 1

    app.dependency_overrides.clear()


def test_revise_outreach_draft_creates_new_version() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()
    v1_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="contributor@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_draft_v1: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "research_brief_id": None,
        "current_version_id": str(v1_id),
        "current_version_number": 1,
        "current_subject": "V1 Subject",
        "current_body": "V1 Body",
        "status": "draft",
        "created_by": str(user_id),
        "created_at": "2026-08-08T10:00:00+00:00",
        "updated_at": "2026-08-08T10:00:00+00:00",
        "deleted_at": None,
    }

    sample_draft_v2: dict[str, Any] = {
        **sample_draft_v1,
        "current_version_number": 2,
        "current_subject": "V2 Revised Subject",
        "current_body": "V2 Revised Body",
        "updated_at": "2026-08-08T10:05:00+00:00",
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    # Returns v1 on first call, v2 on second call
    mock_select.eq.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[sample_draft_v1]),
        MagicMock(data=[sample_draft_v2]),
    ]

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        revise_res = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/revise",
            json={
                "subject": "V2 Revised Subject",
                "body": "V2 Revised Body",
                "generation_source": "human",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        assert revise_res.status_code == 200
        revised_data = revise_res.json()
        assert revised_data["current_version_number"] == 2
        assert revised_data["current_subject"] == "V2 Revised Subject"

    app.dependency_overrides.clear()


def test_draft_status_lifecycle_actions() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="manager@example.com",
        workspace_id=workspace_id,
        role="manager",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "current_version_number": 1,
        "current_subject": "Subject",
        "current_body": "Body",
        "status": "draft",
        "created_by": str(user_id),
        "created_at": "2026-08-08T10:00:00+00:00",
        "updated_at": "2026-08-08T10:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_draft]
    mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)

        # 1. Submit for review
        sub_res = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/submit-review",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert sub_res.status_code == 200

        # 2. Approve
        app_res = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/approve",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert app_res.status_code == 200

        # 3. Reject
        rej_res = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/reject",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert rej_res.status_code == 200

        # 4. Archive
        arc_res = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/archive",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert arc_res.status_code == 200

    app.dependency_overrides.clear()


def test_invalid_status_transition_rejected() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="contributor@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    archived_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "status": "archived",
        "created_by": str(user_id),
        "created_at": "2026-08-08T10:00:00+00:00",
        "updated_at": "2026-08-08T10:00:00+00:00",
        "deleted_at": "2026-08-08T10:05:00+00:00",
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [archived_draft]

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)

        # Attempt to revise an archived draft should fail with 400
        revise_res = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/revise",
            json={"subject": "Test", "body": "Body"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert revise_res.status_code == 400

    app.dependency_overrides.clear()
