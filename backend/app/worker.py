import sys
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.outreach import OutreachDraftCreate, create_outreach_draft_orm
from app.auth import Principal
from app.db import AsyncSessionLocal, AsyncWorkerSessionLocal, tenant_transaction_context
from app.models import (
    JobModel,
    OutreachDraftModel,
    ResearchBriefModel,
    SequenceEnrollmentModel,
    SequenceStepModel,
)

logger = logging.getLogger(__name__)

async def process_jobs() -> None:
    while True:
        try:
            await _claim_and_process_job()
            await _recover_stale_jobs()
        except Exception as e:
            logger.error(f"Error in job worker loop: {e}")
        await asyncio.sleep(5)


async def _claim_and_process_job() -> None:
    async with AsyncWorkerSessionLocal() as session:
        # Use SKIP LOCKED to atomically claim a job
        # For sequence steps, ensure enrollment is active; for other jobs (e.g. research_generation), claim directly
        q = text("""
            SELECT j.id 
            FROM jobs j
            LEFT JOIN sequence_enrollments se ON se.id = (j.payload->>'enrollment_id')::uuid
            WHERE j.status = 'pending' 
              AND j.available_at <= now() 
              AND (j.job_type != 'execute_sequence_step' OR se.status = 'active')
            LIMIT 1
            FOR UPDATE OF j SKIP LOCKED
        """)
        
        result = await session.execute(q)
        job_id_row = result.fetchone()
        
        if not job_id_row:
            return
            
        job_id = job_id_row[0]
        
        job = await session.scalar(select(JobModel).filter_by(id=job_id))
        if not job:
            return
            
        job.status = "running"
        job.locked_at = datetime.now(UTC)
        job.attempts += 1
        await session.commit()
        
        # Execution Phase (as salesos_backend)
        async with AsyncSessionLocal() as exec_session:
            try:
                system_user_id = UUID("00000000-0000-0000-0000-000000000000")
                async with tenant_transaction_context(exec_session, system_user_id, job.workspace_id) as ctx:
                    await _execute_job(ctx, job)
                    # ctx auto-commits on success
                    
                job.status = "completed"
                job.completed_at = datetime.now(UTC)
            except IntegrityError as ie:
                logger.warning(f"Integrity error processing job {job.id}: {ie}")
                job.status = "completed"
                job.completed_at = datetime.now(UTC)
            except Exception as e:
                logger.error(f"Failed to execute job {job.id}: {e}")
                job.last_error = str(e)
                if job.attempts >= job.max_attempts:
                    job.status = "failed"
                else:
                    job.status = "pending"

        # To avoid detached object issues after rollback, do a direct update:
        async with AsyncWorkerSessionLocal() as update_session:
            await update_session.execute(
                text("UPDATE jobs SET status = :status, completed_at = :completed, attempts = :attempts, last_error = :err WHERE id = :id"),
                {
                    "status": job.status,
                    "completed": job.completed_at,
                    "attempts": job.attempts,
                    "err": job.last_error,
                    "id": str(job.id)
                }
            )
            await update_session.commit()


async def _execute_job(session: AsyncSession, job: JobModel) -> None:
    if job.job_type == "execute_sequence_step":
        await _execute_sequence_step_job(session, job)
    elif job.job_type == "research_generation":
        await _execute_research_generation_job(session, job)
    else:
        raise ValueError(f"Unknown job type {job.job_type}")

async def _execute_sequence_step_job(session: AsyncSession, job: JobModel) -> None:
    enrollment_id_str = job.payload.get("enrollment_id")
    step_number = job.payload.get("step_number")
    
    if not enrollment_id_str or not step_number:
        raise ValueError("Missing payload data")
        
    enrollment_id = enrollment_id_str
    
    # 2. Fetch Enrollment
    enrollment = await session.scalar(select(SequenceEnrollmentModel).filter_by(id=enrollment_id))
    if not enrollment or enrollment.status != "active":
        raise ValueError(f"Enrollment {enrollment_id} not active")
        
    # 3. Double check draft uniqueness (optional since DB enforces it, but clean)
    existing_draft = await session.scalar(
        select(OutreachDraftModel).filter_by(
            sequence_enrollment_id=enrollment_id,
            sequence_step_number=step_number
        )
    )
    if existing_draft:
        return # Already generated!
        
    # 4. Load Step
    step = await session.scalar(
        select(SequenceStepModel).filter_by(
            sequence_id=enrollment.sequence_id,
            step_number=step_number
        )
    )
    
    if not step:
        raise ValueError(f"Sequence step {step_number} not found")
        
    # 5. Create Draft via ORM
    principal = Principal(
        user_id=enrollment.enrolled_by or UUID("00000000-0000-0000-0000-000000000000"),
        email="system@salesos.com",
        workspace_id=job.workspace_id,
        role="admin" # Synthetic role for worker
    )
    
    payload = OutreachDraftCreate(
        campaign_id=enrollment.campaign_id,
        contact_id=enrollment.contact_id,
        sequence_enrollment_id=enrollment.id,
        sequence_step_number=step_number,
        subject=step.template_subject or "Outreach Message",
        body=step.template_body or "Hi there...",
        generation_source="template"
    )
    
    await create_outreach_draft_orm(session, payload, principal)


async def _recover_stale_jobs() -> None:
    # Any job stuck in 'running' for > 10 mins without being updated gets reset to pending
    async with AsyncWorkerSessionLocal() as session:
        stale_threshold = datetime.now(UTC) - timedelta(minutes=10)
        await session.execute(
            text("UPDATE jobs SET status = 'pending', locked_at = NULL WHERE status = 'running' AND locked_at < :thresh"),
            {"thresh": stale_threshold}
        )
        await session.commit()



async def _execute_research_generation_job(session: AsyncSession, job: JobModel) -> None:
    brief_id_str = job.payload.get("brief_id")
    if not brief_id_str:
        raise ValueError("Missing brief_id in payload")
        
    brief_id = brief_id_str
    
    brief = await session.scalar(select(ResearchBriefModel).filter_by(id=brief_id))
    if not brief:
        raise ValueError(f"Brief {brief_id} not found")

    # Mock Research Generation Logic
    # We pretend an LLM runs here.
    brief.summary = "Generated summary via worker."
    brief.key_findings = cast(Any, ["Finding A", "Finding B"])
    brief.status = "completed"
    brief.confidence_score = 0.95
    brief.generated_at = datetime.now(UTC)
    brief.updated_at = datetime.now(UTC)

if __name__ == "__main__":
    asyncio.run(process_jobs())
