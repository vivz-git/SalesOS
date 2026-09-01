"use client";

import { useCallback, useEffect, useState } from"react";
import Link from"next/link";
import { Building2, ChevronLeft, ChevronRight, ExternalLink, Plus, Search } from"lucide-react";

import { AccountForm } from"@/components/accounts/account-form";
import { AccountStatusBadge } from"@/components/accounts/account-status-badge";
import { Button } from"@/components/ui/button";
import {
 createAccount,
 fetchAccounts,
 type Account,
 type AccountCreatePayload,
} from"@/lib/api/accounts";
import { fetchCampaigns, type Campaign } from"@/lib/api/campaigns";
import { useWorkspace } from"@/lib/workspace-context";

const PAGE_SIZE = 12;

const STATUS_TABS = [
 { label:"All", value:""},
 { label:"Target", value:"target"},
 { label:"Qualified", value:"qualified"},
 { label:"Disqualified", value:"disqualified"},
 { label:"Archived", value:"archived"},
];

export default function AccountsView() {
 const { activeWorkspace } = useWorkspace();
 const [accounts, setAccounts] = useState<Account[]>([]);
 const [campaigns, setCampaigns] = useState<Campaign[]>([]);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 const [statusFilter, setStatusFilter] = useState("");
 const [campaignFilter, setCampaignFilter] = useState("");
 const [searchQuery, setSearchQuery] = useState("");
 const [page, setPage] = useState(1);
 const [isModalOpen, setIsModalOpen] = useState(false);

 const loadCampaigns = useCallback(async () => {
 if (!activeWorkspace) return;
 try {
 const data = await fetchCampaigns(activeWorkspace.id);
 setCampaigns(data);
 } catch {
 // Ignore campaign load failure in account view fallback
 }
 }, [activeWorkspace]);

 const loadAccounts = useCallback(async () => {
 if (!activeWorkspace) return;
 try {
 setLoading(true);
 setError(null);
 const data = await fetchAccounts(activeWorkspace.id, {
 status: statusFilter || undefined,
 campaign_id: campaignFilter || undefined,
 search: searchQuery || undefined,
 limit: PAGE_SIZE,
 offset: (page - 1) * PAGE_SIZE,
 });
 setCampaigns((prev) => prev);
 setAccounts(data);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load accounts.");
 } finally {
 setLoading(false);
 }
 }, [activeWorkspace, statusFilter, campaignFilter, searchQuery, page]);

 useEffect(() => {
 loadCampaigns();
 }, [loadCampaigns]);

 useEffect(() => {
 loadAccounts();
 }, [loadAccounts]);

 async function handleCreateAccount(payload: AccountCreatePayload) {
 if (!activeWorkspace) return;
 await createAccount(activeWorkspace.id, payload);
 await loadAccounts();
 }

 return (
 <div className="space-y-6">
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
 <div>
 <h2 className="text-lg font-bold tracking-tight text-slate-900">Companies</h2>
 <p className="mt-1 text-sm text-slate-500">
 Target company profiles, qualification status, and campaign assignments.
 </p>
 </div>

 <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2"variant="primary">
 <Plus className="h-4 w-4"/>
 <span>New Account</span>
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
 ?"bg-accent text-white"
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
 value={campaignFilter}
 onChange={(e) => {
 setCampaignFilter(e.target.value);
 setPage(1);
 }}
 className="rounded-md border border-slate-300 px-3 py-1.5 text-[13px] text-slate-900 focus:border-slate-900 focus:outline-none"
 >
 <option value="">All Campaigns</option>
 {campaigns.map((c) => (
 <option key={c.id} value={c.id}>
 {c.name}
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
 placeholder="Search accounts..."
 className="w-full rounded-md border border-slate-300 pl-8 pr-3 py-1.5 text-[13px] text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>
 </div>
 </div>

 {loading ? (
 <div className="flex h-48 w-full items-center justify-center rounded-lg border bg-white p-6 shadow-sm">
 <div className="flex items-center gap-2 text-sm text-slate-500">
 <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"/>
 <span>Loading target accounts...</span>
 </div>
 </div>
 ) : error ? (
 <div className="flex flex-col items-center justify-center rounded-lg border bg-white p-6 text-center shadow-sm">
 <p className="text-sm font-medium text-red-600">{error}</p>
 <Button variant="secondary"size="sm"onClick={loadAccounts} className="mt-3">
 Retry
 </Button>
 </div>
 ) : accounts.length === 0 ? (
 <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">
 <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
 <Building2 className="h-6 w-6"/>
 </div>
 <h3 className="mt-4 text-sm font-bold text-slate-900">No accounts found</h3>
 <p className="mt-1 text-[13px] text-slate-500">
 {searchQuery || campaignFilter
 ?"No company matched your search or filters."
 :"Get started by adding your first target company."}
 </p>
 {!searchQuery && !campaignFilter && (
 <Button onClick={() => setIsModalOpen(true)} className="mt-4"size="sm"variant="primary">
 Create Account
 </Button>
 )}
 </div>
 ) : (
 <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
 {accounts.map((account) => (
 <Link
 key={account.id}
 href={`/accounts/${account.id}`}
 className="group flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-5 shadow-xs transition-all hover:border-slate-300 hover:shadow-md"
 >
 <div>
 <div className="flex items-start justify-between gap-2">
 <h3 className="text-base font-bold text-slate-900 group-hover:text-slate-700">
 {account.name}
 </h3>
 <AccountStatusBadge status={account.status} />
 </div>

 {account.domain && (
 <p className="mt-1 flex items-center gap-1 text-xs font-medium text-slate-500">
 <span>{account.domain}</span>
 <ExternalLink className="h-3 w-3 text-slate-400"/>
 </p>
 )}

 <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-slate-600">
 {account.industry && (
 <div>
 <span className="font-medium text-slate-400">Industry: </span>
 {account.industry}
 </div>
 )}
 {account.employee_count && (
 <div>
 <span className="font-medium text-slate-400">Size: </span>
 {account.employee_count}
 </div>
 )}
 {(account.city || account.country) && (
 <div className="col-span-2">
 <span className="font-medium text-slate-400">Location: </span>
 {[account.city, account.country].filter(Boolean).join(",")}
 </div>
 )}
 </div>
 </div>

 <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-[11px] text-slate-400">
 <span>View Details & Actions →</span>
 </div>
 </Link>
 ))}
 </div>
 )}

 {/* Pagination Controls */}
 <div className="flex items-center justify-between border-t border-slate-200 pt-4">
 <span className="text-[13px] text-slate-500">
 Showing page <span className="font-semibold text-slate-900">{page}</span>
 </span>
 <div className="flex items-center gap-2">
 <Button
 variant="secondary"
 size="sm"
 onClick={() => setPage((p) => Math.max(1, p - 1))}
 disabled={page === 1 || loading}
 className="flex items-center gap-1"
 >
 <ChevronLeft className="h-4 w-4"/>
 <span>Previous</span>
 </Button>
 <Button
 variant="secondary"
 size="sm"
 onClick={() => setPage((p) => p + 1)}
 disabled={accounts.length < PAGE_SIZE || loading}
 className="flex items-center gap-1"
 >
 <span>Next</span>
 <ChevronRight className="h-4 w-4"/>
 </Button>
 </div>
 </div>

 {isModalOpen && (
 <AccountForm
 title="Add Target Company Account"
 onSubmit={handleCreateAccount}
 onClose={() => setIsModalOpen(false)}
 />
 )}
 </div>
 );
}
