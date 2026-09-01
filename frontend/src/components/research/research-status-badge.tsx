import type { JobStatus, ResearchStatus } from"@/lib/api/research";

interface ResearchStatusBadgeProps {
 status: ResearchStatus | JobStatus;
}

export function ResearchStatusBadge({ status }: ResearchStatusBadgeProps) {
 switch (status) {
 case"completed":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-success/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-success ring-1 ring-emerald-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-success/100"/>
 Completed
 </span>
 );
 case"in_progress":
 case"running":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-brand-subtle px-2.5 py-0.5 text-xs font-semibold text-salesos-brand ring-1 ring-salesos-focus/20 ring-inset">
 <span className="h-1.5 w-1.5 animate-ping rounded-full bg-salesos-brand-subtle0"/>
 In Progress
 </span>
 );
 case"queued":
 case"pending":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-warning/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-warning ring-1 ring-amber-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-warning/100"/>
 {status ==="queued"?"Queued":"Pending"}
 </span>
 );
 case"failed":
 default:
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-danger/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-danger ring-1 ring-rose-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-danger/100"/>
 Failed
 </span>
 );
 }
}
