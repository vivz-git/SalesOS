import type { DeliveryStatus } from "@/lib/api/deliveries";
import { CheckCircle2, Clock, Send, AlertTriangle, XCircle, ShieldAlert } from "lucide-react";

interface DeliveryStatusBadgeProps {
  status: DeliveryStatus;
  className?: string;
}

export function DeliveryStatusBadge({ status, className = "" }: DeliveryStatusBadgeProps) {
  switch (status) {
    case "sent":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200 ${className}`}>
          <Send className="h-3 w-3 text-blue-600" />
          <span>Sent (Submitted)</span>
        </span>
      );
    case "delivered":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200 ${className}`}>
          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
          <span>Delivered</span>
        </span>
      );
    case "running":
    case "queued":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800 border border-amber-200 ${className}`}>
          <Clock className="h-3 w-3 text-amber-600" />
          <span className="capitalize">{status}</span>
        </span>
      );
    case "bounced":
    case "complained":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-orange-50 px-2.5 py-0.5 text-xs font-semibold text-orange-800 border border-orange-200 ${className}`}>
          <AlertTriangle className="h-3 w-3 text-orange-600" />
          <span className="capitalize">{status}</span>
        </span>
      );
    case "failed":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 border border-rose-200 ${className}`}>
          <XCircle className="h-3 w-3 text-rose-600" />
          <span>Failed</span>
        </span>
      );
    case "cancelled":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-600 border border-zinc-200 ${className}`}>
          <ShieldAlert className="h-3 w-3 text-zinc-500" />
          <span>Cancelled</span>
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-700 ${className}`}>
          <span className="capitalize">{status}</span>
        </span>
      );
  }
}
