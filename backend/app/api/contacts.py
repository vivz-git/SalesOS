from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal, get_current_principal
from app.db import get_db_session, tenant_transaction_context
from app.models import ContactModel

router = APIRouter(prefix="/v1", tags=["contacts"])

ContactStatus = Literal["active", "unresponsive", "opted_out", "archived"]


class Contact(BaseModel):
    id: UUID
    workspace_id: UUID
    account_id: UUID | None = None
    campaign_id: UUID | None = None
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
    campaign_id: UUID | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    linkedin_url: str | None = Field(default=None, max_length=255)
    is_primary: bool = False


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    account_id: UUID | None = None
    campaign_id: UUID | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    linkedin_url: str | None = Field(default=None, max_length=255)
    is_primary: bool | None = None
    status: ContactStatus | None = None


def _model_to_contact(model: ContactModel) -> Contact:
    return Contact(
        id=model.id,
        workspace_id=model.workspace_id,
        account_id=model.account_id,
        campaign_id=model.campaign_id,
        first_name=model.first_name,
        last_name=model.last_name,
        email=model.email,
        phone=model.phone,
        title=model.title,
        department=model.department,
        linkedin_url=model.linkedin_url,
        is_primary=model.is_primary,
        status=cast(ContactStatus, model.status),
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


@router.post("/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Contact:
    now_utc = datetime.now(UTC)
    contact_id = uuid4()

    new_contact = ContactModel(
        id=contact_id,
        workspace_id=principal.workspace_id,
        account_id=payload.account_id,
        campaign_id=payload.campaign_id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.strip().lower() if payload.email else None,
        phone=payload.phone.strip() if payload.phone else None,
        title=payload.title.strip() if payload.title else None,
        department=payload.department.strip() if payload.department else None,
        linkedin_url=payload.linkedin_url.strip() if payload.linkedin_url else None,
        is_primary=payload.is_primary,
        status="active",
        created_by=principal.user_id,
        created_at=now_utc,
        updated_at=now_utc,
        deleted_at=None,
    )

    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        try:
            ctx.add(new_contact)
            await ctx.flush()
            await ctx.refresh(new_contact)
        except Exception as error:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="contact_creation_failed"
            ) from error

    return _model_to_contact(new_contact)


@router.get("/contacts", response_model=list[Contact])
async def list_contacts(
    account_id: UUID | None = Query(default=None),
    campaign_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[Contact]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(ContactModel).where(ContactModel.workspace_id == principal.workspace_id)
        
        if account_id:
            stmt = stmt.where(ContactModel.account_id == account_id)
        if campaign_id:
            stmt = stmt.where(ContactModel.campaign_id == campaign_id)
            
        if status_filter:
            stmt = stmt.where(ContactModel.status == status_filter)
        else:
            stmt = stmt.where(ContactModel.deleted_at.is_(None))
            
        if search:
            search_lower = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    ContactModel.first_name.ilike(search_lower),
                    ContactModel.last_name.ilike(search_lower),
                    ContactModel.email.ilike(search_lower),
                    ContactModel.title.ilike(search_lower)
                )
            )
            
        stmt = stmt.offset(offset).limit(limit)
        
        result = await ctx.execute(stmt)
        models = result.scalars().all()
        
        return [_model_to_contact(m) for m in models]


@router.get("/contacts/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Contact:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(ContactModel).where(
            ContactModel.id == contact_id,
            ContactModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_found")
            
        return _model_to_contact(model)


@router.patch("/contacts/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Contact:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(ContactModel).where(
            ContactModel.id == contact_id,
            ContactModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_found")
            
        model.updated_at = datetime.now(UTC)
        if payload.first_name is not None:
            model.first_name = payload.first_name.strip()
        if payload.last_name is not None:
            model.last_name = payload.last_name.strip()
        if payload.account_id is not None:
            model.account_id = payload.account_id
        if payload.campaign_id is not None:
            model.campaign_id = payload.campaign_id
        if payload.email is not None:
            model.email = payload.email.strip().lower() if payload.email else None
        if payload.phone is not None:
            model.phone = payload.phone.strip() if payload.phone else None
        if payload.title is not None:
            model.title = payload.title.strip() if payload.title else None
        if payload.department is not None:
            model.department = payload.department.strip() if payload.department else None
        if payload.linkedin_url is not None:
            model.linkedin_url = payload.linkedin_url.strip() if payload.linkedin_url else None
        if payload.is_primary is not None:
            model.is_primary = payload.is_primary
        if payload.status is not None:
            model.status = payload.status
            
        try:
            await ctx.flush()
            await ctx.refresh(model)
        except Exception as error:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="contact_update_failed"
            ) from error
            
        return _model_to_contact(model)


@router.delete("/contacts/{contact_id}", response_model=Contact)
async def delete_contact(
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Contact:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(ContactModel).where(
            ContactModel.id == contact_id,
            ContactModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_found")
            
        now_utc = datetime.now(UTC)
        model.status = "archived"
        model.deleted_at = now_utc
        model.updated_at = now_utc
        
        await ctx.flush()
        await ctx.refresh(model)
        return _model_to_contact(model)


@router.post("/contacts/{contact_id}/actions/archive", response_model=Contact)
async def archive_contact(
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Contact:
    return await delete_contact(contact_id, principal=principal, session=session)


@router.post("/contacts/{contact_id}/actions/restore", response_model=Contact)
async def restore_contact(
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Contact:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(ContactModel).where(
            ContactModel.id == contact_id,
            ContactModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_found")
            
        model.status = "active"
        model.deleted_at = None
        model.updated_at = datetime.now(UTC)
        
        await ctx.flush()
        await ctx.refresh(model)
        return _model_to_contact(model)
