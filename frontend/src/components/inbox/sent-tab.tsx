"use client";

import { useEffect, useState } from"react";
import Link from"next/link";
import { useWorkspace } from"@/lib/workspace-context";
import { fetchDeliveries, type EmailDelivery, type DeliveryStatus } from"@/lib/api/deliveries";
import { DeliveryStatusBadge } from"@/components/deliveries/delivery-status-badge";
import { Send, Eye, AlertCircle, RefreshCw } from"lucide-react";

export function SentTab() {
 const { activeWorkspace } = useWorkspace();
 const [deliveries, setDeliveries] = useState<EmailDelivery[]>([]);
 const [statusFilter, setStatusFilter] = useState<string>("all");
 const [loading, setLoading] = useState<boolean>(true);
 const [error, setError] = useState<string | null>(null);
 const [refreshKey, setRefreshKey] = useState<number>(0);

 useEffect(() => {
 async function loadData() {
 if (!activeWorkspace) return;
 setLoading(true);
 setError(null);
 try {
 const res = await fetchDeliveries(activeWorkspace.id, { status: statusFilter });
 setDeliveries(res);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load delivery records");
 } finally {
 setLoading(false);
 }
 }
 loadData();
 }, [activeWorkspace, statusFilter, refreshKey]);

 return (
 <div className="space-y-6">
 {/* Filter Toolbar */}
 <div className="flex items-center justify-between gap-4 rounded-lg border border-salesos-border bg-salesos-surface p-3 shadow-sm">
 <div className="flex items-center gap-1.5 overflow-x-auto">
 {[
 { id:"all", label:"All Deliveries"},
 { id:"sent", label:"Submitted"},
 { id:"delivered", label:"Delivered"},
 { id:"failed", label:"Failed"},
 { id:"bounced", label:"Bounced"},
 ].map((tab) => (
 <button
 key={tab.id}
 onClick={() => setStatusFilter(tab.id)}
 className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors whitespace-nowrap ${
 statusFilter === tab.id
 ?"bg-salesos-brand-subtle text-salesos-brand"
 :"text-salesos-text-secondary hover:bg-salesos-surface-muted"
 }`}
 >
 {tab.label}
 </button>
 ))}
 </div>

 <div className="flex items-center gap-4">
 <div className="inline-flex items-center gap-1.5 rounded-md border border-salesos-border px-2 py-1 text-[11px] text-salesos-text-secondary font-medium">
 <span>Send Safety On</span>
 </div>
 <button
 onClick={() => setRefreshKey((k) => k + 1)}
 className="inline-flex items-center gap-1 text-xs text-salesos-text-secondary hover:text-salesos-text"
 >
 <RefreshCw className="h-3.5 w-3.5"/>
 <span>Refresh</span>
 </button>
 </div>
 </div>

 {/* Error state */}
 {error && (
 <div className="flex items-center gap-2 rounded-lg border border-salesos-danger/20 bg-salesos-danger/10 p-4 text-xs text-salesos-danger">
 <AlertCircle className="h-4 w-4 text-salesos-danger shrink-0"/>
 <span>{error}</span>
 </div>
 )}

 {/* Table Card */}
 <div className="rounded-lg border border-salesos-border bg-salesos-surface shadow-sm overflow-hidden">
 {loading ? (
 <div className="p-12 text-center text-xs text-salesos-text-secondary/60">Loading delivery records...</div>
 ) : deliveries.length === 0 ? (
 <div className="p-12 text-center text-xs text-salesos-text-secondary space-y-2">
 <Send className="mx-auto h-8 w-8 text-salesos-text-secondary/40"/>
 <p className="font-semibold text-salesos-text">No Email Deliveries Found</p>
 <p className="text-salesos-text-secondary/60">Approved outreach drafts sent by users will appear here.</p>
 </div>
 ) : (
 <table className="w-full text-left text-xs text-salesos-text-secondary">
 <thead className="border-b border-salesos-border bg-salesos-surface-muted text-[11px] font-semibold uppercase tracking-wider text-salesos-text-secondary">
 <tr>
 <th className="px-4 py-3">Recipient</th>
 <th className="px-4 py-3">Subject Line</th>
 <th className="px-4 py-3">Provider & ID</th>
 <th className="px-4 py-3">Status</th>
 <th className="px-4 py-3">Sent At</th>
 <th className="px-4 py-3 text-right">Action</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-salesos-border">
 {deliveries.map((item) => (
 <tr key={item.id} className="hover:bg-salesos-surface-muted/80 transition-colors">
 <td className="px-4 py-3.5 text-[13px] font-medium text-salesos-text truncate max-w-[180px]">{item.recipient_email}</td>
 <td className="px-4 py-3.5 text-[13px] text-salesos-text-secondary max-w-xs truncate">
 {item.subject ||"(No subject)"}
 </td>
 <td className="px-4 py-3.5 text-[11px] text-salesos-text-secondary whitespace-nowrap">
 <span className="capitalize text-[13px] text-salesos-text-secondary">{item.provider}</span>
 </td>
 <td className="px-4 py-3.5">
 <DeliveryStatusBadge status={item.status as DeliveryStatus} />
 </td>
 <td className="px-4 py-3.5 text-[11px] text-salesos-text-secondary whitespace-nowrap">
 {new Date(item.created_at).toLocaleString()}
 </td>
 <td className="px-4 py-3.5 text-right">
 <Link
 href={`/deliveries/${item.id}`}
 className="inline-flex items-center gap-1 text-xs font-semibold text-salesos-brand hover:text-salesos-brand-hover hover:underline"
 >
 <Eye className="h-3.5 w-3.5"/>
 <span>Details</span>
 </Link>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 )}
 </div>
 </div>
 );
}
