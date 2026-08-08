"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import { fetchApprovalQueue, type ApprovalItemDetail } from "@/lib/api/approvals";
import type { DraftStatus } from "@/lib/api/outreach";
import { DraftStatusBadge } from "@/components/outreach/draft-status-badge";
import { CheckCircle2, Search, Sparkles, AlertCircle, Eye, Inbox } from "lucide-react";

export default function ApprovalsPage() {
  const { activeWorkspace } = useWorkspace();
  const [items, setItems] = useState<ApprovalItemDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ready_for_review");
  const [searchQuery, setSearchQuery] = useState<string>("");

  useEffect(() => {
    async function loadQueue() {
      if (!activeWorkspace) return;
      setLoading(true);
      setError(null);
      try {
        const data = await fetchApprovalQueue(activeWorkspace.id, {
          status: statusFilter,
          search: searchQuery.trim() || undefined,
        });
        setItems(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load approval queue");
      } finally {
        setLoading(false);
      }
    }
    loadQueue();
  }, [activeWorkspace, statusFilter, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900">Approval Queue</h1>
          <p className="mt-0.5 text-xs text-zinc-500">
            Review, audit, approve, or reject outreach drafts before external communication.
          </p>
        </div>
      </div>

      {/* Filter Tabs & Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-zinc-200 bg-white p-3 shadow-2xs">
        {/* Status Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto">
          {[
            { id: "ready_for_review", label: "Pending Review" },
            { id: "approved", label: "Approved" },
            { id: "rejected", label: "Rejected" },
            { id: "all", label: "All Items" },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setStatusFilter(tab.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                statusFilter === tab.id
                  ? "bg-purple-600 text-white shadow-2xs"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative sm:w-64">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-zinc-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search subject, prospect..."
            className="w-full rounded-lg border border-zinc-200 bg-zinc-50 pl-8 pr-3 py-1.5 text-xs text-zinc-900 focus:bg-white focus:border-purple-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-zinc-100 border border-zinc-200"></div>
          ))}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800">
          <AlertCircle className="mx-auto h-7 w-7 text-rose-600 mb-1.5" />
          <h3 className="text-sm font-semibold">Error Loading Approval Queue</h3>
          <p className="mt-0.5 text-xs text-rose-600">{error}</p>
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-300 bg-white p-12 text-center">
          <Inbox className="mx-auto h-10 w-10 text-zinc-300 mb-2" />
          <h3 className="text-sm font-semibold text-zinc-800">No Drafts in Approval Queue</h3>
          <p className="mt-1 text-xs text-zinc-400 max-w-sm mx-auto">
            {statusFilter === "ready_for_review"
              ? "All submitted drafts have been reviewed. New AI-generated drafts will appear here when submitted for review."
              : "No outreach drafts found matching the current status filter."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-[11px] font-semibold uppercase text-zinc-500">
                <tr>
                  <th className="px-4 py-3">Subject & Prospect</th>
                  <th className="px-4 py-3">Campaign</th>
                  <th className="px-4 py-3">Version</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">AI Model</th>
                  <th className="px-4 py-3">Submitted</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200">
                {items.map((item) => {
                  const draft = item.draft;
                  const contactName =
                    `${item.contact.first_name || ""} ${item.contact.last_name || ""}`.trim() ||
                    "Unknown Prospect";
                  const accountName = (item.account.name as string) || "Unknown Account";
                  const campaignName = (item.campaign.name as string) || draft.campaign_id;
                  const currentVer = item.current_version;

                  return (
                    <tr key={draft.id} className="hover:bg-zinc-50/80 transition-colors">
                      <td className="px-4 py-3 max-w-xs">
                        <Link
                          href={`/approvals/${draft.id}`}
                          className="font-semibold text-zinc-900 hover:text-purple-600 line-clamp-1"
                        >
                          {draft.current_subject || "(Untitled Subject)"}
                        </Link>
                        <div className="mt-0.5 text-[11px] text-zinc-500">
                          {contactName} · <span className="text-zinc-700 font-medium">{accountName}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-zinc-700 font-medium truncate max-w-[140px]">
                        {campaignName}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center rounded bg-zinc-100 px-2 py-0.5 text-[11px] font-mono text-zinc-700 font-semibold">
                          v{draft.current_version_number}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <DraftStatusBadge status={draft.status as DraftStatus} />
                      </td>
                      <td className="px-4 py-3 text-zinc-600">
                        {currentVer?.model ? (
                          <span className="inline-flex items-center gap-1 rounded bg-purple-50 px-2 py-0.5 text-[11px] font-medium text-purple-700">
                            <Sparkles className="h-3 w-3 shrink-0 text-purple-600" />
                            {currentVer.model}
                          </span>
                        ) : (
                          <span className="text-zinc-400">Human</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-zinc-500 text-[11px]">
                        {draft.updated_at
                          ? new Date(draft.updated_at).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "N/A"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/approvals/${draft.id}`}
                          className="inline-flex items-center gap-1 rounded-lg border border-purple-200 bg-purple-50 px-2.5 py-1 text-xs font-semibold text-purple-700 hover:bg-purple-100 transition-colors"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>Review</span>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
