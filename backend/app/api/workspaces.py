import re
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import AuthUser, Principal, _clients, get_current_principal, get_current_user
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["workspaces"])


class Workspace(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = Field(default=None, max_length=100)


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return cleaned or "workspace"


@router.post("/workspaces", response_model=Workspace, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreate,
    user: AuthUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Workspace:
    _, admin_client = _clients(settings)
    workspace_id = uuid4()
    slug = payload.slug.strip().lower() if payload.slug and payload.slug.strip() else _slugify(payload.name)
    now_iso = datetime.now(UTC).isoformat()

    workspace_data = {
        "id": str(workspace_id),
        "name": payload.name.strip(),
        "slug": slug,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        admin_client.table("workspaces").insert(workspace_data).execute()
        admin_client.table("memberships").insert(
            {
                "id": str(uuid4()),
                "workspace_id": str(workspace_id),
                "user_id": str(user.user_id),
                "role": "owner",
                "created_at": now_iso,
                "updated_at": now_iso,
            }
        ).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="workspace_creation_failed"
        ) from error

    return Workspace(
        id=workspace_id,
        name=payload.name.strip(),
        slug=slug,
        created_at=datetime.fromisoformat(now_iso),
        updated_at=datetime.fromisoformat(now_iso),
    )


@router.get("/workspaces", response_model=list[Workspace])
def list_workspaces(
    user: AuthUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> list[Workspace]:
    _, admin_client = _clients(settings)
    memberships = cast(
        list[dict[str, str]],
        admin_client.table("memberships")
        .select("workspace_id")
        .eq("user_id", str(user.user_id))
        .execute()
        .data
        or [],
    )
    if not memberships:
        return []

    workspace_ids = [m["workspace_id"] for m in memberships if "workspace_id" in m]
    if not workspace_ids:
        return []

    rows = cast(
        list[dict[str, str]],
        admin_client.table("workspaces").select("*").in_("id", workspace_ids).execute().data or [],
    )

    workspaces: list[Workspace] = []
    for r in rows:
        created_at_val = r.get("created_at")
        updated_at_val = r.get("updated_at")
        workspaces.append(
            Workspace(
                id=UUID(r["id"]),
                name=r["name"],
                slug=r["slug"],
                created_at=datetime.fromisoformat(created_at_val) if created_at_val else None,
                updated_at=datetime.fromisoformat(updated_at_val) if updated_at_val else None,
            )
        )
    return workspaces


@router.get("/workspaces/{workspace_id}", response_model=Workspace)
def get_workspace(
    workspace_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Workspace:
    if workspace_id != principal.workspace_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="workspace_access_denied")

    _, admin_client = _clients(settings)
    data = cast(
        list[dict[str, str]],
        admin_client.table("workspaces").select("*").eq("id", str(workspace_id)).execute().data or [],
    )
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workspace_not_found")

    row = data[0]
    created_at_val = row.get("created_at")
    updated_at_val = row.get("updated_at")
    return Workspace(
        id=UUID(row["id"]),
        name=row["name"],
        slug=row["slug"],
        created_at=datetime.fromisoformat(created_at_val) if created_at_val else None,
        updated_at=datetime.fromisoformat(updated_at_val) if updated_at_val else None,
    )
