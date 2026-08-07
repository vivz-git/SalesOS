from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal, require_role
from app.core.config import Settings
from app.main import app


def test_role_guard_allows_matching_role() -> None:
    principal = Principal(user_id=uuid4(), email="a@example.com", workspace_id=uuid4(), role="admin")
    assert require_role("admin")(principal) == principal


def test_role_guard_rejects_non_matching_role() -> None:
    principal = Principal(user_id=uuid4(), email="a@example.com", workspace_id=uuid4(), role="viewer")
    with pytest.raises(HTTPException, match="insufficient_role"):
        require_role("admin")(principal)


def test_get_current_principal_missing_credentials() -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_publishable_key="pub-key",
        supabase_service_role_key="service-key",
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(credentials=None, workspace_id=None, settings=settings)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "authentication_required"


def test_get_current_principal_missing_settings() -> None:
    settings = Settings(supabase_url=None, supabase_publishable_key=None, supabase_service_role_key=None)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(credentials=creds, workspace_id=None, settings=settings)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "auth_unavailable"


@patch("app.auth._clients")
def test_get_current_principal_invalid_session(mock_clients: MagicMock) -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_publishable_key="pub-key",
        supabase_service_role_key="service-key",
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

    mock_auth = MagicMock()
    mock_auth.auth.get_user.side_effect = Exception("Invalid token")
    mock_admin = MagicMock()
    mock_clients.return_value = (mock_auth, mock_admin)

    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(credentials=creds, workspace_id=None, settings=settings)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "invalid_session"


@patch("app.auth._clients")
def test_get_current_principal_no_memberships(mock_clients: MagicMock) -> None:
    user_id = str(uuid4())
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_publishable_key="pub-key",
        supabase_service_role_key="service-key",
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.email = "user@example.com"

    mock_auth = MagicMock()
    mock_auth.auth.get_user.return_value.user = mock_user

    mock_admin = MagicMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    mock_clients.return_value = (mock_auth, mock_admin)

    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(credentials=creds, workspace_id=None, settings=settings)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "workspace_membership_required"


@patch("app.auth._clients")
def test_get_current_principal_single_membership_success(mock_clients: MagicMock) -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_publishable_key="pub-key",
        supabase_service_role_key="service-key",
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

    mock_user = MagicMock()
    mock_user.id = str(user_id)
    mock_user.email = "user@example.com"

    mock_auth = MagicMock()
    mock_auth.auth.get_user.return_value.user = mock_user

    mock_admin = MagicMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"workspace_id": str(workspace_id), "role": "owner"}
    ]

    mock_clients.return_value = (mock_auth, mock_admin)

    principal = get_current_principal(credentials=creds, workspace_id=None, settings=settings)
    assert principal.user_id == user_id
    assert principal.email == "user@example.com"
    assert principal.workspace_id == workspace_id
    assert principal.role == "owner"


@patch("app.auth._clients")
def test_get_current_principal_header_workspace_match(mock_clients: MagicMock) -> None:
    user_id = uuid4()
    target_workspace = uuid4()
    other_workspace = uuid4()

    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_publishable_key="pub-key",
        supabase_service_role_key="service-key",
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

    mock_user = MagicMock()
    mock_user.id = str(user_id)
    mock_user.email = "user@example.com"

    mock_auth = MagicMock()
    mock_auth.auth.get_user.return_value.user = mock_user

    mock_admin = MagicMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"workspace_id": str(other_workspace), "role": "viewer"},
        {"workspace_id": str(target_workspace), "role": "admin"},
    ]

    mock_clients.return_value = (mock_auth, mock_admin)

    principal = get_current_principal(credentials=creds, workspace_id=target_workspace, settings=settings)
    assert principal.workspace_id == target_workspace
    assert principal.role == "admin"


def test_me_endpoint() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    mock_principal = Principal(
        user_id=user_id,
        email="me@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    try:
        client = TestClient(app)
        response = client.get("/v1/me")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user_id)
        assert data["email"] == "me@example.com"
        assert data["workspace_id"] == str(workspace_id)
        assert data["role"] == "owner"
    finally:
        app.dependency_overrides.clear()
