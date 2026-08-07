from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.main import app


def test_create_campaign_endpoint() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    mock_admin = MagicMock()
    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []

    with patch("app.api.campaigns._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            "/v1/campaigns",
            json={
                "name": "Q3 SaaS Outbound",
                "description": "Outbound campaign targeting VP Sales",
                "target_segment": "B2B SaaS 50-200 ARR",
                "icp_definition": "Mid-market B2B tech companies",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Q3 SaaS Outbound"
        assert data["status"] == "draft"
        assert data["workspace_id"] == str(workspace_id)

    app.dependency_overrides.clear()


def test_list_and_get_campaign_endpoints() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    campaign_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="admin",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_campaign = {
        "id": str(campaign_id),
        "workspace_id": str(workspace_id),
        "name": "Enterprise Campaign",
        "description": "Enterprise brief",
        "target_segment": "Enterprise",
        "icp_definition": "Fortune 500",
        "status": "draft",
        "created_by": str(user_id),
        "created_at": "2026-08-07T12:00:00+00:00",
        "updated_at": "2026-08-07T12:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.execute.return_value.data = [sample_campaign]
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_campaign]

    with patch("app.api.campaigns._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        list_res = client.get("/v1/campaigns", headers={"Authorization": "Bearer fake-token"})
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1

        get_res = client.get(
            f"/v1/campaigns/{campaign_id}", headers={"Authorization": "Bearer fake-token"}
        )
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "Enterprise Campaign"

    app.dependency_overrides.clear()


def test_campaign_actions_activate_and_pause() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    campaign_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_campaign = {
        "id": str(campaign_id),
        "workspace_id": str(workspace_id),
        "name": "Action Campaign",
        "status": "active",
        "created_by": str(user_id),
        "created_at": "2026-08-07T12:00:00+00:00",
        "updated_at": "2026-08-07T12:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.execute.return_value.data = [sample_campaign]
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_campaign]
    mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.campaigns._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        act_res = client.post(
            f"/v1/campaigns/{campaign_id}/actions/activate",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert act_res.status_code == 200
        assert act_res.json()["status"] == "active"

    app.dependency_overrides.clear()
