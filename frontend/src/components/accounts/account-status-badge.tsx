import type { AccountStatus } from"@/lib/api/accounts";

interface AccountStatusBadgeProps {
 status: AccountStatus;
}

export function AccountStatusBadge({ status }: AccountStatusBadgeProps) {
 switch (status) {
 case"qualified":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-success/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-success ring-1 ring-emerald-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-success/100"/>
 Qualified
 </span>
 );
 case"disqualified":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-danger/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-danger ring-1 ring-rose-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-danger/100"/>
 Disqualified
 </span>
 );
 case"archived":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-surface-muted px-2.5 py-0.5 text-xs font-semibold text-salesos-text-secondary ring-1 ring-slate-500/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-slate-400"/>
 Archived
 </span>
 );
 case"target":
 default:
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-brand-subtle px-2.5 py-0.5 text-xs font-semibold text-salesos-brand ring-1 ring-salesos-focus/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-brand-subtle0"/>
 Target
 </span>
 );
 }
}
