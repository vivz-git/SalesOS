from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.campaigns import get_campaign
from app.auth import Principal, get_current_principal
from app.core.config import Settings, get_settings
from app.db import get_db_session
from app.models import CampaignModel, JobModel, SequenceDefinitionModel, SequenceEnrollmentModel, SequenceStepModel

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


def _model_to_step(model: SequenceStepModel) -> SequenceStep:
    return SequenceStep(
        id=model.id,
        sequence_id=model.sequence_id,
        step_number=model.step_number,
        delay_days=model.delay_days,
        channel=model.channel,
        step_type=cast(StepType, model.step_type),
        template_subject=model.template_subject,
        template_body=model.template_body
    )


def _model_to_sequence(model: SequenceDefinitionModel, steps: list[SequenceStepModel]) -> SequenceDefinition:
    sorted_steps = sorted(steps, key=lambda s: s.step_number)
    return SequenceDefinition(
        id=model.id,
        workspace_id=model.workspace_id,
        campaign_id=model.campaign_id,
        name=model.name,
        version_number=model.version_number,
        is_active=model.is_active,
        steps=[_model_to_step(s) for s in sorted_steps],
        created_at=model.created_at,
        updated_at=model.updated_at
    )


def _model_to_enrollment(model: SequenceEnrollmentModel) -> SequenceEnrollment:
    return SequenceEnrollment(
        id=model.id,
        workspace_id=model.workspace_id,
        campaign_id=model.campaign_id,
        sequence_id=model.sequence_id,
        contact_id=model.contact_id,
        current_step_number=model.current_step_number,
        status=cast(EnrollmentStatus, model.status),
        stop_reason=model.stop_reason,
        enrolled_by=model.enrolled_by or uuid4(),  # type hint fallback
        enrolled_at=model.enrolled_at,
        updated_at=model.updated_at
    )


@router.post("/campaigns/{campaign_id}/sequences", response_model=SequenceDefinition)
async def create_or_update_sequence(
    campaign_id: UUID,
    payload: SequenceCreatePayload,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceDefinition:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})
    campaign = await session.scalar(select(CampaignModel).filter_by(id=campaign_id, workspace_id=principal.workspace_id))
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")

    now_dt = datetime.now(UTC)
    existing_seq = await session.scalar(
        select(SequenceDefinitionModel)
        .filter_by(campaign_id=campaign.id, workspace_id=principal.workspace_id)
        .order_by(SequenceDefinitionModel.version_number.desc())
        .limit(1)
    )

    if existing_seq:
        # Instead of updating the old one in place, we should ideally version it. 
        # But for simplicity in Phase 3, we'll follow the exact previous behavior: bump version_number.
        existing_seq.version_number += 1
        existing_seq.name = payload.name
        existing_seq.updated_at = now_dt
        seq_id = existing_seq.id
        
        # Delete old steps
        await session.execute(
            text("DELETE FROM sequence_steps WHERE sequence_id = :sid"), 
            {"sid": str(seq_id)}
        )
    else:
        seq_id = uuid4()
        existing_seq = SequenceDefinitionModel(
            id=seq_id,
            workspace_id=principal.workspace_id,
            campaign_id=campaign.id,
            name=payload.name,
            version_number=1,
            is_active=True,
            created_at=now_dt,
            updated_at=now_dt
        )
        session.add(existing_seq)

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

    new_steps: list[SequenceStepModel] = []
    for st_payload in default_steps:
        step_model = SequenceStepModel(
            id=uuid4(),
            sequence_id=seq_id,
            step_number=st_payload.step_number,
            delay_days=st_payload.delay_days,
            channel=st_payload.channel,
            step_type=st_payload.step_type,
            template_subject=st_payload.template_subject,
            template_body=st_payload.template_body,
            created_at=now_dt,
            updated_at=now_dt
        )
        session.add(step_model)
        new_steps.append(step_model)

    await session.commit()
    return _model_to_sequence(existing_seq, new_steps)


@router.get("/campaigns/{campaign_id}/sequences", response_model=SequenceDefinition)
async def get_campaign_sequence(
    campaign_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceDefinition:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})
    campaign = await session.scalar(select(CampaignModel).filter_by(id=campaign_id, workspace_id=principal.workspace_id))
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="campaign_not_found")

    existing_seq = await session.scalar(
        select(SequenceDefinitionModel)
        .filter_by(campaign_id=campaign.id, workspace_id=principal.workspace_id)
        .order_by(SequenceDefinitionModel.version_number.desc())
        .limit(1)
    )

    if existing_seq:
        steps = await session.scalars(select(SequenceStepModel).filter_by(sequence_id=existing_seq.id))
        return _model_to_sequence(existing_seq, list(steps))

    # Create default
    now_dt = datetime.now(UTC)
    seq_id = uuid4()
    default_seq = SequenceDefinitionModel(
        id=seq_id,
        workspace_id=principal.workspace_id,
        campaign_id=campaign.id,
        name=f"{campaign.name} Sequence",
        version_number=1,
        is_active=True,
        created_at=now_dt,
        updated_at=now_dt
    )
    session.add(default_seq)
    
    new_steps = [
        SequenceStepModel(
            id=uuid4(), sequence_id=seq_id, step_number=1, delay_days=0, channel="email", step_type="first_touch",
            template_subject="Introductory Outreach", template_body="Hi, I wanted to reach out regarding our solution...",
            created_at=now_dt, updated_at=now_dt
        ),
        SequenceStepModel(
            id=uuid4(), sequence_id=seq_id, step_number=2, delay_days=3, channel="email", step_type="follow_up",
            template_subject="Quick Follow-Up", template_body="Hi, following up on my previous note...",
            created_at=now_dt, updated_at=now_dt
        )
    ]
    for s in new_steps:
        session.add(s)
        
    await session.commit()
    return _model_to_sequence(default_seq, new_steps)


@router.post("/sequence-enrollments", response_model=SequenceEnrollment)
async def enroll_contact_in_sequence(
    payload: EnrollmentCreatePayload,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceEnrollment:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})

    # 1. Fetch Campaign & Active Sequence Definition
    sequence = await get_campaign_sequence(payload.campaign_id, principal=principal, session=session)

    # 2. Check if active enrollment already exists
    existing_enr = await session.scalar(
        select(SequenceEnrollmentModel)
        .filter_by(workspace_id=principal.workspace_id, campaign_id=payload.campaign_id, contact_id=payload.contact_id)
        .filter(SequenceEnrollmentModel.status.in_(["pending_approval", "active", "paused"]))
        .limit(1)
    )
    if existing_enr:
        return _model_to_enrollment(existing_enr)

    now_dt = datetime.now(UTC)
    enr_id = uuid4()

    enr_model = SequenceEnrollmentModel(
        id=enr_id,
        workspace_id=principal.workspace_id,
        campaign_id=payload.campaign_id,
        sequence_id=sequence.id,
        contact_id=payload.contact_id,
        current_step_number=1,
        status="pending_approval",
        stop_reason=None,
        enrolled_by=principal.user_id,
        enrolled_at=now_dt,
        updated_at=now_dt
    )
    
    # 3. Insert Job (instead of draft)
    job_model = JobModel(
        id=uuid4(),
        workspace_id=principal.workspace_id,
        job_type="execute_sequence_step",
        payload={"enrollment_id": str(enr_id), "step_number": 1},
        status="pending",
        available_at=now_dt,
        created_at=now_dt,
        updated_at=now_dt
    )

    try:
        session.add(enr_model)
        session.add(job_model)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing_enr = await session.scalar(
            select(SequenceEnrollmentModel)
            .filter_by(workspace_id=principal.workspace_id, campaign_id=payload.campaign_id, contact_id=payload.contact_id)
        )
        if existing_enr:
            return _model_to_enrollment(existing_enr)
        raise HTTPException(status_code=400, detail="enrollment_creation_failed_integrity") from None

    return _model_to_enrollment(enr_model)


@router.get("/sequence-enrollments", response_model=list[SequenceEnrollment])
async def list_sequence_enrollments(
    campaign_id: UUID | None = Query(default=None),
    status_filter: str = Query("all", alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[SequenceEnrollment]:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})
    
    q = select(SequenceEnrollmentModel).filter_by(workspace_id=principal.workspace_id)
    if campaign_id:
        q = q.filter_by(campaign_id=campaign_id)
    if status_filter != "all":
        q = q.filter_by(status=status_filter)
        
    q = q.order_by(SequenceEnrollmentModel.enrolled_at.desc()).offset(offset).limit(limit)
    result = await session.scalars(q)
    return [_model_to_enrollment(e) for e in result]


@router.get("/sequence-enrollments/{enrollment_id}", response_model=SequenceEnrollment)
async def get_sequence_enrollment_detail(
    enrollment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceEnrollment:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})
    
    enr = await session.scalar(select(SequenceEnrollmentModel).filter_by(id=enrollment_id, workspace_id=principal.workspace_id))
    if not enr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="sequence_enrollment_not_found")
    return _model_to_enrollment(enr)


@router.post("/sequence-enrollments/{enrollment_id}/actions/pause", response_model=SequenceEnrollment)
async def pause_enrollment(
    enrollment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceEnrollment:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})
    enr = await session.scalar(select(SequenceEnrollmentModel).filter_by(id=enrollment_id, workspace_id=principal.workspace_id))
    if not enr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="sequence_enrollment_not_found")
        
    if enr.status not in ("active", "pending_approval"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"cannot_pause_enrollment_in_{enr.status}_state")
        
    enr.status = "paused"
    enr.updated_at = datetime.now(UTC)
    await session.commit()
    return _model_to_enrollment(enr)


@router.post("/sequence-enrollments/{enrollment_id}/actions/resume", response_model=SequenceEnrollment)
async def resume_enrollment(
    enrollment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceEnrollment:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})
    enr = await session.scalar(select(SequenceEnrollmentModel).filter_by(id=enrollment_id, workspace_id=principal.workspace_id))
    if not enr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="sequence_enrollment_not_found")
        
    if enr.status != "paused":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_resume_non_paused_enrollment")
        
    enr.status = "active"
    enr.updated_at = datetime.now(UTC)
    
    # Optional: we could check if a job needs to be re-awakened here, but the worker will just pick up jobs where enrollment=active
    await session.commit()
    return _model_to_enrollment(enr)


@router.post("/sequence-enrollments/{enrollment_id}/actions/stop", response_model=SequenceEnrollment)
async def stop_enrollment(
    enrollment_id: UUID,
    payload: StatusActionPayload,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> SequenceEnrollment:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})
    enr = await session.scalar(select(SequenceEnrollmentModel).filter_by(id=enrollment_id, workspace_id=principal.workspace_id))
    if not enr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="sequence_enrollment_not_found")
        
    enr.status = "stopped"
    enr.stop_reason = payload.reason or "user_stopped"
    enr.updated_at = datetime.now(UTC)
    await session.commit()
    return _model_to_enrollment(enr)


async def evaluate_sequence_stop_conditions_for_contact(
    workspace_id: str, contact_id: str, reason: str, session: AsyncSession
) -> None:
    '''Evaluates and halts active sequence enrollments when a prospect replies or opts out.'''
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": workspace_id})
    
    q = select(SequenceEnrollmentModel).filter_by(workspace_id=workspace_id, contact_id=contact_id).filter(SequenceEnrollmentModel.status.in_(["pending_approval", "active", "paused"]))
    enrollments = await session.scalars(q)
    
    now_dt = datetime.now(UTC)
    for enr in enrollments:
        enr.status = "stopped"
        enr.stop_reason = reason
        enr.updated_at = now_dt
        
    await session.commit()
