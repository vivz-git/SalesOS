import { request } from "./client";

export type StepType = "first_touch" | "follow_up";
export type EnrollmentStatus =
  | "pending_approval"
  | "active"
  | "paused"
  | "stopped"
  | "completed"
  | "failed";

export interface SequenceStepPayload {
  step_number: number;
  delay_days?: number;
  channel?: string;
  step_type?: StepType;
  template_subject?: string;
  template_body?: string;
}

export interface SequenceStep {
  id: string;
  sequence_id: string;
  step_number: number;
  delay_days: number;
  channel: string;
  step_type: StepType;
  template_subject?: string | null;
  template_body?: string | null;
}

export interface SequenceDefinition {
  id: string;
  workspace_id: string;
  campaign_id: string;
  name: string;
  version_number: number;
  is_active: boolean;
  steps: SequenceStep[];
  created_at: string;
  updated_at: string;
}

export interface SequenceEnrollment {
  id: string;
  workspace_id: string;
  campaign_id: string;
  sequence_id: string;
  contact_id: string;
  current_step_number: number;
  status: EnrollmentStatus;
  stop_reason?: string | null;
  enrolled_by: string;
  enrolled_at: string;
  updated_at: string;
}

export interface EnrollmentFilterParams {
  campaign_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export async function fetchCampaignSequence(
  workspaceId: string,
  campaignId: string
): Promise<SequenceDefinition> {
  return request<SequenceDefinition>(`/v1/campaigns/${campaignId}/sequences`, workspaceId);
}

export async function saveCampaignSequence(
  workspaceId: string,
  campaignId: string,
  name: string,
  steps: SequenceStepPayload[]
): Promise<SequenceDefinition> {
  return request<SequenceDefinition>(`/v1/campaigns/${campaignId}/sequences`, workspaceId, {
    method: "POST",
    body: JSON.stringify({ name, steps }),
  });
}

export async function enrollContactInSequence(
  workspaceId: string,
  campaignId: string,
  contactId: string
): Promise<SequenceEnrollment> {
  return request<SequenceEnrollment>("/v1/sequence-enrollments", workspaceId, {
    method: "POST",
    body: JSON.stringify({ campaign_id: campaignId, contact_id: contactId }),
  });
}

export async function fetchSequenceEnrollments(
  workspaceId: string,
  params: EnrollmentFilterParams = {}
): Promise<SequenceEnrollment[]> {
  const searchParams = new URLSearchParams();
  if (params.campaign_id) searchParams.set("campaign_id", params.campaign_id);
  if (params.status && params.status !== "all") searchParams.set("status", params.status);
  if (params.limit) searchParams.set("limit", params.limit.toString());
  if (params.offset) searchParams.set("offset", params.offset.toString());

  const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return request<SequenceEnrollment[]>(`/v1/sequence-enrollments${queryStr}`, workspaceId);
}

export async function pauseEnrollment(
  workspaceId: string,
  enrollmentId: string
): Promise<SequenceEnrollment> {
  return request<SequenceEnrollment>(
    `/v1/sequence-enrollments/${enrollmentId}/actions/pause`,
    workspaceId,
    { method: "POST" }
  );
}

export async function resumeEnrollment(
  workspaceId: string,
  enrollmentId: string
): Promise<SequenceEnrollment> {
  return request<SequenceEnrollment>(
    `/v1/sequence-enrollments/${enrollmentId}/actions/resume`,
    workspaceId,
    { method: "POST" }
  );
}

export async function stopEnrollment(
  workspaceId: string,
  enrollmentId: string,
  reason?: string
): Promise<SequenceEnrollment> {
  return request<SequenceEnrollment>(
    `/v1/sequence-enrollments/${enrollmentId}/actions/stop`,
    workspaceId,
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    }
  );
}
