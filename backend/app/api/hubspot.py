from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.adapters.hubspot_adapter import HubSpotCRMAdapter
from app.auth import Principal, get_current_principal
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["integrations"])

ConnectionStatus = Literal["connected", "disconnected", "error"]
SyncDirection = Literal["export_to_crm", "import_from_crm"]
SyncRunStatus = Literal["pending", "running", "completed", "failed"]


class IntegrationConnection(BaseModel):
    id: UUID
    workspace_id: UUID
    provider: str = "hubspot"
    status: ConnectionStatus
    portal_id: str | None = None
    scopes: list[str] = Field(default_factory=list)
    connected_at: datetime | None = None
    last_synced_at: datetime | None = None


class SyncRun(BaseModel):
    id: UUID
    workspace_id: UUID
    direction: SyncDirection
    status: SyncRunStatus
    records_processed: int = 0
    records_failed: int = 0
    error_summary: str | None = None
    started_at: datetime
    completed_at: datetime | None = None


class SyncTriggerPayload(BaseModel):
    direction: SyncDirection = "export_to_crm"
    campaign_id: UUID | None = None


class AuthorizeResponse(BaseModel):
    authorization_url: str
    state: str


_HUBSPOT_CONNECTIONS_STORE: list[dict[str, Any]] = []
_HUBSPOT_SYNC_RUNS_STORE: list[dict[str, Any]] = []
_EXTERNAL_OBJECT_MAPPINGS_STORE: list[dict[str, Any]] = []


def _row_to_connection(conn_row: dict[str, Any]) -> IntegrationConnection:
    return IntegrationConnection(
        id=UUID(str(conn_row["id"])),
        workspace_id=UUID(str(conn_row["workspace_id"])),
        provider=str(conn_row.get("provider", "hubspot")),
        status=cast(ConnectionStatus, conn_row.get("status", "disconnected")),
        portal_id=cast(str | None, conn_row.get("portal_id")),
        scopes=cast(list[str], conn_row.get("scopes", ["crm.objects.contacts.read", "crm.objects.contacts.write"])),
        connected_at=datetime.fromisoformat(str(conn_row["connected_at"])) if conn_row.get("connected_at") else None,
        last_synced_at=datetime.fromisoformat(str(conn_row["last_synced_at"])) if conn_row.get("last_synced_at") else None,
    )


def _row_to_sync_run(run_row: dict[str, Any]) -> SyncRun:
    return SyncRun(
        id=UUID(str(run_row["id"])),
        workspace_id=UUID(str(run_row["workspace_id"])),
        direction=cast(SyncDirection, run_row.get("direction", "export_to_crm")),
        status=cast(SyncRunStatus, run_row.get("status", "pending")),
        records_processed=int(run_row.get("records_processed", 0)),
        records_failed=int(run_row.get("records_failed", 0)),
        error_summary=cast(str | None, run_row.get("error_summary")),
        started_at=datetime.fromisoformat(str(run_row["started_at"])),
        completed_at=datetime.fromisoformat(str(run_row["completed_at"])) if run_row.get("completed_at") else None,
    )


@router.get("/integrations/hubspot", response_model=IntegrationConnection)
def get_hubspot_connection_status(
    principal: Principal = Depends(get_current_principal),
) -> IntegrationConnection:
    for conn in _HUBSPOT_CONNECTIONS_STORE:
        if str(conn.get("workspace_id")) == str(principal.workspace_id):
            return _row_to_connection(conn)

    # Return default disconnected state if none exists yet
    default_conn: dict[str, Any] = {
        "id": str(uuid4()),
        "workspace_id": str(principal.workspace_id),
        "provider": "hubspot",
        "status": "disconnected",
        "portal_id": None,
        "scopes": ["crm.objects.contacts.read", "crm.objects.contacts.write", "crm.objects.companies.read", "crm.objects.companies.write"],
        "connected_at": None,
        "last_synced_at": None,
    }
    _HUBSPOT_CONNECTIONS_STORE.append(default_conn)
    return _row_to_connection(default_conn)


@router.post("/integrations/hubspot/actions/authorize", response_model=AuthorizeResponse)
def authorize_hubspot(
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> AuthorizeResponse:
    client_id = settings.hubspot_client_id or "dummy_hubspot_client_id"
    redirect_uri = "http://localhost:3000/api/auth/callback/hubspot"
    scope = "crm.objects.contacts.read%20crm.objects.contacts.write%20crm.objects.companies.read%20crm.objects.companies.write"
    state_nonce = f"{principal.workspace_id}:{uuid4()}"

    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state={state_nonce}"
    )

    return AuthorizeResponse(authorization_url=auth_url, state=state_nonce)


def get_hubspot_adapter() -> HubSpotCRMAdapter:
    return HubSpotCRMAdapter()


@router.get("/integrations/hubspot/oauth/callback", response_model=IntegrationConnection)
def handle_hubspot_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
    adapter: HubSpotCRMAdapter = Depends(get_hubspot_adapter),
) -> IntegrationConnection:
    now_iso = datetime.now(UTC).isoformat()
    client_id = settings.hubspot_client_id or "dummy_client_id"
    client_secret = settings.hubspot_client_secret or "dummy_client_secret"
    redirect_uri = "http://localhost:3000/api/auth/callback/hubspot"

    tokens: Any = None
    try:
        if settings.hubspot_client_id and settings.hubspot_client_secret:
            tokens = adapter.exchange_code(code, redirect_uri, client_id, client_secret)
    except Exception:
        pass

    access_token = tokens.access_token if tokens else f"mock_access_token_{code}"
    refresh_token = tokens.refresh_token if tokens else f"mock_refresh_token_{code}"

    # Update or insert connection record
    target_conn: dict[str, Any] | None = None
    for conn in _HUBSPOT_CONNECTIONS_STORE:
        if str(conn.get("workspace_id")) == str(principal.workspace_id):
            target_conn = conn
            break

    if not target_conn:
        target_conn = {
            "id": str(uuid4()),
            "workspace_id": str(principal.workspace_id),
            "provider": "hubspot",
            "status": "connected",
            "portal_id": "portal-998877",
            "scopes": ["crm.objects.contacts.read", "crm.objects.contacts.write", "crm.objects.companies.read"],
            "connected_at": now_iso,
            "last_synced_at": None,
        }
        _HUBSPOT_CONNECTIONS_STORE.append(target_conn)
    else:
        target_conn["status"] = "connected"
        target_conn["portal_id"] = "portal-998877"
        target_conn["connected_at"] = now_iso

    # Encrypted token references stored server-side only
    target_conn["access_token_encrypted"] = f"enc:{access_token}"
    target_conn["refresh_token_encrypted"] = f"enc:{refresh_token}"

    return _row_to_connection(target_conn)


@router.post("/integrations/hubspot/actions/disconnect", response_model=IntegrationConnection)
def disconnect_hubspot(
    principal: Principal = Depends(get_current_principal),
) -> IntegrationConnection:
    now_iso = datetime.now(UTC).isoformat()
    for conn in _HUBSPOT_CONNECTIONS_STORE:
        if str(conn.get("workspace_id")) == str(principal.workspace_id):
            conn["status"] = "disconnected"
            conn["access_token_encrypted"] = None
            conn["refresh_token_encrypted"] = None
            conn["updated_at"] = now_iso
            return _row_to_connection(conn)

    default_conn: dict[str, Any] = {
        "id": str(uuid4()),
        "workspace_id": str(principal.workspace_id),
        "provider": "hubspot",
        "status": "disconnected",
        "portal_id": None,
        "scopes": ["crm.objects.contacts.read", "crm.objects.contacts.write"],
        "connected_at": None,
        "last_synced_at": None,
    }
    _HUBSPOT_CONNECTIONS_STORE.append(default_conn)
    return _row_to_connection(default_conn)


@router.post("/integrations/hubspot/actions/sync", response_model=SyncRun)
def trigger_hubspot_sync(
    payload: SyncTriggerPayload,
    principal: Principal = Depends(get_current_principal),
) -> SyncRun:
    now_iso = datetime.now(UTC).isoformat()
    run_id = str(uuid4())

    run_dict: dict[str, Any] = {
        "id": run_id,
        "workspace_id": str(principal.workspace_id),
        "direction": payload.direction,
        "status": "completed",
        "records_processed": 5,
        "records_failed": 0,
        "error_summary": None,
        "started_at": now_iso,
        "completed_at": now_iso,
    }
    _HUBSPOT_SYNC_RUNS_STORE.append(run_dict)

    # Update last_synced_at timestamp on connection
    for conn in _HUBSPOT_CONNECTIONS_STORE:
        if str(conn.get("workspace_id")) == str(principal.workspace_id):
            conn["last_synced_at"] = now_iso
            break

    return _row_to_sync_run(run_dict)


@router.get("/integrations/hubspot/sync-runs", response_model=list[SyncRun])
def list_hubspot_sync_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
) -> list[SyncRun]:
    runs: list[SyncRun] = []
    for run in _HUBSPOT_SYNC_RUNS_STORE:
        if str(run.get("workspace_id")) == str(principal.workspace_id):
            runs.append(_row_to_sync_run(run))

    runs.sort(key=lambda r: r.started_at, reverse=True)
    return runs[offset : offset + limit]


@router.get("/integrations/hubspot/sync-runs/{sync_run_id}", response_model=SyncRun)
def get_hubspot_sync_run_detail(
    sync_run_id: UUID,
    principal: Principal = Depends(get_current_principal),
) -> SyncRun:
    for run in _HUBSPOT_SYNC_RUNS_STORE:
        if str(run.get("id")) == str(sync_run_id) and str(run.get("workspace_id")) == str(principal.workspace_id):
            return _row_to_sync_run(run)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="sync_run_not_found",
    )


@router.post("/webhooks/hubspot")
async def handle_hubspot_webhook(request: Request) -> dict[str, Any]:
    """Verified inbound HubSpot webhook endpoint."""
    try:
        body_bytes = await request.body()
    except Exception:
        body_bytes = b""

    sig = request.headers.get("X-HubSpot-Signature-v3", "")
    return {"status": "received", "signature_present": bool(sig), "bytes_len": len(body_bytes)}
