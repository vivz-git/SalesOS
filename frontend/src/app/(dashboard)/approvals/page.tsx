"use client";

import { useEffect, useState } from"react";
import Link from"next/link";
import { useWorkspace } from"@/lib/workspace-context";
import { fetchContacts } from "@/lib/api/contacts";
import { fetchOutreachDrafts, type OutreachDraft, type DraftStatus } from"@/lib/api/outreach";
import { DraftStatusBadge } from"@/components/outreach/draft-status-badge";
import { Plus, Search, FileText, AlertCircle, RefreshCw, ChevronRight } from"lucide-react";

export default function ApprovalsPage() {
 const { activeWorkspace } = useWorkspace();
 const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
 const [loading, setLoading] = useState<boolean>(true);
 const [error, setError] = useState<string | null>(null);
 const [statusFilter, setStatusFilter] = useState<string>("all");
 const [searchQuery, setSearchQuery] = useState<string>("");
 const [contactsMap, setContactsMap] = useState<Record<string, string>>({});

 async function loadDrafts() {
 if (!activeWorkspace) return;
 setLoading(true);
 setError(null);

 try {
 const filter = statusFilter ==="all"? undefined : statusFilter;
 const data = await fetchOutreachDrafts(activeWorkspace.id, { status: filter });
 setDrafts(data);
 const contacts = await fetchContacts(activeWorkspace.id);
 const map: Record<string, string> = {};
 for (const contact of contacts) {
  map[contact.id] = contact.first_name + (contact.last_name ? " " + contact.last_name : "");
 }
 setContactsMap(map);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load outreach drafts");
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
 { id:"all", label:"All Drafts"},
 { id:"draft", label:"Draft"},
 { id:"ready_for_review", label:"Ready for Review"},
 { id:"approved", label:"Approved"},
 { id:"rejected", label:"Rejected"},
 { id:"archived", label:"Archived"},
 ];

 return (
 <div className="mx-auto max-w-7xl space-y-6 p-6">
 {/* Header */}
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
 <div>
 <h1 className="text-2xl font-bold tracking-tight text-salesos-text">Approvals</h1>
 <p className="mt-1 text-sm text-salesos-text-secondary">
 Create, version, and review personalized message drafts for outreach campaigns.
 </p>
 </div>

 <Link
 href="/outreach/new"
 className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition-colors"
 >
 <Plus className="h-4 w-4"/>
 Create Draft
 </Link>
 </div>

 {/* Controls Bar */}
 <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-salesos-border pb-3">
 {/* Status Filter Tabs */}
 <div className="flex flex-wrap gap-1">
 {filterTabs.map((tab) => (
 <button
 key={tab.id}
 type="button"
 onClick={() => setStatusFilter(tab.id)}
 className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
 statusFilter === tab.id
 ?"bg-salesos-brand text-white"
 :"text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text"
 }`}
 >
 {tab.label}
 </button>
 ))}
 </div>

 {/* Search Input & Refresh */}
 <div className="flex items-center gap-2">
 <div className="relative flex-1 sm:w-64">
 <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-salesos-text-secondary/60"/>
 <input
 type="text"
 placeholder="Search subject or body..."
 value={searchQuery}
 onChange={(e) => setSearchQuery(e.target.value)}
 className="w-full rounded-lg border border-salesos-border bg-salesos-surface pl-9 pr-3 py-1.5 text-xs text-salesos-text focus:border-slate-400 focus:outline-none"
 />
 </div>

 <button
 type="button"
 onClick={loadDrafts}
 className="rounded-lg border border-salesos-border p-1.5 text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text"
 title="Refresh list"
 >
 <RefreshCw className="h-4 w-4"/>
 </button>
 </div>
 </div>

 {/* Error state */}
 {error && (
 <div className="flex items-center gap-2 rounded-lg border border-salesos-danger/20 bg-salesos-danger/10 p-4 text-sm text-salesos-danger">
 <AlertCircle className="h-5 w-5 text-salesos-danger shrink-0"/>
 <span>{error}</span>
 </div>
 )}

 {/* Loading state */}
 {loading && (
 <div className="space-y-3">
 {[1, 2, 3].map((i) => (
 <div key={i} className="animate-pulse rounded-lg border border-salesos-border bg-salesos-surface p-4">
 <div className="h-4 w-1/3 rounded bg-salesos-surface-muted mb-2"></div>
 <div className="h-3 w-2/3 rounded bg-salesos-surface-muted mb-2"></div>
 <div className="h-3 w-1/4 rounded bg-salesos-surface-muted"></div>
 </div>
 ))}
 </div>
 )}

 {/* Empty state */}
 {!loading && !error && filteredDrafts.length === 0 && (
 <div className="rounded-lg border border-dashed border-salesos-border bg-salesos-surface p-12 text-center">
 <FileText className="mx-auto h-10 w-10 text-salesos-text-secondary/60"/>
 <h3 className="mt-3 text-sm font-semibold text-salesos-text">No outreach drafts found</h3>
 <p className="mt-1 text-xs text-salesos-text-secondary">
 {statusFilter !=="all"
 ? `No drafts currently match the filter"${statusFilter}".`
 :"Get started by creating a new outreach draft for a contact and campaign."}
 </p>
 <div className="mt-4">
 <Link
 href="/outreach/new"
 className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800"
 >
 <Plus className="h-3.5 w-3.5"/>
 New Outreach Draft
 </Link>
 </div>
 </div>
 )}

 {/* Drafts List */}
 {!loading && !error && filteredDrafts.length > 0 && (
 <div className="divide-y divide-slate-200 rounded-lg border border-salesos-border bg-salesos-surface shadow-sm">
 {filteredDrafts.map((draft) => (
 <div
 key={draft.id}
 className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 gap-3 transition-colors hover:bg-salesos-surface-muted/60"
 >
 <div className="space-y-1.5 flex-1 min-w-0">
 <div className="flex items-center gap-2.5 flex-wrap">
 <Link
 href={`/outreach/${draft.id}`}
 className="text-sm font-semibold text-salesos-text hover:text-blue-600 truncate"
 >
 {draft.current_subject ||"(Untitled Subject)"}
 </Link>
 <DraftStatusBadge status={draft.status as DraftStatus} />
 <span className="rounded bg-salesos-surface-muted px-1.5 py-0.5 text-[11px] font-medium text-salesos-text-secondary">
 v{draft.current_version_number}
 </span>
 </div>

 <p className="text-[13px] text-salesos-text-secondary line-clamp-2 border-salesos-border">
 {draft.current_body ||"No body content..."}
 </p>

 <div className="flex items-center gap-4 text-xs text-salesos-text-secondary flex-wrap">
 {draft.campaign_id && <span>Campaign: <span className="font-medium text-salesos-text-secondary">Active Campaign</span></span>}
 <span>Prospect: <span className="font-medium text-salesos-text-secondary">{contactsMap[draft.contact_id] || "Unknown Prospect"}</span></span>
 {draft.created_at && (
 <span>Created: {new Date(draft.created_at).toLocaleDateString()}</span>
 )}
 </div>
 </div>

 <div className="flex items-center gap-2 shrink-0">
 <Link
 href={`/outreach/${draft.id}`}
 className="inline-flex items-center gap-1 rounded-lg border border-salesos-border px-3 py-1.5 text-xs font-semibold text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text transition-colors"
 >
 <span>Review Draft</span>
 <ChevronRight className="h-3.5 w-3.5"/>
 </Link>
 </div>
 </div>
 ))}
 </div>
 )}
 </div>
 );
}
