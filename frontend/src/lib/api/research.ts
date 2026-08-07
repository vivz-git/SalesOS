export type ResearchStatus = "pending" | "in_progress" | "completed" | "failed";
export type JobStatus = "queued" | "running" | "completed" | "failed";

export interface ResearchBrief {
  id: string;
  workspace_id: string;
  account_id: string;
  contact_id: string | null;
  summary: string | null;
  key_findings: string[] | null;
  status: ResearchStatus;
  confidence_score: number | null;
  confidence_reason: string | null;
  provider: string | null;
  model: string | null;
  prompt_version: string | null;
  generated_at: string | null;
  token_usage: number | null;
  estimated_cost: number | null;
  duration_ms: number | null;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
}

export interface ResearchBriefCreatePayload {
  account_id: string;
  contact_id?: string;
  summary?: string;
  key_findings?: string[];
}

export interface ResearchBriefUpdatePayload {
  summary?: string;
  key_findings?: string[];
  confidence_score?: number;
  confidence_reason?: string;
  status?: ResearchStatus;
}

export interface ResearchSource {
  id: string;
  workspace_id: string;
  brief_id: string;
  url: string | null;
  title: string | null;
  source_type: string;
  snippet: string | null;
  confidence: number;
  raw_content_hash: string | null;
  retrieved_at: string | null;
}

export interface ResearchSourceCreatePayload {
  url?: string;
  title?: string;
  source_type?: string;
  snippet?: string;
  confidence?: number;
  raw_content_hash?: string;
}

export interface ResearchJob {
  id: string;
  workspace_id: string;
  brief_id: string;
  status: JobStatus;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface ResearchBriefFilterParams {
  account_id?: string;
  contact_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

async function request<T>(
  url: string,
  workspaceId: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("X-SalesOS-Workspace-Id", workspaceId);
  headers.set("Content-Type", "application/json");

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchResearchBriefs(
  workspaceId: string,
  params: ResearchBriefFilterParams = {}
): Promise<ResearchBrief[]> {
  const searchParams = new URLSearchParams();
  if (params.account_id) searchParams.set("account_id", params.account_id);
  if (params.contact_id) searchParams.set("contact_id", params.contact_id);
  if (params.status) searchParams.set("status", params.status);
  if (params.limit !== undefined) searchParams.set("limit", params.limit.toString());
  if (params.offset !== undefined) searchParams.set("offset", params.offset.toString());

  const queryString = searchParams.toString();
  const url = `/api/v1/research/briefs${queryString ? `?${queryString}` : ""}`;
  return request<ResearchBrief[]>(url, workspaceId);
}

export async function fetchResearchBrief(
  workspaceId: string,
  briefId: string
): Promise<ResearchBrief> {
  return request<ResearchBrief>(`/api/v1/research/briefs/${briefId}`, workspaceId);
}

export async function createResearchBrief(
  workspaceId: string,
  payload: ResearchBriefCreatePayload
): Promise<ResearchBrief> {
  return request<ResearchBrief>(`/api/v1/research/briefs`, workspaceId, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateResearchBrief(
  workspaceId: string,
  briefId: string,
  payload: ResearchBriefUpdatePayload
): Promise<ResearchBrief> {
  return request<ResearchBrief>(`/api/v1/research/briefs/${briefId}`, workspaceId, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteResearchBrief(
  workspaceId: string,
  briefId: string
): Promise<ResearchBrief> {
  return request<ResearchBrief>(`/api/v1/research/briefs/${briefId}`, workspaceId, {
    method: "DELETE",
  });
}

export async function appendResearchSource(
  workspaceId: string,
  briefId: string,
  payload: ResearchSourceCreatePayload
): Promise<ResearchSource> {
  return request<ResearchSource>(`/api/v1/research/briefs/${briefId}/sources`, workspaceId, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchResearchSources(
  workspaceId: string,
  briefId: string
): Promise<ResearchSource[]> {
  return request<ResearchSource[]>(`/api/v1/research/briefs/${briefId}/sources`, workspaceId);
}

export async function triggerResearchJob(
  workspaceId: string,
  briefId: string
): Promise<ResearchJob> {
  return request<ResearchJob>(`/api/v1/research/briefs/${briefId}/actions/trigger`, workspaceId, {
    method: "POST",
  });
}
