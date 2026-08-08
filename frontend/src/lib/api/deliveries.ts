import { request } from "./outreach";

export type DeliveryStatus =
  | "queued"
  | "running"
  | "sent"
  | "delivered"
  | "failed"
  | "bounced"
  | "complained"
  | "cancelled";

export interface EmailDelivery {
  id: string;
  workspace_id: string;
  draft_id: string;
  version_id: string;
  version_number: number;
  contact_id: string;
  recipient_email: string;
  subject: string;
  body: string;
  provider: string;
  provider_message_id: string | null;
  status: DeliveryStatus;
  idempotency_key: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  error_message: string | null;
}

export interface DeliveryFilterParams {
  status?: string;
  limit?: number;
  offset?: number;
}

export async function createDelivery(
  workspaceId: string,
  draftId: string,
  overrideRecipientEmail?: string
): Promise<EmailDelivery> {
  return request<EmailDelivery>("/v1/deliveries", workspaceId, {
    method: "POST",
    body: JSON.stringify({
      draft_id: draftId,
      override_recipient_email: overrideRecipientEmail,
    }),
  });
}

export async function fetchDeliveries(
  workspaceId: string,
  params: DeliveryFilterParams = {}
): Promise<EmailDelivery[]> {
  const searchParams = new URLSearchParams();
  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }
  if (params.limit) searchParams.set("limit", params.limit.toString());
  if (params.offset) searchParams.set("offset", params.offset.toString());

  const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return request<EmailDelivery[]>(`/v1/deliveries${queryStr}`, workspaceId);
}

export async function fetchDeliveryDetail(
  workspaceId: string,
  deliveryId: string
): Promise<EmailDelivery> {
  return request<EmailDelivery>(`/v1/deliveries/${deliveryId}`, workspaceId);
}

export async function cancelDelivery(
  workspaceId: string,
  deliveryId: string
): Promise<EmailDelivery> {
  return request<EmailDelivery>(`/v1/deliveries/${deliveryId}/actions/cancel`, workspaceId, {
    method: "POST",
  });
}
