"use client";

import { useEffect, useState } from"react";
import { useWorkspace } from"@/lib/workspace-context";
import {
 fetchHubspotStatus,
 authorizeHubspot,
 disconnectHubspot,
 triggerHubspotSync,
 fetchHubspotSyncRuns,
 type IntegrationConnection,
 type SyncRun,
} from"@/lib/api/hubspot";
import { HubspotStatusBadge } from"@/components/integrations/hubspot-status-badge";
import {
 Link2,
 RefreshCw,
 Unlink,
 CheckCircle2,
 AlertCircle,
 Clock,
 Shield,
} from"lucide-react";

export default function SettingsPage() {
 const { activeWorkspace } = useWorkspace();
 const [connection, setConnection] = useState<IntegrationConnection | null>(null);
 const [syncRuns, setSyncRuns] = useState<SyncRun[]>([]);
 const [loading, setLoading] = useState<boolean>(true);
 const [syncing, setSyncing] = useState<boolean>(false);
 const [error, setError] = useState<string | null>(null);
 const [msg, setMsg] = useState<string | null>(null);

 async function loadData() {
 if (!activeWorkspace) return;
 setLoading(true);
 setError(null);
 try {
 const conn = await fetchHubspotStatus(activeWorkspace.id);
 setConnection(conn);
 if (conn.status ==="connected") {
 const runs = await fetchHubspotSyncRuns(activeWorkspace.id);
 setSyncRuns(runs);
 }
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load HubSpot integration status");
 } finally {
 setLoading(false);
 }
 }

 useEffect(() => {
 loadData();
 }, [activeWorkspace]);

 async function handleConnect() {
 if (!activeWorkspace) return;
 try {
 const res = await authorizeHubspot(activeWorkspace.id);
 window.location.href = res.authorization_url;
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to initiate OAuth authorization");
 }
 }

 async function handleDisconnect() {
 if (!activeWorkspace) return;
 try {
 const updated = await disconnectHubspot(activeWorkspace.id);
 setConnection(updated);
 setSyncRuns([]);
 setMsg("HubSpot portal connection disconnected.");
 setTimeout(() => setMsg(null), 4000);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to disconnect HubSpot portal");
 }
 }

 async function handleTriggerSync() {
 if (!activeWorkspace) return;
 setSyncing(true);
 setMsg(null);
 try {
 const newRun = await triggerHubspotSync(activeWorkspace.id,"export_to_crm");
 setMsg(`Sync completed successfully. ${newRun.records_processed} records synced.`);
 loadData();
 setTimeout(() => setMsg(null), 4000);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to trigger CRM sync");
 } finally {
 setSyncing(false);
 }
 }

 return (
 <div className="mx-auto max-w-5xl space-y-6 p-6">
 {/* Header */}
 <div>
 <h1 className="text-2xl font-bold tracking-tight text-slate-900">Workspace Settings & Integrations</h1>
 <p className="mt-1 text-xs text-slate-500">
 Manage workspace settings, tenant authorization, and external CRM integrations.
 </p>
 </div>

 {error && (
 <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-800">
 <AlertCircle className="h-4 w-4 text-red-600 shrink-0"/>
 <span>{error}</span>
 </div>
 )}

 {msg && (
 <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-900 font-semibold">
 <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0"/>
 <span>{msg}</span>
 </div>
 )}

 {/* HubSpot Integration Card */}
 <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
 <div className="space-y-1">
 <div className="flex items-center gap-3">
 <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
 <Link2 className="h-5 w-5 text-amber-600"/>
 <span>HubSpot CRM Integration</span>
 </h2>
 {connection && <HubspotStatusBadge status={connection.status} />}
 </div>
 <p className="text-xs text-slate-500">
 Synchronize Contacts, Companies, Outbound Email Deliveries, and Inbound Prospect Replies.
 </p>
 </div>

 <div className="flex items-center gap-2 shrink-0">
 {connection?.status ==="connected"? (
 <>
 <button
 type="button"
 onClick={handleTriggerSync}
 disabled={syncing}
 className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3.5 py-2 text-xs font-semibold text-accent-foreground hover:bg-accent-hover transition-colors shadow-sm focus:outline-none"
 >
 <RefreshCw className={`h-3.5 w-3.5 ${syncing ?"animate-spin":""}`} />
 <span>{syncing ?"Syncing...":"Sync Now"}</span>
 </button>
 <button
 type="button"
 onClick={handleDisconnect}
 className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors focus:outline-none"
 >
 <Unlink className="h-3.5 w-3.5"/>
 <span>Disconnect</span>
 </button>
 </>
 ) : (
 <button
 type="button"
 onClick={handleConnect}
 className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-xs font-semibold text-accent-foreground hover:bg-accent-hover transition-colors shadow-sm focus:outline-none"
 >
 <Link2 className="h-4 w-4"/>
 <span>Connect HubSpot Portal</span>
 </button>
 )}
 </div>
 </div>

 {/* Portal & Connection Metadata */}
 {connection && connection.status ==="connected"&& (
 <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
 <div>
 <span className="font-semibold text-slate-500 block">HubSpot Portal ID</span>
 <span className="font-mono text-slate-900 font-bold">{connection.portal_id ||"portal-998877"}</span>
 </div>
 <div>
 <span className="font-semibold text-slate-500 block">Connected At</span>
 <span className="text-slate-900">{connection.connected_at ? new Date(connection.connected_at).toLocaleString() :"Active"}</span>
 </div>
 <div>
 <span className="font-semibold text-slate-500 block">Last Synced</span>
 <span className="text-slate-900">{connection.last_synced_at ? new Date(connection.last_synced_at).toLocaleString() :"Never"}</span>
 </div>
 </div>
 )}

 {/* Sync History Table */}
 {connection?.status ==="connected"&& (
 <div className="space-y-3 pt-2">
 <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
 <Clock className="h-3.5 w-3.5 text-slate-500"/>
 <span>Recent Synchronization Runs</span>
 </h3>

 <div className="rounded-xl border border-slate-200 overflow-hidden">
 {loading ? (
 <div className="p-8 text-center text-xs text-slate-400">Loading sync history...</div>
 ) : syncRuns.length === 0 ? (
 <div className="p-8 text-center text-xs text-slate-400">No sync runs recorded yet.</div>
 ) : (
 <table className="w-full text-left text-xs text-slate-700">
 <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
 <tr>
 <th className="px-4 py-2.5">Sync Run ID</th>
 <th className="px-4 py-2.5">Direction</th>
 <th className="px-4 py-2.5">Status</th>
 <th className="px-4 py-2.5">Processed</th>
 <th className="px-4 py-2.5">Started At</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100">
 {syncRuns.map((run) => (
 <tr key={run.id} className="hover:bg-slate-50">
 <td className="px-4 py-2.5 font-mono text-[11px] text-slate-600">{run.id.substring(0, 8)}...</td>
 <td className="px-4 py-2.5 capitalize">{run.direction.replace(/_/g,"")}</td>
 <td className="px-4 py-2.5 font-semibold text-emerald-700 capitalize">{run.status}</td>
 <td className="px-4 py-2.5 font-semibold text-slate-900">{run.records_processed} items</td>
 <td className="px-4 py-2.5 font-mono text-[11px] text-slate-500">
 {new Date(run.started_at).toLocaleString()}
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 )}
 </div>
 </div>
 )}

 <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-700 flex items-start gap-2">
 <Shield className="h-4 w-4 text-slate-500 shrink-0 mt-0.5"/>
 <span>
 Server-side token protection: OAuth tokens are stored securely. No autonomous background sending occurs.
 </span>
 </div>
 </div>
 </div>
 );
}
