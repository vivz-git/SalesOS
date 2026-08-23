from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.groq_provider import GroqLLMProvider
from app.adapters.llm_provider import LLMGenerationRequest, LLMProviderInterface
from app.auth import Principal, get_current_principal
from app.core.config import Settings, get_settings
from app.db import get_db_session, tenant_transaction_context
from app.models import (
    AccountModel,
    CampaignModel,
    ContactModel,
    DraftVersionModel,
    OutreachDraftModel,
    ResearchBriefModel,
    ResearchSourceModel,
)

router = APIRouter(prefix="/v1", tags=["outreach"])

DraftStatus = Literal["draft", "ready_for_review", "approved", "rejected", "superseded", "archived"]
GenerationSource = Literal["human", "ai_generated", "template", "ai_assisted"]


class DraftVersion(BaseModel):
    id: UUID
    workspace_id: UUID
    draft_id: UUID
    version_number: int
    subject: str | None = None
    body: str
    generation_source: GenerationSource = "human"
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    research_brief_id: UUID | None = None
    research_brief_version: int | None = None
    evidence_references: list[dict[str, Any]] | None = None
    created_by: UUID | None = None
    created_at: datetime | None = None


class OutreachDraft(BaseModel):
    id: UUID
    workspace_id: UUID
    campaign_id: UUID
    contact_id: UUID
    sequence_enrollment_id: UUID | None = None
    sequence_step_number: int | None = None
    research_brief_id: UUID | None = None
    current_version_id: UUID | None = None
    current_version_number: int = 1
    current_subject: str | None = None
    current_body: str | None = None
    status: DraftStatus = "draft"
    created_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    versions: list[DraftVersion] | None = None


class OutreachDraftCreate(BaseModel):
    campaign_id: UUID
    contact_id: UUID
    sequence_enrollment_id: UUID | None = None
    sequence_step_number: int | None = None
    research_brief_id: UUID | None = None
    subject: str | None = Field(default=None, max_length=255)
    body: str = Field(..., min_length=1, max_length=10000)
    generation_source: GenerationSource = Field(default="human")
    provider: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    prompt_version: str | None = Field(default=None, max_length=50)
    evidence_references: list[dict[str, Any]] | None = None


class OutreachDraftRevise(BaseModel):
    subject: str | None = Field(default=None, max_length=255)
    body: str = Field(..., min_length=1, max_length=10000)
    generation_source: GenerationSource = Field(default="human")
    provider: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    prompt_version: str | None = Field(default=None, max_length=50)
    research_brief_id: UUID | None = None
    evidence_references: list[dict[str, Any]] | None = None


def _row_to_version(model: DraftVersionModel) -> DraftVersion:
    evidence_references: list[dict[str, Any]] | None = None
    if isinstance(model.evidence_references, list):
        evidence_references = [item for item in model.evidence_references if isinstance(item, dict)]

    return DraftVersion(
        id=model.id,
        workspace_id=model.workspace_id,
        draft_id=model.draft_id,
        version_number=model.version_number,
        subject=model.subject,
        body=model.body,
        generation_source=cast(GenerationSource, model.generation_source),
        provider=model.provider,
        model=model.model,
        prompt_version=model.prompt_version,
        research_brief_id=model.research_brief_id,
        research_brief_version=model.research_brief_version,
        evidence_references=evidence_references,
        created_by=model.created_by,
        created_at=model.created_at,
    )


def _row_to_draft(model: OutreachDraftModel, versions: list[DraftVersion] | None = None) -> OutreachDraft:
    return OutreachDraft(
        id=model.id,
        workspace_id=model.workspace_id,
        campaign_id=model.campaign_id,
        contact_id=model.contact_id,
        sequence_enrollment_id=model.sequence_enrollment_id,
        sequence_step_number=model.sequence_step_number,
        research_brief_id=model.research_brief_id,
        current_version_id=model.current_version_id,
        current_version_number=model.current_version_number,
        current_subject=model.current_subject,
        current_body=model.current_body,
        status=cast(DraftStatus, model.status),
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
        versions=versions,
    )


async def create_outreach_draft_orm(
    session: AsyncSession,
    payload: OutreachDraftCreate,
    principal: Principal,
) -> OutreachDraft:
    draft_id = uuid4()
    version_id = uuid4()
    now_dt = datetime.now(UTC)

    draft_model = OutreachDraftModel(
        id=draft_id,
        workspace_id=principal.workspace_id,
        campaign_id=payload.campaign_id,
        contact_id=payload.contact_id,
        sequence_enrollment_id=payload.sequence_enrollment_id,
        sequence_step_number=payload.sequence_step_number,
        research_brief_id=payload.research_brief_id,
        current_version_id=None,  # Set to None initially to avoid circular dependency, then update
        current_version_number=1,
        current_subject=payload.subject.strip() if payload.subject else None,
        current_body=payload.body.strip(),
        status="draft",
        created_by=principal.user_id,
        created_at=now_dt,
        updated_at=now_dt,
    )
    session.add(draft_model)
    await session.flush()

    version_model = DraftVersionModel(
        id=version_id,
        workspace_id=principal.workspace_id,
        draft_id=draft_id,
        version_number=1,
        subject=payload.subject.strip() if payload.subject else None,
        body=payload.body.strip(),
        generation_source=payload.generation_source,
        provider=payload.provider,
        model=payload.model,
        prompt_version=payload.prompt_version,
        research_brief_id=payload.research_brief_id,
        research_brief_version=1 if payload.research_brief_id else None,
        evidence_references=payload.evidence_references or [],
        created_by=principal.user_id,
        created_at=now_dt,
    )
    session.add(version_model)
    await session.flush()

    draft_model.current_version_id = version_id
    
    # We must explicitly return the constructed ORM objects. 
    # Because they're already added to session, we can just use them.
    v = _row_to_version(version_model)
    return _row_to_draft(draft_model, versions=[v])


@router.post("/outreach/drafts", response_model=OutreachDraft, status_code=status.HTTP_201_CREATED)
async def create_outreach_draft(
    payload: OutreachDraftCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        draft = await create_outreach_draft_orm(session, payload, principal)
        return draft


@router.get("/outreach/drafts", response_model=list[OutreachDraft])
async def list_outreach_drafts(
    campaign_id: UUID | None = Query(default=None),
    contact_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[OutreachDraft]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        stmt = select(OutreachDraftModel).filter_by(workspace_id=principal.workspace_id)
        if campaign_id:
            stmt = stmt.filter_by(campaign_id=campaign_id)
        if contact_id:
            stmt = stmt.filter_by(contact_id=contact_id)
        if status_filter:
            stmt = stmt.filter_by(status=status_filter)
        if status_filter != "archived":
            stmt = stmt.filter(OutreachDraftModel.deleted_at.is_(None))

        stmt = stmt.order_by(OutreachDraftModel.updated_at.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        models = result.scalars().all()
        return [_row_to_draft(m) for m in models]


@router.get("/outreach/drafts/{draft_id}", response_model=OutreachDraft)
async def get_outreach_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")
        
        # fetch versions
        stmt = select(DraftVersionModel).filter_by(draft_id=draft_id).order_by(DraftVersionModel.version_number.asc())
        v_result = await session.execute(stmt)
        v_models = v_result.scalars().all()
        
        versions = [_row_to_version(v) for v in v_models]
        return _row_to_draft(model, versions=versions)


@router.get("/outreach/drafts/{draft_id}/versions", response_model=list[DraftVersion])
async def list_draft_versions(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[DraftVersion]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")

        stmt = select(DraftVersionModel).filter_by(draft_id=draft_id).order_by(DraftVersionModel.version_number.asc())
        v_result = await session.execute(stmt)
        v_models = v_result.scalars().all()
        return [_row_to_version(v) for v in v_models]


@router.post("/outreach/drafts/{draft_id}/actions/revise", response_model=OutreachDraft)
async def revise_outreach_draft(
    draft_id: UUID,
    payload: OutreachDraftRevise,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")
            
        if model.status in ("archived", "approved"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"cannot_revise_draft_in_{model.status}_state",
            )

        version_id = uuid4()
        next_version_num = model.current_version_number + 1
        now_dt = datetime.now(UTC)

        rb_id = payload.research_brief_id or model.research_brief_id

        version_model = DraftVersionModel(
            id=version_id,
            workspace_id=principal.workspace_id,
            draft_id=draft_id,
            version_number=next_version_num,
            subject=payload.subject.strip() if payload.subject else None,
            body=payload.body.strip(),
            generation_source=payload.generation_source,
            provider=payload.provider,
            model=payload.model,
            prompt_version=payload.prompt_version,
            research_brief_id=rb_id,
            research_brief_version=1 if rb_id else None,
            evidence_references=payload.evidence_references or [],
            created_by=principal.user_id,
            created_at=now_dt,
        )
        session.add(version_model)

        model.current_version_id = version_id
        model.current_version_number = next_version_num
        model.current_subject = payload.subject.strip() if payload.subject else None
        model.current_body = payload.body.strip()
        model.updated_at = now_dt

        await session.flush()
        await session.refresh(model)

        # return full draft
        stmt = select(DraftVersionModel).filter_by(draft_id=draft_id).order_by(DraftVersionModel.version_number.asc())
        v_result = await session.execute(stmt)
        versions = [_row_to_version(v) for v in v_result.scalars().all()]
        return _row_to_draft(model, versions=versions)


@router.post("/outreach/drafts/{draft_id}/actions/submit-review", response_model=OutreachDraft)
async def submit_draft_for_review(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")
            
        if model.status not in ("draft", "rejected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"cannot_submit_review_for_status_{model.status}",
            )

        model.status = "ready_for_review"
        model.updated_at = datetime.now(UTC)
        await session.flush()
        await session.refresh(model)
        return _row_to_draft(model)


@router.post("/outreach/drafts/{draft_id}/actions/approve", response_model=OutreachDraft)
async def approve_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    # Actually, approval logic is primarily in /approvals, but this endpoint exists.
    # To avoid rewriting logic, just use the ORM simple status transition.
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")
            
        if model.status != "ready_for_review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"cannot_approve_draft_in_{model.status}_state",
            )

        model.status = "approved"
        model.updated_at = datetime.now(UTC)
        await session.flush()
        await session.refresh(model)
        return _row_to_draft(model)


@router.post("/outreach/drafts/{draft_id}/actions/reject", response_model=OutreachDraft)
async def reject_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")
            
        if model.status != "ready_for_review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"cannot_reject_draft_in_{model.status}_state",
            )

        model.status = "rejected"
        model.updated_at = datetime.now(UTC)
        await session.flush()
        await session.refresh(model)
        return _row_to_draft(model)


@router.post("/outreach/drafts/{draft_id}/actions/return-to-draft", response_model=OutreachDraft)
async def return_draft_to_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")
            
        if model.status not in ("ready_for_review", "rejected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"cannot_return_draft_to_draft_in_{model.status}_state",
            )

        model.status = "draft"
        model.updated_at = datetime.now(UTC)
        await session.flush()
        await session.refresh(model)
        return _row_to_draft(model)


@router.post("/outreach/drafts/{draft_id}/actions/archive", response_model=OutreachDraft)
async def archive_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")

        now_dt = datetime.now(UTC)
        model.status = "archived"
        model.deleted_at = now_dt
        model.updated_at = now_dt
        await session.flush()
        await session.refresh(model)
        return _row_to_draft(model)


@router.delete("/outreach/drafts/{draft_id}", response_model=OutreachDraft)
async def delete_outreach_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    return await archive_draft(draft_id, principal=principal, session=session)


class OutreachGenerationJob(BaseModel):
    id: UUID
    workspace_id: UUID
    draft_id: UUID
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    generated_version_number: int | None = None
    draft: OutreachDraft | None = None


def get_llm_provider(settings: Settings = Depends(get_settings)) -> LLMProviderInterface:
    return GroqLLMProvider(api_key=settings.groq_api_key, model=settings.groq_model)


@router.post("/outreach/drafts/{draft_id}/actions/generate", response_model=OutreachDraft)
async def generate_outreach_draft_action(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
    llm_provider: LLMProviderInterface = Depends(get_llm_provider),
) -> OutreachDraft:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(OutreachDraftModel, draft_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")
            
        if model.status in ("archived", "approved"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"cannot_generate_draft_in_{model.status}_state",
            )

        # 1. Load context
        campaign = await session.get(CampaignModel, model.campaign_id)
        contact = await session.get(ContactModel, model.contact_id)
        account = None
        if contact and contact.account_id:
            account = await session.get(AccountModel, contact.account_id)

        brief = None
        sources: list[ResearchSourceModel] = []
        if model.research_brief_id:
            brief = await session.get(ResearchBriefModel, model.research_brief_id)
            stmt = select(ResearchSourceModel).filter_by(brief_id=model.research_brief_id)
            res = await session.execute(stmt)
            sources = list(res.scalars().all())
            
        key_findings: list[str] = []
        if brief and isinstance(brief.key_findings, list):
            key_findings = [str(k) for k in brief.key_findings]
            
        sources_data = []
        for s in sources:
            sources_data.append({
                "url": s.url,
                "title": s.title,
                "source_type": s.source_type,
                "snippet": s.snippet,
                "confidence": s.confidence,
            })

        gen_request = LLMGenerationRequest(
            campaign_name=campaign.name if campaign else "Outreach Campaign",
            campaign_description=campaign.description if campaign else None,
            target_segment=campaign.target_segment if campaign else None,
            icp_definition=campaign.icp_definition if campaign else None,
            contact_name=f"{contact.first_name} {contact.last_name}".strip() if contact else "Prospect",
            contact_title=contact.title if contact else None,
            contact_department=contact.department if contact else None,
            account_name=account.name if account else None,
            account_domain=account.domain if account else None,
            research_summary=brief.summary if brief else None,
            research_key_findings=key_findings,
            research_sources=sources_data,
            prompt_version="v1.0.0",
        )

        try:
            gen_result = llm_provider.generate_outreach_draft(gen_request)
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ai_draft_generation_failed: {error}",
            ) from error

        # Generate new version
        version_id = uuid4()
        next_version_num = model.current_version_number + 1
        now_dt = datetime.now(UTC)

        version_model = DraftVersionModel(
            id=version_id,
            workspace_id=principal.workspace_id,
            draft_id=draft_id,
            version_number=next_version_num,
            subject=gen_result.subject,
            body=gen_result.body,
            generation_source=gen_result.generation_source,
            provider=gen_result.provider,
            model=gen_result.model,
            prompt_version=gen_result.prompt_version,
            research_brief_id=model.research_brief_id,
            research_brief_version=1 if model.research_brief_id else None,
            evidence_references=gen_result.evidence_references,
            created_by=principal.user_id,
            created_at=now_dt,
        )
        session.add(version_model)

        model.current_version_id = version_id
        model.current_version_number = next_version_num
        model.current_subject = gen_result.subject
        model.current_body = gen_result.body
        model.updated_at = now_dt

        await session.flush()
        await session.refresh(model)

        # return full draft
        stmt_v = select(DraftVersionModel).filter_by(draft_id=draft_id).order_by(DraftVersionModel.version_number.asc())
        v_result = await session.execute(stmt_v)
        versions = [_row_to_version(v) for v in v_result.scalars().all()]
        return _row_to_draft(model, versions=versions)
