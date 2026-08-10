from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import Principal, get_current_principal
from app.main import app

pytestmark = pytest.mark.asyncio



async def test_contact_crud_integration(seeded_workspace: Any) -> None:
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
            res = await client.post("/v1/contacts", json={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@acme.com",
                "title": "VP Sales"
            })
            
            if res.status_code == 500 and "connection" in res.text.lower():
                pytest.skip("Database unavailable for integration test")
                
            assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
            data = res.json()
            contact_id = data["id"]
            assert data["first_name"] == "Jane"
            assert data["last_name"] == "Doe"
            assert data["email"] == "jane@acme.com"
            
            # 2. Get
            res_get = await client.get(f"/v1/contacts/{contact_id}")
            assert res_get.status_code == 200
            
            # 3. Update
            res_patch = await client.patch(f"/v1/contacts/{contact_id}", json={"phone": "+1234567890"})
            assert res_patch.status_code == 200
            assert res_patch.json()["phone"] == "+1234567890"
            
            # 4. Cross-workspace isolation
            other_principal = Principal(
                user_id=user_id, email="test@example.com", workspace_id=uuid4(), role="owner"
            )
            app.dependency_overrides[get_current_principal] = lambda: other_principal
            
            assert (await client.get(f"/v1/contacts/{contact_id}")).status_code == 404
            assert (await client.patch(f"/v1/contacts/{contact_id}", json={"first_name": "Hacked"})).status_code == 404
            
            app.dependency_overrides[get_current_principal] = lambda: mock_principal
            
            # 5. Delete (Soft delete)
            res_delete = await client.delete(f"/v1/contacts/{contact_id}")
            assert res_delete.status_code == 200
            assert res_delete.json()["status"] == "archived"
            assert res_delete.json()["deleted_at"] is not None
            
            # 6. List filtering
            res_list = await client.get("/v1/contacts")
            assert len([c for c in res_list.json() if c["id"] == contact_id]) == 0
            
    finally:
        app.dependency_overrides.clear()
