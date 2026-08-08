import { describe, expect, it, vi } from "vitest";
import {
  approveApprovalItem,
  fetchApprovalItem,
  fetchApprovalQueue,
  rejectApprovalItem,
  returnApprovalItemToDraft,
} from "./approvals";

global.fetch = vi.fn();

describe("approvals API client", () => {
  const workspaceId = "ws-12345";

  it("fetches approval queue items with query filters", async () => {
    const mockItems = [
      {
        draft: {
          id: "d-1",
          workspace_id: workspaceId,
          campaign_id: "c-1",
          contact_id: "ct-1",
          status: "ready_for_review",
          current_version_number: 2,
        },
        campaign: { name: "Enterprise Campaign" },
        contact: { first_name: "John", last_name: "Doe" },
        account: { name: "Acme Corp" },
        research_brief: {},
        evidence_sources: [],
        review_history: [],
      },
    ];

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockItems,
    });

    const result = await fetchApprovalQueue(workspaceId, { status: "ready_for_review" });
    expect(result).toEqual(mockItems);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/approvals?status=ready_for_review",
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );
  });

  it("fetches detailed approval item context", async () => {
    const mockDetail = {
      draft: { id: "d-1", status: "ready_for_review" },
      campaign: { name: "Campaign 1" },
      contact: { first_name: "Jane" },
      account: { name: "Company" },
      review_history: [],
    };

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockDetail,
    });

    const result = await fetchApprovalItem(workspaceId, "d-1");
    expect(result).toEqual(mockDetail);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/approvals/d-1",
      expect.objectContaining({ headers: expect.any(Headers) })
    );
  });

  it("triggers approve action with reviewer notes", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ draft: { id: "d-1", status: "approved" } }),
    });

    const result = await approveApprovalItem(workspaceId, "d-1", "Looks good");
    expect(result.draft.status).toBe("approved");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/approvals/d-1/actions/approve",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ notes: "Looks good" }),
      })
    );
  });

  it("triggers reject action with reviewer reason", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ draft: { id: "d-1", status: "rejected" } }),
    });

    const result = await rejectApprovalItem(workspaceId, "d-1", "Needs pricing fix");
    expect(result.draft.status).toBe("rejected");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/approvals/d-1/actions/reject",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ notes: "Needs pricing fix" }),
      })
    );
  });

  it("triggers return-to-draft action", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ draft: { id: "d-1", status: "draft" } }),
    });

    const result = await returnApprovalItemToDraft(workspaceId, "d-1", "Return for edit");
    expect(result.draft.status).toBe("draft");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/approvals/d-1/actions/return-to-draft",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ notes: "Return for edit" }),
      })
    );
  });
});
