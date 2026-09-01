import type { ReplyState } from"@/lib/api/conversations";
import { Calendar, Clock, UserCheck, ShieldAlert, AlertCircle } from"lucide-react";

interface ReplyClassificationBadgeProps {
 state: ReplyState | null | undefined;
 className?: string;
}

export function ReplyClassificationBadge({ state, className =""}: ReplyClassificationBadgeProps) {
 if (!state) {
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500 ${className}`}>
 <span>Unclassified</span>
 </span>
 );
 }

 switch (state) {
 case"interested":
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-800 ${className}`}>
 <Calendar className="h-3 w-3 text-emerald-600"/>
 <span>Interested</span>
 </span>
 );
 case"not_now":
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-800 ${className}`}>
 <Clock className="h-3 w-3 text-amber-600"/>
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
 <span className={`inline-flex items-center gap-1 rounded-md bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-800 ${className}`}>
 <ShieldAlert className="h-3 w-3 text-rose-600"/>
 <span>Opt-Out</span>
 </span>
 );
 case"out_of_office":
 return (
 <span className={`inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700 ${className}`}>
 <Clock className="h-3 w-3 text-slate-600"/>
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
