import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.outreach import OutreachDraftCreate, create_outreach_draft_orm
from app.auth import Principal
from app.db import AsyncSessionLocal
from app.models import (
    JobModel,
    OutreachDraftModel,
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
    async with AsyncSessionLocal() as session:
        # Use SKIP LOCKED to atomically claim a job
        # We also JOIN sequence_enrollments to ensure we only claim jobs for active enrollments
        q = text("""
            SELECT j.id 
            FROM jobs j
            JOIN sequence_enrollments se ON se.id = (j.payload->>'enrollment_id')::uuid
            WHERE j.status = 'pending' 
              AND j.available_at <= now() 
              AND se.status = 'active'
            LIMIT 1
            FOR UPDATE SKIP LOCKED
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
        
        try:
            await _execute_job(session, job)
            job.status = "completed"
            job.completed_at = datetime.now(UTC)
        except IntegrityError as ie:
            logger.warning(f"Integrity error processing job {job.id}: {ie}")
            # If draft already exists, consider it completed safely
            await session.rollback()
            job.status = "completed"
            job.completed_at = datetime.now(UTC)
        except Exception as e:
            logger.error(f"Failed to execute job {job.id}: {e}")
            await session.rollback()
            job.last_error = str(e)
            if job.attempts >= job.max_attempts:
                job.status = "failed"
            else:
                job.status = "pending"
        finally:
            pass

        # To avoid detached object issues after rollback, do a direct update:
        async with AsyncSessionLocal() as update_session:
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
    if job.job_type != "execute_sequence_step":
        raise ValueError(f"Unknown job type {job.job_type}")
        
    enrollment_id_str = job.payload.get("enrollment_id")
    step_number = job.payload.get("step_number")
    
    if not enrollment_id_str or not step_number:
        raise ValueError("Missing payload data")
        
    enrollment_id = UUID(enrollment_id_str)
    
    # 1. Set Workspace RLS Context
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(job.workspace_id)})
    
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
    
    # Flush and commit is handled by the caller or we can do it here. 
    # Let's commit it here because the job state is saved independently.
    await session.commit()


async def _recover_stale_jobs() -> None:
    # Any job stuck in 'running' for > 10 mins without being updated gets reset to pending
    async with AsyncSessionLocal() as session:
        stale_threshold = datetime.now(UTC) - timedelta(minutes=10)
        await session.execute(
            text("UPDATE jobs SET status = 'pending', locked_at = NULL WHERE status = 'running' AND locked_at < :thresh"),
            {"thresh": stale_threshold}
        )
        await session.commit()

