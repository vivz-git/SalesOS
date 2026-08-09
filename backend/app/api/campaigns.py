from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal, get_current_principal
from app.db import get_db_session, tenant_transaction_context
from app.models import CampaignModel

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


def _model_to_campaign(model: CampaignModel) -> Campaign:
    return Campaign(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        description=model.description,
        target_segment=model.target_segment,
        icp_definition=model.icp_definition,
        status=cast(CampaignStatus, model.status),
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


@router.post("/campaigns", response_model=Campaign, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Campaign:
    now_utc = datetime.now(UTC)
    campaign_id = uuid4()
    
    new_campaign = CampaignModel(
        id=campaign_id,
        workspace_id=principal.workspace_id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        target_segment=payload.target_segment.strip() if payload.target_segment else None,
        icp_definition=payload.icp_definition.strip() if payload.icp_definition else None,
        status="draft",
        created_by=principal.user_id,
        created_at=now_utc,
        updated_at=now_utc,
        deleted_at=None,
    )

    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        try:
            ctx.add(new_campaign)
            await ctx.flush()
            await ctx.refresh(new_campaign)
        except Exception as error:
            
            print(f"CAMPAIGN INSERT ERROR: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="campaign_creation_failed"
            ) from error

    return _model_to_campaign(new_campaign)


@router.get("/campaigns", response_model=list[Campaign])
async def list_campaigns(
    status_filter: str | None = Query(default=None, alias="status"),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[Campaign]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(CampaignModel).where(CampaignModel.workspace_id == principal.workspace_id)
        if status_filter:
            stmt = stmt.where(CampaignModel.status == status_filter)
        
        result = await ctx.execute(stmt)
        models = result.scalars().all()
        
        campaigns = []
        for m in models:
            if status_filter != "archived" and m.deleted_at is not None:
                continue
            campaigns.append(_model_to_campaign(m))
            
        return campaigns


@router.get("/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Campaign:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(CampaignModel).where(
            CampaignModel.id == campaign_id,
            CampaignModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")
            
        return _model_to_campaign(model)


@router.patch("/campaigns/{campaign_id}", response_model=Campaign)
async def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Campaign:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(CampaignModel).where(
            CampaignModel.id == campaign_id,
            CampaignModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")
            
        model.updated_at = datetime.now(UTC)
        if payload.name is not None:
            model.name = payload.name.strip()
        if payload.description is not None:
            model.description = payload.description.strip() if payload.description else None
        if payload.target_segment is not None:
            model.target_segment = payload.target_segment.strip() if payload.target_segment else None
        if payload.icp_definition is not None:
            model.icp_definition = payload.icp_definition.strip() if payload.icp_definition else None
            
        try:
            await ctx.flush()
            await ctx.refresh(model)
        except Exception as error:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="campaign_update_failed"
            ) from error
            
        return _model_to_campaign(model)


@router.delete("/campaigns/{campaign_id}", response_model=Campaign)
async def delete_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Campaign:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(CampaignModel).where(
            CampaignModel.id == campaign_id,
            CampaignModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")
            
        now_utc = datetime.now(UTC)
        model.status = "archived"
        model.deleted_at = now_utc
        model.updated_at = now_utc
        
        await ctx.flush()
        await ctx.refresh(model)
        return _model_to_campaign(model)


@router.post("/campaigns/{campaign_id}/actions/activate", response_model=Campaign)
async def activate_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Campaign:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(CampaignModel).where(
            CampaignModel.id == campaign_id,
            CampaignModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")
            
        model.status = "active"
        model.updated_at = datetime.now(UTC)
        
        await ctx.flush()
        await ctx.refresh(model)
        return _model_to_campaign(model)


@router.post("/campaigns/{campaign_id}/actions/pause", response_model=Campaign)
async def pause_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Campaign:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(CampaignModel).where(
            CampaignModel.id == campaign_id,
            CampaignModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")
            
        model.status = "paused"
        model.updated_at = datetime.now(UTC)
        
        await ctx.flush()
        await ctx.refresh(model)
        return _model_to_campaign(model)


@router.post("/campaigns/{campaign_id}/actions/archive", response_model=Campaign)
async def archive_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Campaign:
    return await delete_campaign(campaign_id, principal=principal, session=session)


@router.post("/campaigns/{campaign_id}/actions/restore", response_model=Campaign)
async def restore_campaign(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Campaign:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id) as ctx:
        stmt = select(CampaignModel).where(
            CampaignModel.id == campaign_id,
            CampaignModel.workspace_id == principal.workspace_id
        )
        result = await ctx.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")
            
        model.status = "draft"
        model.deleted_at = None
        model.updated_at = datetime.now(UTC)
        
        await ctx.flush()
        await ctx.refresh(model)
        return _model_to_campaign(model)
