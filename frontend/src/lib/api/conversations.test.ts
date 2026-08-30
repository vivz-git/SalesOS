import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  fetchConversations,
  fetchConversationDetail,
  ingestInboundReply,
  reclassifyConversation,
  updateConversationStatus,
} from "./conversations";

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("Conversations API Client", () => {
  const workspaceId = "ws-999";

  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("fetchConversations requests GET /api/v1/conversations with parameters", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [{ id: "c1", status: "active", current_reply_state: "interested" }],
    });

    const results = await fetchConversations(workspaceId, { status: "active" });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/conversations?status=active",
      expect.objectContaining({ headers: expect.any(Headers) })
    );
    expect(results).toHaveLength(1);
  });

  it("fetchConversationDetail requests GET /api/v1/conversations/:id", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "c1", status: "needs_human_action" }),
    });

    const detail = await fetchConversationDetail(workspaceId, "c1");
    expect(mockFetch).toHaveBeenCalledWith("/api/v1/conversations/c1", expect.any(Object));
    expect(detail.status).toBe("needs_human_action");
  });

  it("ingestInboundReply sends POST to /api/v1/conversations/simulate", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "c1", current_reply_state: "interested" }),
    });

    const result = await ingestInboundReply(workspaceId, {
      sender_email: "p@ex.com",
      recipient_email: "r@ex.com",
      subject: "Re: Hi",
      body: "Sounds good!",
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/conversations/simulate",
      expect.objectContaining({ method: "POST" })
    );
    expect(result.current_reply_state).toBe("interested");
  });

  it("reclassifyConversation sends POST to classify action endpoint", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "c1", current_reply_state: "unsubscribe" }),
    });

    const result = await reclassifyConversation(workspaceId, "c1", "unsubscribe");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/conversations/c1/actions/classify",
      expect.objectContaining({ method: "POST" })
    );
    expect(result.current_reply_state).toBe("unsubscribe");
  });

  it("updateConversationStatus sends POST to status action endpoint", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "c1", status: "closed" }),
    });

    const result = await updateConversationStatus(workspaceId, "c1", "closed");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/conversations/c1/actions/update-status",
      expect.objectContaining({ method: "POST" })
    );
    expect(result.status).toBe("closed");
  });
});
