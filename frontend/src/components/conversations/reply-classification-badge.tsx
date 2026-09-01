import type { ReplyState } from"@/lib/api/conversations";
import { Calendar, Clock, UserCheck, ShieldAlert, AlertCircle } from"lucide-react";

interface ReplyClassificationBadgeProps {
 state: ReplyState | null | undefined;
 className?: string;
}

export function ReplyClassificationBadge({ state, className =""}: ReplyClassificationBadgeProps) {
 if (!state) {
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-salesos-surface-muted px-2 py-0.5 text-[11px] font-medium text-salesos-text-secondary ${className}`}>
 <span>Unclassified</span>
 </span>
 );
 }

 switch (state) {
 case"interested":
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-salesos-success/10 px-2 py-0.5 text-[11px] font-medium text-salesos-success ${className}`}>
 <Calendar className="h-3 w-3 text-salesos-success"/>
 <span>Interested</span>
 </span>
 );
 case"not_now":
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-salesos-warning/10 px-2 py-0.5 text-[11px] font-medium text-salesos-warning ${className}`}>
 <Clock className="h-3 w-3 text-salesos-warning"/>
 <span>Not Now</span>
 </span>
 );
 case"referral":
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-800 ${className}`}>
 <UserCheck className="h-3 w-3 text-blue-600"/>
 <span>Referral</span>
 </span>
 );
 case"unsubscribe":
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-salesos-danger/10 px-2 py-0.5 text-[11px] font-medium text-salesos-danger ${className}`}>
 <ShieldAlert className="h-3 w-3 text-salesos-danger"/>
 <span>Opt-Out</span>
 </span>
 );
 case"out_of_office":
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-salesos-surface-muted px-2 py-0.5 text-[11px] font-medium text-salesos-text-secondary ${className}`}>
 <Clock className="h-3 w-3 text-salesos-text-secondary"/>
 <span>Out of Office</span>
 </span>
 );
 case"ambiguous":
 default:
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-orange-50 px-2 py-0.5 text-[11px] font-medium text-orange-800 ${className}`}>
 <AlertCircle className="h-3 w-3 text-orange-600"/>
 <span>Needs Review</span>
 </span>
 );
 }
}
