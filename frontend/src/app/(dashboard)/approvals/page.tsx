"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import { fetchOutreachDrafts, type OutreachDraft, type DraftStatus } from "@/lib/api/outreach";
import { DraftStatusBadge } from "@/components/outreach/draft-status-badge";
import { Plus, Search, FileText, AlertCircle, RefreshCw, ChevronRight } from "lucide-react";

export default function ApprovalsPage() {
  const { activeWorkspace } = useWorkspace();
  const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  async function loadDrafts() {
    if (!activeWorkspace) return;
    setLoading(true);
    setError(null);

    try {
      const filter = statusFilter === "all" ? undefined : statusFilter;
      const data = await fetchOutreachDrafts(activeWorkspace.id, { status: filter });
      setDrafts(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load outreach drafts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDrafts();
  }, [activeWorkspace, statusFilter]);

  const filteredDrafts = drafts.filter((d) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (d.current_subject && d.current_subject.toLowerCase().includes(q)) ||
      (d.current_body && d.current_body.toLowerCase().includes(q)) ||
      d.id.toLowerCase().includes(q)
    );
  });

  const filterTabs: { id: string; label: string }[] = [
    { id: "all", label: "All Drafts" },
    { id: "draft", label: "Draft" },
    { id: "ready_for_review", label: "Ready for Review" },
    { id: "approved", label: "Approved" },
    { id: "rejected", label: "Rejected" },
    { id: "archived", label: "Archived" },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">Approvals</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Create, version, and review personalized message drafts for outreach campaigns.
          </p>
        </div>

        <Link
          href="/outreach/new"
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-zinc-800 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Create Draft
        </Link>
      </div>

      {/* Controls Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-zinc-200 pb-3">
        {/* Status Filter Tabs */}
        <div className="flex flex-wrap gap-1">
          {filterTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setStatusFilter(tab.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                statusFilter === tab.id
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Input & Refresh */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Search subject or body..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 bg-white pl-9 pr-3 py-1.5 text-xs text-zinc-900 focus:border-zinc-900 focus:outline-hidden"
            />
          </div>

          <button
            type="button"
            onClick={loadDrafts}
            className="rounded-lg border border-zinc-200 p-1.5 text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
            title="Refresh list"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          <AlertCircle className="h-5 w-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse rounded-xl border border-zinc-200 bg-white p-4">
              <div className="h-4 w-1/3 rounded bg-zinc-200 mb-2"></div>
              <div className="h-3 w-2/3 rounded bg-zinc-100 mb-2"></div>
              <div className="h-3 w-1/4 rounded bg-zinc-100"></div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && filteredDrafts.length === 0 && (
        <div className="rounded-xl border border-dashed border-zinc-300 bg-white p-12 text-center">
          <FileText className="mx-auto h-10 w-10 text-zinc-400" />
          <h3 className="mt-3 text-sm font-semibold text-zinc-900">No outreach drafts found</h3>
          <p className="mt-1 text-xs text-zinc-500">
            {statusFilter !== "all"
              ? `No drafts currently match the filter "${statusFilter}".`
              : "Get started by creating a new outreach draft for a contact and campaign."}
          </p>
          <div className="mt-4">
            <Link
              href="/outreach/new"
              className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-800"
            >
              <Plus className="h-3.5 w-3.5" />
              New Outreach Draft
            </Link>
          </div>
        </div>
      )}

      {/* Drafts List */}
      {!loading && !error && filteredDrafts.length > 0 && (
        <div className="divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white shadow-2xs">
          {filteredDrafts.map((draft) => (
            <div
              key={draft.id}
              className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 gap-3 transition-colors hover:bg-zinc-50/60"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <Link
                    href={`/outreach/${draft.id}`}
                    className="text-sm font-semibold text-zinc-900 hover:text-blue-600 truncate"
                  >
                    {draft.current_subject || "(Untitled Subject)"}
                  </Link>
                  <DraftStatusBadge status={draft.status as DraftStatus} />
                  <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[11px] font-mono text-zinc-600">
                    v{draft.current_version_number}
                  </span>
                </div>

                <p className="text-xs text-zinc-600 line-clamp-2 font-mono bg-zinc-50 p-2 rounded border border-zinc-100">
                  {draft.current_body || "No body content..."}
                </p>

                <div className="flex items-center gap-4 text-xs text-zinc-500 flex-wrap">
                  <span>Campaign: <span className="font-mono text-zinc-700">{draft.campaign_id ? draft.campaign_id.slice(0, 8) + '...' : 'None'}</span></span>
                  <span>Contact: <span className="font-mono text-zinc-700">{draft.contact_id.slice(0, 8)}...</span></span>
                  {draft.created_at && (
                    <span>Created: {new Date(draft.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Link
                  href={`/outreach/${draft.id}`}
                  className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900 transition-colors"
                >
                  <span>Review Draft</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
