from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.main import app


def test_cannot_directly_approve_draft_in_draft_state() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="approver@example.com",
        workspace_id=workspace_id,
        role="admin",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "current_version_id": str(uuid4()),
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
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_draft]

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            f"/v1/approvals/{draft_id}/actions/approve",
            json={"notes": "Direct approval attempt"},
        )
        assert response.status_code == 400
        assert "cannot_approve_draft_in_draft_state" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_approve_ready_for_review_draft_success() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()
    version_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="approver@example.com",
        workspace_id=workspace_id,
        role="admin",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    ready_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "current_version_id": str(version_id),
        "current_version_number": 2,
        "current_subject": "AI Subject V2",
        "current_body": "AI Body V2",
        "status": "ready_for_review",
        "created_by": str(user_id),
        "created_at": "2026-08-08T10:00:00+00:00",
        "updated_at": "2026-08-08T10:05:00+00:00",
        "deleted_at": None,
    }

    approved_draft: dict[str, Any] = {
        **ready_draft,
        "status": "approved",
        "updated_at": "2026-08-08T10:10:00+00:00",
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value

    # Side-effect returns for get_outreach_draft calls:
    # 1: Initial draft lookup (ready_for_review)
    # 2: Post-update draft lookup (approved)
    # 3: Detail build lookup (campaigns, contacts, etc.)
    mock_select.eq.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[ready_draft]),
        MagicMock(data=[approved_draft]),
        MagicMock(data=[]),
        MagicMock(data=[]),
    ]
    mock_select.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {
            "id": str(version_id),
            "workspace_id": str(workspace_id),
            "draft_id": str(draft_id),
            "version_number": 2,
            "subject": "AI Subject V2",
            "body": "AI Body V2",
            "generation_source": "ai_generated",
        }
    ]

    mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [approved_draft]
    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        with patch("app.api.approvals._clients", return_value=(MagicMock(), mock_admin)):
            client = TestClient(app)
            response = client.post(
                f"/v1/approvals/{draft_id}/actions/approve",
                json={"notes": "Approved after evidence verification"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["draft"]["status"] == "approved"
            assert len(data["review_history"]) >= 1
            latest_audit = data["review_history"][-1]
            assert latest_audit["decision"] == "approved"
            assert latest_audit["reviewer_id"] == str(user_id)
            assert latest_audit["notes"] == "Approved after evidence verification"

    app.dependency_overrides.clear()


def test_reject_ready_for_review_draft_success() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()
    version_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="reviewer@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    ready_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "current_version_id": str(version_id),
        "current_version_number": 1,
        "current_subject": "Bad Subject",
        "current_body": "Bad Body",
        "status": "ready_for_review",
        "created_by": str(user_id),
    }

    rejected_draft: dict[str, Any] = {
        **ready_draft,
        "status": "rejected",
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value

    mock_select.eq.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[ready_draft]),
        MagicMock(data=[rejected_draft]),
        MagicMock(data=[]),
        MagicMock(data=[]),
    ]
    mock_select.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = []

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        with patch("app.api.approvals._clients", return_value=(MagicMock(), mock_admin)):
            client = TestClient(app)
            response = client.post(
                f"/v1/approvals/{draft_id}/actions/reject",
                json={"notes": "Incorrect pricing reference"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["draft"]["status"] == "rejected"

    app.dependency_overrides.clear()


def test_return_to_draft_action() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="reviewer@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    rejected_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "status": "rejected",
        "current_version_number": 1,
    }

    returned_draft: dict[str, Any] = {
        **rejected_draft,
        "status": "draft",
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value

    mock_select.eq.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[rejected_draft]),
        MagicMock(data=[returned_draft]),
        MagicMock(data=[]),
        MagicMock(data=[]),
    ]
    mock_select.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = []

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        with patch("app.api.approvals._clients", return_value=(MagicMock(), mock_admin)):
            client = TestClient(app)
            response = client.post(
                f"/v1/approvals/{draft_id}/actions/return-to-draft",
                json={"notes": "Please rewrite introduction paragraph"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["draft"]["status"] == "draft"

    app.dependency_overrides.clear()


def test_cross_workspace_approval_access_denied() -> None:
    user_id = uuid4()
    user_workspace_id = uuid4()
    draft_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@tenant-a.com",
        workspace_id=user_workspace_id,
        role="admin",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    # DB query returns empty array because draft workspace_id != principal workspace_id
    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.get(f"/v1/approvals/{draft_id}")
        assert response.status_code == 404
        assert "draft_not_found" in response.json()["detail"]

    app.dependency_overrides.clear()
