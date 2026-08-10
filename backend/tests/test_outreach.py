from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db import get_db_session, tenant_transaction_context

pytestmark = pytest.mark.asyncio

async def test_outreach_draft_versioning_and_delivery(seeded_workspace: Any) -> None:
    workspace_id, user_id = seeded_workspace
    
    session_generator = get_db_session()
    session = await anext(session_generator)
    
    try:
        camp_id = uuid4()
        contact_id = uuid4()
        seq_id = uuid4()
        enroll_id = uuid4()
        draft_id = uuid4()
        version_id = uuid4()
        
        async with tenant_transaction_context(session, user_id, workspace_id) as ctx:
            await ctx.execute(text("INSERT INTO campaigns (id, workspace_id, name, created_by, status) VALUES (:cid, :wid, 'Camp', :uid, 'active')"), {"cid": str(camp_id), "wid": str(workspace_id), "uid": str(user_id)})
            await ctx.execute(text("INSERT INTO contacts (id, workspace_id, first_name, last_name, email) VALUES (:cid, :wid, 'Test', 'Contact', 'test@example.com')"), {"cid": str(contact_id), "wid": str(workspace_id)})
            await ctx.execute(text("INSERT INTO sequence_definitions (id, workspace_id, campaign_id, name, version_number, is_active) VALUES (:sid, :wid, :cid, 'Seq', 1, true)"), {"sid": str(seq_id), "wid": str(workspace_id), "cid": str(camp_id)})
            await ctx.execute(text("INSERT INTO sequence_enrollments (id, workspace_id, campaign_id, sequence_id, contact_id, current_step_number, status, enrolled_by) VALUES (:eid, :wid, :cid, :sid, :contactid, 1, 'active', :uid)"), {"eid": str(enroll_id), "wid": str(workspace_id), "cid": str(camp_id), "sid": str(seq_id), "contactid": str(contact_id), "uid": str(user_id)})
            
            # A. Create OutreachDraft
            await ctx.execute(text("INSERT INTO outreach_drafts (id, workspace_id, campaign_id, contact_id, sequence_enrollment_id, sequence_step_number, status, created_by) VALUES (:did, :wid, :cid, :contactid, :eid, 1, 'draft', :uid)"), {"did": str(draft_id), "wid": str(workspace_id), "cid": str(camp_id), "contactid": str(contact_id), "eid": str(enroll_id), "uid": str(user_id)})
            
            # B. Create Initial DraftVersion
            await ctx.execute(text("INSERT INTO draft_versions (id, workspace_id, draft_id, version_number, subject, body, created_by) VALUES (:vid, :wid, :did, 1, 'Subj', 'Body', :uid)"), {"vid": str(version_id), "wid": str(workspace_id), "did": str(draft_id), "uid": str(user_id)})
            
            # Update Draft's current version
            await ctx.execute(text("UPDATE outreach_drafts SET current_version_number = 1, current_version_id = :vid WHERE id = :did"), {"vid": str(version_id), "did": str(draft_id)})
            
            # Verify Draft version is updated
            res = await ctx.execute(text("SELECT current_version_number, status FROM outreach_drafts WHERE id = :did"), {"did": str(draft_id)})
            row = res.fetchone()
            assert cast(Any, row).current_version_number == 1
            assert cast(Any, row).status == 'draft'
            
        # C. Status progression and Delivery Creation
        delivery_id = uuid4()
        idemp = str(uuid4())
        async with tenant_transaction_context(session, user_id, workspace_id) as ctx:
            await ctx.execute(text("UPDATE outreach_drafts SET status = 'approved' WHERE id = :did"), {"did": str(draft_id)})
            
            await ctx.execute(text("INSERT INTO deliveries (id, workspace_id, draft_id, version_number, contact_id, recipient_email, idempotency_key, status) VALUES (:delid, :wid, :did, 1, :contactid, 'test@example.com', :idemp, 'queued')"), {"delid": str(delivery_id), "wid": str(workspace_id), "did": str(draft_id), "contactid": str(contact_id), "idemp": idemp})
            

        async with tenant_transaction_context(session, user_id, workspace_id) as ctx:
            res = await ctx.execute(text("SELECT status FROM deliveries WHERE id = :delid"), {"delid": str(delivery_id)})
            row = res.fetchone()
            assert cast(Any, row).status == 'queued'
            
    finally:
        await session.close()
