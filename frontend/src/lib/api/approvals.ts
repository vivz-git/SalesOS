import { request, type OutreachDraft, type DraftVersion } from "./outreach";

export interface ApprovalAuditRecord {
  id: string;
  workspace_id: string;
  draft_id: string;
  version_id?: string | null;
  version_number: number;
  reviewer_id: string;
  reviewer_email?: string | null;
  decision: "approved" | "rejected" | "returned_to_draft";
  notes?: string | null;
  created_at: string;
}

export interface ApprovalItemDetail {
  draft: OutreachDraft;
  campaign: Record<string, unknown>;
  contact: Record<string, unknown>;
  account: Record<string, unknown>;
  research_brief: Record<string, unknown>;
  evidence_sources: Array<Record<string, unknown>>;
  current_version?: DraftVersion | null;
  review_history: ApprovalAuditRecord[];
}

export interface FetchApprovalQueueParams {
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export async function fetchApprovalQueue(
  workspaceId: string,
  params: FetchApprovalQueueParams = {}
): Promise<ApprovalItemDetail[]> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.search) query.set("search", params.search);
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));

  const path = `/api/v1/approvals${query.toString() ? `?${query.toString()}` : ""}`;
  return request<ApprovalItemDetail[]>(path, workspaceId);
}

export async function fetchApprovalItem(
  workspaceId: string,
  draftId: string
): Promise<ApprovalItemDetail> {
  return request<ApprovalItemDetail>(`/api/v1/approvals/${draftId}`, workspaceId);
}

export async function approveApprovalItem(
  workspaceId: string,
  draftId: string,
  notes?: string
): Promise<ApprovalItemDetail> {
  return request<ApprovalItemDetail>(`/api/v1/approvals/${draftId}/actions/approve`, workspaceId, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}

export async function rejectApprovalItem(
  workspaceId: string,
  draftId: string,
  notes?: string
): Promise<ApprovalItemDetail> {
  return request<ApprovalItemDetail>(`/api/v1/approvals/${draftId}/actions/reject`, workspaceId, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}

export async function returnApprovalItemToDraft(
  workspaceId: string,
  draftId: string,
  notes?: string
): Promise<ApprovalItemDetail> {
  return request<ApprovalItemDetail>(`/api/v1/approvals/${draftId}/actions/return-to-draft`, workspaceId, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}
