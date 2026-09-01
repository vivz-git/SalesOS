"use client";

import { useEffect, useState } from"react";
import { useWorkspace } from"@/lib/workspace-context";
import {
 fetchWeeklyReportsList,
 generateWeeklyReport,
 type ReportRun,
} from"@/lib/api/reports";
import {
 BarChart3,
 RefreshCw,
 CheckCircle2,
 AlertCircle,
 TrendingUp,
 Mail,
 MessageSquare,

 ShieldAlert,
 Calendar,
 Zap,
} from"lucide-react";

export default function ReportsPage() {
 const { activeWorkspace } = useWorkspace();
 const [reports, setReports] = useState<ReportRun[]>([]);
 const [selectedReport, setSelectedReport] = useState<ReportRun | null>(null);
 const [loading, setLoading] = useState<boolean>(true);
 const [generating, setGenerating] = useState<boolean>(false);
 const [error, setError] = useState<string | null>(null);
 const [msg, setMsg] = useState<string | null>(null);

 async function loadData() {
 if (!activeWorkspace) return;
 setLoading(true);
 setError(null);
 try {
 const data = await fetchWeeklyReportsList(activeWorkspace.id);
 setReports(data);
 if (data.length > 0) {
 setSelectedReport(data[0]);
 }
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load weekly reports");
 } finally {
 setLoading(false);
 }
 }

 useEffect(() => {
 loadData();
 }, [activeWorkspace]);

 async function handleGenerateDigest() {
 if (!activeWorkspace) return;
 setGenerating(true);
 setMsg(null);
 try {
 const newReport = await generateWeeklyReport(activeWorkspace.id);
 setMsg("New Weekly Digest generated and persisted successfully.");
 await loadData();
 setSelectedReport(newReport);
 setTimeout(() => setMsg(null), 4000);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to generate weekly digest");
 } finally {
 setGenerating(false);
 }
 }

 const m = selectedReport?.metrics_snapshot;

 return (
 <div className="mx-auto max-w-6xl space-y-6 p-6">
 {/* Header */}
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
 <div>
 <h1 className="text-2xl font-bold tracking-tight text-salesos-text\">Weekly Performance & Activity Digest</h1>
 <p className="mt-1 text-xs text-salesos-text-secondary">
 Weekly workspace activity, delivery rates, and conversion metrics.
 </p>
 </div>

 <button
 type="button"
 onClick={handleGenerateDigest}
 disabled={generating}
 className="inline-flex items-center gap-1.5 rounded-lg bg-salesos-brand px-4 py-2 text-xs font-semibold text-white hover:bg-salesos-brand-hover transition-colors shrink-0 shadow-sm focus:outline-none"
 >
 <RefreshCw className={`h-3.5 w-3.5 ${generating ?"animate-spin":""}`} />
 <span>{generating ?"Generating...":"Generate Digest"}</span>
 </button>
 </div>

 {error && (
 <div className="flex items-center gap-2 rounded-xl border border-salesos-danger/20 bg-salesos-danger/10 p-4 text-xs text-salesos-danger">
 <AlertCircle className="h-4 w-4 text-salesos-danger shrink-0"/>
 <span>{error}</span>
 </div>
 )}

 {msg && (
 <div className="flex items-center gap-2 rounded-xl border border-salesos-success/20 bg-salesos-success/10 p-4 text-xs text-emerald-900 font-semibold">
 <CheckCircle2 className="h-4 w-4 text-salesos-success shrink-0"/>
 <span>{msg}</span>
 </div>
 )}

 {loading ? (
 <div className="p-12 text-center text-xs text-salesos-text-secondary/60">Loading performance metrics and digest...</div>
 ) : selectedReport && m ? (
 <>
 {/* Calendar Period & Title Card */}
 <div className="flex items-center justify-between rounded-xl border border-salesos-border bg-salesos-surface p-4 shadow-sm">
 <div className="flex items-center gap-2">
 <Calendar className="h-5 w-5 text-salesos-brand"/>
 <div>
 <h2 className="text-sm font-bold text-salesos-text">{selectedReport.title}</h2>
 <p className="text-[11px] text-salesos-text-secondary">
 Calendar Period: {new Date(selectedReport.period_start).toLocaleDateString()} – {new Date(selectedReport.period_end).toLocaleDateString()}
 </p>
 </div>
 </div>

 {reports.length > 1 && (
 <select
 value={selectedReport.id}
 onChange={(e) => {
 const r = reports.find((item) => item.id === e.target.value);
 if (r) setSelectedReport(r);
 }}
 className="rounded-lg border border-salesos-border bg-salesos-surface-muted p-2 text-xs font-semibold text-salesos-text focus:border-salesos-focus focus:outline-none"
 >
 {reports.map((rep) => (
 <option key={rep.id} value={rep.id}>
 {rep.title}
 </option>
 ))}
 </select>
 )}
 </div>

 {/* Metric KPI Cards */}
 <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-4 shadow-sm space-y-1">
 <span className="text-xs font-semibold text-salesos-text-secondary flex items-center gap-1">
 <TrendingUp className="h-3.5 w-3.5 text-salesos-brand"/>
 Approval Rate
 </span>
 <div className="text-2xl font-bold text-salesos-brand">{m.approval_rate}%</div>
 <p className="text-[11px] text-salesos-text-secondary/60">
 {m.drafts_approved_count} approved / {m.drafts_submitted_count} submitted
 </p>
 </div>

 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-4 shadow-sm space-y-1">
 <span className="text-xs font-semibold text-salesos-text-secondary flex items-center gap-1">
 <Mail className="h-3.5 w-3.5 text-blue-600"/>
 Delivery Rate
 </span>
 <div className="text-2xl font-bold text-blue-900">{m.delivery_rate}%</div>
 <p className="text-[11px] text-salesos-text-secondary/60">
 {m.emails_delivered_count} delivered / {m.emails_sent_count} sent
 </p>
 </div>

 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-4 shadow-sm space-y-1">
 <span className="text-xs font-semibold text-salesos-text-secondary flex items-center gap-1">
 <MessageSquare className="h-3.5 w-3.5 text-salesos-success"/>
 Interested Reply Rate
 </span>
 <div className="text-2xl font-bold text-emerald-900">{m.interested_reply_rate}%</div>
 <p className="text-[11px] text-salesos-text-secondary/60">
 {m.interested_replies_count} interested / {m.replies_received_count} replies
 </p>
 </div>

 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-4 shadow-sm space-y-1">
 <span className="text-xs font-semibold text-salesos-text-secondary flex items-center gap-1">
 <Zap className="h-3.5 w-3.5 text-salesos-warning"/>
 CRM Synced Records
 </span>
 <div className="text-2xl font-bold text-amber-900">{m.crm_synced_records_count}</div>
 <p className="text-[11px] text-salesos-text-secondary/60">HubSpot items updated</p>
 </div>
 </div>

 {/* Detailed Metric Grid & Executive Summary */}
 <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
 {/* Left 2 Cols: Executive Summary & Recommended Actions */}
 <div className="space-y-6 lg:col-span-2">
 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-6 shadow-sm space-y-4">
 <h2 className="text-sm font-bold text-salesos-text flex items-center gap-2 border-b border-salesos-border pb-3">
 <BarChart3 className="h-4 w-4 text-salesos-brand"/>
 <span>Executive Summary</span>
 </h2>
 <p className="text-xs text-salesos-text-secondary leading-relaxed whitespace-pre-wrap bg-salesos-surface-muted p-4 rounded-lg border border-salesos-border">
 {selectedReport.executive_summary}
 </p>
 </div>

 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-6 shadow-sm space-y-4">
 <h2 className="text-sm font-bold text-salesos-text flex items-center gap-2 border-b border-salesos-border pb-3">
 <TrendingUp className="h-4 w-4 text-salesos-success"/>
 <span>Recommended Campaign & Outreach Actions</span>
 </h2>
 <ul className="space-y-2 text-xs text-salesos-text-secondary">
 {selectedReport.recommended_actions.map((act, idx) => (
 <li key={idx} className="flex items-start gap-2 bg-salesos-surface-muted p-3 rounded-lg border border-salesos-border">
 <CheckCircle2 className="h-4 w-4 text-salesos-success shrink-0 mt-0.5"/>
 <span>{act}</span>
 </li>
 ))}
 </ul>
 </div>
 </div>

 {/* Right Col: Activity Breakdown */}
 <div className="space-y-6">
 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-5 shadow-sm space-y-4 text-xs">
 <h2 className="text-xs font-semibold uppercase tracking-wider text-salesos-text-secondary/60">
 Activity Breakdown
 </h2>

 <div className="space-y-2.5 divide-y divide-salesos-border">
 <div className="flex justify-between pt-1">
 <span className="text-salesos-text-secondary">Active Campaigns</span>
 <span className="font-bold text-salesos-text">{m.campaigns_count}</span>
 </div>
 <div className="flex justify-between pt-2">
 <span className="text-salesos-text-secondary">Accounts Researched</span>
 <span className="font-bold text-salesos-text">{m.accounts_researched_count}</span>
 </div>
 <div className="flex justify-between pt-2">
 <span className="text-salesos-text-secondary">Contacts Enrolled</span>
 <span className="font-bold text-salesos-text">{m.contacts_enrolled_count}</span>
 </div>
 <div className="flex justify-between pt-2">
 <span className="text-salesos-text-secondary">Drafts Generated</span>
 <span className="font-bold text-salesos-text">{m.drafts_generated_count}</span>
 </div>
 <div className="flex justify-between pt-2">
 <span className="text-salesos-text-secondary">Drafts Submitted</span>
 <span className="font-bold text-salesos-text">{m.drafts_submitted_count}</span>
 </div>
 <div className="flex justify-between pt-2">
 <span className="text-salesos-text-secondary">Drafts Approved</span>
 <span className="font-bold text-salesos-text">{m.drafts_approved_count}</span>
 </div>
 <div className="flex justify-between pt-2">
 <span className="text-salesos-text-secondary">Emails Bounced</span>
 <span className="font-bold text-salesos-danger">{m.emails_bounced_count}</span>
 </div>
 <div className="flex justify-between pt-2">
 <span className="text-salesos-text-secondary">Opt-Out Rate</span>
 <span className="font-bold text-salesos-danger">{m.opt_out_rate}%</span>
 </div>
 </div>
 </div>

 <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-2">
 <ShieldAlert className="h-4 w-4 text-blue-600 shrink-0 mt-0.5"/>
 <span>
 Metrics are calculated deterministically from stored records. No autonomous sending occurs.
 </span>
 </div>
 </div>
 </div>
 </>
 ) : null}
 </div>
 );
}
