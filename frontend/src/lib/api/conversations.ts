import { request } from "./client";

export type ReplyState =
  | "interested"
  | "not_now"
  | "referral"
  | "unsubscribe"
  | "out_of_office"
  | "ambiguous";

export type ConversationStatus = "active" | "needs_human_action" | "closed" | "opt_out";

export interface ConversationMessage {
  id: string;
  workspace_id: string;
  conversation_id: string;
  direction: "inbound" | "outbound";
  sender_email: string;
  recipient_email: string;
  subject: string;
  body: string;
  provider_message_id?: string | null;
  delivery_id?: string | null;
  created_at: string;
}

export interface ReplyClassification {
  id: string;
  conversation_id: string;
  message_id: string;
  reply_state: ReplyState;
  confidence_score: number;
  explanation: string;
  needs_human_action: boolean;
  classified_at: string;
}

export interface Conversation {
  id: string;
  workspace_id: string;
  contact_id: string;
  contact_name?: string | null;
  contact_email?: string | null;
  account_name?: string | null;
  campaign_id?: string | null;
  delivery_id?: string | null;
  status: ConversationStatus;
  current_reply_state?: ReplyState | null;
  last_message_at: string;
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
  last_classification?: ReplyClassification | null;
}

export interface ConversationFilterParams {
  status?: string;
  reply_state?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface InboundReplyPayload {
  workspace_id?: string;
  sender_email: string;
  recipient_email: string;
  subject: string;
  body: string;
  provider_message_id?: string;
  in_reply_to_provider_message_id?: string;
}

export async function fetchConversations(
  workspaceId: string,
  params: ConversationFilterParams = {}
): Promise<Conversation[]> {
  const searchParams = new URLSearchParams();
  if (params.status && params.status !== "all") searchParams.set("status", params.status);
  if (params.reply_state && params.reply_state !== "all")
    searchParams.set("reply_state", params.reply_state);
  if (params.search) searchParams.set("search", params.search);
  if (params.limit) searchParams.set("limit", params.limit.toString());
  if (params.offset) searchParams.set("offset", params.offset.toString());

  const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return request<Conversation[]>(`/api/v1/conversations${queryStr}`, workspaceId);
}

export async function fetchConversationDetail(
  workspaceId: string,
  conversationId: string
): Promise<Conversation> {
  return request<Conversation>(`/api/v1/conversations/${conversationId}`, workspaceId);
}

export async function ingestInboundReply(
  workspaceId: string,
  payload: InboundReplyPayload
): Promise<Conversation> {
  return request<Conversation>("/api/v1/conversations/inbound", workspaceId, {
    method: "POST",
    body: JSON.stringify({ ...payload, workspace_id: workspaceId }),
  });
}

export async function reclassifyConversation(
  workspaceId: string,
  conversationId: string,
  replyState: ReplyState,
  explanation?: string
): Promise<Conversation> {
  return request<Conversation>(`/api/v1/conversations/${conversationId}/actions/classify`, workspaceId, {
    method: "POST",
    body: JSON.stringify({ reply_state: replyState, explanation }),
  });
}

export async function updateConversationStatus(
  workspaceId: string,
  conversationId: string,
  status: ConversationStatus
): Promise<Conversation> {
  return request<Conversation>(
    `/api/v1/conversations/${conversationId}/actions/update-status`,
    workspaceId,
    {
      method: "POST",
      body: JSON.stringify({ status }),
    }
  );
}
