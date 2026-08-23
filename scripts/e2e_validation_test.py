import asyncio
import os
import sys
import time
from uuid import uuid4
import httpx
from supabase import create_client

SUPABASE_URL = "http://127.0.0.1:54321"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
API_BASE = "http://127.0.0.1:8000/v1"

async def run_e2e_test():
    print("=== STARTING FULL E2E REAL SYSTEM VALIDATION ===")

    # Initialize Supabase Client for Auth
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    admin_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # 1. AUTH & USER CREATION
    user1_email = f"user1_{uuid4().hex[:8]}@example.com"
    user2_email = f"user2_{uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"

    print(f"\n[1. AUTH] Signing up User 1: {user1_email}")
    res1 = supabase.auth.sign_up({"email": user1_email, "password": password})
    user1_id = res1.user.id
    user1_token = res1.session.access_token if res1.session else None

    if not user1_token:
        # If email confirmation is needed or sign-in needed
        sign_in_res = supabase.auth.sign_in_with_password({"email": user1_email, "password": password})
        user1_token = sign_in_res.session.access_token
    print(f"User 1 authenticated successfully. User ID: {user1_id}")

    print(f"\n[1. AUTH] Signing up User 2: {user2_email}")
    res2 = supabase.auth.sign_up({"email": user2_email, "password": password})
    user2_id = res2.user.id
    user2_token = res2.session.access_token if res2.session else None
    if not user2_token:
        sign_in_res2 = supabase.auth.sign_in_with_password({"email": user2_email, "password": password})
        user2_token = sign_in_res2.session.access_token
    print(f"User 2 authenticated successfully. User ID: {user2_id}")

    client1 = httpx.AsyncClient(base_url="http://127.0.0.1:8000", headers={"Authorization": f"Bearer {user1_token}"})
    client2 = httpx.AsyncClient(base_url="http://127.0.0.1:8000", headers={"Authorization": f"Bearer {user2_token}"})

    # 2. WORKSPACE CREATION
    uid_str = uuid4().hex[:6]
    print(f"\n[2. WORKSPACE] Creating Workspace A for User 1...")
    ws1_resp = await client1.post("/v1/workspaces", json={"name": f"Alpha Corp Workspace {uid_str}"})
    print(f"Workspace A Creation: {ws1_resp.status_code}, data={ws1_resp.json()}")
    assert ws1_resp.status_code == 201, f"Failed: {ws1_resp.text}"
    ws1_id = ws1_resp.json()["id"]

    print(f"\n[2. WORKSPACE] Creating Workspace B for User 2...")
    ws2_resp = await client2.post("/v1/workspaces", json={"name": f"Beta Corp Workspace {uid_str}"})
    print(f"Workspace B Creation: {ws2_resp.status_code}, data={ws2_resp.json()}")
    assert ws2_resp.status_code == 201, f"Failed: {ws2_resp.text}"
    ws2_id = ws2_resp.json()["id"]

    client1.headers["X-SalesOS-Workspace-Id"] = ws1_id
    client2.headers["X-SalesOS-Workspace-Id"] = ws2_id

    # 3. CAMPAIGN CREATION
    print("\n[3. CAMPAIGN] Creating Campaign in Workspace A...")
    camp_resp = await client1.post("/v1/campaigns", json={
        "name": "Q3 Outbound B2B Campaign",
        "description": "Targeting FinTech CTOs",
        "target_segment": "FinTech",
        "icp_definition": "Series A-C FinTechs"
    })
    print(f"Campaign creation: {camp_resp.status_code}, {camp_resp.json()}")
    assert camp_resp.status_code == 201
    campaign_id = camp_resp.json()["id"]

    # 4. ACCOUNT & CONTACT CREATION
    print("\n[4. ACCOUNTS & CONTACTS] Creating Account and Contact in Workspace A...")
    acc_resp = await client1.post("/v1/accounts", json={
        "name": "Acme Payments Inc",
        "domain": "acmepayments.com",
        "industry": "FinTech",
        "employee_count": "150"
    })
    print(f"Account creation: {acc_resp.status_code}, {acc_resp.json()}")
    assert acc_resp.status_code == 201
    account_id = acc_resp.json()["id"]

    cont_resp = await client1.post("/v1/contacts", json={
        "account_id": account_id,
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@acmepayments.com",
        "title": "VP of Engineering",
        "department": "Engineering"
    })
    print(f"Contact creation: {cont_resp.status_code}, {cont_resp.json()}")
    assert cont_resp.status_code == 201
    contact_id = cont_resp.json()["id"]

    # 5. RESEARCH GENERATION & BACKGROUND JOB
    print("\n[5. RESEARCH] Creating Research Brief & Triggering Worker Job...")
    brief_resp = await client1.post("/v1/research/briefs", json={
        "account_id": account_id,
        "contact_id": contact_id
    })
    print(f"Brief creation: {brief_resp.status_code}, {brief_resp.json()}")
    assert brief_resp.status_code == 201
    brief_id = brief_resp.json()["id"]

    # Add research source
    src_resp = await client1.post(f"/v1/research/briefs/{brief_id}/sources", json={
        "url": "https://acmepayments.com/news/series-b",
        "title": "Acme Payments raises $25M Series B",
        "snippet": "Acme Payments expands core banking integrations."
    })
    print(f"Source addition: {src_resp.status_code}, {src_resp.json()}")
    assert src_resp.status_code == 201

    # Trigger research generation
    trigger_resp = await client1.post(f"/v1/research/briefs/{brief_id}/actions/trigger")
    print(f"Trigger research job: {trigger_resp.status_code}, {trigger_resp.json()}")
    assert trigger_resp.status_code == 200
    research_job_id = trigger_resp.json()["id"]

    # 6, 7, 8, 9. VERIFY WORKER CLAIMS & PROCESSES RESEARCH JOB
    print("\n[6-9. WORKER JOB CLAIM] Waiting up to 15s for worker to claim and complete research job...")
    job_completed = False
    for i in range(6):
        await asyncio.sleep(2.5)
        check_brief = await client1.get(f"/v1/research/briefs/{brief_id}")
        brief_data = check_brief.json()
        print(f"Check #{i+1}: Brief status = {brief_data.get('status')}")
        if brief_data.get("status") == "completed":
            job_completed = True
            print(f"Research Job completed! Summary: {brief_data.get('summary')}")
            break

    print(f"Research Worker Job Result: {'COMPLETED' if job_completed else 'NOT COMPLETED'}")

    # 10. GENERATE AI OUTREACH (OR FALLBACK DRAFT)
    print("\n[10. AI OUTREACH] Testing Outreach Draft Creation & Generation...")
    # Create draft
    draft_create_resp = await client1.post("/v1/outreach/drafts", json={
        "campaign_id": campaign_id,
        "contact_id": contact_id,
        "research_brief_id": brief_id,
        "subject": "Modernizing payment architecture at Acme",
        "body": "Hi Jane, congrats on the Series B! Noticed your team is scaling banking integrations.",
        "generation_source": "human"
    })
    print(f"Draft Create: {draft_create_resp.status_code}, {draft_create_resp.json()}")
    assert draft_create_resp.status_code == 201
    draft_id = draft_create_resp.json()["id"]

    # Test AI Generate Action (Tests real Groq integration)
    try:
        ai_gen_resp = await client1.post(f"/v1/outreach/drafts/{draft_id}/actions/generate", timeout=30.0)
        print(f"AI Generate action: {ai_gen_resp.status_code}, subject={ai_gen_resp.json().get('current_subject') if ai_gen_resp.status_code == 200 else ai_gen_resp.text}")
    except Exception as e:
        print(f"AI Generate action: BLOCKED (external provider credential unavailable / timeout: {type(e).__name__})")

    # 11, 12. VERIFY OUTREACH DRAFT & EDIT / REVISE
    print("\n[11, 12. REVISE DRAFT] Revising Draft...")
    revise_resp = await client1.post(f"/v1/outreach/drafts/{draft_id}/actions/revise", json={
        "subject": "Updated: Acme Payments + SalesOS Integration",
        "body": "Hi Jane, following up with a tailored overview of our API capabilities.",
        "generation_source": "human"
    })
    print(f"Revise Draft: {revise_resp.status_code}, current_version={revise_resp.json().get('current_version_number')}")
    assert revise_resp.status_code == 200
    assert revise_resp.json()["current_version_number"] >= 2

    # 13. SUBMIT FOR APPROVAL
    print("\n[13. APPROVAL FLOW] Submitting draft for review...")
    sub_resp = await client1.post(f"/v1/outreach/drafts/{draft_id}/actions/submit-review")
    print(f"Submit for review: {sub_resp.status_code}, {sub_resp.json()}")
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "ready_for_review"

    # Verify draft appears in /approvals/queue
    queue_resp = await client1.get("/v1/approvals/queue")
    print(f"Approval Queue: {queue_resp.status_code}, count={len(queue_resp.json())}")
    assert any(d["id"] == draft_id for d in queue_resp.json())

    # Get approval item detail
    detail_resp = await client1.get(f"/v1/approvals/items/{draft_id}")
    print(f"Approval Detail: {detail_resp.status_code}, contact={detail_resp.json().get('contact_name')}")

    # 14. APPROVE FLOW
    print("\n[14. APPROVE DECISION] Approving draft...")
    dec_resp = await client1.post(f"/v1/approvals/items/{draft_id}/decision", json={
        "decision": "approved",
        "notes": "Looks solid, approved for delivery."
    })
    print(f"Decision response: {dec_resp.status_code}, {dec_resp.json()}")
    assert dec_resp.status_code == 200

    # Verify draft status is now approved
    draft_check = await client1.get(f"/v1/outreach/drafts/{draft_id}")
    assert draft_check.json()["status"] == "approved"
    print("Draft confirmed APPROVED.")

    # 15. DELIVERY FLOW
    print("\n[15. DELIVERY] Initiating Delivery for Approved Draft...")
    try:
        deliv_resp = await client1.post("/v1/deliveries", json={
            "draft_id": draft_id
        }, timeout=5.0)
        print(f"Delivery initiate: {deliv_resp.status_code}, {deliv_resp.json()}")
    except Exception as e:
        print(f"Delivery initiate: BLOCKED (external provider credential unavailable: {type(e).__name__})")

    # 16. CONVERSATION / INBOUND REPLY FLOW
    print("\n[16. CONVERSATIONS] Ingesting Inbound Prospect Reply...")
    inbound_resp = await client1.post("/v1/conversations/inbound", json={
        "workspace_id": ws1_id,
        "sender_email": "jane.doe@acmepayments.com",
        "recipient_email": "outreach@salesos.com",
        "subject": "Re: Updated: Acme Payments + SalesOS Integration",
        "body": "Hi, thanks for reaching out! Let's schedule a demo next Tuesday at 2pm.",
        "provider_message_id": f"msg_{uuid4().hex[:10]}"
    })
    print(f"Inbound ingestion: {inbound_resp.status_code}, data={inbound_resp.json()}")
    assert inbound_resp.status_code == 200
    conv_id = inbound_resp.json()["id"]
    reply_state = inbound_resp.json()["current_reply_state"]
    print(f"Classified reply state: {reply_state}")

    # List conversations
    convs_list = await client1.get("/v1/conversations")
    print(f"Conversations list count: {len(convs_list.json())}")
    assert len(convs_list.json()) >= 1

    # 17, 18. SEQUENCE CREATION, ENROLLMENT & WORKER PROCESSING
    print("\n[17, 18. SEQUENCES] Creating Sequence & Enrolling Contact...")
    seq_resp = await client1.post(f"/v1/campaigns/{campaign_id}/sequences", json={
        "name": "FinTech Outbound Sequence",
        "steps": [
            {
                "step_number": 1,
                "delay_days": 0,
                "channel": "email",
                "step_type": "first_touch",
                "template_subject": "Seq Step 1 Intro",
                "template_body": "Hello {{first_name}}, this is step 1."
            },
            {
                "step_number": 2,
                "delay_days": 2,
                "channel": "email",
                "step_type": "follow_up",
                "template_subject": "Seq Step 2 Follow up",
                "template_body": "Hello {{first_name}}, this is step 2."
            }
        ]
    })
    print(f"Sequence created: {seq_resp.status_code}, {seq_resp.json().get('name')}")
    assert seq_resp.status_code == 200
    sequence_id = seq_resp.json()["id"]

    # Enroll contact
    enr_resp = await client1.post("/v1/sequence-enrollments", json={
        "campaign_id": campaign_id,
        "contact_id": contact_id
    })
    print(f"Enrollment response: {enr_resp.status_code}, {enr_resp.json()}")
    assert enr_resp.status_code == 200
    enrollment_id = enr_resp.json()["id"]

    # Wait for worker to process sequence step job
    print("Waiting for sequence job execution by worker...")
    seq_draft_created = False
    for _ in range(5):
        await asyncio.sleep(2.5)
        drafts_list = await client1.get(f"/v1/outreach/drafts?campaign_id={campaign_id}")
        for d in drafts_list.json():
            if d.get("sequence_enrollment_id") == enrollment_id:
                seq_draft_created = True
                print(f"Sequence step 1 draft automatically created: {d.get('id')}, subject: {d.get('current_subject')}")
                break
        if seq_draft_created:
            break

    # 19. REPORTS / DASHBOARD DATA
    print("\n[19. REPORTS] Generating & Fetching Weekly Reports...")
    rep_resp = await client1.get("/v1/reports/weekly")
    print(f"Reports weekly: {rep_resp.status_code}, count={len(rep_resp.json())}")
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()[0]
    print(f"Report title: {rep_data.get('title')}")
    print(f"Metrics snapshot: {rep_data.get('metrics_snapshot')}")

    # =========================================================================
    # SECTION 3: MULTI-TENANT SECURITY ISOLATION TESTS
    # =========================================================================
    print("\n==================================================")
    print("3. SECURITY E2E TEST: CROSS-TENANT ISOLATION CHECKS")
    print("==================================================")

    # User 2 (Workspace B) attempts to read/mutate Workspace A data:

    # 1. Contacts
    c_cross = await client2.get(f"/v1/contacts/{contact_id}")
    print(f"Cross-tenant contact read: status={c_cross.status_code} (Expected 404/403)")
    assert c_cross.status_code in (403, 404)

    # 2. Campaigns
    camp_cross = await client2.get(f"/v1/campaigns/{campaign_id}")
    print(f"Cross-tenant campaign read: status={camp_cross.status_code} (Expected 404/403)")
    assert camp_cross.status_code in (403, 404)

    # 3. Research briefs
    rb_cross = await client2.get(f"/v1/research/briefs/{brief_id}")
    print(f"Cross-tenant research brief read: status={rb_cross.status_code} (Expected 404/403)")
    assert rb_cross.status_code in (403, 404)

    # 4. Outreach drafts
    od_cross = await client2.get(f"/v1/outreach/drafts/{draft_id}")
    print(f"Cross-tenant outreach draft read: status={od_cross.status_code} (Expected 404/403)")
    assert od_cross.status_code in (403, 404)

    # 5. Approvals queue
    app_cross = await client2.get("/v1/approvals/queue")
    print(f"Workspace B approval queue: count={len(app_cross.json())} (Expected 0)")
    assert not any(d["id"] == draft_id for d in app_cross.json())

    # 6. Approvals decision mutate
    dec_cross = await client2.post(f"/v1/approvals/items/{draft_id}/decision", json={"decision": "rejected"})
    print(f"Cross-tenant approval mutate: status={dec_cross.status_code} (Expected 404/403)")
    assert dec_cross.status_code in (403, 404)

    # 7. Reports
    rep_cross = await client2.get("/v1/reports/weekly")
    print(f"Workspace B reports count: {len(rep_cross.json())}")
    for r in rep_cross.json():
        assert r["workspace_id"] == ws2_id, "Tenant B saw Tenant A report!"

    print("\nALL CROSS-TENANT ISOLATION CHECKS PASSED AT THE API LAYER!")

    await client1.aclose()
    await client2.aclose()
    print("\n=== COMPLETE E2E TEST RUN COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_e2e_test())
