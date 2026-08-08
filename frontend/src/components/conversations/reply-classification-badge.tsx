import type { ReplyState } from "@/lib/api/conversations";
import { Sparkles, Calendar, Clock, UserCheck, ShieldAlert, AlertCircle } from "lucide-react";

interface ReplyClassificationBadgeProps {
  state: ReplyState | null | undefined;
  className?: string;
}

export function ReplyClassificationBadge({ state, className = "" }: ReplyClassificationBadgeProps) {
  if (!state) {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-500 ${className}`}>
        <span>Unclassified</span>
      </span>
    );
  }

  switch (state) {
    case "interested":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200 ${className}`}>
          <Calendar className="h-3 w-3 text-emerald-600" />
          <span>Interested</span>
        </span>
      );
    case "not_now":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800 border border-amber-200 ${className}`}>
          <Clock className="h-3 w-3 text-amber-600" />
          <span>Not Now</span>
        </span>
      );
    case "referral":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-800 border border-blue-200 ${className}`}>
          <UserCheck className="h-3 w-3 text-blue-600" />
          <span>Referral</span>
        </span>
      );
    case "unsubscribe":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-800 border border-rose-200 ${className}`}>
          <ShieldAlert className="h-3 w-3 text-rose-600" />
          <span>Opt-Out</span>
        </span>
      );
    case "out_of_office":
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-semibold text-purple-800 border border-purple-200 ${className}`}>
          <Sparkles className="h-3 w-3 text-purple-600" />
          <span>Out of Office</span>
        </span>
      );
    case "ambiguous":
    default:
      return (
        <span className={`inline-flex items-center gap-1 rounded-full bg-orange-50 px-2.5 py-0.5 text-xs font-semibold text-orange-800 border border-orange-200 ${className}`}>
          <AlertCircle className="h-3 w-3 text-orange-600" />
          <span>Needs Review</span>
        </span>
      );
  }
}
