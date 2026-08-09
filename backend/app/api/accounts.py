from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal, get_current_principal
from app.db import get_db_session, tenant_transaction_context
from app.models import AccountModel

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


def _model_to_account(model: AccountModel) -> Account:
    return Account(
        id=model.id,
        workspace_id=model.workspace_id,
        campaign_id=model.campaign_id,
        name=model.name,
        domain=model.domain,
        industry=model.industry,
        employee_count=model.employee_count,
        city=model.city,
        state=model.state,
        country=model.country,
        status=cast(AccountStatus, model.status),
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


@router.post("/accounts", response_model=Account, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    now_utc = datetime.now(UTC)
    account_id = uuid4()

    new_account = AccountModel(
        id=account_id,
        workspace_id=principal.workspace_id,
        campaign_id=payload.campaign_id,
        name=payload.name.strip(),
        domain=payload.domain.strip().lower() if payload.domain else None,
        industry=payload.industry.strip() if payload.industry else None,
        employee_count=payload.employee_count.strip() if payload.employee_count else None,
        city=payload.city.strip() if payload.city else None,
        state=payload.state.strip() if payload.state else None,
        country=payload.country.strip() if payload.country else None,
        status="target",
        created_by=principal.user_id,
        created_at=now_utc,
        updated_at=now_utc,
        deleted_at=None,
    )

    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        try:
            ctx.add(new_account)
            await ctx.flush()
            await ctx.refresh(new_account)
        except Exception as error:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="account_creation_failed"
            ) from error

    return _model_to_account(new_account)


@router.get("/accounts", response_model=list[Account])
async def list_accounts(
    campaign_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[Account]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(AccountModel).where(AccountModel.workspace_id == principal.workspace_id)
        
        if campaign_id:
            stmt = stmt.where(AccountModel.campaign_id == campaign_id)
            
        if status_filter:
            stmt = stmt.where(AccountModel.status == status_filter)
        else:
            stmt = stmt.where(AccountModel.deleted_at.is_(None))
            
        if search:
            search_lower = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    AccountModel.name.ilike(search_lower),
                    AccountModel.domain.ilike(search_lower)
                )
            )
            
        stmt = stmt.offset(offset).limit(limit)
        
        result = await ctx.execute(stmt)
        models = result.scalars().all()
        
        return [_model_to_account(m) for m in models]


@router.get("/accounts/{account_id}", response_model=Account)
async def get_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(AccountModel).where(
            AccountModel.id == account_id,
            AccountModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account_not_found")
            
        return _model_to_account(model)


@router.patch("/accounts/{account_id}", response_model=Account)
async def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(AccountModel).where(
            AccountModel.id == account_id,
            AccountModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account_not_found")
            
        model.updated_at = datetime.now(UTC)
        if payload.name is not None:
            model.name = payload.name.strip()
        if payload.campaign_id is not None:
            model.campaign_id = payload.campaign_id
        if payload.domain is not None:
            model.domain = payload.domain.strip().lower() if payload.domain else None
        if payload.industry is not None:
            model.industry = payload.industry.strip() if payload.industry else None
        if payload.employee_count is not None:
            model.employee_count = payload.employee_count.strip() if payload.employee_count else None
        if payload.city is not None:
            model.city = payload.city.strip() if payload.city else None
        if payload.state is not None:
            model.state = payload.state.strip() if payload.state else None
        if payload.country is not None:
            model.country = payload.country.strip() if payload.country else None
        if payload.status is not None:
            model.status = payload.status
            
        try:
            await ctx.flush()
            await ctx.refresh(model)
        except Exception as error:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="account_update_failed"
            ) from error
            
        return _model_to_account(model)


@router.delete("/accounts/{account_id}", response_model=Account)
async def delete_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(AccountModel).where(
            AccountModel.id == account_id,
            AccountModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account_not_found")
            
        now_utc = datetime.now(UTC)
        model.status = "archived"
        model.deleted_at = now_utc
        model.updated_at = now_utc
        
        await ctx.flush()
        await ctx.refresh(model)
        return _model_to_account(model)


@router.post("/accounts/{account_id}/actions/archive", response_model=Account)
async def archive_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    return await delete_account(account_id, principal=principal, session=session)


@router.post("/accounts/{account_id}/actions/restore", response_model=Account)
async def restore_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(AccountModel).where(
            AccountModel.id == account_id,
            AccountModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account_not_found")
            
        model.status = "target"
        model.deleted_at = None
        model.updated_at = datetime.now(UTC)
        
        await ctx.flush()
        await ctx.refresh(model)
        return _model_to_account(model)
