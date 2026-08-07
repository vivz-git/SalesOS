import type { JobStatus, ResearchStatus } from "@/lib/api/research";

interface ResearchStatusBadgeProps {
  status: ResearchStatus | JobStatus;
}

export function ResearchStatusBadge({ status }: ResearchStatusBadgeProps) {
  switch (status) {
    case "completed":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Completed
        </span>
      );
    case "in_progress":
    case "running":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 ring-1 ring-indigo-600/20 ring-inset">
          <span className="h-1.5 w-1.5 animate-ping rounded-full bg-indigo-500" />
          In Progress
        </span>
      );
    case "queued":
    case "pending":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 ring-1 ring-amber-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          {status === "queued" ? "Queued" : "Pending"}
        </span>
      );
    case "failed":
    default:
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-600/20 ring-inset">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
          Failed
        </span>
      );
  }
}
