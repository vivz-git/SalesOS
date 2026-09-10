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


def test_create_workspace_endpoint_new_user_no_prior_state() -> None:
    """A brand-new authenticated user with no existing workspaces/memberships
    can create their first workspace and is inserted as its owner."""
    user_id = uuid4()
    mock_user = AuthUser(user_id=user_id, email="new-user@example.com")

    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_admin = MagicMock()
    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []

    with patch("app.api.workspaces._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            "/v1/workspaces",
            json={"name": "Vivspace"},
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Vivspace"
        assert data["slug"] == "vivspace"

        insert_calls = mock_admin.table.call_args_list
        assert insert_calls[0].args == ("workspaces",)
        assert insert_calls[1].args == ("memberships",)

        membership_payload = mock_admin.table.return_value.insert.call_args_list[1].args[0]
        assert membership_payload["user_id"] == str(user_id)
        assert membership_payload["role"] == "owner"

    app.dependency_overrides.clear()


def test_create_workspace_membership_failure_rolls_back_workspace_and_is_logged() -> None:
    """If the owner-membership insert fails, the orphaned workspace row must be
    rolled back (so a retry with the same name doesn't hit a slug conflict) and
    the real database exception must be logged rather than silently discarded."""
    user_id = uuid4()
    mock_user = AuthUser(user_id=user_id, email="new-user@example.com")

    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_admin = MagicMock()
    membership_error = RuntimeError("new row violates row-level security policy for table memberships")

    table_mocks: list[tuple[str, MagicMock]] = []

    def insert_side_effect(table_name: str) -> MagicMock:
        insert_mock = MagicMock()
        if table_name == "memberships":
            insert_mock.insert.return_value.execute.side_effect = membership_error
        else:
            insert_mock.insert.return_value.execute.return_value.data = []
        insert_mock.delete.return_value.eq.return_value.execute.return_value.data = []
        table_mocks.append((table_name, insert_mock))
        return insert_mock

    mock_admin.table.side_effect = insert_side_effect

    with (
        patch("app.api.workspaces._clients", return_value=(MagicMock(), mock_admin)),
        patch("app.api.workspaces.logger") as mock_logger,
    ):
        client = TestClient(app)
        response = client.post(
            "/v1/workspaces",
            json={"name": "Vivspace"},
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "workspace_creation_failed"

        # The orphaned workspace row must actually be deleted, targeting the id
        # that was just inserted - not merely logged as a failure.
        workspace_mocks = [mock for name, mock in table_mocks if name == "workspaces"]
        inserted_workspace_id = workspace_mocks[0].insert.call_args.args[0]["id"]

        rollback_mocks = [mock for mock in workspace_mocks if mock.delete.called]
        assert len(rollback_mocks) == 1, "expected exactly one rollback delete on workspaces"
        rollback_mocks[0].delete.return_value.eq.assert_called_once_with("id", inserted_workspace_id)
        rollback_mocks[0].delete.return_value.eq.return_value.execute.assert_called_once()

        # The underlying exception must be surfaced via logging, not swallowed.
        assert mock_logger.error.called
        logged_messages = " ".join(str(call) for call in mock_logger.error.call_args_list)
        assert "memberships" in logged_messages.lower() or str(membership_error) in logged_messages

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
