import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.exc import OperationalError

from app.main import app
from app.auth import Principal, get_current_principal

pytestmark = pytest.mark.asyncio

async def test_account_crud_integration(seeded_workspace):
    workspace_id, user_id = seeded_workspace
    
    mock_principal = Principal(
        user_id=user_id,
        email="test@example.com",
        workspace_id=workspace_id,
        role="owner"
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Create
            res = await client.post("/v1/accounts", json={
                "name": "Acme Corp",
                "domain": "acme.com",
                "industry": "Manufacturing"
            })
            
            if res.status_code == 500 and "connection" in res.text.lower():
                pytest.skip("Database unavailable for integration test")
                
            assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
            data = res.json()
            account_id = data["id"]
            assert data["name"] == "Acme Corp"
            assert data["domain"] == "acme.com"
            
            # 2. Get
            res_get = await client.get(f"/v1/accounts/{account_id}")
            assert res_get.status_code == 200
            
            # 3. Update
            res_patch = await client.patch(f"/v1/accounts/{account_id}", json={"employee_count": "1000-5000"})
            assert res_patch.status_code == 200
            assert res_patch.json()["employee_count"] == "1000-5000"
            
            # 4. Cross-workspace isolation
            other_principal = Principal(
                user_id=user_id, email="test@example.com", workspace_id=uuid4(), role="owner"
            )
            app.dependency_overrides[get_current_principal] = lambda: other_principal
            
            assert (await client.get(f"/v1/accounts/{account_id}")).status_code == 404
            assert (await client.patch(f"/v1/accounts/{account_id}", json={"name": "Hacked"})).status_code == 404
            
            app.dependency_overrides[get_current_principal] = lambda: mock_principal
            
            # 5. Delete (Soft delete)
            res_delete = await client.delete(f"/v1/accounts/{account_id}")
            assert res_delete.status_code == 200
            assert res_delete.json()["status"] == "archived"
            assert res_delete.json()["deleted_at"] is not None
            
            # 6. List filtering
            res_list = await client.get("/v1/accounts")
            assert len([a for a in res_list.json() if a["id"] == account_id]) == 0
            
    finally:
        app.dependency_overrides.clear()
