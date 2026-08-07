from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import AuthUser, Principal, get_current_principal, get_current_user
from app.main import app


def test_create_workspace_endpoint() -> None:
    user_id = uuid4()
    mock_user = AuthUser(user_id=user_id, email="creator@example.com")

    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_admin = MagicMock()
    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []

    with patch("app.api.workspaces._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            "/v1/workspaces",
            json={"name": "Acme Ventures", "slug": "acme-ventures"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Acme Ventures"
        assert data["slug"] == "acme-ventures"
        assert "id" in data

    app.dependency_overrides.clear()


def test_list_workspaces_endpoint() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    mock_user = AuthUser(user_id=user_id, email="creator@example.com")

    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_admin = MagicMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"workspace_id": str(workspace_id)}
    ]
    mock_admin.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [
        {
            "id": str(workspace_id),
            "name": "Acme Corp",
            "slug": "acme-corp",
            "created_at": "2026-08-07T12:00:00+00:00",
            "updated_at": "2026-08-07T12:00:00+00:00",
        }
    ]

    with patch("app.api.workspaces._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.get(
            "/v1/workspaces",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(workspace_id)
        assert data[0]["name"] == "Acme Corp"

    app.dependency_overrides.clear()


def test_get_workspace_success() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    mock_principal = Principal(
        user_id=user_id,
        email="owner@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    mock_admin = MagicMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": str(workspace_id),
            "name": "Target Workspace",
            "slug": "target-workspace",
            "created_at": "2026-08-07T12:00:00+00:00",
            "updated_at": "2026-08-07T12:00:00+00:00",
        }
    ]

    with patch("app.api.workspaces._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.get(
            f"/v1/workspaces/{workspace_id}",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(workspace_id)
        assert data["name"] == "Target Workspace"

    app.dependency_overrides.clear()


def test_get_workspace_access_denied_for_other_workspace() -> None:
    user_id = uuid4()
    active_workspace = uuid4()
    other_workspace = uuid4()
    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=active_workspace,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    client = TestClient(app)
    response = client.get(
        f"/v1/workspaces/{other_workspace}",
        headers={"Authorization": "Bearer fake-token"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "workspace_access_denied"

    app.dependency_overrides.clear()
