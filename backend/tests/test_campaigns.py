from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import Principal, get_current_principal
from app.main import app

pytestmark = pytest.mark.asyncio



async def test_campaign_crud_integration(seeded_workspace: Any) -> None:
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
            res = await client.post("/v1/campaigns", json={
                "name": "Integration Campaign",
                "description": "Integration test"
            })
            
            if res.status_code == 500 and "connection" in res.text.lower():
                pytest.skip("Database unavailable for integration test")
                
            assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
            data = res.json()
            campaign_id = data["id"]
            assert data["name"] == "Integration Campaign"
            
            # 2. Get
            res_get = await client.get(f"/v1/campaigns/{campaign_id}")
            assert res_get.status_code == 200
            
            # 3. Update
            res_patch = await client.patch(f"/v1/campaigns/{campaign_id}", json={"name": "Updated Campaign"})
            assert res_patch.status_code == 200
            assert res_patch.json()["name"] == "Updated Campaign"
            
            # 4. Cross-workspace isolation check
            other_workspace_id = uuid4()
            other_principal = Principal(
                user_id=user_id, email="test@example.com", workspace_id=other_workspace_id, role="owner"
            )
            app.dependency_overrides[get_current_principal] = lambda: other_principal
            
            res_cross = await client.get(f"/v1/campaigns/{campaign_id}")
            assert res_cross.status_code == 404, "Cross-workspace read should be 404"
            
            res_cross_patch = await client.patch(f"/v1/campaigns/{campaign_id}", json={"name": "Hacked"})
            assert res_cross_patch.status_code == 404, "Cross-workspace update should be 404"
            
            app.dependency_overrides[get_current_principal] = lambda: mock_principal
            
            # 5. Delete (Soft delete)
            res_delete = await client.delete(f"/v1/campaigns/{campaign_id}")
            assert res_delete.status_code == 200
            assert res_delete.json()["status"] == "archived"
            assert res_delete.json()["deleted_at"] is not None
            
            # 6. List filters out soft-deleted
            res_list = await client.get("/v1/campaigns")
            assert res_list.status_code == 200
            assert len([c for c in res_list.json() if c["id"] == campaign_id]) == 0
            
            res_list_archived = await client.get("/v1/campaigns?status=archived")
            assert res_list_archived.status_code == 200
            assert any(c["id"] == campaign_id for c in res_list_archived.json())
            
    finally:
        app.dependency_overrides.clear()
