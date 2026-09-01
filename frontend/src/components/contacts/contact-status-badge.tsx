import type { ContactStatus } from"@/lib/api/contacts";

interface ContactStatusBadgeProps {
 status: ContactStatus;
}

export function ContactStatusBadge({ status }: ContactStatusBadgeProps) {
 switch (status) {
 case"active":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-success/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-success ring-1 ring-emerald-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-success/100"/>
 Active
 </span>
 );
 case"unresponsive":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-warning/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-warning ring-1 ring-amber-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-warning/100"/>
 Unresponsive
 </span>
 );
 case"opted_out":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-danger/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-danger ring-1 ring-rose-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-danger/100"/>
 Opted Out
 </span>
 );
 case"archived":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-surface-muted px-2.5 py-0.5 text-xs font-semibold text-salesos-text-secondary ring-1 ring-slate-500/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-slate-400"/>
 Archived
 </span>
 );
 default:
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-surface-muted px-2.5 py-0.5 text-xs font-semibold text-salesos-text-secondary ring-1 ring-slate-500/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-slate-400"/>
 {status}
 </span>
 );
 }
}
