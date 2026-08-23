import { request } from './client';
export type CampaignStatus = "draft" | "active" | "paused" | "archived";

export interface Campaign {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  target_segment: string | null;
  icp_definition: string | null;
  status: CampaignStatus;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
}

export interface CampaignCreatePayload {
  name: string;
  description?: string;
  target_segment?: string;
  icp_definition?: string;
}

export interface CampaignUpdatePayload {
  name?: string;
  description?: string;
  target_segment?: string;
  icp_definition?: string;
}


export async function fetchCampaigns(
  workspaceId: string,
  statusFilter?: string
): Promise<Campaign[]> {
  const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
  return request<Campaign[]>(`/api/v1/campaigns${query}`, workspaceId);
}

export async function fetchCampaign(
  workspaceId: string,
  campaignId: string
): Promise<Campaign> {
  return request<Campaign>(`/api/v1/campaigns/${campaignId}`, workspaceId);
}

export async function createCampaign(
  workspaceId: string,
  payload: CampaignCreatePayload
): Promise<Campaign> {
  return request<Campaign>(`/api/v1/campaigns`, workspaceId, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCampaign(
  workspaceId: string,
  campaignId: string,
  payload: CampaignUpdatePayload
): Promise<Campaign> {
  return request<Campaign>(`/api/v1/campaigns/${campaignId}`, workspaceId, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteCampaign(
  workspaceId: string,
  campaignId: string
): Promise<Campaign> {
  return request<Campaign>(`/api/v1/campaigns/${campaignId}`, workspaceId, {
    method: "DELETE",
  });
}

export async function activateCampaign(
  workspaceId: string,
  campaignId: string
): Promise<Campaign> {
  return request<Campaign>(`/api/v1/campaigns/${campaignId}/actions/activate`, workspaceId, {
    method: "POST",
  });
}

export async function pauseCampaign(
  workspaceId: string,
  campaignId: string
): Promise<Campaign> {
  return request<Campaign>(`/api/v1/campaigns/${campaignId}/actions/pause`, workspaceId, {
    method: "POST",
  });
}

export async function archiveCampaign(
  workspaceId: string,
  campaignId: string
): Promise<Campaign> {
  return request<Campaign>(`/api/v1/campaigns/${campaignId}/actions/archive`, workspaceId, {
    method: "POST",
  });
}

export async function restoreCampaign(
  workspaceId: string,
  campaignId: string
): Promise<Campaign> {
  return request<Campaign>(`/api/v1/campaigns/${campaignId}/actions/restore`, workspaceId, {
    method: "POST",
  });
}
