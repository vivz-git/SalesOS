import type { AccountStatus } from "@/lib/api/accounts";

interface AccountStatusBadgeProps {
  status: AccountStatus;
}

export function AccountStatusBadge({ status }: AccountStatusBadgeProps) {
  switch (status) {
    case "qualified":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Qualified
        </span>
      );
    case "disqualified":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
          Disqualified
        </span>
      );
    case "archived":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-600 ring-1 ring-zinc-500/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
          Archived
        </span>
      );
    case "target":
    default:
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 ring-1 ring-indigo-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
          Target
        </span>
      );
  }
}
