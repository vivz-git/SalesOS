import type { CampaignStatus } from"@/lib/api/campaigns";

interface CampaignStatusBadgeProps {
 status: CampaignStatus;
}

export function CampaignStatusBadge({ status }: CampaignStatusBadgeProps) {
 switch (status) {
 case"active":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-success/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-success ring-1 ring-emerald-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-success/100"/>
 Active
 </span>
 );
 case"paused":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-warning/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-warning ring-1 ring-amber-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-salesos-warning/100"/>
 Paused
 </span>
 );
 case"archived":
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-surface-muted px-2.5 py-0.5 text-xs font-semibold text-salesos-text-secondary ring-1 ring-slate-500/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-slate-400"/>
 Archived
 </span>
 );
 case"draft":
 default:
 return (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-semibold text-sky-700 ring-1 ring-sky-600/20 ring-inset">
 <span className="h-1.5 w-1.5 rounded-full bg-sky-500"/>
 Draft
 </span>
 );
 }
}
