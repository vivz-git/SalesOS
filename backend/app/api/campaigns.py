from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["campaigns"])

CampaignStatus = Literal["draft", "active", "paused", "archived"]


class Campaign(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None = None
    target_segment: str | None = None
    icp_definition: str | None = None
    status: CampaignStatus = "draft"
    created_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    target_segment: str | None = Field(default=None, max_length=255)
    icp_definition: str | None = Field(default=None, max_length=2000)


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    target_segment: str | None = Field(default=None, max_length=255)
    icp_definition: str | None = Field(default=None, max_length=2000)


def _row_to_campaign(row: dict[str, str | None]) -> Campaign:
    created_at_val = row.get("created_at")
    updated_at_val = row.get("updated_at")
    deleted_at_val = row.get("deleted_at")
    return Campaign(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        name=str(row["name"]),
        description=row.get("description"),
        target_segment=row.get("target_segment"),
        icp_definition=row.get("icp_definition"),
        status=cast(CampaignStatus, row.get("status", "draft")),
        created_by=UUID(str(row["created_by"])) if row.get("created_by") else None,
        created_at=datetime.fromisoformat(created_at_val) if created_at_val else None,
        updated_at=datetime.fromisoformat(updated_at_val) if updated_at_val else None,
        deleted_at=datetime.fromisoformat(deleted_at_val) if deleted_at_val else None,
    )


@router.post("/campaigns", response_model=Campaign, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Campaign:
    _, admin_client = _clients(settings)
    campaign_id = uuid4()
    now_iso = datetime.now(UTC).isoformat()

    row = {
        "id": str(campaign_id),
        "workspace_id": str(principal.workspace_id),
        "name": payload.name.strip(),
        "description": payload.description.strip() if payload.description else None,
        "target_segment": payload.target_segment.strip() if payload.target_segment else None,
        "icp_definition": payload.icp_definition.strip() if payload.icp_definition else None,
        "status": "draft",
        "created_by": str(principal.user_id),
        "created_at": now_iso,
        "updated_at": now_iso,
        "deleted_at": None,
    }

    try:
        admin_client.table("campaigns").insert(row).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="campaign_creation_failed"
        ) from error

    return _row_to_campaign(row)


@router.get("/campaigns", response_model=list[Campaign])
def list_campaigns(
    status_filter: str | None = Query(default=None, alias="status"),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[Campaign]:
    _, admin_client = _clients(settings)

    query = admin_client.table("campaigns").select("*").eq("workspace_id", str(principal.workspace_id))
    if status_filter:
        query = query.eq("status", status_filter)

    rows = cast(list[dict[str, str | None]], query.execute().data or [])

    campaigns: list[Campaign] = []
    for r in rows:
        if status_filter != "archived" and r.get("deleted_at") is not None:
            continue
        campaigns.append(_row_to_campaign(r))

    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Campaign:
    _, admin_client = _clients(settings)
    rows = cast(
        list[dict[str, str | None]],
        admin_client.table("campaigns")
        .select("*")
        .eq("id", str(campaign_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")

    return _row_to_campaign(rows[0])


@router.patch("/campaigns/{campaign_id}", response_model=Campaign)
def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Campaign:
    get_campaign(campaign_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates: dict[str, str | None] = {"updated_at": datetime.now(UTC).isoformat()}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.description is not None:
        updates["description"] = payload.description.strip() if payload.description else None
    if payload.target_segment is not None:
        updates["target_segment"] = payload.target_segment.strip() if payload.target_segment else None
    if payload.icp_definition is not None:
        updates["icp_definition"] = payload.icp_definition.strip() if payload.icp_definition else None

    try:
        admin_client.table("campaigns").update(updates).eq("id", str(campaign_id)).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="campaign_update_failed"
        ) from error

    return get_campaign(campaign_id, principal=principal, settings=settings)


@router.delete("/campaigns/{campaign_id}", response_model=Campaign)
def delete_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Campaign:
    get_campaign(campaign_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    now_iso = datetime.now(UTC).isoformat()
    updates = {"status": "archived", "deleted_at": now_iso, "updated_at": now_iso}

    admin_client.table("campaigns").update(updates).eq("id", str(campaign_id)).execute()
    return get_campaign(campaign_id, principal=principal, settings=settings)


@router.post("/campaigns/{campaign_id}/actions/activate", response_model=Campaign)
def activate_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Campaign:
    get_campaign(campaign_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates = {"status": "active", "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("campaigns").update(updates).eq("id", str(campaign_id)).execute()
    return get_campaign(campaign_id, principal=principal, settings=settings)


@router.post("/campaigns/{campaign_id}/actions/pause", response_model=Campaign)
def pause_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Campaign:
    get_campaign(campaign_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates = {"status": "paused", "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("campaigns").update(updates).eq("id", str(campaign_id)).execute()
    return get_campaign(campaign_id, principal=principal, settings=settings)


@router.post("/campaigns/{campaign_id}/actions/archive", response_model=Campaign)
def archive_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Campaign:
    return delete_campaign(campaign_id, principal=principal, settings=settings)


@router.post("/campaigns/{campaign_id}/actions/restore", response_model=Campaign)
def restore_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Campaign:
    get_campaign(campaign_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates = {"status": "draft", "deleted_at": None, "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("campaigns").update(updates).eq("id", str(campaign_id)).execute()
    return get_campaign(campaign_id, principal=principal, settings=settings)
