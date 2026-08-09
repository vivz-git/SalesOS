import pytest
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.db import AsyncSessionLocal
from app.worker import _claim_and_process_job
from app.auth import Principal

pytestmark = pytest.mark.asyncio

async def test_worker_atomicity_and_concurrency(seeded_workspace) -> None:
    workspace_id, user_id = seeded_workspace
    
    # 1. Create campaign & contact directly using SQL
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(workspace_id)})
        
        campaign_id = uuid4()
        contact_id = uuid4()
        seq_id = uuid4()
        
        await session.execute(text("INSERT INTO campaigns (id, workspace_id, name, status, created_by) VALUES (:cid, :wid, 'Camp', 'active', :uid)"), {"cid": str(campaign_id), "wid": str(workspace_id), "uid": str(user_id)})
        await session.execute(text("INSERT INTO contacts (id, workspace_id, first_name, last_name, email) VALUES (:cid, :wid, 'John', 'Doe', 'j@x.com')"), {"cid": str(contact_id), "wid": str(workspace_id)})
        
        await session.execute(text("INSERT INTO sequence_definitions (id, workspace_id, campaign_id, name, version_number, is_active) VALUES (:sid, :wid, :cid, 'Seq', 1, true)"), {"sid": str(seq_id), "wid": str(workspace_id), "cid": str(campaign_id)})
        await session.execute(text("INSERT INTO sequence_steps (id, sequence_id, step_number, delay_days, channel, step_type, template_subject, template_body) VALUES (:sid, :seqid, 1, 0, 'email', 'first_touch', 'Sub', 'Body')"), {"sid": str(uuid4()), "seqid": str(seq_id)})
        
        enroll_id = uuid4()
        await session.execute(text("INSERT INTO sequence_enrollments (id, workspace_id, campaign_id, sequence_id, contact_id, current_step_number, status, enrolled_by) VALUES (:eid, :wid, :cid, :seqid, :contactid, 1, 'active', :uid)"), {"eid": str(enroll_id), "wid": str(workspace_id), "cid": str(campaign_id), "seqid": str(seq_id), "contactid": str(contact_id), "uid": str(user_id)})
        
        job_id = uuid4()
        payload = {"enrollment_id": str(enroll_id), "step_number": 1}
        import json
        await session.execute(text("INSERT INTO jobs (id, workspace_id, job_type, payload, status, available_at) VALUES (:jid, :wid, 'execute_sequence_step', :payload, 'pending', now())"), {"jid": str(job_id), "wid": str(workspace_id), "payload": json.dumps(payload)})
        
        await session.commit()
    
    # Run workers until queue is empty or max tries reached
    for _ in range(10):
        await asyncio.gather(
            _claim_and_process_job(),
            _claim_and_process_job(),
            _claim_and_process_job()
        )
    
    # Verify Job is completed and exactly one Draft exists
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(workspace_id)})
        row = (await session.execute(text("SELECT status, last_error FROM jobs WHERE id = :id"), {"id": str(job_id)})).fetchone()
        job = row[0]
        err = row[1]
        print(f"JOB STATUS: {job}, ERROR: {err}")
        assert job == "completed"
        
        drafts = (await session.execute(text("SELECT COUNT(*) FROM outreach_drafts WHERE sequence_enrollment_id = :eid"), {"eid": str(enroll_id)})).scalar()
        assert drafts == 1

