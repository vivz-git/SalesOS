from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.campaigns import get_campaign
from app.api.outreach import OutreachDraftCreate, create_outreach_draft
from app.auth import Principal, get_current_principal
from app.core.config import Settings, get_settings
from app.db import get_db_session

router = APIRouter(prefix="/v1", tags=["sequences"])

StepType = Literal["first_touch", "follow_up"]
EnrollmentStatus = Literal["pending_approval", "active", "paused", "stopped", "completed", "failed"]


class SequenceStepPayload(BaseModel):
    step_number: int = Field(ge=1)
    delay_days: int = Field(default=0, ge=0)
    channel: str = Field(default="email")
    step_type: StepType = "first_touch"
    template_subject: str | None = Field(default=None, max_length=255)
    template_body: str | None = Field(default=None)


class SequenceStep(BaseModel):
    id: UUID
    sequence_id: UUID
    step_number: int
    delay_days: int
    channel: str
    step_type: StepType
    template_subject: str | None = None
    template_body: str | None = None


class SequenceCreatePayload(BaseModel):
    name: str = Field(default="Outreach Sequence", max_length=255)
    steps: list[SequenceStepPayload] = Field(default_factory=list)


class SequenceDefinition(BaseModel):
    id: UUID
    workspace_id: UUID
    campaign_id: UUID
    name: str
    version_number: int
    is_active: bool
    steps: list[SequenceStep]
    created_at: datetime
    updated_at: datetime


class EnrollmentCreatePayload(BaseModel):
    campaign_id: UUID
    contact_id: UUID


class SequenceEnrollment(BaseModel):
    id: UUID
    workspace_id: UUID
    campaign_id: UUID
    sequence_id: UUID
    contact_id: UUID
    current_step_number: int
    status: EnrollmentStatus
    stop_reason: str | None = None
    enrolled_by: UUID
    enrolled_at: datetime
    updated_at: datetime


class StatusActionPayload(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


_SEQUENCES_STORE: list[dict[str, Any]] = []
_SEQUENCE_STEPS_STORE: list[dict[str, Any]] = []
_SEQUENCE_ENROLLMENTS_STORE: list[dict[str, Any]] = []


def _row_to_sequence(seq_row: dict[str, Any]) -> SequenceDefinition:
    seq_id = UUID(str(seq_row["id"]))
    ws_id = UUID(str(seq_row["workspace_id"]))

    steps: list[SequenceStep] = []
    for step_row in _SEQUENCE_STEPS_STORE:
        if str(step_row.get("sequence_id")) == str(seq_id):
            steps.append(
                SequenceStep(
                    id=UUID(str(step_row["id"])),
                    sequence_id=seq_id,
                    step_number=int(step_row["step_number"]),
                    delay_days=int(step_row.get("delay_days", 0)),
                    channel=str(step_row.get("channel", "email")),
                    step_type=cast(StepType, step_row.get("step_type", "first_touch")),
                    template_subject=cast(str | None, step_row.get("template_subject")),
                    template_body=cast(str | None, step_row.get("template_body")),
                )
            )
    steps.sort(key=lambda s: s.step_number)

    return SequenceDefinition(
        id=seq_id,
        workspace_id=ws_id,
        campaign_id=UUID(str(seq_row["campaign_id"])),
        name=str(seq_row.get("name", "Outreach Sequence")),
        version_number=int(seq_row.get("version_number", 1)),
        is_active=bool(seq_row.get("is_active", True)),
        steps=steps,
        created_at=datetime.fromisoformat(str(seq_row["created_at"])),
        updated_at=datetime.fromisoformat(str(seq_row["updated_at"])),
    )


def _row_to_enrollment(enr_row: dict[str, Any]) -> SequenceEnrollment:
    return SequenceEnrollment(
        id=UUID(str(enr_row["id"])),
        workspace_id=UUID(str(enr_row["workspace_id"])),
        campaign_id=UUID(str(enr_row["campaign_id"])),
        sequence_id=UUID(str(enr_row["sequence_id"])),
        contact_id=UUID(str(enr_row["contact_id"])),
        current_step_number=int(enr_row.get("current_step_number", 1)),
        status=cast(EnrollmentStatus, enr_row.get("status", "pending_approval")),
        stop_reason=cast(str | None, enr_row.get("stop_reason")),
        enrolled_by=UUID(str(enr_row.get("enrolled_by", uuid4()))),
        enrolled_at=datetime.fromisoformat(str(enr_row["enrolled_at"])),
        updated_at=datetime.fromisoformat(str(enr_row["updated_at"])),
    )


@router.post("/campaigns/{campaign_id}/sequences", response_model=SequenceDefinition)
async def create_or_update_sequence(
    campaign_id: UUID,
    payload: SequenceCreatePayload,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceDefinition:
    # Verify campaign exists & workspace authorization
    campaign = await get_campaign(campaign_id, principal=principal, session=session)

    now_iso = datetime.now(UTC).isoformat()
    existing_seq: dict[str, Any] | None = None

    for s in _SEQUENCES_STORE:
        if str(s.get("campaign_id")) == str(campaign.id) and str(s.get("workspace_id")) == str(principal.workspace_id):
            existing_seq = s
            break

    if existing_seq:
        seq_id = str(existing_seq["id"])
        version_num = int(existing_seq.get("version_number", 1)) + 1
        existing_seq["version_number"] = version_num
        existing_seq["name"] = payload.name
        existing_seq["updated_at"] = now_iso
        # Remove old steps
        global _SEQUENCE_STEPS_STORE
        _SEQUENCE_STEPS_STORE = [st for st in _SEQUENCE_STEPS_STORE if str(st.get("sequence_id")) != seq_id]
    else:
        seq_id = str(uuid4())
        version_num = 1
        existing_seq = {
            "id": seq_id,
            "workspace_id": str(principal.workspace_id),
            "campaign_id": str(campaign.id),
            "name": payload.name,
            "version_number": version_num,
            "is_active": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        _SEQUENCES_STORE.append(existing_seq)

    # Insert steps
    default_steps = payload.steps or [
        SequenceStepPayload(
            step_number=1,
            delay_days=0,
            channel="email",
            step_type="first_touch",
            template_subject="Introductory Conversation",
            template_body="Hi {{first_name}}, I noticed your recent work...",
        ),
        SequenceStepPayload(
            step_number=2,
            delay_days=3,
            channel="email",
            step_type="follow_up",
            template_subject="Following up on my previous message",
            template_body="Hi {{first_name}}, wanted to check if you had a chance to read...",
        ),
    ]

    for st_payload in default_steps:
        step_id = str(uuid4())
        _SEQUENCE_STEPS_STORE.append({
            "id": step_id,
            "sequence_id": seq_id,
            "step_number": st_payload.step_number,
            "delay_days": st_payload.delay_days,
            "channel": st_payload.channel,
            "step_type": st_payload.step_type,
            "template_subject": st_payload.template_subject,
            "template_body": st_payload.template_body,
        })

    return _row_to_sequence(existing_seq)


@router.get("/campaigns/{campaign_id}/sequences", response_model=SequenceDefinition)
async def get_campaign_sequence(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceDefinition:
    campaign = await get_campaign(campaign_id, principal=principal, session=session)

    for s in _SEQUENCES_STORE:
        if str(s.get("campaign_id")) == str(campaign.id) and str(s.get("workspace_id")) == str(principal.workspace_id):
            return _row_to_sequence(s)

    # Create default sequence definition if none exists yet
    now_iso = datetime.now(UTC).isoformat()
    seq_id = str(uuid4())
    default_seq: dict[str, Any] = {
        "id": seq_id,
        "workspace_id": str(principal.workspace_id),
        "campaign_id": str(campaign.id),
        "name": f"{campaign.name} Sequence",
        "version_number": 1,
        "is_active": True,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    _SEQUENCES_STORE.append(default_seq)

    _SEQUENCE_STEPS_STORE.extend([
        {
            "id": str(uuid4()),
            "sequence_id": seq_id,
            "step_number": 1,
            "delay_days": 0,
            "channel": "email",
            "step_type": "first_touch",
            "template_subject": "Introductory Outreach",
            "template_body": "Hi, I wanted to reach out regarding our solution...",
        },
        {
            "id": str(uuid4()),
            "sequence_id": seq_id,
            "step_number": 2,
            "delay_days": 3,
            "channel": "email",
            "step_type": "follow_up",
            "template_subject": "Quick Follow-Up",
            "template_body": "Hi, following up on my previous note...",
        },
    ])

    return _row_to_sequence(default_seq)


@router.post("/sequence-enrollments", response_model=SequenceEnrollment)
async def enroll_contact_in_sequence(
    payload: EnrollmentCreatePayload,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceEnrollment:
    # 1. Fetch Campaign & Active Sequence Definition
    sequence = await get_campaign_sequence(payload.campaign_id, principal=principal, session=session)

    # 2. Check if active enrollment already exists
    for enr in _SEQUENCE_ENROLLMENTS_STORE:
        if (
            str(enr.get("workspace_id")) == str(principal.workspace_id)
            and str(enr.get("campaign_id")) == str(payload.campaign_id)
            and str(enr.get("contact_id")) == str(payload.contact_id)
            and enr.get("status") in ("pending_approval", "active", "paused")
        ):
            return _row_to_enrollment(enr)

    now_iso = datetime.now(UTC).isoformat()
    enr_id = str(uuid4())

    enr_dict: dict[str, Any] = {
        "id": enr_id,
        "workspace_id": str(principal.workspace_id),
        "campaign_id": str(payload.campaign_id),
        "sequence_id": str(sequence.id),
        "contact_id": str(payload.contact_id),
        "current_step_number": 1,
        "status": "pending_approval",
        "stop_reason": None,
        "enrolled_by": str(principal.user_id),
        "enrolled_at": now_iso,
        "updated_at": now_iso,
    }
    _SEQUENCE_ENROLLMENTS_STORE.append(enr_dict)

    # 3. Create Step 1 OutreachDraft in 'draft' state (Approval-Gated, Zero Auto-Send)
    step1 = sequence.steps[0] if sequence.steps else None
    subject_text = step1.template_subject if (step1 and step1.template_subject) else "Outreach Message"
    body_text = step1.template_body if (step1 and step1.template_body) else "Hi, reaching out regarding our solution..."

    draft_req = OutreachDraftCreate(
        campaign_id=payload.campaign_id,
        contact_id=payload.contact_id,
        subject=subject_text,
        body=body_text,
    )
    create_outreach_draft(draft_req, principal=principal, settings=settings)

    return _row_to_enrollment(enr_dict)


@router.get("/sequence-enrollments", response_model=list[SequenceEnrollment])
def list_sequence_enrollments(
    campaign_id: UUID | None = Query(default=None),
    status_filter: str = Query("all", alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
) -> list[SequenceEnrollment]:
    results: list[SequenceEnrollment] = []
    for enr in _SEQUENCE_ENROLLMENTS_STORE:
        if str(enr.get("workspace_id")) == str(principal.workspace_id):
            if campaign_id and str(enr.get("campaign_id")) != str(campaign_id):
                continue
            if status_filter != "all" and enr.get("status") != status_filter:
                continue

            results.append(_row_to_enrollment(enr))

    results.sort(key=lambda e: e.enrolled_at, reverse=True)
    return results[offset : offset + limit]


@router.get("/sequence-enrollments/{enrollment_id}", response_model=SequenceEnrollment)
def get_sequence_enrollment_detail(
    enrollment_id: UUID,
    principal: Principal = Depends(get_current_principal),
) -> SequenceEnrollment:
    for enr in _SEQUENCE_ENROLLMENTS_STORE:
        if str(enr.get("id")) == str(enrollment_id) and str(enr.get("workspace_id")) == str(principal.workspace_id):
            return _row_to_enrollment(enr)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="sequence_enrollment_not_found",
    )


@router.post("/sequence-enrollments/{enrollment_id}/actions/pause", response_model=SequenceEnrollment)
def pause_enrollment(
    enrollment_id: UUID,
    principal: Principal = Depends(get_current_principal),
) -> SequenceEnrollment:
    for enr in _SEQUENCE_ENROLLMENTS_STORE:
        if str(enr.get("id")) == str(enrollment_id) and str(enr.get("workspace_id")) == str(principal.workspace_id):
            curr_status = enr.get("status")
            if curr_status not in ("active", "pending_approval"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"cannot_pause_enrollment_in_{curr_status}_state",
                )
            enr["status"] = "paused"
            enr["updated_at"] = datetime.now(UTC).isoformat()
            return _row_to_enrollment(enr)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="sequence_enrollment_not_found",
    )


@router.post("/sequence-enrollments/{enrollment_id}/actions/resume", response_model=SequenceEnrollment)
def resume_enrollment(
    enrollment_id: UUID,
    principal: Principal = Depends(get_current_principal),
) -> SequenceEnrollment:
    for enr in _SEQUENCE_ENROLLMENTS_STORE:
        if str(enr.get("id")) == str(enrollment_id) and str(enr.get("workspace_id")) == str(principal.workspace_id):
            if enr.get("status") != "paused":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="cannot_resume_non_paused_enrollment",
                )
            enr["status"] = "active"
            enr["updated_at"] = datetime.now(UTC).isoformat()
            return _row_to_enrollment(enr)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="sequence_enrollment_not_found",
    )


@router.post("/sequence-enrollments/{enrollment_id}/actions/stop", response_model=SequenceEnrollment)
def stop_enrollment(
    enrollment_id: UUID,
    payload: StatusActionPayload,
    principal: Principal = Depends(get_current_principal),
) -> SequenceEnrollment:
    for enr in _SEQUENCE_ENROLLMENTS_STORE:
        if str(enr.get("id")) == str(enrollment_id) and str(enr.get("workspace_id")) == str(principal.workspace_id):
            enr["status"] = "stopped"
            enr["stop_reason"] = payload.reason or "user_stopped"
            enr["updated_at"] = datetime.now(UTC).isoformat()
            return _row_to_enrollment(enr)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="sequence_enrollment_not_found",
    )


def evaluate_sequence_stop_conditions_for_contact(
    workspace_id: str, contact_id: str, reason: str
) -> None:
    """Evaluates and halts active sequence enrollments when a prospect replies or opts out."""
    now_iso = datetime.now(UTC).isoformat()
    for enr in _SEQUENCE_ENROLLMENTS_STORE:
        enr_ws = str(enr.get("workspace_id"))
        enr_contact = str(enr.get("contact_id"))
        if enr_ws == workspace_id and (enr_contact == contact_id or not contact_id or enr_contact):
            if enr.get("status") in ("pending_approval", "active", "paused"):
                enr["status"] = "stopped"
                enr["stop_reason"] = reason
                enr["updated_at"] = now_iso
