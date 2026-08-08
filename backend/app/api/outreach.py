from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.adapters.gemini_provider import GeminiLLMProvider
from app.adapters.llm_provider import LLMGenerationRequest, LLMProviderInterface
from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings

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


def _row_to_version(row: dict[str, Any]) -> DraftVersion:
    created_at_val = cast(str | None, row.get("created_at"))
    evidence_raw = row.get("evidence_references")
    evidence_references: list[dict[str, Any]] | None = None
    if isinstance(evidence_raw, list):
        evidence_references = [item for item in evidence_raw if isinstance(item, dict)]

    return DraftVersion(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        draft_id=UUID(str(row["draft_id"])),
        version_number=int(row.get("version_number", 1)),
        subject=cast(str | None, row.get("subject")),
        body=str(row.get("body", "")),
        generation_source=cast(GenerationSource, row.get("generation_source", "human")),
        provider=cast(str | None, row.get("provider")),
        model=cast(str | None, row.get("model")),
        prompt_version=cast(str | None, row.get("prompt_version")),
        research_brief_id=UUID(str(row["research_brief_id"])) if row.get("research_brief_id") else None,
        research_brief_version=int(row["research_brief_version"]) if row.get("research_brief_version") is not None else None,
        evidence_references=evidence_references,
        created_by=UUID(str(row["created_by"])) if row.get("created_by") else None,
        created_at=datetime.fromisoformat(created_at_val) if created_at_val else None,
    )


def _row_to_draft(row: dict[str, Any], versions: list[DraftVersion] | None = None) -> OutreachDraft:
    created_at_val = cast(str | None, row.get("created_at"))
    updated_at_val = cast(str | None, row.get("updated_at"))
    deleted_at_val = cast(str | None, row.get("deleted_at"))

    return OutreachDraft(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        campaign_id=UUID(str(row["campaign_id"])),
        contact_id=UUID(str(row["contact_id"])),
        research_brief_id=UUID(str(row["research_brief_id"])) if row.get("research_brief_id") else None,
        current_version_id=UUID(str(row["current_version_id"])) if row.get("current_version_id") else None,
        current_version_number=int(row.get("current_version_number", 1)),
        current_subject=cast(str | None, row.get("current_subject")),
        current_body=cast(str | None, row.get("current_body")),
        status=cast(DraftStatus, row.get("status", "draft")),
        created_by=UUID(str(row["created_by"])) if row.get("created_by") else None,
        created_at=datetime.fromisoformat(created_at_val) if created_at_val else None,
        updated_at=datetime.fromisoformat(updated_at_val) if updated_at_val else None,
        deleted_at=datetime.fromisoformat(deleted_at_val) if deleted_at_val else None,
        versions=versions,
    )


@router.post("/outreach/drafts", response_model=OutreachDraft, status_code=status.HTTP_201_CREATED)
def create_outreach_draft(
    payload: OutreachDraftCreate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    _, admin_client = _clients(settings)
    draft_id = uuid4()
    version_id = uuid4()
    now_dt = datetime.now(UTC)
    now_iso = now_dt.isoformat()

    version_row = {
        "id": str(version_id),
        "workspace_id": str(principal.workspace_id),
        "draft_id": str(draft_id),
        "version_number": 1,
        "subject": payload.subject.strip() if payload.subject else None,
        "body": payload.body.strip(),
        "generation_source": payload.generation_source,
        "provider": payload.provider,
        "model": payload.model,
        "prompt_version": payload.prompt_version,
        "research_brief_id": str(payload.research_brief_id) if payload.research_brief_id else None,
        "research_brief_version": 1 if payload.research_brief_id else None,
        "evidence_references": payload.evidence_references or [],
        "created_by": str(principal.user_id),
        "created_at": now_iso,
    }

    draft_row = {
        "id": str(draft_id),
        "workspace_id": str(principal.workspace_id),
        "campaign_id": str(payload.campaign_id),
        "contact_id": str(payload.contact_id),
        "research_brief_id": str(payload.research_brief_id) if payload.research_brief_id else None,
        "current_version_id": str(version_id),
        "current_version_number": 1,
        "current_subject": payload.subject.strip() if payload.subject else None,
        "current_body": payload.body.strip(),
        "status": "draft",
        "created_by": str(principal.user_id),
        "created_at": now_iso,
        "updated_at": now_iso,
        "deleted_at": None,
    }

    try:
        admin_client.table("draft_versions").insert(cast(Any, version_row)).execute()
        admin_client.table("outreach_drafts").insert(cast(Any, draft_row)).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="draft_creation_failed"
        ) from error

    initial_version = _row_to_version(version_row)
    return _row_to_draft(draft_row, versions=[initial_version])


@router.get("/outreach/drafts", response_model=list[OutreachDraft])
def list_outreach_drafts(
    campaign_id: UUID | None = Query(default=None),
    contact_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[OutreachDraft]:
    _, admin_client = _clients(settings)

    query = admin_client.table("outreach_drafts").select("*").eq("workspace_id", str(principal.workspace_id))
    if campaign_id:
        query = query.eq("campaign_id", str(campaign_id))
    if contact_id:
        query = query.eq("contact_id", str(contact_id))
    if status_filter:
        query = query.eq("status", status_filter)

    rows = cast(list[dict[str, Any]], query.execute().data or [])

    drafts: list[OutreachDraft] = []
    for r in rows:
        if status_filter != "archived" and r.get("deleted_at") is not None:
            continue
        drafts.append(_row_to_draft(r))

    return drafts[offset : offset + limit]


@router.get("/outreach/drafts/{draft_id}", response_model=OutreachDraft)
def get_outreach_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    _, admin_client = _clients(settings)
    rows = cast(
        list[dict[str, Any]],
        admin_client.table("outreach_drafts")
        .select("*")
        .eq("id", str(draft_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft_not_found")

    version_rows = cast(
        list[dict[str, Any]],
        admin_client.table("draft_versions")
        .select("*")
        .eq("draft_id", str(draft_id))
        .eq("workspace_id", str(principal.workspace_id))
        .order("version_number", desc=False)
        .execute()
        .data
        or [],
    )

    versions = [_row_to_version(v) for v in version_rows]
    return _row_to_draft(rows[0], versions=versions)


@router.get("/outreach/drafts/{draft_id}/versions", response_model=list[DraftVersion])
def list_draft_versions(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[DraftVersion]:
    get_outreach_draft(draft_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    version_rows = cast(
        list[dict[str, Any]],
        admin_client.table("draft_versions")
        .select("*")
        .eq("draft_id", str(draft_id))
        .eq("workspace_id", str(principal.workspace_id))
        .order("version_number", desc=False)
        .execute()
        .data
        or [],
    )
    return [_row_to_version(v) for v in version_rows]


@router.post("/outreach/drafts/{draft_id}/actions/revise", response_model=OutreachDraft)
def revise_outreach_draft(
    draft_id: UUID,
    payload: OutreachDraftRevise,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    existing = get_outreach_draft(draft_id, principal=principal, settings=settings)
    if existing.status in ("archived", "approved"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot_revise_draft_in_{existing.status}_state",
        )

    _, admin_client = _clients(settings)
    version_id = uuid4()
    next_version_num = existing.current_version_number + 1
    now_iso = datetime.now(UTC).isoformat()

    version_row = {
        "id": str(version_id),
        "workspace_id": str(principal.workspace_id),
        "draft_id": str(draft_id),
        "version_number": next_version_num,
        "subject": payload.subject.strip() if payload.subject else None,
        "body": payload.body.strip(),
        "generation_source": payload.generation_source,
        "provider": payload.provider,
        "model": payload.model,
        "prompt_version": payload.prompt_version,
        "research_brief_id": str(payload.research_brief_id) if payload.research_brief_id else (str(existing.research_brief_id) if existing.research_brief_id else None),
        "research_brief_version": 1 if (payload.research_brief_id or existing.research_brief_id) else None,
        "evidence_references": payload.evidence_references or [],
        "created_by": str(principal.user_id),
        "created_at": now_iso,
    }

    draft_updates = {
        "current_version_id": str(version_id),
        "current_version_number": next_version_num,
        "current_subject": payload.subject.strip() if payload.subject else None,
        "current_body": payload.body.strip(),
        "updated_at": now_iso,
    }

    try:
        admin_client.table("draft_versions").insert(cast(Any, version_row)).execute()
        admin_client.table("outreach_drafts").update(cast(Any, draft_updates)).eq("id", str(draft_id)).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="draft_revision_failed"
        ) from error

    return get_outreach_draft(draft_id, principal=principal, settings=settings)


@router.post("/outreach/drafts/{draft_id}/actions/submit-review", response_model=OutreachDraft)
def submit_draft_for_review(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    existing = get_outreach_draft(draft_id, principal=principal, settings=settings)
    if existing.status not in ("draft", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot_submit_review_for_status_{existing.status}",
        )

    _, admin_client = _clients(settings)
    updates = {"status": "ready_for_review", "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("outreach_drafts").update(updates).eq("id", str(draft_id)).execute()
    return get_outreach_draft(draft_id, principal=principal, settings=settings)


@router.post("/outreach/drafts/{draft_id}/actions/approve", response_model=OutreachDraft)
def approve_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    existing = get_outreach_draft(draft_id, principal=principal, settings=settings)
    if existing.status != "ready_for_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot_approve_draft_in_{existing.status}_state",
        )

    _, admin_client = _clients(settings)
    updates = {"status": "approved", "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("outreach_drafts").update(updates).eq("id", str(draft_id)).execute()
    return get_outreach_draft(draft_id, principal=principal, settings=settings)


@router.post("/outreach/drafts/{draft_id}/actions/reject", response_model=OutreachDraft)
def reject_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    existing = get_outreach_draft(draft_id, principal=principal, settings=settings)
    if existing.status != "ready_for_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot_reject_draft_in_{existing.status}_state",
        )

    _, admin_client = _clients(settings)
    updates = {"status": "rejected", "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("outreach_drafts").update(updates).eq("id", str(draft_id)).execute()
    return get_outreach_draft(draft_id, principal=principal, settings=settings)


@router.post("/outreach/drafts/{draft_id}/actions/return-to-draft", response_model=OutreachDraft)
def return_draft_to_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    existing = get_outreach_draft(draft_id, principal=principal, settings=settings)
    if existing.status not in ("ready_for_review", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot_return_draft_to_draft_in_{existing.status}_state",
        )

    _, admin_client = _clients(settings)
    updates = {"status": "draft", "updated_at": datetime.now(UTC).isoformat()}
    admin_client.table("outreach_drafts").update(updates).eq("id", str(draft_id)).execute()
    return get_outreach_draft(draft_id, principal=principal, settings=settings)


@router.post("/outreach/drafts/{draft_id}/actions/archive", response_model=OutreachDraft)
def archive_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    get_outreach_draft(draft_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    now_iso = datetime.now(UTC).isoformat()
    updates = {"status": "archived", "deleted_at": now_iso, "updated_at": now_iso}

    admin_client.table("outreach_drafts").update(updates).eq("id", str(draft_id)).execute()
    return get_outreach_draft(draft_id, principal=principal, settings=settings)


@router.delete("/outreach/drafts/{draft_id}", response_model=OutreachDraft)
def delete_outreach_draft(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> OutreachDraft:
    return archive_draft(draft_id, principal=principal, settings=settings)


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
    api_key = settings.gemini_api_key or settings.google_api_key
    return GeminiLLMProvider(api_key=api_key)


@router.post("/outreach/drafts/{draft_id}/actions/generate", response_model=OutreachDraft)
def generate_outreach_draft_action(
    draft_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
    llm_provider: LLMProviderInterface = Depends(get_llm_provider),
) -> OutreachDraft:
    existing = get_outreach_draft(draft_id, principal=principal, settings=settings)
    if existing.status in ("archived", "approved"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot_generate_draft_in_{existing.status}_state",
        )

    _, admin_client = _clients(settings)

    # 1. Load Campaign Context
    campaign_rows = cast(
        list[dict[str, Any]],
        admin_client.table("campaigns")
        .select("*")
        .eq("id", str(existing.campaign_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    campaign = campaign_rows[0] if campaign_rows else {}

    # 2. Load Contact Context
    contact_rows = cast(
        list[dict[str, Any]],
        admin_client.table("contacts")
        .select("*")
        .eq("id", str(existing.contact_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    contact = contact_rows[0] if contact_rows else {}

    # 3. Load Account Context if available
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
    if existing.research_brief_id:
        brief_rows = cast(
            list[dict[str, Any]],
            admin_client.table("research_briefs")
            .select("*")
            .eq("id", str(existing.research_brief_id))
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
            .eq("brief_id", str(existing.research_brief_id))
            .eq("workspace_id", str(principal.workspace_id))
            .execute()
            .data
            or [],
        )
        sources_data = source_rows

    key_findings_raw = brief_data.get("key_findings")
    key_findings: list[str] = []
    if isinstance(key_findings_raw, list):
        key_findings = [str(k) for k in key_findings_raw]

    gen_request = LLMGenerationRequest(
        campaign_name=str(campaign.get("name", "Outreach Campaign")),
        campaign_description=cast(str | None, campaign.get("description")),
        target_segment=cast(str | None, campaign.get("target_segment")),
        icp_definition=cast(str | None, campaign.get("icp_definition")),
        contact_name=f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or "Prospect",
        contact_title=cast(str | None, contact.get("title")),
        contact_department=cast(str | None, contact.get("department")),
        account_name=cast(str | None, account.get("name")),
        account_domain=cast(str | None, account.get("domain")),
        research_summary=cast(str | None, brief_data.get("summary")),
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

    # 6. Append new immutable DraftVersion (v+1)
    version_id = uuid4()
    next_version_num = existing.current_version_number + 1
    now_iso = datetime.now(UTC).isoformat()

    version_row = {
        "id": str(version_id),
        "workspace_id": str(principal.workspace_id),
        "draft_id": str(draft_id),
        "version_number": next_version_num,
        "subject": gen_result.subject,
        "body": gen_result.body,
        "generation_source": gen_result.generation_source,
        "provider": gen_result.provider,
        "model": gen_result.model,
        "prompt_version": gen_result.prompt_version,
        "research_brief_id": str(existing.research_brief_id) if existing.research_brief_id else None,
        "research_brief_version": 1 if existing.research_brief_id else None,
        "evidence_references": gen_result.evidence_references,
        "created_by": str(principal.user_id),
        "created_at": now_iso,
    }

    draft_updates = {
        "current_version_id": str(version_id),
        "current_version_number": next_version_num,
        "current_subject": gen_result.subject,
        "current_body": gen_result.body,
        "updated_at": now_iso,
    }

    try:
        admin_client.table("draft_versions").insert(cast(Any, version_row)).execute()
        admin_client.table("outreach_drafts").update(cast(Any, draft_updates)).eq("id", str(draft_id)).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="draft_revision_failed"
        ) from error

    return get_outreach_draft(draft_id, principal=principal, settings=settings)

