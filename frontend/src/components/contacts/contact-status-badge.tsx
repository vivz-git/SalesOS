import type { ContactStatus } from "@/lib/api/contacts";

interface ContactStatusBadgeProps {
  status: ContactStatus;
}

export function ContactStatusBadge({ status }: ContactStatusBadgeProps) {
  switch (status) {
    case "active":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Active
        </span>
      );
    case "unresponsive":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 ring-1 ring-amber-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          Unresponsive
        </span>
      );
    case "opted_out":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
          Opted Out
        </span>
      );
    case "archived":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-600 ring-1 ring-zinc-500/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
          Archived
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-600 ring-1 ring-zinc-500/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
          {status}
        </span>
      );
  }
}
