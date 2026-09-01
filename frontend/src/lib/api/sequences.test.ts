import { describe, it, expect, vi, beforeEach } from"vitest";
import {
 fetchCampaignSequence,
 saveCampaignSequence,
 enrollContactInSequence,
 fetchSequenceEnrollments,
 pauseEnrollment,
 resumeEnrollment,
 stopEnrollment,
} from"./sequences";

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("Sequences API Client", () => {
 const workspaceId ="ws-111";
 const campaignId ="camp-222";

 beforeEach(() => {
 mockFetch.mockReset();
 });

 it("fetchCampaignSequence requests GET /api/v1/campaigns/:id/sequences", async () => {
 mockFetch.mockResolvedValueOnce({
 ok: true,
 json: async () => ({ id:"seq-1", campaign_id: campaignId, steps: [] }),
 });

 const res = await fetchCampaignSequence(workspaceId, campaignId);
 expect(mockFetch).toHaveBeenCalledWith(
 `/api/v1/campaigns/${campaignId}/sequences`,
 expect.objectContaining({ headers: expect.any(Headers) })
 );
 expect(res.id).toBe("seq-1");
 });

 it("saveCampaignSequence sends POST to /api/v1/campaigns/:id/sequences", async () => {
 mockFetch.mockResolvedValueOnce({
 ok: true,
 json: async () => ({ id:"seq-1", version_number: 2 }),
 });

 const steps = [
 { step_number: 1, delay_days: 0, template_subject:"S1", template_body:"B1"},
 { step_number: 2, delay_days: 3, template_subject:"S2", template_body:"B2"},
 ];

 const updated = await saveCampaignSequence(workspaceId, campaignId,"Custom Seq", steps);

 expect(mockFetch).toHaveBeenCalledWith(
 `/api/v1/campaigns/${campaignId}/sequences`,
 expect.objectContaining({ method:"POST"})
 );
 expect(updated.version_number).toBe(2);
 });

 it("enrollContactInSequence sends POST to /api/v1/sequence-enrollments", async () => {
 mockFetch.mockResolvedValueOnce({
 ok: true,
 json: async () => ({ id:"enr-1", status:"pending_approval"}),
 });

 const enr = await enrollContactInSequence(workspaceId, campaignId,"contact-333");
 expect(mockFetch).toHaveBeenCalledWith(
"/api/v1/sequence-enrollments",
 expect.objectContaining({ method:"POST"})
 );
 expect(enr.status).toBe("pending_approval");
 });

 it("fetchSequenceEnrollments requests GET /api/v1/sequence-enrollments with parameters", async () => {
 mockFetch.mockResolvedValueOnce({
 ok: true,
 json: async () => [{ id:"enr-1", status:"active"}],
 });

 const results = await fetchSequenceEnrollments(workspaceId, { campaign_id: campaignId });
 expect(mockFetch).toHaveBeenCalledWith(
 `/api/v1/sequence-enrollments?campaign_id=${campaignId}`,
 expect.any(Object)
 );
 expect(results).toHaveLength(1);
 });

 it("pauseEnrollment, resumeEnrollment, and stopEnrollment execute action endpoints", async () => {
 mockFetch
 .mockResolvedValueOnce({ ok: true, json: async () => ({ id:"e1", status:"paused"}) })
 .mockResolvedValueOnce({ ok: true, json: async () => ({ id:"e1", status:"active"}) })
 .mockResolvedValueOnce({ ok: true, json: async () => ({ id:"e1", status:"stopped"}) });

 const paused = await pauseEnrollment(workspaceId,"e1");
 expect(paused.status).toBe("paused");

 const resumed = await resumeEnrollment(workspaceId,"e1");
 expect(resumed.status).toBe("active");

 const stopped = await stopEnrollment(workspaceId,"e1","manual");
 expect(stopped.status).toBe("stopped");
 });
});
