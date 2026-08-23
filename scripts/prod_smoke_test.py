import asyncio
import uuid
import httpx
from supabase import create_client

PROD_SUPABASE_URL = "https://pfkrgczcyxqhidlwlarh.supabase.co"
PROD_SUPABASE_ANON_KEY = "sb_publishable_Ceg-8xS6muKiPU1S3BrPgQ_wZHJEPga"
PROD_API_BASE = "https://salesos-production-927e.up.railway.app"

async def run_prod_smoke_test():
    print(f"=== PRODUCTION AUTHENTICATED E2E SMOKE TEST ===")
    print(f"API Target: {PROD_API_BASE}")
    print(f"Supabase Target: {PROD_SUPABASE_URL}")

    # 1. Check /health
    async with httpx.AsyncClient() as client:
        health_resp = await client.get(f"{PROD_API_BASE}/health")
        print(f"\n[GET /health] -> HTTP {health_resp.status_code}: {health_resp.json()}")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"

    # 2. Supabase Auth Signup / Signin
    print("\n[Auth] Initializing Supabase client & signing up smoke test user...")
    supabase = create_client(PROD_SUPABASE_URL, PROD_SUPABASE_ANON_KEY)
    
    unique_id = uuid.uuid4().hex[:8]
    email = f"smoketest_{unique_id}@gmail.com"
    password = f"SmokePass_{unique_id}!99"

    auth_res = supabase.auth.sign_up({"email": email, "password": password})
    user_id = auth_res.user.id
    token = auth_res.session.access_token if auth_res.session else None

    if not token:
        print("[Auth] Signing in to retrieve session token...")
        sign_in_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        token = sign_in_res.session.access_token

    print(f"[Auth] Session established successfully! User ID: {user_id}")
    print(f"[Auth] Access Token: Bearer {token[:12]}...{token[-8:]}")

    # 3. Authenticated Client
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(base_url=PROD_API_BASE, headers=headers, timeout=20.0) as client:
        # 4. Workspaces
        print("\n[Workspaces] Calling GET /v1/workspaces...")
        ws_get_res = await client.get("/v1/workspaces")
        print(f"[GET /v1/workspaces] -> HTTP {ws_get_res.status_code}: {ws_get_res.json()}")
        assert ws_get_res.status_code == 200, f"GET /v1/workspaces failed: {ws_get_res.text}"

        print("\n[Workspaces] Calling POST /v1/workspaces to create smoke test workspace...")
        ws_create_res = await client.post("/v1/workspaces", json={
            "name": f"Production Smoke Workspace {unique_id}",
            "slug": f"smoke-ws-{unique_id}"
        })
        print(f"[POST /v1/workspaces] -> HTTP {ws_create_res.status_code}: {ws_create_res.json()}")
        assert ws_create_res.status_code in (200, 201), f"POST /v1/workspaces failed: {ws_create_res.text}"
        workspace_id = ws_create_res.json()["id"]

        # Attach workspace header for tenant-scoped operations
        client.headers["X-SalesOS-Workspace-Id"] = workspace_id

        # 5. /v1/me
        print("\n[Identity] Calling GET /v1/me...")
        me_res = await client.get("/v1/me")
        print(f"[GET /v1/me] -> HTTP {me_res.status_code}: {me_res.json()}")
        assert me_res.status_code == 200, f"GET /v1/me failed: {me_res.text}"

        # 6. Campaigns
        print("\n[Campaigns] Calling POST /v1/campaigns...")
        camp_create_res = await client.post("/v1/campaigns", json={
            "name": f"Smoke Test Outbound Campaign {unique_id}",
            "description": "Production verification campaign",
            "target_segment": "Enterprise SaaS",
            "icp_definition": "Series B+ B2B software companies"
        })
        print(f"[POST /v1/campaigns] -> HTTP {camp_create_res.status_code}: {camp_create_res.json()}")
        assert camp_create_res.status_code in (200, 201), f"POST /v1/campaigns failed: {camp_create_res.text}"
        campaign_id = camp_create_res.json()["id"]

        print("[Campaigns] Calling GET /v1/campaigns...")
        camp_get_res = await client.get("/v1/campaigns")
        print(f"[GET /v1/campaigns] -> HTTP {camp_get_res.status_code} (Found {len(camp_get_res.json())} campaigns)")
        assert camp_get_res.status_code == 200

        # 7. Accounts
        print("\n[Accounts] Calling POST /v1/accounts...")
        acc_create_res = await client.post("/v1/accounts", json={
            "campaign_id": campaign_id,
            "name": f"Acme Smoke Corp {unique_id}",
            "domain": f"acme-{unique_id}.com",
            "industry": "Software",
            "employee_count": "250"
        })
        print(f"[POST /v1/accounts] -> HTTP {acc_create_res.status_code}: {acc_create_res.json()}")
        assert acc_create_res.status_code in (200, 201), f"POST /v1/accounts failed: {acc_create_res.text}"
        account_id = acc_create_res.json()["id"]

        print("[Accounts] Calling GET /v1/accounts...")
        acc_get_res = await client.get("/v1/accounts")
        print(f"[GET /v1/accounts] -> HTTP {acc_get_res.status_code} (Found {len(acc_get_res.json())} accounts)")
        assert acc_get_res.status_code == 200

        # 8. Contacts
        print("\n[Contacts] Calling POST /v1/contacts...")
        cont_create_res = await client.post("/v1/contacts", json={
            "account_id": account_id,
            "first_name": "Alex",
            "last_name": "Taylor",
            "email": f"alex.taylor@{unique_id}.io",
            "title": "Head of Engineering",
            "department": "Engineering"
        })
        print(f"[POST /v1/contacts] -> HTTP {cont_create_res.status_code}: {cont_create_res.json()}")
        assert cont_create_res.status_code in (200, 201), f"POST /v1/contacts failed: {cont_create_res.text}"

        print("[Contacts] Calling GET /v1/contacts...")
        cont_get_res = await client.get("/v1/contacts")
        print(f"[GET /v1/contacts] -> HTTP {cont_get_res.status_code} (Found {len(cont_get_res.json())} contacts)")
        assert cont_get_res.status_code == 200

    print("\n=== ALL AUTHENTICATED PRODUCTION SMOKE TESTS PASSED ===")

if __name__ == "__main__":
    asyncio.run(run_prod_smoke_test())
