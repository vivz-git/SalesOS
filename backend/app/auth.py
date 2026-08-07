from collections.abc import Callable
from typing import Literal, cast
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import Client, create_client

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)
Role = Literal["owner", "admin", "manager", "contributor", "viewer"]


class Principal(BaseModel):
    user_id: UUID
    email: str | None
    workspace_id: UUID
    role: Role


def _clients(settings: Settings) -> tuple[Client, Client]:
    if not all(
        [settings.supabase_url, settings.supabase_publishable_key, settings.supabase_service_role_key]
    ):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="auth_unavailable")
    assert settings.supabase_url
    assert settings.supabase_publishable_key
    assert settings.supabase_service_role_key
    return (
        create_client(settings.supabase_url, settings.supabase_publishable_key),
        create_client(settings.supabase_url, settings.supabase_service_role_key),
    )


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    workspace_id: UUID | None = Header(default=None, alias="X-SalesOS-Workspace-Id"),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")

    auth_client, admin_client = _clients(settings)
    try:
        user_response = auth_client.auth.get_user(credentials.credentials)
        user = user_response.user if user_response else None
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_session") from error
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_session")

    memberships = cast(list[dict[str, str]], (
        admin_client.table("memberships")
        .select("workspace_id,role")
        .eq("user_id", str(user.id))
        .execute()
        .data
    ) or [])
    if not memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="workspace_membership_required")

    active_membership = next(
        (membership for membership in memberships if workspace_id and membership["workspace_id"] == str(workspace_id)),
        memberships[0] if workspace_id is None and len(memberships) == 1 else None,
    )
    if active_membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="workspace_access_denied")

    return Principal(
        user_id=UUID(user.id),
        email=user.email,
        workspace_id=UUID(active_membership["workspace_id"]),
        role=cast(Role, active_membership["role"]),
    )


def require_role(*roles: Role) -> Callable[[Principal], Principal]:
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient_role")
        return principal

    return dependency
