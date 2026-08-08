import type { DraftStatus } from "@/lib/api/outreach";
import { CheckCircle2, Clock, FileEdit, Archive, XCircle, RefreshCw } from "lucide-react";

interface DraftStatusBadgeProps {
  status: DraftStatus;
  className?: string;
}

export function DraftStatusBadge({ status, className = "" }: DraftStatusBadgeProps) {
  switch (status) {
    case "draft":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800 ring-1 ring-amber-600/20 ${className}`}
        >
          <FileEdit className="h-3.5 w-3.5 text-amber-600" />
          Draft
        </span>
      );
    case "ready_for_review":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-800 ring-1 ring-blue-600/20 ${className}`}
        >
          <Clock className="h-3.5 w-3.5 text-blue-600" />
          Ready for Review
        </span>
      );
    case "approved":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-600/20 ${className}`}
        >
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
          Approved
        </span>
      );
    case "rejected":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-800 ring-1 ring-rose-600/20 ${className}`}
        >
          <XCircle className="h-3.5 w-3.5 text-rose-600" />
          Rejected
        </span>
      );
    case "superseded":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-purple-50 px-2.5 py-1 text-xs font-semibold text-purple-800 ring-1 ring-purple-600/20 ${className}`}
        >
          <RefreshCw className="h-3.5 w-3.5 text-purple-600" />
          Superseded
        </span>
      );
    case "archived":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-semibold text-zinc-700 ring-1 ring-zinc-500/20 ${className}`}
        >
          <Archive className="h-3.5 w-3.5 text-zinc-500" />
          Archived
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700 ${className}`}
        >
          {status}
        </span>
      );
  }
}
