from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["contacts"])

ContactStatus = Literal["active", "unresponsive", "opted_out", "archived"]


class Contact(BaseModel):
    id: UUID
    workspace_id: UUID
    account_id: UUID | None = None
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    department: str | None = None
    linkedin_url: str | None = None
    is_primary: bool = False
    status: ContactStatus = "active"
    created_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class ContactCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    account_id: UUID | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=150)
    department: str | None = Field(default=None, max_length=100)
    linkedin_url: str | None = Field(default=None, max_length=255)
    is_primary: bool = False
    status: ContactStatus = "active"


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    account_id: UUID | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=150)
    department: str | None = Field(default=None, max_length=100)
    linkedin_url: str | None = Field(default=None, max_length=255)
    is_primary: bool | None = None
    status: ContactStatus | None = None


def _row_to_contact(row: dict[str, str | bool | None]) -> Contact:
    created_at_val = cast(str | None, row.get("created_at"))
    updated_at_val = cast(str | None, row.get("updated_at"))
    deleted_at_val = cast(str | None, row.get("deleted_at"))
    return Contact(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        account_id=UUID(str(row["account_id"])) if row.get("account_id") else None,
        first_name=str(row["first_name"]),
        last_name=str(row["last_name"]),
        email=cast(str | None, row.get("email")),
        phone=cast(str | None, row.get("phone")),
        title=cast(str | None, row.get("title")),
        department=cast(str | None, row.get("department")),
        linkedin_url=cast(str | None, row.get("linkedin_url")),
        is_primary=bool(row.get("is_primary", False)),
        status=cast(ContactStatus, row.get("status", "active")),
        created_by=UUID(str(row["created_by"])) if row.get("created_by") else None,
        created_at=datetime.fromisoformat(created_at_val) if created_at_val else None,
        updated_at=datetime.fromisoformat(updated_at_val) if updated_at_val else None,
        deleted_at=datetime.fromisoformat(deleted_at_val) if deleted_at_val else None,
    )


@router.post("/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Contact:
    _, admin_client = _clients(settings)
    contact_id = uuid4()
    now_iso = datetime.now(UTC).isoformat()

    row = {
        "id": str(contact_id),
        "workspace_id": str(principal.workspace_id),
        "account_id": str(payload.account_id) if payload.account_id else None,
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "email": payload.email.strip().lower() if payload.email else None,
        "phone": payload.phone.strip() if payload.phone else None,
        "title": payload.title.strip() if payload.title else None,
        "department": payload.department.strip() if payload.department else None,
        "linkedin_url": payload.linkedin_url.strip() if payload.linkedin_url else None,
        "is_primary": payload.is_primary,
        "status": payload.status,
        "created_by": str(principal.user_id),
        "created_at": now_iso,
        "updated_at": now_iso,
        "deleted_at": None,
    }

    try:
        admin_client.table("contacts").insert(row).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="contact_creation_failed"
        ) from error

    return _row_to_contact(row)


@router.get("/contacts", response_model=list[Contact])
def list_contacts(
    account_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[Contact]:
    _, admin_client = _clients(settings)

    query = admin_client.table("contacts").select("*").eq("workspace_id", str(principal.workspace_id))
    if account_id:
        query = query.eq("account_id", str(account_id))
    if status_filter:
        query = query.eq("status", status_filter)

    rows = cast(list[dict[str, str | bool | None]], query.execute().data or [])

    contacts: list[Contact] = []
    for r in rows:
        if status_filter != "archived" and r.get("deleted_at") is not None:
            continue
        if search:
            search_lower = search.lower()
            fname = str(r.get("first_name") or "").lower()
            lname = str(r.get("last_name") or "").lower()
            email_val = str(r.get("email") or "").lower()
            title_val = str(r.get("title") or "").lower()
            if (
                search_lower not in fname
                and search_lower not in lname
                and search_lower not in email_val
                and search_lower not in title_val
            ):
                continue
        contacts.append(_row_to_contact(r))

    paginated = contacts[offset : offset + limit]
    return paginated


@router.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Contact:
    _, admin_client = _clients(settings)
    rows = cast(
        list[dict[str, str | bool | None]],
        admin_client.table("contacts")
        .select("*")
        .eq("id", str(contact_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_found")

    return _row_to_contact(rows[0])


@router.patch("/contacts/{contact_id}", response_model=Contact)
def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Contact:
    get_contact(contact_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates: dict[str, str | bool | None] = {"updated_at": datetime.now(UTC).isoformat()}
    if payload.first_name is not None:
        updates["first_name"] = payload.first_name.strip()
    if payload.last_name is not None:
        updates["last_name"] = payload.last_name.strip()
    if payload.account_id is not None:
        updates["account_id"] = str(payload.account_id) if payload.account_id else None
    if payload.email is not None:
        updates["email"] = payload.email.strip().lower() if payload.email else None
    if payload.phone is not None:
        updates["phone"] = payload.phone.strip() if payload.phone else None
    if payload.title is not None:
        updates["title"] = payload.title.strip() if payload.title else None
    if payload.department is not None:
        updates["department"] = payload.department.strip() if payload.department else None
    if payload.linkedin_url is not None:
        updates["linkedin_url"] = payload.linkedin_url.strip() if payload.linkedin_url else None
    if payload.is_primary is not None:
        updates["is_primary"] = payload.is_primary
    if payload.status is not None:
        updates["status"] = payload.status

    try:
        admin_client.table("contacts").update(updates).eq("id", str(contact_id)).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="contact_update_failed"
        ) from error

    return get_contact(contact_id, principal=principal, settings=settings)


@router.delete("/contacts/{contact_id}", response_model=Contact)
def delete_contact(
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Contact:
    get_contact(contact_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    now_iso = datetime.now(UTC).isoformat()
    updates = {"status": "archived", "deleted_at": now_iso, "updated_at": now_iso}

    admin_client.table("contacts").update(updates).eq("id", str(contact_id)).execute()
    return get_contact(contact_id, principal=principal, settings=settings)


@router.post("/contacts/{contact_id}/actions/archive", response_model=Contact)
def archive_contact(
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Contact:
    return delete_contact(contact_id, principal=principal, settings=settings)


@router.post("/contacts/{contact_id}/actions/restore", response_model=Contact)
def restore_contact(
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Contact:
    get_contact(contact_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates = {"status": "active", "deleted_at": None, "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("contacts").update(updates).eq("id", str(contact_id)).execute()
    return get_contact(contact_id, principal=principal, settings=settings)
