from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal, get_current_principal
from app.db import get_db_session, tenant_transaction_context
from app.models import JobModel, ResearchBriefModel, ResearchSourceModel

router = APIRouter(prefix="/v1", tags=["research"])

ResearchStatus = Literal["pending", "in_progress", "completed", "failed"]
JobStatus = Literal["queued", "running", "completed", "failed"]


class ResearchBrief(BaseModel):
    id: UUID
    workspace_id: UUID
    account_id: UUID
    contact_id: UUID | None = None
    summary: str | None = None
    key_findings: list[str] | None = None
    status: ResearchStatus = "pending"
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_reason: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    generated_at: datetime | None = None
    token_usage: int | None = None
    estimated_cost: float | None = None
    duration_ms: int | None = None
    created_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class ResearchBriefCreate(BaseModel):
    account_id: UUID
    contact_id: UUID | None = None
    summary: str | None = Field(default=None, max_length=2000)
    key_findings: list[str] | None = None


class ResearchBriefUpdate(BaseModel):
    summary: str | None = Field(default=None, max_length=2000)
    key_findings: list[str] | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_reason: str | None = Field(default=None, max_length=1000)
    status: ResearchStatus | None = None


class ResearchSource(BaseModel):
    id: UUID
    workspace_id: UUID
    brief_id: UUID
    url: str | None = None
    title: str | None = None
    source_type: str = "website"
    snippet: str | None = None
    confidence: float = 1.0
    raw_content_hash: str | None = None
    retrieved_at: datetime | None = None


class ResearchSourceCreate(BaseModel):
    url: str | None = Field(default=None, max_length=500)
    title: str | None = Field(default=None, max_length=255)
    source_type: str = Field(default="website", max_length=50)
    snippet: str | None = Field(default=None, max_length=2000)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    raw_content_hash: str | None = Field(default=None, max_length=128)


class ResearchJob(BaseModel):
    id: UUID
    workspace_id: UUID
    brief_id: UUID
    status: JobStatus = "queued"
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


def _row_to_brief(row: ResearchBriefModel) -> ResearchBrief:
    key_findings_raw = row.key_findings
    key_findings: list[str] | None = None
    if isinstance(key_findings_raw, list):
        key_findings = [str(item) for item in key_findings_raw]

    return ResearchBrief(
        id=row.id,
        workspace_id=row.workspace_id,
        account_id=row.account_id,
        contact_id=row.contact_id,
        summary=row.summary,
        key_findings=key_findings,
        status=cast(ResearchStatus, row.status),
        confidence_score=row.confidence_score,
        confidence_reason=row.confidence_reason,
        provider=row.provider,
        model=row.model,
        prompt_version=row.prompt_version,
        generated_at=row.generated_at,
        token_usage=row.token_usage,
        estimated_cost=row.estimated_cost,
        duration_ms=row.duration_ms,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
        deleted_at=row.deleted_at,
    )


def _row_to_source(row: ResearchSourceModel) -> ResearchSource:
    return ResearchSource(
        id=row.id,
        workspace_id=row.workspace_id,
        brief_id=row.brief_id,
        url=row.url,
        title=row.title,
        source_type=row.source_type,
        snippet=row.snippet,
        confidence=row.confidence or 1.0,
        raw_content_hash=row.raw_content_hash,
        retrieved_at=row.retrieved_at,
    )


@router.post("/research/briefs", response_model=ResearchBrief, status_code=status.HTTP_201_CREATED)
async def create_research_brief(
    payload: ResearchBriefCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchBrief:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        brief_id = uuid4()
        now_dt = datetime.now(UTC)

        model = ResearchBriefModel(
            id=brief_id,
            workspace_id=principal.workspace_id,
            account_id=payload.account_id,
            contact_id=payload.contact_id,
            summary=payload.summary.strip() if payload.summary else None,
            key_findings=payload.key_findings or [],
            status="pending",
            created_by=principal.user_id,
            created_at=now_dt,
            updated_at=now_dt,
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        
        return _row_to_brief(model)


@router.get("/research/briefs", response_model=list[ResearchBrief])
async def list_research_briefs(
    account_id: UUID | None = Query(default=None),
    contact_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[ResearchBrief]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        stmt = select(ResearchBriefModel).filter_by(workspace_id=principal.workspace_id)
        
        if account_id:
            stmt = stmt.filter_by(account_id=account_id)
        if contact_id:
            stmt = stmt.filter_by(contact_id=contact_id)
        if status_filter:
            stmt = stmt.filter_by(status=status_filter)
        else:
            stmt = stmt.filter(ResearchBriefModel.deleted_at.is_(None))

        stmt = stmt.order_by(ResearchBriefModel.created_at.desc()).offset(offset).limit(limit)
        
        result = await session.execute(stmt)
        models = result.scalars().all()
        return [_row_to_brief(m) for m in models]


@router.get("/research/briefs/{brief_id}", response_model=ResearchBrief)
async def get_research_brief(
    brief_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchBrief:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(ResearchBriefModel, brief_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="brief_not_found")
        return _row_to_brief(model)


@router.patch("/research/briefs/{brief_id}", response_model=ResearchBrief)
async def update_research_brief(
    brief_id: UUID,
    payload: ResearchBriefUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchBrief:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(ResearchBriefModel, brief_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="brief_not_found")

        model.updated_at = datetime.now(UTC)
        if payload.summary is not None:
            model.summary = payload.summary.strip() if payload.summary else None
        if payload.key_findings is not None:
            model.key_findings = cast(Any, payload.key_findings)
        if payload.confidence_score is not None:
            model.confidence_score = payload.confidence_score
        if payload.confidence_reason is not None:
            model.confidence_reason = payload.confidence_reason.strip() if payload.confidence_reason else None
        if payload.status is not None:
            model.status = payload.status

        await session.commit()
        await session.refresh(model)
        return _row_to_brief(model)


@router.delete("/research/briefs/{brief_id}", response_model=ResearchBrief)
async def delete_research_brief(
    brief_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchBrief:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(ResearchBriefModel, brief_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="brief_not_found")

        now_dt = datetime.now(UTC)
        model.status = "failed"
        model.deleted_at = now_dt
        model.updated_at = now_dt
        
        await session.commit()
        await session.refresh(model)
        return _row_to_brief(model)


@router.post("/research/briefs/{brief_id}/sources", response_model=ResearchSource, status_code=status.HTTP_201_CREATED)
async def append_research_source(
    brief_id: UUID,
    payload: ResearchSourceCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchSource:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        brief = await session.get(ResearchBriefModel, brief_id)
        if not brief or str(brief.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="brief_not_found")

        source_id = uuid4()
        model = ResearchSourceModel(
            id=source_id,
            workspace_id=principal.workspace_id,
            brief_id=brief.id,
            url=payload.url.strip() if payload.url else None,
            title=payload.title.strip() if payload.title else None,
            source_type=payload.source_type,
            snippet=payload.snippet.strip() if payload.snippet else None,
            confidence=payload.confidence,
            raw_content_hash=payload.raw_content_hash.strip() if payload.raw_content_hash else None,
            retrieved_at=datetime.now(UTC),
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return _row_to_source(model)


@router.get("/research/briefs/{brief_id}/sources", response_model=list[ResearchSource])
async def list_research_sources(
    brief_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[ResearchSource]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        brief = await session.get(ResearchBriefModel, brief_id)
        if not brief or str(brief.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="brief_not_found")

        stmt = select(ResearchSourceModel).filter_by(brief_id=brief_id, workspace_id=principal.workspace_id)
        result = await session.execute(stmt)
        models = result.scalars().all()
        return [_row_to_source(m) for m in models]


@router.post("/research/briefs/{brief_id}/actions/trigger", response_model=ResearchJob)
async def trigger_research_job(
    brief_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchJob:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        brief = await session.get(ResearchBriefModel, brief_id)
        if not brief or str(brief.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="brief_not_found")

        now_dt = datetime.now(UTC)
        
        # Update brief status to in_progress
        brief.status = "in_progress"
        brief.updated_at = now_dt

        job_id = uuid4()
        job_model = JobModel(
            id=job_id,
            workspace_id=principal.workspace_id,
            job_type="research_generation",
            payload={"brief_id": str(brief.id)},
            status="pending",
            attempts=0,
            max_attempts=3,
            available_at=now_dt,
            created_at=now_dt,
            updated_at=now_dt,
        )
        session.add(job_model)
        await session.commit()

        return ResearchJob(
            id=job_id,
            workspace_id=principal.workspace_id,
            brief_id=brief.id,
            status="queued",
            created_at=now_dt,
        )
