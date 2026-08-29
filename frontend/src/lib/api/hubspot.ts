import { request } from "./client";

export type ConnectionStatus = "connected" | "disconnected" | "error";
export type SyncDirection = "export_to_crm" | "import_from_crm";
export type SyncRunStatus = "pending" | "running" | "completed" | "failed";

export interface IntegrationConnection {
  id: string;
  workspace_id: string;
  provider: string;
  status: ConnectionStatus;
  portal_id?: string | null;
  scopes: string[];
  connected_at?: string | null;
  last_synced_at?: string | null;
}

export interface SyncRun {
  id: string;
  workspace_id: string;
  direction: SyncDirection;
  status: SyncRunStatus;
  records_processed: number;
  records_failed: number;
  error_summary?: string | null;
  started_at: string;
  completed_at?: string | null;
}

export interface AuthorizeResponse {
  authorization_url: string;
  state: string;
}

export async function fetchHubspotStatus(workspaceId: string): Promise<IntegrationConnection> {
  return request<IntegrationConnection>("/api/v1/integrations/hubspot", workspaceId);
}

export async function authorizeHubspot(workspaceId: string): Promise<AuthorizeResponse> {
  return request<AuthorizeResponse>("/api/v1/integrations/hubspot/actions/authorize", workspaceId, {
    method: "POST",
  });
}

export async function disconnectHubspot(workspaceId: string): Promise<IntegrationConnection> {
  return request<IntegrationConnection>("/api/v1/integrations/hubspot/actions/disconnect", workspaceId, {
    method: "POST",
  });
}

export async function triggerHubspotSync(
  workspaceId: string,
  direction: SyncDirection = "export_to_crm"
): Promise<SyncRun> {
  return request<SyncRun>("/api/v1/integrations/hubspot/actions/sync", workspaceId, {
    method: "POST",
    body: JSON.stringify({ direction }),
  });
}

export async function fetchHubspotSyncRuns(
  workspaceId: string,
  limit: number = 20,
  offset: number = 0
): Promise<SyncRun[]> {
  return request<SyncRun[]>(
    `/api/v1/integrations/hubspot/sync-runs?limit=${limit}&offset=${offset}`,
    workspaceId
  );
}

export async function fetchHubspotSyncRunDetail(
  workspaceId: string,
  syncRunId: string
): Promise<SyncRun> {
  return request<SyncRun>(`/api/v1/integrations/hubspot/sync-runs/${syncRunId}`, workspaceId);
}
