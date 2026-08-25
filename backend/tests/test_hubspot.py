from unittest.mock import MagicMock
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from app.adapters.hubspot_adapter import HubSpotCRMAdapter
from app.auth import Principal, get_current_principal
from app.main import app


def test_get_hubspot_connection_status_and_authorize() -> None:
    user_id = uuid4()
    ws_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="admin@company.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    client = TestClient(app)

    # 1. Get status (disconnected by default)
    get_resp = client.get("/v1/integrations/hubspot")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "disconnected"

    # 2. Begin OAuth authorization
    auth_resp = client.post("/v1/integrations/hubspot/actions/authorize")
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    assert "https://app.hubspot.com/oauth/authorize" in auth_data["authorization_url"]
    assert "http://localhost:3000/api/auth/callback/hubspot" in auth_data["authorization_url"]
    assert str(ws_id) in auth_data["state"]

    app.dependency_overrides.clear()


def test_hubspot_authorize_production_url() -> None:
    user_id = uuid4()
    ws_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="admin@company.com",
        workspace_id=ws_id,
        role="admin",
    )

    from app.core.config import Settings, get_settings

    mock_settings = Settings(frontend_url="https://sales-os-frontend-7lttf3ju-vercel-vivs-projects.vercel.app")

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_settings] = lambda: mock_settings
    client = TestClient(app)

    auth_resp = client.post("/v1/integrations/hubspot/actions/authorize")
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    assert "https://sales-os-frontend-7lttf3ju-vercel-vivs-projects.vercel.app/api/auth/callback/hubspot" in auth_data["authorization_url"]

    app.dependency_overrides.clear()


def test_oauth_v3_callback_stores_tokens_encrypted() -> None:
    user_id = uuid4()
    ws_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="admin@company.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    client = TestClient(app)

    # Execute callback
    cb_resp = client.get("/v1/integrations/hubspot/oauth/callback?code=sample_code_123&state=state_456")
    assert cb_resp.status_code == 200
    conn_data = cb_resp.json()
    assert conn_data["status"] == "connected"
    assert conn_data["portal_id"] == "portal-998877"

    # Ensure sensitive tokens are NOT exposed in API response
    assert "access_token" not in conn_data
    assert "refresh_token" not in conn_data

    app.dependency_overrides.clear()


def test_trigger_hubspot_sync_and_list_runs() -> None:
    user_id = uuid4()
    ws_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="admin@company.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    client = TestClient(app)

    # Trigger sync
    sync_resp = client.post(
        "/v1/integrations/hubspot/actions/sync",
        json={"direction": "export_to_crm"},
    )
    assert sync_resp.status_code == 200
    run_data = sync_resp.json()
    assert run_data["status"] == "completed"
    assert run_data["records_processed"] == 5

    run_id = run_data["id"]

    # List sync runs
    list_resp = client.get("/v1/integrations/hubspot/sync-runs")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Get sync run detail
    detail_resp = client.get(f"/v1/integrations/hubspot/sync-runs/{run_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == run_id

    # Disconnect connection
    disc_resp = client.post("/v1/integrations/hubspot/actions/disconnect")
    assert disc_resp.status_code == 200
    assert disc_resp.json()["status"] == "disconnected"

    app.dependency_overrides.clear()


def test_hubspot_adapter_v4_association_resolution_and_v3_apis() -> None:
    mock_http = MagicMock(spec=httpx.Client)

    # Mock OAuth Token v3 Response
    token_res = MagicMock()
    token_res.json.return_value = {
        "access_token": "acc_v3_token",
        "refresh_token": "ref_v3_token",
        "expires_in": 1800,
        "token_type": "bearer",
    }
    token_res.raise_for_status = MagicMock()

    # Mock Association GET v4 Response
    assoc_res = MagicMock()
    assoc_res.status_code = 200
    assoc_res.json.return_value = {
        "results": [{"category": "HUBSPOT_DEFINED", "typeId": 1, "label": "Primary"}]
    }

    # Mock Object Upsert Response
    object_res = MagicMock()
    object_res.status_code = 200
    object_res.json.return_value = {"id": "hs-obj-1001", "properties": {"email": "test@company.com"}}
    object_res.raise_for_status = MagicMock()

    mock_http.post.side_effect = lambda url, **kwargs: token_res if "oauth/v3/token" in url else object_res
    mock_http.get.return_value = assoc_res
    mock_http.patch.return_value = object_res
    mock_http.put.return_value = MagicMock(status_code=200)

    adapter = HubSpotCRMAdapter(http_client=mock_http)

    # 1. Test OAuth v3 exchange
    token_resp = adapter.exchange_code("code1", "http://redirect", "cid", "csecret")
    assert token_resp.access_token == "acc_v3_token"
    assert token_resp.refresh_token == "ref_v3_token"

    # 2. Test OAuth v3 refresh
    ref_resp = adapter.refresh_access_token("ref_v3_token", "cid", "csecret")
    assert ref_resp.access_token == "acc_v3_token"

    # 3. Test GET v4 association label resolution
    assoc_type = adapter.resolve_association_type("acc_v3_token", "contact", "company")
    assert assoc_type.category == "HUBSPOT_DEFINED"
    assert assoc_type.type_id == 1

    # 4. Test Contact & Company upsert
    contact = adapter.create_or_update_contact("acc_v3_token", "test@company.com", "Jane", "Doe")
    assert contact["id"] == "hs-obj-1001"

    company = adapter.create_or_update_company("acc_v3_token", "targetcompany.com", "Target Co")
    assert company["id"] == "hs-obj-1001"

    # 5. Test object association
    associated = adapter.associate_objects("acc_v3_token", "contact", "c1", "company", "co1", assoc_type)
    assert associated is True

    # 6. Test Sales Email activity
    activity = adapter.create_sales_email_activity("acc_v3_token", "Subject", "Body", direction="EMAIL")
    assert activity["id"] == "hs-obj-1001"
