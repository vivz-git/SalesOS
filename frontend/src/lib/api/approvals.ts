import { type OutreachDraft, type DraftVersion } from "./outreach";
import { request } from "./client";

export type ApprovalDecision = "approved" | "rejected" | "returned_to_draft";

export interface ApprovalAuditRecord {
  id: string;
  workspace_id: string;
  draft_id: string;
  version_id?: string | null;
  version_number: number;
  reviewer_id: string;
  reviewer_email?: string | null;
  decision: ApprovalDecision;
  notes?: string | null;
  created_at: string;
}

export interface ApprovalItemDetail {
  draft: OutreachDraft;
  campaign_name?: string | null;
  contact_name?: string | null;
  contact_email?: string | null;
  account_name?: string | null;
  recent_history?: ApprovalAuditRecord[];
  campaign?: Record<string, unknown>;
  contact?: Record<string, unknown>;
  account?: Record<string, unknown>;
  research_brief?: Record<string, unknown>;
  evidence_sources?: Array<Record<string, unknown>>;
  current_version?: DraftVersion | null;
  review_history?: ApprovalAuditRecord[];
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
): Promise<OutreachDraft[]> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.search) query.set("search", params.search);
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));

  const queryStr = query.toString() ? `?${query.toString()}` : "";
  const path = `/api/v1/approvals/queue${queryStr}`;
  return request<OutreachDraft[]>(path, workspaceId);
}

export async function fetchApprovalItem(
  workspaceId: string,
  draftId: string
): Promise<ApprovalItemDetail> {
  return request<ApprovalItemDetail>(`/api/v1/approvals/items/${draftId}`, workspaceId);
}

export async function submitApprovalDecision(
  workspaceId: string,
  draftId: string,
  decision: ApprovalDecision,
  notes?: string
): Promise<ApprovalAuditRecord> {
  return request<ApprovalAuditRecord>(`/api/v1/approvals/items/${draftId}/decision`, workspaceId, {
    method: "POST",
    body: JSON.stringify({ decision, notes }),
  });
}

export async function approveApprovalItem(
  workspaceId: string,
  draftId: string,
  notes?: string
): Promise<ApprovalAuditRecord> {
  return submitApprovalDecision(workspaceId, draftId, "approved", notes);
}

export async function rejectApprovalItem(
  workspaceId: string,
  draftId: string,
  notes?: string
): Promise<ApprovalAuditRecord> {
  return submitApprovalDecision(workspaceId, draftId, "rejected", notes);
}

export async function returnApprovalItemToDraft(
  workspaceId: string,
  draftId: string,
  notes?: string
): Promise<ApprovalAuditRecord> {
  return submitApprovalDecision(workspaceId, draftId, "returned_to_draft", notes);
}
