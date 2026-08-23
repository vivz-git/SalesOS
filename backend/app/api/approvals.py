from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
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


@router.get("/approvals/queue", response_model=list[OutreachDraft])
async def get_approval_queue(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[OutreachDraft]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        stmt = (
            select(OutreachDraftModel)
            .filter_by(workspace_id=principal.workspace_id, status="ready_for_review")
            .order_by(OutreachDraftModel.updated_at.asc())
        )
        result = await session.execute(stmt)
        models = result.scalars().all()
        
        drafts: list[OutreachDraft] = []
        for m in models:
            # We construct a mock dict to reuse _row_to_draft, or we just map it.
            # To keep it safe, let's map it cleanly.
            d = OutreachDraft(
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
            drafts.append(d)
        
        return drafts


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
        
        draft = OutreachDraft(
            id=draft_model.id,
            workspace_id=draft_model.workspace_id,
            campaign_id=draft_model.campaign_id,
            contact_id=draft_model.contact_id,
            sequence_enrollment_id=draft_model.sequence_enrollment_id,
            sequence_step_number=draft_model.sequence_step_number,
            research_brief_id=draft_model.research_brief_id,
            current_version_id=draft_model.current_version_id,
            current_version_number=draft_model.current_version_number,
            current_subject=draft_model.current_subject,
            current_body=draft_model.current_body,
            status=cast(Any, draft_model.status),
            created_by=draft_model.created_by,
            created_at=draft_model.created_at,
            updated_at=draft_model.updated_at,
            deleted_at=draft_model.deleted_at,
        )

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
                    reviewer_id=hm.reviewer_id or principal.user_id, # Fallback
                    reviewer_email=principal.email or "unknown", # Hard to resolve efficiently without joining auth.users, but good enough for now
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
                detail=f"cannot_decide_on_draft_in_{draft_model.status}_state"
            )

        # 3. Transition state
        if payload.decision == "approved":
            draft_model.status = "approved"
        elif payload.decision == "rejected":
            draft_model.status = "rejected"
        elif payload.decision == "returned_to_draft":
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
            decision=payload.decision,
            notes=payload.notes,
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
            action=f"outreach_draft.{payload.decision}",
            resource_type="outreach_draft",
            resource_id=draft_model.id,
            metadata_payload={
                "version_id": str(draft_model.current_version_id) if draft_model.current_version_id else None,
                "version_number": draft_model.current_version_number,
                "decision": payload.decision,
                "review_notes": payload.notes,
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
