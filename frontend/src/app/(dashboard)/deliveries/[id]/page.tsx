"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import { fetchDeliveryDetail, cancelDelivery, type EmailDelivery } from "@/lib/api/deliveries";
import { DeliveryStatusBadge } from "@/components/deliveries/delivery-status-badge";
import { ArrowLeft, Send, AlertCircle, CheckCircle2, ShieldAlert, Key, Mail, Clock } from "lucide-react";

interface DeliveryDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function DeliveryDetailPage({ params }: DeliveryDetailPageProps) {
  const { id: deliveryId } = use(params);
  const { activeWorkspace } = useWorkspace();
  const [delivery, setDelivery] = useState<EmailDelivery | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      if (!activeWorkspace || !deliveryId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await fetchDeliveryDetail(activeWorkspace.id, deliveryId);
        setDelivery(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load delivery detail");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [activeWorkspace, deliveryId]);

  async function handleCancel() {
    if (!activeWorkspace || !deliveryId) return;
    try {
      const updated = await cancelDelivery(activeWorkspace.id, deliveryId);
      setDelivery(updated);
      setActionMsg("Delivery cancelled");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to cancel delivery");
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div className="h-6 w-32 animate-pulse rounded bg-zinc-200"></div>
        <div className="h-48 animate-pulse rounded-xl bg-zinc-100 border border-zinc-200"></div>
      </div>
    );
  }

  if (error || !delivery) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800">
          <AlertCircle className="mx-auto h-8 w-8 text-rose-600 mb-2" />
          <h3 className="text-base font-semibold">Delivery Record Not Found</h3>
          <p className="mt-1 text-xs">{error || "Unable to locate delivery record"}</p>
          <div className="mt-4">
            <Link href="/deliveries" className="text-xs font-semibold text-purple-700 underline">
              Return to Deliveries List
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isCancellable = delivery.status === "queued" || delivery.status === "running";

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Back Button */}
      <div>
        <Link
          href="/deliveries"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500 hover:text-zinc-900 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Deliveries</span>
        </Link>
      </div>

      {actionMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 text-xs font-semibold text-emerald-900">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Main Header Banner */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-2xs space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-bold tracking-tight text-zinc-900 flex items-center gap-2">
                <Send className="h-5 w-5 text-purple-600" />
                <span>Outbound Delivery Record</span>
              </h1>
              <DeliveryStatusBadge status={delivery.status} />
            </div>
            <p className="text-xs text-zinc-500">
              Recipient: <strong className="text-zinc-900">{delivery.recipient_email}</strong>
            </p>
          </div>

          {isCancellable && (
            <button
              onClick={handleCancel}
              className="rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition-colors"
            >
              Cancel Delivery
            </button>
          )}
        </div>
      </div>

      {/* Grid Content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: Email Message details */}
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-2xs space-y-4">
            <h2 className="text-sm font-semibold text-zinc-900 flex items-center gap-2 border-b border-zinc-100 pb-3">
              <Mail className="h-4 w-4 text-purple-600" />
              <span>Delivered Message Payload</span>
            </h2>
            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wide text-zinc-400">Subject</label>
                <div className="mt-1 rounded-lg border border-zinc-200 bg-zinc-50 p-3 font-semibold text-zinc-900">
                  {delivery.subject}
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wide text-zinc-400">Body Content</label>
                <div className="mt-1 whitespace-pre-wrap rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-zinc-800 leading-relaxed min-h-[140px]">
                  {delivery.body}
                </div>
              </div>
            </div>
          </div>

          {delivery.error_message && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs space-y-1">
              <h3 className="font-semibold text-rose-900 flex items-center gap-1.5">
                <AlertCircle className="h-4 w-4 text-rose-600" />
                <span>Provider Error Response</span>
              </h3>
              <p className="text-rose-800 font-mono text-[11px] bg-white p-2 rounded border border-rose-200">
                {delivery.error_message}
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Metadata & Idempotency */}
        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs space-y-3 text-xs">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <Key className="h-3.5 w-3.5 text-zinc-500" />
              <span>Delivery Metadata</span>
            </h2>
            <div className="space-y-2 font-mono text-[11px]">
              <div>
                <span className="text-zinc-500">Provider:</span>{" "}
                <strong className="text-zinc-900 capitalize">{delivery.provider}</strong>
              </div>
              <div>
                <span className="text-zinc-500">Message ID:</span>{" "}
                <span className="text-zinc-800">{delivery.provider_message_id || "N/A"}</span>
              </div>
              <div>
                <span className="text-zinc-500">Version No:</span>{" "}
                <span className="text-zinc-800">v{delivery.version_number}</span>
              </div>
              <div className="pt-2 border-t border-zinc-100">
                <span className="text-zinc-500">Idempotency Key:</span>
                <p className="text-[10px] text-zinc-700 bg-zinc-50 p-1.5 rounded border border-zinc-200 mt-1 truncate">
                  {delivery.idempotency_key}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs space-y-3 text-xs">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-zinc-500" />
              <span>Timestamp Audit</span>
            </h2>
            <div className="space-y-1.5 text-zinc-600 text-[11px]">
              <div>Requested: <strong className="text-zinc-800">{new Date(delivery.created_at).toLocaleString()}</strong></div>
              <div>Updated: <strong className="text-zinc-800">{new Date(delivery.updated_at).toLocaleString()}</strong></div>
            </div>
          </div>

          <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-2">
            <ShieldAlert className="h-4 w-4 text-blue-600 shrink-0 mt-0.5" />
            <span>
              Outbound email request approved and sent via human authorization.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
