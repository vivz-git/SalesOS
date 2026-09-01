"use client";

import { useEffect, useState } from"react";
import Link from"next/link";
import { useWorkspace } from"@/lib/workspace-context";
import { fetchApprovalQueue } from"@/lib/api/approvals";
import { ChevronRight } from"lucide-react";

export default function DashboardHomePage() {
 const { activeWorkspace } = useWorkspace();
 const [pendingCount, setPendingCount] = useState<number>(0);
 const [loadingCount, setLoadingCount] = useState<boolean>(true);

 useEffect(() => {
 async function loadPending() {
 if (!activeWorkspace) return;
 setLoadingCount(true);
 try {
 const queue = await fetchApprovalQueue(activeWorkspace.id, {
 status:"ready_for_review",
 });
 setPendingCount(queue.length);
 } catch {
 // Fallback gracefully
 } finally {
 setLoadingCount(false);
 }
 }
 loadPending();
 }, [activeWorkspace]);

 return (
 <div className="space-y-8">
 {/* Page header */}
 <div>
 <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
 {activeWorkspace ? activeWorkspace.name :"Dashboard"}
 </h1>
 <p className="mt-1 text-sm text-slate-500">
 What needs your attention today.
 </p>
 </div>

 {/* Attention items */}
 <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
 {/* Pending Approvals — only live metric shown */}
 <Link
 href="/approvals?status=ready_for_review"
 className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-indigo-200"
 >
 <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
 Pending Approvals
 </p>
 <p
 className={`mt-2 text-3xl font-bold tabular-nums ${
 loadingCount
 ?"text-slate-200"
 : pendingCount > 0
 ?"text-indigo-600"
 :"text-slate-400"
 }`}
 >
 {loadingCount ?"—": pendingCount}
 </p>
 <p className="mt-2 flex items-center gap-1 text-[13px] font-medium text-slate-500 group-hover:text-indigo-600 transition-colors">
 Review queue
 <ChevronRight className="h-3.5 w-3.5"/>
 </p>
 </Link>

 {/* Prospects — navigate to action */}
 <Link
 href="/prospects"
 className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-slate-300"
 >
 <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
 Prospects
 </p>
 <p className="mt-2 text-[13px] text-slate-600">
 Manage contacts and target companies.
 </p>
 <p className="mt-2 flex items-center gap-1 text-[13px] font-medium text-slate-500 group-hover:text-slate-900 transition-colors">
 View prospects
 <ChevronRight className="h-3.5 w-3.5"/>
 </p>
 </Link>

 {/* Inbox — navigate to action */}
 <Link
 href="/inbox"
 className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-slate-300"
 >
 <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
 Replies
 </p>
 <p className="mt-2 text-[13px] text-slate-600">
 Prospect replies and sent email status.
 </p>
 <p className="mt-2 flex items-center gap-1 text-[13px] font-medium text-slate-500 group-hover:text-slate-900 transition-colors">
 Open inbox
 <ChevronRight className="h-3.5 w-3.5"/>
 </p>
 </Link>
 </div>
 </div>
 );
}
