"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import { fetchDeliveries, type EmailDelivery, type DeliveryStatus } from "@/lib/api/deliveries";
import { DeliveryStatusBadge } from "@/components/deliveries/delivery-status-badge";
import { Send, Eye, ShieldAlert, AlertCircle, RefreshCw } from "lucide-react";

export default function DeliveriesListPage() {
  const { activeWorkspace } = useWorkspace();
  const [deliveries, setDeliveries] = useState<EmailDelivery[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      if (!activeWorkspace) return;
      setLoading(true);
      setError(null);
      try {
        const res = await fetchDeliveries(activeWorkspace.id, { status: statusFilter });
        setDeliveries(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load delivery records");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [activeWorkspace, statusFilter]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 flex items-center gap-2">
            <Send className="h-6 w-6 text-purple-600" />
            <span>Email Deliveries</span>
          </h1>
          <p className="mt-1 text-xs text-zinc-500">
            Outbound email delivery log and provider-normalized delivery statuses.
          </p>
        </div>

        {/* Safety Indicator */}
        <div className="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs text-blue-900 font-medium">
          <ShieldAlert className="h-4 w-4 text-blue-600 shrink-0" />
          <span>Zero Autonomous Sends • Human Initiated</span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex items-center justify-between gap-4 rounded-xl border border-zinc-200 bg-white p-4 shadow-2xs">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {[
            { id: "all", label: "All Deliveries" },
            { id: "sent", label: "Sent (Submitted)" },
            { id: "delivered", label: "Delivered" },
            { id: "failed", label: "Failed" },
            { id: "bounced", label: "Bounced" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors whitespace-nowrap ${
                statusFilter === tab.id
                  ? "bg-purple-100 text-purple-900"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <button
          onClick={() => setStatusFilter((prev) => prev)}
          className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-900"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800">
          <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Table Card */}
      <div className="rounded-xl border border-zinc-200 bg-white shadow-2xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-zinc-400">Loading delivery records...</div>
        ) : deliveries.length === 0 ? (
          <div className="p-12 text-center text-xs text-zinc-500 space-y-2">
            <Send className="mx-auto h-8 w-8 text-zinc-300" />
            <p className="font-semibold text-zinc-800">No Email Deliveries Found</p>
            <p className="text-zinc-400">Approved outreach drafts sent by users will appear here.</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs text-zinc-700">
            <thead className="border-b border-zinc-200 bg-zinc-50 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              <tr>
                <th className="px-4 py-3">Recipient</th>
                <th className="px-4 py-3">Subject Line</th>
                <th className="px-4 py-3">Provider & ID</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Sent At</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {deliveries.map((item) => (
                <tr key={item.id} className="hover:bg-zinc-50/80 transition-colors">
                  <td className="px-4 py-3.5 font-semibold text-zinc-900">{item.recipient_email}</td>
                  <td className="px-4 py-3.5 font-medium text-zinc-800 max-w-xs truncate">
                    {item.subject || "(No subject)"}
                  </td>
                  <td className="px-4 py-3.5 font-mono text-[11px] text-zinc-500">
                    <span className="capitalize">{item.provider}</span>: {item.provider_message_id ? item.provider_message_id.slice(0, 16) : "N/A"}
                  </td>
                  <td className="px-4 py-3.5">
                    <DeliveryStatusBadge status={item.status as DeliveryStatus} />
                  </td>
                  <td className="px-4 py-3.5 font-mono text-[11px] text-zinc-500">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <Link
                      href={`/deliveries/${item.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-purple-600 hover:text-purple-900 hover:underline"
                    >
                      <Eye className="h-3.5 w-3.5" />
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
