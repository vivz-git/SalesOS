import { request } from './client';
export type DraftStatus = "draft" | "ready_for_review" | "approved" | "rejected" | "superseded" | "archived";
export type GenerationSource = "human" | "ai_generated" | "template" | "ai_assisted";

export interface EvidenceReference {
  url?: string;
  title?: string;
  snippet?: string;
  source_type?: string;
}

export interface DraftVersion {
  id: string;
  workspace_id: string;
  draft_id: string;
  version_number: number;
  subject: string | null;
  body?: string;
  generation_source: GenerationSource;
  provider: string | null;
  model: string | null;
  prompt_version: string | null;
  research_brief_id: string | null;
  research_brief_version: number | null;
  evidence_references: EvidenceReference[] | null;
  created_by: string | null;
  created_at: string | null;
}

export interface OutreachDraft {
  id: string;
  workspace_id: string;
  campaign_id: string;
  contact_id: string;
  research_brief_id: string | null;
  current_version_id: string | null;
  current_version_number: number;
  current_subject: string | null;
  current_body: string | null;
  status: DraftStatus;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
  versions?: DraftVersion[];
}

export interface OutreachDraftCreatePayload {
  campaign_id: string;
  contact_id: string;
  research_brief_id?: string;
  subject?: string;
  body?: string;
  generation_source?: GenerationSource;
  provider?: string;
  model?: string;
  prompt_version?: string;
  evidence_references?: EvidenceReference[];
}

export interface OutreachDraftRevisePayload {
  subject?: string;
  body?: string;
  generation_source?: GenerationSource;
  provider?: string;
  model?: string;
  prompt_version?: string;
  research_brief_id?: string;
  evidence_references?: EvidenceReference[];
}

export interface OutreachDraftFilterParams {
  campaign_id?: string;
  contact_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}


export async function fetchOutreachDrafts(
  workspaceId: string,
  params: OutreachDraftFilterParams = {}
): Promise<OutreachDraft[]> {
  const searchParams = new URLSearchParams();
  if (params.campaign_id) searchParams.set("campaign_id", params.campaign_id);
  if (params.contact_id) searchParams.set("contact_id", params.contact_id);
  if (params.status) searchParams.set("status", params.status);
  if (params.limit !== undefined) searchParams.set("limit", params.limit.toString());
  if (params.offset !== undefined) searchParams.set("offset", params.offset.toString());

  const queryString = searchParams.toString();
  const url = `/api/v1/outreach/drafts${queryString ? `?${queryString}` : ""}`;
  return request<OutreachDraft[]>(url, workspaceId);
}

export async function fetchOutreachDraft(
  workspaceId: string,
  draftId: string
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts/${draftId}`, workspaceId);
}

export async function createOutreachDraft(
  workspaceId: string,
  payload: OutreachDraftCreatePayload
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts`, workspaceId, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviseOutreachDraft(
  workspaceId: string,
  draftId: string,
  payload: OutreachDraftRevisePayload
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts/${draftId}/actions/revise`, workspaceId, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchDraftVersions(
  workspaceId: string,
  draftId: string
): Promise<DraftVersion[]> {
  return request<DraftVersion[]>(`/api/v1/outreach/drafts/${draftId}/versions`, workspaceId);
}

export async function submitDraftForReview(
  workspaceId: string,
  draftId: string
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts/${draftId}/actions/submit-review`, workspaceId, {
    method: "POST",
  });
}

export async function approveDraft(
  workspaceId: string,
  draftId: string
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts/${draftId}/actions/approve`, workspaceId, {
    method: "POST",
  });
}

export async function rejectDraft(
  workspaceId: string,
  draftId: string
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts/${draftId}/actions/reject`, workspaceId, {
    method: "POST",
  });
}

export async function archiveDraft(
  workspaceId: string,
  draftId: string
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts/${draftId}/actions/archive`, workspaceId, {
    method: "POST",
  });
}

export async function deleteDraft(
  workspaceId: string,
  draftId: string
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts/${draftId}`, workspaceId, {
    method: "DELETE",
  });
}

export async function generateOutreachDraft(
  workspaceId: string,
  draftId: string
): Promise<OutreachDraft> {
  return request<OutreachDraft>(`/api/v1/outreach/drafts/${draftId}/actions/generate`, workspaceId, {
    method: "POST",
  });
}
