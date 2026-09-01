import { describe, it, expect, vi, beforeEach } from"vitest";
import {
 createDelivery,
 fetchDeliveries,
 fetchDeliveryDetail,
 cancelDelivery,
} from"./deliveries";

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("Deliveries API Client", () => {
 const workspaceId ="ws-12345";

 beforeEach(() => {
 mockFetch.mockReset();
 });

 it("createDelivery sends POST request to /api/v1/deliveries with workspace header", async () => {
 mockFetch.mockResolvedValueOnce({
 ok: true,
 json: async () => ({
 id:"del-101",
 workspace_id: workspaceId,
 draft_id:"draft-789",
 status:"sent",
 recipient_email:"prospect@example.com",
 }),
 });

 const result = await createDelivery(workspaceId,"draft-789");

 expect(mockFetch).toHaveBeenCalledWith(
"/api/v1/deliveries",
 expect.objectContaining({
 method:"POST",
 body: JSON.stringify({ draft_id:"draft-789"}),
 })
 );
 expect(result.status).toBe("sent");
 expect(result.id).toBe("del-101");
 });

 it("fetchDeliveries sends GET request to /api/v1/deliveries with workspace header and filter params", async () => {
 mockFetch.mockResolvedValueOnce({
 ok: true,
 json: async () => [
 { id:"del-1", status:"sent"},
 { id:"del-2", status:"delivered"},
 ],
 });

 const results = await fetchDeliveries(workspaceId, { status:"sent"});

 expect(mockFetch).toHaveBeenCalledWith(
"/api/v1/deliveries?status=sent",
 expect.objectContaining({
 headers: expect.any(Headers),
 })
 );
 expect(results).toHaveLength(2);
 });

 it("fetchDeliveryDetail sends GET request for specific delivery ID", async () => {
 mockFetch.mockResolvedValueOnce({
 ok: true,
 json: async () => ({ id:"del-555", status:"delivered"}),
 });

 const detail = await fetchDeliveryDetail(workspaceId,"del-555");
 expect(mockFetch).toHaveBeenCalledWith("/api/v1/deliveries/del-555", expect.any(Object));
 expect(detail.id).toBe("del-555");
 });

 it("cancelDelivery sends POST request to cancel action endpoint", async () => {
 mockFetch.mockResolvedValueOnce({
 ok: true,
 json: async () => ({ id:"del-555", status:"cancelled"}),
 });

 const updated = await cancelDelivery(workspaceId,"del-555");
 expect(mockFetch).toHaveBeenCalledWith(
"/api/v1/deliveries/del-555/actions/cancel",
 expect.objectContaining({ method:"POST"})
 );
 expect(updated.status).toBe("cancelled");
 });
});
