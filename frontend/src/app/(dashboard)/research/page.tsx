"use client";

import { useCallback, useEffect, useState } from"react";
import Link from"next/link";
import { ChevronLeft, ChevronRight, FileSearch, Plus, Search } from"lucide-react";

import { ResearchForm } from"@/components/research/research-form";
import { ResearchStatusBadge } from"@/components/research/research-status-badge";
import { Button } from"@/components/ui/button";
import { fetchAccounts, type Account } from"@/lib/api/accounts";
import {
 createResearchBrief,
 fetchResearchBriefs,
 type ResearchBrief,
 type ResearchBriefCreatePayload,
} from"@/lib/api/research";
import { useWorkspace } from"@/lib/workspace-context";

const PAGE_SIZE = 12;

const STATUS_TABS = [
 { label:"All", value:""},
 { label:"Completed", value:"completed"},
 { label:"In Progress", value:"in_progress"},
 { label:"Pending", value:"pending"},
 { label:"Failed", value:"failed"},
];

export default function ResearchPage() {
 const { activeWorkspace } = useWorkspace();
 const [briefs, setBriefs] = useState<ResearchBrief[]>([]);
 const [accounts, setAccounts] = useState<Account[]>([]);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 const [statusFilter, setStatusFilter] = useState("");
 const [accountFilter, setAccountFilter] = useState("");
 const [searchQuery, setSearchQuery] = useState("");
 const [page, setPage] = useState(1);
 const [isModalOpen, setIsModalOpen] = useState(false);

 const loadAccounts = useCallback(async () => {
 if (!activeWorkspace) return;
 try {
 const data = await fetchAccounts(activeWorkspace.id);
 setAccounts(data);
 } catch {
 // Ignore account load failure fallback
 }
 }, [activeWorkspace]);

 const loadBriefs = useCallback(async () => {
 if (!activeWorkspace) return;
 try {
 setLoading(true);
 setError(null);
 const data = await fetchResearchBriefs(activeWorkspace.id, {
 status: statusFilter || undefined,
 account_id: accountFilter || undefined,
 limit: PAGE_SIZE,
 offset: (page - 1) * PAGE_SIZE,
 });
 setBriefs(data);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load research briefs.");
 } finally {
 setLoading(false);
 }
 }, [activeWorkspace, statusFilter, accountFilter, page]);

 useEffect(() => {
 loadAccounts();
 }, [loadAccounts]);

 useEffect(() => {
 loadBriefs();
 }, [loadBriefs]);

 async function handleCreateBrief(payload: ResearchBriefCreatePayload) {
 if (!activeWorkspace) return;
 await createResearchBrief(activeWorkspace.id, payload);
 await loadBriefs();
 }

 const accountMap = new Map(accounts.map((a) => [a.id, a]));

 const filteredBriefs = briefs.filter((b) => {
 if (!searchQuery) return true;
 const s = searchQuery.toLowerCase();
 const summaryMatch = b.summary ? b.summary.toLowerCase().includes(s) : false;
 const accountMatch = accountMap.get(b.account_id)?.name.toLowerCase().includes(s);
 return summaryMatch || accountMatch;
 });

 return (
 <div className="space-y-6">
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
 <div>
 <h1 className="text-2xl font-bold tracking-tight text-slate-900">Research Briefs</h1>
 <p className="mt-1 text-sm text-slate-500">
 Account intelligence, decision-maker briefs, confidence evaluations, and source provenance.
 </p>
 </div>

 <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
 <Plus className="h-4 w-4"/>
 <span>New Research Brief</span>
 </Button>
 </div>

 <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-3">
 <div className="flex items-center gap-1 overflow-x-auto">
 {STATUS_TABS.map((tab) => {
 const isActive = statusFilter === tab.value;
 return (
 <button
 key={tab.value}
 type="button"
 onClick={() => {
 setStatusFilter(tab.value);
 setPage(1);
 }}
 className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
 isActive
 ?"bg-slate-900 text-white"
 :"text-slate-600 hover:bg-slate-100 hover:text-slate-900"
 }`}
 >
 {tab.label}
 </button>
 );
 })}
 </div>

 <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
 <select
 value={accountFilter}
 onChange={(e) => {
 setAccountFilter(e.target.value);
 setPage(1);
 }}
 className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-900 focus:border-slate-900 focus:outline-none"
 >
 <option value="">All Accounts</option>
 {accounts.map((a) => (
 <option key={a.id} value={a.id}>
 {a.name}
 </option>
 ))}
 </select>

 <div className="relative w-full sm:w-56">
 <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400"/>
 <input
 type="text"
 value={searchQuery}
 onChange={(e) => {
 setSearchQuery(e.target.value);
 setPage(1);
 }}
 placeholder="Search briefs..."
 className="w-full rounded-md border border-slate-300 pl-8 pr-3 py-1.5 text-xs text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>
 </div>
 </div>

 {loading ? (
 <div className="flex h-48 w-full items-center justify-center rounded-xl border bg-white p-6 shadow-sm">
 <div className="flex items-center gap-2 text-sm text-slate-500">
 <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"/>
 <span>Loading research briefs...</span>
 </div>
 </div>
 ) : error ? (
 <div className="flex flex-col items-center justify-center rounded-xl border bg-white p-6 text-center shadow-sm">
 <p className="text-sm font-medium text-red-600">{error}</p>
 <Button variant="outline"size="sm"onClick={loadBriefs} className="mt-3">
 Retry
 </Button>
 </div>
 ) : filteredBriefs.length === 0 ? (
 <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">
 <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
 <FileSearch className="h-6 w-6"/>
 </div>
 <h3 className="mt-4 text-sm font-bold text-slate-900">No research briefs found</h3>
 <p className="mt-1 text-xs text-slate-500">
 {searchQuery || accountFilter
 ?"No brief matched your search or account filter."
 :"Get started by creating your first company research brief."}
 </p>
 {!searchQuery && !accountFilter && (
 <Button onClick={() => setIsModalOpen(true)} className="mt-4"size="sm">
 New Research Brief
 </Button>
 )}
 </div>
 ) : (
 <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
 {filteredBriefs.map((brief) => {
 const targetAccount = accountMap.get(brief.account_id);
 return (
 <Link
 key={brief.id}
 href={`/research/${brief.id}`}
 className="group flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:border-slate-300 hover:shadow-md"
 >
 <div>
 <div className="flex items-start justify-between gap-2">
 <h3 className="text-base font-bold text-slate-900 group-hover:text-slate-700">
 {targetAccount ? targetAccount.name :"Target Account Brief"}
 </h3>
 <ResearchStatusBadge status={brief.status} />
 </div>

 {brief.summary && (
 <p className="mt-2 text-xs text-slate-600 line-clamp-2">
 {brief.summary}
 </p>
 )}

 {brief.confidence_score !== null && (
 <div className="mt-3 flex items-center gap-1.5 text-xs">
 <span className="font-semibold text-slate-500">Confidence:</span>
 <span className="font-bold text-emerald-700">
 {Math.round(brief.confidence_score * 100)}%
 </span>
 </div>
 )}
 </div>

 <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-[11px] text-slate-400">
 <span>View Findings & Provenance →</span>
 </div>
 </Link>
 );
 })}
 </div>
 )}

 {/* Pagination Controls */}
 <div className="flex items-center justify-between border-t border-slate-200 pt-4">
 <span className="text-xs text-slate-500">
 Showing page <span className="font-semibold text-slate-900">{page}</span>
 </span>
 <div className="flex items-center gap-2">
 <Button
 variant="outline"
 size="sm"
 onClick={() => setPage((p) => Math.max(1, p - 1))}
 disabled={page === 1 || loading}
 className="flex items-center gap-1"
 >
 <ChevronLeft className="h-4 w-4"/>
 <span>Previous</span>
 </Button>
 <Button
 variant="outline"
 size="sm"
 onClick={() => setPage((p) => p + 1)}
 disabled={briefs.length < PAGE_SIZE || loading}
 className="flex items-center gap-1"
 >
 <span>Next</span>
 <ChevronRight className="h-4 w-4"/>
 </Button>
 </div>
 </div>

 {isModalOpen && (
 <ResearchForm
 title="Create Research Brief"
 onSubmit={handleCreateBrief}
 onClose={() => setIsModalOpen(false)}
 />
 )}
 </div>
 );
}
