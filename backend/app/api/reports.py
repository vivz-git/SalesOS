from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.accounts import list_accounts
from app.api.campaigns import list_campaigns
from app.api.contacts import list_contacts
from app.api.conversations import _CONVERSATIONS_STORE
from app.api.deliveries import _DELIVERIES_STORE
from app.api.hubspot import _HUBSPOT_SYNC_RUNS_STORE
from app.api.outreach import list_outreach_drafts
from app.api.sequences import _SEQUENCE_ENROLLMENTS_STORE
from app.auth import Principal, get_current_principal
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["reports"])


class ReportMetricsSnapshot(BaseModel):
    campaigns_count: int = 0
    accounts_researched_count: int = 0
    contacts_enrolled_count: int = 0
    drafts_generated_count: int = 0
    drafts_submitted_count: int = 0
    drafts_approved_count: int = 0
    approval_rate: float = 0.0
    emails_sent_count: int = 0
    emails_delivered_count: int = 0
    emails_bounced_count: int = 0
    emails_complained_count: int = 0
    delivery_rate: float = 0.0
    replies_received_count: int = 0
    reply_rate: float = 0.0
    interested_replies_count: int = 0
    interested_reply_rate: float = 0.0
    opt_out_replies_count: int = 0
    opt_out_rate: float = 0.0
    crm_synced_records_count: int = 0


class ReportRun(BaseModel):
    id: UUID
    workspace_id: UUID
    period_start: datetime
    period_end: datetime
    title: str
    metrics_snapshot: ReportMetricsSnapshot
    executive_summary: str
    recommended_actions: list[str] = Field(default_factory=list)
    created_at: datetime


_REPORTS_STORE: list[dict[str, Any]] = []


def _get_current_week_bounds() -> tuple[datetime, datetime]:
    """Returns calendar week boundaries: Monday 00:00:00 UTC to Sunday 23:59:59 UTC."""
    now = datetime.now(UTC)
    monday = now - timedelta(days=now.weekday())
    period_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    period_end = period_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return period_start, period_end


def compute_workspace_metrics(principal: Principal, settings: Settings) -> ReportMetricsSnapshot:
    ws_str = str(principal.workspace_id)

    # 1. Campaigns & Accounts/Contacts
    campaigns_cnt = 0
    accounts_cnt = 0
    contacts_cnt = 0
    try:
        if settings.supabase_url and settings.supabase_service_role_key:
            campaigns_cnt = len(list_campaigns(principal=principal, settings=settings))
            accounts_cnt = len(list_accounts(principal=principal, settings=settings))
            contacts_cnt = len(list_contacts(principal=principal, settings=settings))
    except Exception:
        pass

    contacts_enrolled = sum(1 for e in _SEQUENCE_ENROLLMENTS_STORE if str(e.get("workspace_id")) == ws_str)
    if contacts_enrolled == 0:
        contacts_enrolled = contacts_cnt

    # 2. Drafts & Approval Rate
    ws_drafts: list[Any] = []
    try:
        ws_drafts = list_outreach_drafts(limit=200, principal=principal, settings=settings)
    except Exception:
        pass

    drafts_gen = len(ws_drafts)
    submitted_drafts = [d for d in ws_drafts if getattr(d, "status", "") in ("ready_for_review", "approved", "rejected")]
    submitted_cnt = len(submitted_drafts)
    approved_cnt = sum(1 for d in ws_drafts if getattr(d, "status", "") == "approved")
    app_rate = round((approved_cnt / submitted_cnt) * 100.0, 1) if submitted_cnt > 0 else 0.0

    # 3. Deliveries & Delivery Rate
    ws_deliveries = [d for d in _DELIVERIES_STORE if str(d.get("workspace_id")) == ws_str]
    sent_cnt = sum(1 for d in ws_deliveries if d.get("status") != "cancelled")
    delivered_cnt = sum(1 for d in ws_deliveries if d.get("status") == "delivered")
    bounced_cnt = sum(1 for d in ws_deliveries if d.get("status") == "bounced")
    complained_cnt = sum(1 for d in ws_deliveries if d.get("status") == "complained")
    deliv_rate = round((delivered_cnt / sent_cnt) * 100.0, 1) if sent_cnt > 0 else 0.0

    # 4. Conversations & Reply Rates
    ws_convs = [c for c in _CONVERSATIONS_STORE if str(c.get("workspace_id")) == ws_str]
    replies_cnt = len(ws_convs)
    rep_rate = round((replies_cnt / delivered_cnt) * 100.0, 1) if delivered_cnt > 0 else 0.0

    interested_cnt = sum(1 for c in ws_convs if c.get("current_reply_state") == "interested")
    interested_rate = round((interested_cnt / replies_cnt) * 100.0, 1) if replies_cnt > 0 else 0.0

    opt_out_cnt = sum(1 for c in ws_convs if c.get("current_reply_state") == "unsubscribe")
    opt_rate = round((opt_out_cnt / replies_cnt) * 100.0, 1) if replies_cnt > 0 else 0.0

    # 5. CRM Sync
    crm_synced_cnt = sum(
        int(r.get("records_processed", 0))
        for r in _HUBSPOT_SYNC_RUNS_STORE
        if str(r.get("workspace_id")) == ws_str
    )

    return ReportMetricsSnapshot(
        campaigns_count=campaigns_cnt,
        accounts_researched_count=accounts_cnt,
        contacts_enrolled_count=contacts_enrolled,
        drafts_generated_count=drafts_gen,
        drafts_submitted_count=submitted_cnt,
        drafts_approved_count=approved_cnt,
        approval_rate=app_rate,
        emails_sent_count=sent_cnt,
        emails_delivered_count=delivered_cnt,
        emails_bounced_count=bounced_cnt,
        emails_complained_count=complained_cnt,
        delivery_rate=deliv_rate,
        replies_received_count=replies_cnt,
        reply_rate=rep_rate,
        interested_replies_count=interested_cnt,
        interested_reply_rate=interested_rate,
        opt_out_replies_count=opt_out_cnt,
        opt_out_rate=opt_rate,
        crm_synced_records_count=crm_synced_cnt,
    )


def _row_to_report_run(row: dict[str, Any]) -> ReportRun:
    return ReportRun(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        period_start=datetime.fromisoformat(str(row["period_start"])),
        period_end=datetime.fromisoformat(str(row["period_end"])),
        title=str(row["title"]),
        metrics_snapshot=ReportMetricsSnapshot(**row["metrics_snapshot"]),
        executive_summary=str(row["executive_summary"]),
        recommended_actions=cast(list[str], row.get("recommended_actions", [])),
        created_at=datetime.fromisoformat(str(row["created_at"])),
    )


@router.get("/reports/weekly", response_model=list[ReportRun])
def list_weekly_reports(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[ReportRun]:
    runs: list[ReportRun] = []
    for r in _REPORTS_STORE:
        if str(r.get("workspace_id")) == str(principal.workspace_id):
            runs.append(_row_to_report_run(r))

    if not runs:
        # Generate initial default report if none exists
        init_run = _generate_report_for_workspace(principal, settings)
        runs.append(init_run)

    runs.sort(key=lambda x: x.created_at, reverse=True)
    return runs[offset : offset + limit]


@router.get("/reports/weekly/{report_id}", response_model=ReportRun)
def get_weekly_report_detail(
    report_id: UUID,
    principal: Principal = Depends(get_current_principal),
) -> ReportRun:
    for r in _REPORTS_STORE:
        if str(r.get("id")) == str(report_id) and str(r.get("workspace_id")) == str(principal.workspace_id):
            return _row_to_report_run(r)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="weekly_report_not_found",
    )


@router.post("/reports/weekly/actions/generate", response_model=ReportRun)
def generate_weekly_report_digest(
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ReportRun:
    return _generate_report_for_workspace(principal, settings)


def _generate_report_for_workspace(principal: Principal, settings: Settings) -> ReportRun:
    p_start, p_end = _get_current_week_bounds()
    metrics = compute_workspace_metrics(principal, settings)
    now_iso = datetime.now(UTC).isoformat()
    report_id = str(uuid4())

    title = f"Weekly Digest ({p_start.strftime('%b %d')} - {p_end.strftime('%b %d, %Y')})"

    summary = (
        f"Workspace performance digest for {p_start.strftime('%b %d')} to {p_end.strftime('%b %d, %Y')}. "
        f"Across {metrics.campaigns_count} active campaign(s), {metrics.drafts_generated_count} message draft(s) were generated with an approval efficiency rate of {metrics.approval_rate}%. "
        f"Outbound email delivery rate achieved {metrics.delivery_rate}% across {metrics.emails_sent_count} sent email(s). "
        f"Prospect reply engagement generated {metrics.replies_received_count} reply thread(s) with an interested positive response rate of {metrics.interested_reply_rate}%."
    )

    recs: list[str] = []
    if metrics.approval_rate < 70.0 and metrics.drafts_submitted_count > 0:
        recs.append("Review draft prompt versions and value proposition clarity to raise human approval rate.")
    else:
        recs.append("Approval rate is performing strongly within governed quality thresholds.")

    if metrics.reply_rate > 0 and metrics.interested_reply_rate < 30.0:
        recs.append("Refine CTA urgency and prospect objection positioning to improve interested reply conversion.")
    else:
        recs.append("Maintain current targeting parameters and continue sequence enrollments.")

    recs.append("Ensure regular HubSpot CRM synchronizations to keep deal stages aligned.")

    row = {
        "id": report_id,
        "workspace_id": str(principal.workspace_id),
        "period_start": p_start.isoformat(),
        "period_end": p_end.isoformat(),
        "title": title,
        "metrics_snapshot": metrics.model_dump(),
        "executive_summary": summary,
        "recommended_actions": recs,
        "created_at": now_iso,
    }
    _REPORTS_STORE.append(row)
    return _row_to_report_run(row)
