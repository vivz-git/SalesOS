import { describe, expect, it, vi } from "vitest";
import {
  approveDraft,
  createOutreachDraft,
  fetchOutreachDrafts,
  generateOutreachDraft,
  rejectDraft,
  reviseOutreachDraft,
  submitDraftForReview,
} from "./outreach";

global.fetch = vi.fn();

describe("outreach API client", () => {
  const workspaceId = "ws-12345";

  it("fetches outreach drafts list with workspace header", async () => {
    const mockDrafts = [
      {
        id: "d-1",
        workspace_id: workspaceId,
        campaign_id: "c-1",
        contact_id: "ct-1",
        status: "draft",
        current_version_number: 1,
      },
    ];

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockDrafts,
    });

    const result = await fetchOutreachDrafts(workspaceId, { status: "draft" });
    expect(result).toEqual(mockDrafts);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/outreach/drafts?status=draft",
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );
  });

  it("triggers AI outreach draft generation action", async () => {
    const mockGenerated = {
      id: "d-1",
      workspace_id: workspaceId,
      campaign_id: "c-1",
      contact_id: "ct-1",
      current_subject: "AI Generated Subject",
      current_body: "AI Generated Body Content",
      status: "draft",
      current_version_number: 2,
    };

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockGenerated,
    });

    const res = await generateOutreachDraft(workspaceId, "d-1");
    expect(res.current_version_number).toBe(2);
    expect(res.current_subject).toBe("AI Generated Subject");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/outreach/drafts/d-1/actions/generate",
      expect.objectContaining({
        method: "POST",
      })
    );
  });

  it("creates an outreach draft", async () => {
    const mockCreated = {
      id: "d-2",
      workspace_id: workspaceId,
      campaign_id: "c-1",
      contact_id: "ct-1",
      current_subject: "Hello",
      current_body: "World",
      status: "draft",
      current_version_number: 1,
    };

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockCreated,
    });

    const res = await createOutreachDraft(workspaceId, {
      campaign_id: "c-1",
      contact_id: "ct-1",
      subject: "Hello",
      body: "World",
    });

    expect(res.id).toBe("d-2");
    expect(res.current_subject).toBe("Hello");
  });


  it("creates a campaign-free outreach draft", async () => {
    const mockCreated = {
      id: "d-3",
      workspace_id: workspaceId,
      contact_id: "ct-1",
      current_subject: "Hello Campaign Free",
      current_body: "World Campaign Free",
      status: "draft",
      current_version_number: 1,
    };

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockCreated,
    });

    const res = await createOutreachDraft(workspaceId, {
      contact_id: "ct-1",
      subject: "Hello Campaign Free",
      body: "World Campaign Free",
    });

    expect(res.id).toBe("d-3");
    expect(res.current_subject).toBe("Hello Campaign Free");
    expect(res.campaign_id).toBeUndefined();
  });

  it("revises an outreach draft", async () => {
    const mockRevised = {
      id: "d-2",
      workspace_id: workspaceId,
      campaign_id: "c-1",
      contact_id: "ct-1",
      current_subject: "Hello V2",
      current_body: "World V2",
      status: "draft",
      current_version_number: 2,
    };

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockRevised,
    });

    const res = await reviseOutreachDraft(workspaceId, "d-2", {
      subject: "Hello V2",
      body: "World V2",
    });

    expect(res.current_version_number).toBe(2);
  });

  it("executes status transition actions", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ id: "d-1", status: "ready_for_review" }),
    });

    const submitRes = await submitDraftForReview(workspaceId, "d-1");
    expect(submitRes.status).toBe("ready_for_review");

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ id: "d-1", status: "approved" }),
    });
    const appRes = await approveDraft(workspaceId, "d-1");
    expect(appRes.status).toBe("approved");

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ id: "d-1", status: "rejected" }),
    });
    const rejRes = await rejectDraft(workspaceId, "d-1");
    expect(rejRes.status).toBe("rejected");
  });
});
