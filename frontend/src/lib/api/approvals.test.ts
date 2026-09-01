import { describe, expect, it, vi } from"vitest";
import {
 approveApprovalItem,
 fetchApprovalItem,
 fetchApprovalQueue,
 rejectApprovalItem,
 returnApprovalItemToDraft,
} from"./approvals";

global.fetch = vi.fn();

describe("approvals API client", () => {
 const workspaceId ="ws-12345";

 it("fetches approval queue items with query filters", async () => {
 const mockDrafts = [
 {
 id:"d-1",
 workspace_id: workspaceId,
 campaign_id:"c-1",
 contact_id:"ct-1",
 status:"ready_for_review",
 current_version_number: 2,
 },
 ];

 (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
 ok: true,
 json: async () => mockDrafts,
 });

 const result = await fetchApprovalQueue(workspaceId, { status:"ready_for_review"});
 expect(result).toEqual(mockDrafts);
 expect(global.fetch).toHaveBeenCalledWith(
"/api/v1/approvals/queue?status=ready_for_review",
 expect.objectContaining({
 headers: expect.any(Headers),
 })
 );
 });

 it("fetches detailed approval item context", async () => {
 const mockDetail = {
 draft: { id:"d-1", status:"ready_for_review"},
 campaign_name:"Campaign 1",
 contact_name:"Jane Doe",
 account_name:"Company",
 recent_history: [],
 };

 (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
 ok: true,
 json: async () => mockDetail,
 });

 const result = await fetchApprovalItem(workspaceId,"d-1");
 expect(result).toEqual(mockDetail);
 expect(global.fetch).toHaveBeenCalledWith(
"/api/v1/approvals/items/d-1",
 expect.objectContaining({ headers: expect.any(Headers) })
 );
 });

 it("triggers approve action with reviewer notes", async () => {
 (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
 ok: true,
 json: async () => ({ id:"dec-1", decision:"approved", notes:"Looks good"}),
 });

 const result = await approveApprovalItem(workspaceId,"d-1","Looks good");
 expect(result.decision).toBe("approved");
 expect(global.fetch).toHaveBeenCalledWith(
"/api/v1/approvals/items/d-1/decision",
 expect.objectContaining({
 method:"POST",
 body: JSON.stringify({ decision:"approved", notes:"Looks good"}),
 })
 );
 });

 it("triggers reject action with reviewer reason", async () => {
 (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
 ok: true,
 json: async () => ({ id:"dec-2", decision:"rejected", notes:"Needs pricing fix"}),
 });

 const result = await rejectApprovalItem(workspaceId,"d-1","Needs pricing fix");
 expect(result.decision).toBe("rejected");
 expect(global.fetch).toHaveBeenCalledWith(
"/api/v1/approvals/items/d-1/decision",
 expect.objectContaining({
 method:"POST",
 body: JSON.stringify({ decision:"rejected", notes:"Needs pricing fix"}),
 })
 );
 });

 it("triggers return-to-draft action", async () => {
 (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
 ok: true,
 json: async () => ({ id:"dec-3", decision:"returned_to_draft", notes:"Return for edit"}),
 });

 const result = await returnApprovalItemToDraft(workspaceId,"d-1","Return for edit");
 expect(result.decision).toBe("returned_to_draft");
 expect(global.fetch).toHaveBeenCalledWith(
"/api/v1/approvals/items/d-1/decision",
 expect.objectContaining({
 method:"POST",
 body: JSON.stringify({ decision:"returned_to_draft", notes:"Return for edit"}),
 })
 );
 });
});
