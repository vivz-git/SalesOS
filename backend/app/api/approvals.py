from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.outreach import OutreachDraft
from app.auth import Principal, get_current_principal
from app.db import get_db_session, tenant_transaction_context
from app.models import (
    AccountModel,
    ApprovalDecisionModel,
    AuditEventModel,
    CampaignModel,
    ContactModel,
    OutreachDraftModel,
)

router = APIRouter(prefix="/v1", tags=["approvals"])


class ApprovalAuditRecord(BaseModel):
    id: UUID
    workspace_id: UUID
    draft_id: UUID
    version_id: UUID | None = None
    version_number: int
    reviewer_id: UUID
    reviewer_email: str
    decision: Literal["approved", "rejected", "returned_to_draft"]
    notes: str | None = None
    created_at: datetime


class ApprovalItemDetail(BaseModel):
    draft: OutreachDraft
    campaign_name: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    account_name: str | None = None
    recent_history: list[ApprovalAuditRecord] = Field(default_factory=list)


class ApprovalDecisionPayload(BaseModel):
    decision: Literal["approved", "rejected", "returned_to_draft"]
    notes: str | None = Field(default=None, max_length=2000)


class ApprovalActionPayload(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


def _model_to_draft(m: OutreachDraftModel) -> OutreachDraft:
    return OutreachDraft(
        id=m.id,
        workspace_id=m.workspace_id,
        campaign_id=m.campaign_id,
        contact_id=m.contact_id,
        sequence_enrollment_id=m.sequence_enrollment_id,
        sequence_step_number=m.sequence_step_number,
        research_brief_id=m.research_brief_id,
        current_version_id=m.current_version_id,
        current_version_number=m.current_version_number,
        current_subject=m.current_subject,
        current_body=m.current_body,
        status=cast(Any, m.status),
        created_by=m.created_by,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
    )


async def _execute_approval_decision(
    draft_id: UUID,
    decision: Literal["approved", "rejected", "returned_to_draft"],
    notes: str | None,
    principal: Principal,
    session: AsyncSession,
) -> ApprovalAuditRecord:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        # 1. Lock the draft FOR UPDATE
        stmt = (
            select(OutreachDraftModel)
            .filter_by(id=draft_id, workspace_id=principal.workspace_id)
            .with_for_update()
        )
        result = await session.execute(stmt)
        draft_model = result.scalar_one_or_none()

        if not draft_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")

        # 2. Verify state
        if draft_model.status != "ready_for_review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"cannot_decide_on_draft_in_{draft_model.status}_state",
            )

        # 3. Transition state
        if decision == "approved":
            draft_model.status = "approved"
        elif decision == "rejected":
            draft_model.status = "rejected"
        elif decision == "returned_to_draft":
            draft_model.status = "draft"

        now_dt = datetime.now(UTC)
        draft_model.updated_at = now_dt

        # 4. Create Decision Record
        decision_id = uuid4()
        decision_model = ApprovalDecisionModel(
            id=decision_id,
            workspace_id=principal.workspace_id,
            draft_id=draft_model.id,
            version_id=draft_model.current_version_id,
            version_number=draft_model.current_version_number,
            reviewer_id=principal.user_id,
            decision=decision,
            notes=notes,
            created_at=now_dt,
        )
        session.add(decision_model)

        # 5. Create Audit Event
        audit_id = uuid4()
        audit_model = AuditEventModel(
            id=audit_id,
            workspace_id=principal.workspace_id,
            actor_type="user",
            actor_id=principal.user_id,
            action=f"outreach_draft.{decision}",
            resource_type="outreach_draft",
            resource_id=draft_model.id,
            metadata_payload={
                "version_id": str(draft_model.current_version_id)
                if draft_model.current_version_id
                else None,
                "version_number": draft_model.current_version_number,
                "decision": decision,
                "review_notes": notes,
                "reviewer_email": principal.email,
            },
            created_at=now_dt,
        )
        session.add(audit_model)

        # 6. Flush transaction
        await session.flush()
        await session.refresh(decision_model)

        return ApprovalAuditRecord(
            id=decision_model.id,
            workspace_id=decision_model.workspace_id,
            draft_id=decision_model.draft_id,
            version_id=decision_model.version_id,
            version_number=decision_model.version_number,
            reviewer_id=principal.user_id,
            reviewer_email=principal.email or "unknown",
            decision=cast(Any, decision_model.decision),
            notes=decision_model.notes,
            created_at=decision_model.created_at,
        )


@router.get("/approvals", response_model=list[OutreachDraft])
@router.get("/approvals/queue", response_model=list[OutreachDraft])
async def list_approval_queue(
    status_filter: str = Query("ready_for_review", alias="status"),
    campaign_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[OutreachDraft]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        stmt = select(OutreachDraftModel).filter_by(workspace_id=principal.workspace_id)
        if status_filter != "all":
            stmt = stmt.filter_by(status=status_filter)
        if campaign_id:
            stmt = stmt.filter_by(campaign_id=campaign_id)

        stmt = stmt.order_by(OutreachDraftModel.updated_at.asc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        models = result.scalars().all()

        return [_model_to_draft(m) for m in models]


@router.get("/approvals/{draft_id}", response_model=ApprovalItemDetail)
@router.get("/approvals/items/{draft_id}", response_model=ApprovalItemDetail)
async def get_approval_item_detail(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalItemDetail:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        draft_model = await session.get(OutreachDraftModel, draft_id)
        if not draft_model or str(draft_model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")

        draft = _model_to_draft(draft_model)

        campaign = await session.get(CampaignModel, draft.campaign_id)
        contact = await session.get(ContactModel, draft.contact_id)
        account = None
        if contact and contact.account_id:
            account = await session.get(AccountModel, contact.account_id)

        # Load history
        hist_stmt = (
            select(ApprovalDecisionModel)
            .filter_by(draft_id=draft.id, workspace_id=principal.workspace_id)
            .order_by(ApprovalDecisionModel.created_at.desc())
        )
        hist_result = await session.execute(hist_stmt)
        hist_models = hist_result.scalars().all()

        history: list[ApprovalAuditRecord] = []
        for hm in hist_models:
            history.append(
                ApprovalAuditRecord(
                    id=hm.id,
                    workspace_id=hm.workspace_id,
                    draft_id=hm.draft_id,
                    version_id=hm.version_id,
                    version_number=hm.version_number,
                    reviewer_id=hm.reviewer_id or principal.user_id,
                    reviewer_email=principal.email or "unknown",
                    decision=cast(Any, hm.decision),
                    notes=hm.notes,
                    created_at=hm.created_at,
                )
            )

        return ApprovalItemDetail(
            draft=draft,
            campaign_name=campaign.name if campaign else None,
            contact_name=f"{contact.first_name} {contact.last_name}".strip() if contact else None,
            contact_email=contact.email if contact else None,
            account_name=account.name if account else None,
            recent_history=history,
        )


@router.post("/approvals/items/{draft_id}/decision", response_model=ApprovalAuditRecord)
async def submit_approval_decision(
    draft_id: UUID,
    payload: ApprovalDecisionPayload,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalAuditRecord:
    return await _execute_approval_decision(
        draft_id=draft_id,
        decision=payload.decision,
        notes=payload.notes,
        principal=principal,
        session=session,
    )


@router.post("/approvals/{draft_id}/actions/approve", response_model=ApprovalAuditRecord)
async def approve_draft_action(
    draft_id: UUID,
    payload: ApprovalActionPayload | None = None,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalAuditRecord:
    notes = payload.notes if payload else None
    return await _execute_approval_decision(
        draft_id=draft_id,
        decision="approved",
        notes=notes,
        principal=principal,
        session=session,
    )


@router.post("/approvals/{draft_id}/actions/reject", response_model=ApprovalAuditRecord)
async def reject_draft_action(
    draft_id: UUID,
    payload: ApprovalActionPayload | None = None,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalAuditRecord:
    notes = payload.notes if payload else None
    return await _execute_approval_decision(
        draft_id=draft_id,
        decision="rejected",
        notes=notes,
        principal=principal,
        session=session,
    )


@router.post("/approvals/{draft_id}/actions/return-to-draft", response_model=ApprovalAuditRecord)
@router.post("/approvals/{draft_id}/actions/return_to_draft", response_model=ApprovalAuditRecord)
async def return_draft_action(
    draft_id: UUID,
    payload: ApprovalActionPayload | None = None,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalAuditRecord:
    notes = payload.notes if payload else None
    return await _execute_approval_decision(
        draft_id=draft_id,
        decision="returned_to_draft",
        notes=notes,
        principal=principal,
        session=session,
    )
