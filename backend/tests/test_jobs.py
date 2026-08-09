import pytest
import json
from uuid import uuid4
from datetime import datetime, UTC, timedelta
from sqlalchemy import text
from app.db import AsyncSessionLocal
from app.worker import _recover_stale_jobs

pytestmark = pytest.mark.asyncio

async def test_job_stale_recovery(seeded_workspace) -> None:
    workspace_id, _ = seeded_workspace
    
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(workspace_id)})
        
        job_id = uuid4()
        locked = datetime.now(UTC) - timedelta(minutes=15)
        
        await session.execute(
            text("INSERT INTO jobs (id, workspace_id, job_type, payload, status, available_at, locked_at) VALUES (:id, :wid, 'dummy', '{}', 'running', now(), :locked)"),
            {"id": str(job_id), "wid": str(workspace_id), "locked": locked}
        )
        await session.commit()
        
    await _recover_stale_jobs()
    
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(workspace_id)})
        status = (await session.execute(text("SELECT status FROM jobs WHERE id = :id"), {"id": str(job_id)})).scalar()
        assert status == "pending"
