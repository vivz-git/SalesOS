import pytest
from uuid import uuid4
from sqlalchemy import text
from app.db import AsyncSessionLocal
from app.worker import _execute_job
from app.models import JobModel
import json

pytestmark = pytest.mark.asyncio

async def test_worker_cannot_dispatch_email(seeded_workspace, monkeypatch) -> None:
    # 1. Monkeypatch EmailProvider to raise an exception if it's somehow called
    def mock_send(*args, **kwargs):
        raise RuntimeError("Worker attempted to send an email! GOVERNANCE VIOLATION!")
        
    monkeypatch.setattr("app.adapters.resend_provider.ResendEmailProvider.send_email", mock_send)
    
    workspace_id, user_id = seeded_workspace
    
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
        await session.execute(text("INSERT INTO jobs (id, workspace_id, job_type, payload, status, available_at) VALUES (:jid, :wid, 'execute_sequence_step', :payload, 'pending', now())"), {"jid": str(job_id), "wid": str(workspace_id), "payload": json.dumps(payload)})
        await session.commit()

        job_query = await session.execute(text("SELECT * FROM jobs WHERE id = :jid"), {"jid": str(job_id)})
        job_row = job_query.mappings().first()
        
        # Need an actual JobModel object for the worker method signature
        job = JobModel(**job_row)
        
        # Worker must succeed in creating draft, without hitting the mock exception
        await _execute_job(session, job)
        
        drafts = (await session.execute(text("SELECT COUNT(*) FROM outreach_drafts WHERE sequence_enrollment_id = :eid"), {"eid": str(enroll_id)})).scalar()
        assert drafts == 1
