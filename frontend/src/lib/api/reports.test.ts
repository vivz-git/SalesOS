import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  fetchWeeklyReportsList,
  fetchWeeklyReportDetail,
  generateWeeklyReport,
} from "./reports";

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("Reports API Client", () => {
  const workspaceId = "ws-777";

  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("fetchWeeklyReportsList requests GET /v1/reports/weekly", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [{ id: "rep-1", title: "Weekly Digest" }],
    });

    const reports = await fetchWeeklyReportsList(workspaceId);
    expect(mockFetch).toHaveBeenCalledWith(
      "/v1/reports/weekly?limit=10&offset=0",
      expect.objectContaining({ headers: expect.any(Headers) })
    );
    expect(reports).toHaveLength(1);
  });

  it("fetchWeeklyReportDetail requests GET /v1/reports/weekly/:id", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "rep-1", title: "Digest Detail" }),
    });

    const detail = await fetchWeeklyReportDetail(workspaceId, "rep-1");
    expect(mockFetch).toHaveBeenCalledWith("/v1/reports/weekly/rep-1", expect.any(Object));
    expect(detail.id).toBe("rep-1");
  });

  it("generateWeeklyReport sends POST to /v1/reports/weekly/actions/generate", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "rep-2", title: "On-Demand Digest" }),
    });

    const generated = await generateWeeklyReport(workspaceId);
    expect(mockFetch).toHaveBeenCalledWith(
      "/v1/reports/weekly/actions/generate",
      expect.objectContaining({ method: "POST" })
    );
    expect(generated.id).toBe("rep-2");
  });
});
