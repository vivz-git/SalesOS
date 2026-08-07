from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings

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


def _row_to_brief(row: dict[str, Any]) -> ResearchBrief:
    created_at_val = cast(str | None, row.get("created_at"))
    updated_at_val = cast(str | None, row.get("updated_at"))
    deleted_at_val = cast(str | None, row.get("deleted_at"))
    generated_at_val = cast(str | None, row.get("generated_at"))

    key_findings_raw = row.get("key_findings")
    key_findings: list[str] | None = None
    if isinstance(key_findings_raw, list):
        key_findings = [str(item) for item in key_findings_raw]

    return ResearchBrief(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        account_id=UUID(str(row["account_id"])),
        contact_id=UUID(str(row["contact_id"])) if row.get("contact_id") else None,
        summary=cast(str | None, row.get("summary")),
        key_findings=key_findings,
        status=cast(ResearchStatus, row.get("status", "pending")),
        confidence_score=float(row["confidence_score"]) if row.get("confidence_score") is not None else None,
        confidence_reason=cast(str | None, row.get("confidence_reason")),
        provider=cast(str | None, row.get("provider")),
        model=cast(str | None, row.get("model")),
        prompt_version=cast(str | None, row.get("prompt_version")),
        generated_at=datetime.fromisoformat(generated_at_val) if generated_at_val else None,
        token_usage=int(row["token_usage"]) if row.get("token_usage") is not None else None,
        estimated_cost=float(row["estimated_cost"]) if row.get("estimated_cost") is not None else None,
        duration_ms=int(row["duration_ms"]) if row.get("duration_ms") is not None else None,
        created_by=UUID(str(row["created_by"])) if row.get("created_by") else None,
        created_at=datetime.fromisoformat(created_at_val) if created_at_val else None,
        updated_at=datetime.fromisoformat(updated_at_val) if updated_at_val else None,
        deleted_at=datetime.fromisoformat(deleted_at_val) if deleted_at_val else None,
    )


def _row_to_source(row: dict[str, Any]) -> ResearchSource:
    retrieved_at_val = cast(str | None, row.get("retrieved_at"))
    return ResearchSource(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        brief_id=UUID(str(row["brief_id"])),
        url=cast(str | None, row.get("url")),
        title=cast(str | None, row.get("title")),
        source_type=str(row.get("source_type", "website")),
        snippet=cast(str | None, row.get("snippet")),
        confidence=float(row.get("confidence", 1.0)),
        raw_content_hash=cast(str | None, row.get("raw_content_hash")),
        retrieved_at=datetime.fromisoformat(retrieved_at_val) if retrieved_at_val else None,
    )


@router.post("/research/briefs", response_model=ResearchBrief, status_code=status.HTTP_201_CREATED)
def create_research_brief(
    payload: ResearchBriefCreate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ResearchBrief:
    _, admin_client = _clients(settings)
    brief_id = uuid4()
    now_iso = datetime.now(UTC).isoformat()

    row = {
        "id": str(brief_id),
        "workspace_id": str(principal.workspace_id),
        "account_id": str(payload.account_id),
        "contact_id": str(payload.contact_id) if payload.contact_id else None,
        "summary": payload.summary.strip() if payload.summary else None,
        "key_findings": payload.key_findings or [],
        "status": "pending",
        "confidence_score": None,
        "confidence_reason": None,
        "provider": None,
        "model": None,
        "prompt_version": None,
        "generated_at": None,
        "token_usage": None,
        "estimated_cost": None,
        "duration_ms": None,
        "created_by": str(principal.user_id),
        "created_at": now_iso,
        "updated_at": now_iso,
        "deleted_at": None,
    }

    try:
        admin_client.table("research_briefs").insert(row).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="brief_creation_failed"
        ) from error

    return _row_to_brief(row)


@router.get("/research/briefs", response_model=list[ResearchBrief])
def list_research_briefs(
    account_id: UUID | None = Query(default=None),
    contact_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[ResearchBrief]:
    _, admin_client = _clients(settings)

    query = admin_client.table("research_briefs").select("*").eq("workspace_id", str(principal.workspace_id))
    if account_id:
        query = query.eq("account_id", str(account_id))
    if contact_id:
        query = query.eq("contact_id", str(contact_id))
    if status_filter:
        query = query.eq("status", status_filter)

    rows = cast(list[dict[str, Any]], query.execute().data or [])

    briefs: list[ResearchBrief] = []
    for r in rows:
        if status_filter != "archived" and r.get("deleted_at") is not None:
            continue
        briefs.append(_row_to_brief(r))

    paginated = briefs[offset : offset + limit]
    return paginated


@router.get("/research/briefs/{brief_id}", response_model=ResearchBrief)
def get_research_brief(
    brief_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ResearchBrief:
    _, admin_client = _clients(settings)
    rows = cast(
        list[dict[str, Any]],
        admin_client.table("research_briefs")
        .select("*")
        .eq("id", str(brief_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="brief_not_found")

    return _row_to_brief(rows[0])


@router.patch("/research/briefs/{brief_id}", response_model=ResearchBrief)
def update_research_brief(
    brief_id: UUID,
    payload: ResearchBriefUpdate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ResearchBrief:
    get_research_brief(brief_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    updates: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
    if payload.summary is not None:
        updates["summary"] = payload.summary.strip() if payload.summary else None
    if payload.key_findings is not None:
        updates["key_findings"] = payload.key_findings
    if payload.confidence_score is not None:
        updates["confidence_score"] = payload.confidence_score
    if payload.confidence_reason is not None:
        updates["confidence_reason"] = payload.confidence_reason.strip() if payload.confidence_reason else None
    if payload.status is not None:
        updates["status"] = payload.status

    try:
        admin_client.table("research_briefs").update(updates).eq("id", str(brief_id)).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="brief_update_failed"
        ) from error

    return get_research_brief(brief_id, principal=principal, settings=settings)


@router.delete("/research/briefs/{brief_id}", response_model=ResearchBrief)
def delete_research_brief(
    brief_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ResearchBrief:
    get_research_brief(brief_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    now_iso = datetime.now(UTC).isoformat()
    updates = {"status": "failed", "deleted_at": now_iso, "updated_at": now_iso}

    admin_client.table("research_briefs").update(updates).eq("id", str(brief_id)).execute()
    return get_research_brief(brief_id, principal=principal, settings=settings)


@router.post("/research/briefs/{brief_id}/sources", response_model=ResearchSource, status_code=status.HTTP_201_CREATED)
def append_research_source(
    brief_id: UUID,
    payload: ResearchSourceCreate,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ResearchSource:
    get_research_brief(brief_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    source_id = uuid4()
    now_iso = datetime.now(UTC).isoformat()

    row = {
        "id": str(source_id),
        "workspace_id": str(principal.workspace_id),
        "brief_id": str(brief_id),
        "url": payload.url.strip() if payload.url else None,
        "title": payload.title.strip() if payload.title else None,
        "source_type": payload.source_type,
        "snippet": payload.snippet.strip() if payload.snippet else None,
        "confidence": payload.confidence,
        "raw_content_hash": payload.raw_content_hash.strip() if payload.raw_content_hash else None,
        "retrieved_at": now_iso,
    }

    try:
        admin_client.table("research_sources").insert(row).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="source_creation_failed"
        ) from error

    return _row_to_source(row)


@router.get("/research/briefs/{brief_id}/sources", response_model=list[ResearchSource])
def list_research_sources(
    brief_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[ResearchSource]:
    get_research_brief(brief_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    rows = cast(
        list[dict[str, Any]],
        admin_client.table("research_sources")
        .select("*")
        .eq("brief_id", str(brief_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )

    return [_row_to_source(r) for r in rows]


@router.post("/research/briefs/{brief_id}/actions/trigger", response_model=ResearchJob)
def trigger_research_job(
    brief_id: UUID,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ResearchJob:
    brief = get_research_brief(brief_id, principal=principal, settings=settings)
    _, admin_client = _clients(settings)

    now_dt = datetime.now(UTC)
    now_iso = now_dt.isoformat()

    # Update brief status to in_progress
    admin_client.table("research_briefs").update(
        {"status": "in_progress", "updated_at": now_iso}
    ).eq("id", str(brief.id)).execute()

    job_id = uuid4()
    job = ResearchJob(
        id=job_id,
        workspace_id=principal.workspace_id,
        brief_id=brief.id,
        status="queued",
        created_at=now_dt,
    )
    return job
