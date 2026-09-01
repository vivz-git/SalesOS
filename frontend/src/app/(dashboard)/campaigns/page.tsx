"use client";

import { useCallback, useEffect, useState } from"react";
import Link from"next/link";
import { Megaphone, Plus, Search } from"lucide-react";

import { CampaignForm } from"@/components/campaigns/campaign-form";
import { CampaignStatusBadge } from"@/components/campaigns/campaign-status-badge";
import { Button } from"@/components/ui/button";
import {
 createCampaign,
 fetchCampaigns,
 type Campaign,
 type CampaignCreatePayload,
} from"@/lib/api/campaigns";
import { useWorkspace } from"@/lib/workspace-context";

const STATUS_TABS = [
 { label:"All", value:""},
 { label:"Active", value:"active"},
 { label:"Draft", value:"draft"},
 { label:"Paused", value:"paused"},
 { label:"Archived", value:"archived"},
];

export default function CampaignsPage() {
 const { activeWorkspace } = useWorkspace();
 const [campaigns, setCampaigns] = useState<Campaign[]>([]);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);
 const [statusFilter, setStatusFilter] = useState("");
 const [searchQuery, setSearchQuery] = useState("");
 const [isModalOpen, setIsModalOpen] = useState(false);

 const loadCampaigns = useCallback(async () => {
 if (!activeWorkspace) return;
 try {
 setLoading(true);
 setError(null);
 const data = await fetchCampaigns(activeWorkspace.id, statusFilter || undefined);
 setCampaigns(data);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load campaigns.");
 } finally {
 setLoading(false);
 }
 }, [activeWorkspace, statusFilter]);

 useEffect(() => {
 loadCampaigns();
 }, [loadCampaigns]);

 async function handleCreateCampaign(payload: CampaignCreatePayload) {
 if (!activeWorkspace) return;
 await createCampaign(activeWorkspace.id, payload);
 await loadCampaigns();
 }

 const filteredCampaigns = campaigns.filter((c) =>
 c.name.toLowerCase().includes(searchQuery.toLowerCase())
 );

 return (
 <div className="space-y-6">
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
 <div>
 <h1 className="text-2xl font-bold tracking-tight text-salesos-text">Campaigns</h1>
 <p className="mt-1 text-sm text-salesos-text-secondary">
 Manage outbound ICP definitions, target segments, and campaign lifecycle.
 </p>
 </div>

 <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
 <Plus className="h-4 w-4"/>
 <span>New Campaign</span>
 </Button>
 </div>

 <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-salesos-border pb-3">
 <div className="flex items-center gap-1 overflow-x-auto">
 {STATUS_TABS.map((tab) => {
 const isActive = statusFilter === tab.value;
 return (
 <button
 key={tab.value}
 type="button"
 onClick={() => setStatusFilter(tab.value)}
 className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
 isActive
 ?"bg-slate-900 text-white"
 :"text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text"
 }`}
 >
 {tab.label}
 </button>
 );
 })}
 </div>

 <div className="relative w-full sm:w-64">
 <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-salesos-text-secondary/60"/>
 <input
 type="text"
 value={searchQuery}
 onChange={(e) => setSearchQuery(e.target.value)}
 placeholder="Search campaigns..."
 className="w-full rounded-md border border-salesos-border pl-8 pr-3 py-1.5 text-xs text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>
 </div>

 {loading ? (
 <div className="flex h-48 w-full items-center justify-center rounded-xl border bg-salesos-surface p-6 shadow-sm">
 <div className="flex items-center gap-2 text-sm text-salesos-text-secondary">
 <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"/>
 <span>Loading campaigns...</span>
 </div>
 </div>
 ) : error ? (
 <div className="flex flex-col items-center justify-center rounded-xl border bg-salesos-surface p-6 text-center shadow-sm">
 <p className="text-sm font-medium text-salesos-danger">{error}</p>
 <Button variant="outline"size="sm"onClick={loadCampaigns} className="mt-3">
 Retry
 </Button>
 </div>
 ) : filteredCampaigns.length === 0 ? (
 <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-salesos-border bg-salesos-surface p-12 text-center shadow-sm">
 <div className="flex h-12 w-12 items-center justify-center rounded-full bg-salesos-surface-muted text-salesos-text-secondary">
 <Megaphone className="h-6 w-6"/>
 </div>
 <h3 className="mt-4 text-sm font-bold text-salesos-text">No campaigns found</h3>
 <p className="mt-1 text-xs text-salesos-text-secondary">
 {searchQuery
 ?"No campaign matched your search."
 :"Get started by creating your first outbound sales campaign."}
 </p>
 {!searchQuery && (
 <Button onClick={() => setIsModalOpen(true)} className="mt-4"size="sm">
 Create Campaign
 </Button>
 )}
 </div>
 ) : (
 <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
 {filteredCampaigns.map((campaign) => (
 <Link
 key={campaign.id}
 href={`/campaigns/${campaign.id}`}
 className="group flex flex-col justify-between rounded-xl border border-salesos-border bg-salesos-surface p-5 shadow-xs transition-all hover:border-salesos-border hover:shadow-md"
 >
 <div>
 <div className="flex items-start justify-between gap-2">
 <h3 className="text-base font-bold text-salesos-text group-hover:text-salesos-text-secondary">
 {campaign.name}
 </h3>
 <CampaignStatusBadge status={campaign.status} />
 </div>
 {campaign.target_segment && (
 <p className="mt-1 text-xs font-medium text-salesos-text-secondary">
 Target: {campaign.target_segment}
 </p>
 )}
 {campaign.description && (
 <p className="mt-2 text-xs text-salesos-text-secondary line-clamp-2">
 {campaign.description}
 </p>
 )}
 </div>

 <div className="mt-4 flex items-center justify-between border-t border-salesos-border pt-3 text-[11px] text-salesos-text-secondary/60">
 <span>View Brief & Actions →</span>
 </div>
 </Link>
 ))}
 </div>
 )}

 {isModalOpen && (
 <CampaignForm
 title="Create Outbound Campaign"
 onSubmit={handleCreateCampaign}
 onClose={() => setIsModalOpen(false)}
 />
 )}
 </div>
 );
}
