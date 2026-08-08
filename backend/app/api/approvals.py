from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.outreach import (
    DraftVersion,
    OutreachDraft,
    approve_draft,
    get_outreach_draft,
    reject_draft,
    return_draft_to_draft,
)
from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["approvals"])

# In-memory audit log store for approval audit records when database table is unavailable
_APPROVAL_AUDIT_LOGS: list[dict[str, Any]] = []


class ApprovalActionRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class ApprovalAuditRecord(BaseModel):
    id: UUID
    workspace_id: UUID
    draft_id: UUID
    version_id: UUID | None = None
    version_number: int
    reviewer_id: UUID
    reviewer_email: str | None = None
    decision: Literal["approved", "rejected", "returned_to_draft"]
    notes: str | None = None
    created_at: datetime


class ApprovalItemDetail(BaseModel):
    draft: OutreachDraft
    campaign: dict[str, Any] = Field(default_factory=dict)
    contact: dict[str, Any] = Field(default_factory=dict)
    account: dict[str, Any] = Field(default_factory=dict)
    research_brief: dict[str, Any] = Field(default_factory=dict)
    evidence_sources: list[dict[str, Any]] = Field(default_factory=list)
    current_version: DraftVersion | None = None
    review_history: list[ApprovalAuditRecord] = Field(default_factory=list)


def _get_audit_history(draft_id: UUID, workspace_id: UUID) -> list[ApprovalAuditRecord]:
    records: list[ApprovalAuditRecord] = []
    for log in _APPROVAL_AUDIT_LOGS:
        if str(log.get("draft_id")) == str(draft_id) and str(log.get("workspace_id")) == str(workspace_id):
            records.append(
                ApprovalAuditRecord(
                    id=UUID(str(log["id"])),
                    workspace_id=UUID(str(log["workspace_id"])),
                    draft_id=UUID(str(log["draft_id"])),
                    version_id=UUID(str(log["version_id"])) if log.get("version_id") else None,
                    version_number=int(log.get("version_number", 1)),
                    reviewer_id=UUID(str(log["reviewer_id"])),
                    reviewer_email=cast(str | None, log.get("reviewer_email")),
                    decision=cast(Literal["approved", "rejected", "returned_to_draft"], log["decision"]),
                    notes=cast(str | None, log.get("notes")),
                    created_at=datetime.fromisoformat(str(log["created_at"])),
                )
            )
    return records


def _record_audit_event(
    principal: Principal,
    draft: OutreachDraft,
    decision: Literal["approved", "rejected", "returned_to_draft"],
    notes: str | None,
    settings: Settings,
) -> ApprovalAuditRecord:
    record_id = uuid4()
    now_iso = datetime.now(UTC).isoformat()
    record_dict = {
        "id": str(record_id),
        "workspace_id": str(principal.workspace_id),
        "draft_id": str(draft.id),
        "version_id": str(draft.current_version_id) if draft.current_version_id else None,
        "version_number": draft.current_version_number,
        "reviewer_id": str(principal.user_id),
        "reviewer_email": principal.email,
        "decision": decision,
        "notes": notes,
        "created_at": now_iso,
    }

    # Record in memory
    _APPROVAL_AUDIT_LOGS.append(record_dict)

    # Attempt database audit_events persist if available
    try:
        _, admin_client = _clients(settings)
        audit_event = {
            "id": str(record_id),
            "workspace_id": str(principal.workspace_id),
            "actor_type": "user",
            "actor_id": str(principal.user_id),
            "action": f"outreach_draft.{decision}",
            "resource_type": "outreach_draft",
            "resource_id": str(draft.id),
            "metadata": {
                "version_id": str(draft.current_version_id) if draft.current_version_id else None,
                "version_number": draft.current_version_number,
                "decision": decision,
                "review_notes": notes,
                "reviewer_email": principal.email,
            },
            "created_at": now_iso,
        }
        admin_client.table("audit_events").insert(cast(Any, audit_event)).execute()
    except Exception:
        pass

    return ApprovalAuditRecord(
        id=record_id,
        workspace_id=principal.workspace_id,
        draft_id=draft.id,
        version_id=draft.current_version_id,
        version_number=draft.current_version_number,
        reviewer_id=principal.user_id,
        reviewer_email=principal.email,
        decision=decision,
        notes=notes,
        created_at=datetime.fromisoformat(now_iso),
    )


def _build_approval_item_detail(
    draft: OutreachDraft,
    principal: Principal,
    settings: Settings,
) -> ApprovalItemDetail:
    _, admin_client = _clients(settings)

    # 1. Load Campaign
    campaign_rows = cast(
        list[dict[str, Any]],
        admin_client.table("campaigns")
        .select("*")
        .eq("id", str(draft.campaign_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    campaign = campaign_rows[0] if campaign_rows else {}

    # 2. Load Contact
    contact_rows = cast(
        list[dict[str, Any]],
        admin_client.table("contacts")
        .select("*")
        .eq("id", str(draft.contact_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    contact = contact_rows[0] if contact_rows else {}

    # 3. Load Account if available
    account: dict[str, Any] = {}
    account_id = contact.get("account_id")
    if account_id:
        account_rows = cast(
            list[dict[str, Any]],
            admin_client.table("accounts")
            .select("*")
            .eq("id", str(account_id))
            .eq("workspace_id", str(principal.workspace_id))
            .execute()
            .data
            or [],
        )
        if account_rows:
            account = account_rows[0]

    # 4. Load Research Brief & Sources if available
    brief_data: dict[str, Any] = {}
    sources_data: list[dict[str, Any]] = []
    if draft.research_brief_id:
        brief_rows = cast(
            list[dict[str, Any]],
            admin_client.table("research_briefs")
            .select("*")
            .eq("id", str(draft.research_brief_id))
            .eq("workspace_id", str(principal.workspace_id))
            .execute()
            .data
            or [],
        )
        if brief_rows:
            brief_data = brief_rows[0]

        source_rows = cast(
            list[dict[str, Any]],
            admin_client.table("research_sources")
            .select("*")
            .eq("brief_id", str(draft.research_brief_id))
            .eq("workspace_id", str(principal.workspace_id))
            .execute()
            .data
            or [],
        )
        sources_data = source_rows

    current_version: DraftVersion | None = None
    if draft.versions:
        for v in draft.versions:
            if v.version_number == draft.current_version_number:
                current_version = v
                break
        if not current_version and draft.versions:
            current_version = draft.versions[-1]

    audit_history = _get_audit_history(draft.id, principal.workspace_id)

    return ApprovalItemDetail(
        draft=draft,
        campaign=campaign,
        contact=contact,
        account=account,
        research_brief=brief_data,
        evidence_sources=sources_data,
        current_version=current_version,
        review_history=audit_history,
    )


@router.get("/approvals", response_model=list[ApprovalItemDetail])
def list_approval_queue(
    status_filter: str = Query("ready_for_review", alias="status"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[ApprovalItemDetail]:
    _, admin_client = _clients(settings)
    query = (
        admin_client.table("outreach_drafts")
        .select("*")
        .eq("workspace_id", str(principal.workspace_id))
        .is_("deleted_at", "null")
    )

    if status_filter != "all":
        query = query.eq("status", status_filter)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    rows = cast(list[dict[str, Any]], query.execute().data or [])

    items: list[ApprovalItemDetail] = []
    for row in rows:
        draft_id = UUID(str(row["id"]))
        draft = get_outreach_draft(draft_id, principal=principal, settings=settings)
        detail = _build_approval_item_detail(draft, principal=principal, settings=settings)

        if search:
            s_lower = search.lower()
            subj = (draft.current_subject or "").lower()
            contact_name = f"{detail.contact.get('first_name', '')} {detail.contact.get('last_name', '')}".lower()
            acct_name = (detail.account.get("name") or "").lower()
            if not (s_lower in subj or s_lower in contact_name or s_lower in acct_name):
                continue

        items.append(detail)

    return items


@router.get("/approvals/{draft_id}", response_model=ApprovalItemDetail)
def get_approval_item_detail(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ApprovalItemDetail:
    draft = get_outreach_draft(draft_id, principal=principal, settings=settings)
    return _build_approval_item_detail(draft, principal=principal, settings=settings)


@router.post("/approvals/{draft_id}/actions/approve", response_model=ApprovalItemDetail)
def approve_approval_item(
    draft_id: UUID,
    action_req: ApprovalActionRequest = ApprovalActionRequest(),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ApprovalItemDetail:
    updated_draft = approve_draft(draft_id, principal=principal, settings=settings)
    _record_audit_event(
        principal=principal,
        draft=updated_draft,
        decision="approved",
        notes=action_req.notes,
        settings=settings,
    )
    return _build_approval_item_detail(updated_draft, principal=principal, settings=settings)


@router.post("/approvals/{draft_id}/actions/reject", response_model=ApprovalItemDetail)
def reject_approval_item(
    draft_id: UUID,
    action_req: ApprovalActionRequest = ApprovalActionRequest(),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ApprovalItemDetail:
    updated_draft = reject_draft(draft_id, principal=principal, settings=settings)
    _record_audit_event(
        principal=principal,
        draft=updated_draft,
        decision="rejected",
        notes=action_req.notes,
        settings=settings,
    )
    return _build_approval_item_detail(updated_draft, principal=principal, settings=settings)


@router.post("/approvals/{draft_id}/actions/return-to-draft", response_model=ApprovalItemDetail)
def return_approval_item_to_draft(
    draft_id: UUID,
    action_req: ApprovalActionRequest = ApprovalActionRequest(),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ApprovalItemDetail:
    updated_draft = return_draft_to_draft(draft_id, principal=principal, settings=settings)
    _record_audit_event(
        principal=principal,
        draft=updated_draft,
        decision="returned_to_draft",
        notes=action_req.notes,
        settings=settings,
    )
    return _build_approval_item_detail(updated_draft, principal=principal, settings=settings)
