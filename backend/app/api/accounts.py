from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["accounts"])

AccountStatus = Literal["target", "qualified", "disqualified", "archived"]


class Account(BaseModel):
    id: UUID
    workspace_id: UUID
    campaign_id: UUID | None = None
    name: str
    domain: str | None = None
    industry: str | None = None
    employee_count: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    status: AccountStatus = "target"
    created_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    campaign_id: UUID | None = None
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=100)
    employee_count: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    status: AccountStatus = "target"


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    campaign_id: UUID | None = None
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=100)
    employee_count: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    status: AccountStatus | None = None


def _row_to_account(row: dict[str, str | None]) -> Account:
    created_at_val = row.get("created_at")
    updated_at_val = row.get("updated_at")
    deleted_at_val = row.get("deleted_at")
    return Account(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        campaign_id=UUID(str(row["campaign_id"])) if row.get("campaign_id") else None,
        name=str(row["name"]),
        domain=row.get("domain"),
        industry=row.get("industry"),
        employee_count=row.get("employee_count"),
        city=row.get("city"),
        state=row.get("state"),
        country=row.get("country"),
        status=cast(AccountStatus, row.get("status", "target")),
        created_by=UUID(str(row["created_by"])) if row.get("created_by") else None,
        created_at=datetime.fromisoformat(created_at_val) if created_at_val else None,
        updated_at=datetime.fromisoformat(updated_at_val) if updated_at_val else None,
        deleted_at=datetime.fromisoformat(deleted_at_val) if deleted_at_val else None,
    )


@router.post("/accounts", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Account:
    _, admin_client = _clients(settings)
    account_id = uuid4()
    now_iso = datetime.now(UTC).isoformat()

    row = {
        "id": str(account_id),
        "workspace_id": str(principal.workspace_id),
        "campaign_id": str(payload.campaign_id) if payload.campaign_id else None,
        "name": payload.name.strip(),
        "domain": payload.domain.strip().lower() if payload.domain else None,
        "industry": payload.industry.strip() if payload.industry else None,
        "employee_count": payload.employee_count.strip() if payload.employee_count else None,
        "city": payload.city.strip() if payload.city else None,
        "state": payload.state.strip() if payload.state else None,
        "country": payload.country.strip() if payload.country else None,
        "status": payload.status,
        "created_by": str(principal.user_id),
        "created_at": now_iso,
        "updated_at": now_iso,
        "deleted_at": None,
    }

    try:
        admin_client.table("accounts").insert(row).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="account_creation_failed"
        ) from error

    return _row_to_account(row)


@router.get("/accounts", response_model=list[Account])
def list_accounts(
    campaign_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[Account]:
    _, admin_client = _clients(settings)

    query = admin_client.table("accounts").select("*").eq("workspace_id", str(principal.workspace_id))
    if campaign_id:
        query = query.eq("campaign_id", str(campaign_id))
    if status_filter:
        query = query.eq("status", status_filter)

    rows = cast(list[dict[str, str | None]], query.execute().data or [])

    accounts: list[Account] = []
    for r in rows:
        if status_filter != "archived" and r.get("deleted_at") is not None:
            continue
        if search:
            search_lower = search.lower()
            name_val = str(r.get("name") or "").lower()
            domain_val = str(r.get("domain") or "").lower()
            if search_lower not in name_val and search_lower not in domain_val:
                continue
        accounts.append(_row_to_account(r))

    paginated = accounts[offset : offset + limit]
    return paginated


@router.get("/accounts/{account_id}", response_model=Account)
def get_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Account:
    _, admin_client = _clients(settings)
    rows = cast(
        list[dict[str, str | None]],
        admin_client.table("accounts")
        .select("*")
        .eq("id", str(account_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account_not_found")

    return _row_to_account(rows[0])


@router.patch("/accounts/{account_id}", response_model=Account)
def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Account:
    get_account(account_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates: dict[str, str | None] = {"updated_at": datetime.now(UTC).isoformat()}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.campaign_id is not None:
        updates["campaign_id"] = str(payload.campaign_id) if payload.campaign_id else None
    if payload.domain is not None:
        updates["domain"] = payload.domain.strip().lower() if payload.domain else None
    if payload.industry is not None:
        updates["industry"] = payload.industry.strip() if payload.industry else None
    if payload.employee_count is not None:
        updates["employee_count"] = payload.employee_count.strip() if payload.employee_count else None
    if payload.city is not None:
        updates["city"] = payload.city.strip() if payload.city else None
    if payload.state is not None:
        updates["state"] = payload.state.strip() if payload.state else None
    if payload.country is not None:
        updates["country"] = payload.country.strip() if payload.country else None
    if payload.status is not None:
        updates["status"] = payload.status

    try:
        admin_client.table("accounts").update(updates).eq("id", str(account_id)).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="account_update_failed"
        ) from error

    return get_account(account_id, principal=principal, settings=settings)


@router.delete("/accounts/{account_id}", response_model=Account)
def delete_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Account:
    get_account(account_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    now_iso = datetime.now(UTC).isoformat()
    updates = {"status": "archived", "deleted_at": now_iso, "updated_at": now_iso}

    admin_client.table("accounts").update(updates).eq("id", str(account_id)).execute()
    return get_account(account_id, principal=principal, settings=settings)


@router.post("/accounts/{account_id}/actions/archive", response_model=Account)
def archive_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Account:
    return delete_account(account_id, principal=principal, settings=settings)


@router.post("/accounts/{account_id}/actions/restore", response_model=Account)
def restore_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Account:
    get_account(account_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates = {"status": "target", "deleted_at": None, "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("accounts").update(updates).eq("id", str(account_id)).execute()
    return get_account(account_id, principal=principal, settings=settings)
