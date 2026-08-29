import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  fetchHubspotStatus,
  authorizeHubspot,
  disconnectHubspot,
  triggerHubspotSync,
  fetchHubspotSyncRuns,
  fetchHubspotSyncRunDetail,
} from "./hubspot";

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("HubSpot API Client", () => {
  const workspaceId = "ws-555";

  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("fetchHubspotStatus requests GET /api/v1/integrations/hubspot", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "c1", status: "connected", portal_id: "portal-1" }),
    });

    const status = await fetchHubspotStatus(workspaceId);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/integrations/hubspot",
      expect.objectContaining({ headers: expect.any(Headers) })
    );
    expect(status.status).toBe("connected");
  });

  it("authorizeHubspot sends POST to /api/v1/integrations/hubspot/actions/authorize", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorization_url: "https://app.hubspot.com/oauth/authorize", state: "st" }),
    });

    const auth = await authorizeHubspot(workspaceId);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/integrations/hubspot/actions/authorize",
      expect.objectContaining({ method: "POST" })
    );
    expect(auth.authorization_url).toContain("hubspot.com");
  });

  it("disconnectHubspot sends POST to /api/v1/integrations/hubspot/actions/disconnect", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "c1", status: "disconnected" }),
    });

    const res = await disconnectHubspot(workspaceId);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/integrations/hubspot/actions/disconnect",
      expect.objectContaining({ method: "POST" })
    );
    expect(res.status).toBe("disconnected");
  });

  it("triggerHubspotSync sends POST to /api/v1/integrations/hubspot/actions/sync", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "sr-1", status: "completed", records_processed: 5 }),
    });

    const run = await triggerHubspotSync(workspaceId, "export_to_crm");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/integrations/hubspot/actions/sync",
      expect.objectContaining({ method: "POST" })
    );
    expect(run.records_processed).toBe(5);
  });

  it("fetchHubspotSyncRuns and fetchHubspotSyncRunDetail execute history endpoints", async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [{ id: "sr-1", status: "completed" }] })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: "sr-1", status: "completed" }) });

    const runs = await fetchHubspotSyncRuns(workspaceId);
    expect(runs).toHaveLength(1);

    const detail = await fetchHubspotSyncRunDetail(workspaceId, "sr-1");
    expect(detail.id).toBe("sr-1");
  });
});
