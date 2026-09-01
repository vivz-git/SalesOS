import type { DraftStatus } from"@/lib/api/outreach";
import { CheckCircle2, Clock, FileEdit, Archive, XCircle, RefreshCw } from"lucide-react";

interface DraftStatusBadgeProps {
 status: DraftStatus;
 className?: string;
}

export function DraftStatusBadge({ status, className =""}: DraftStatusBadgeProps) {
 switch (status) {
 case"draft":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-800 ${className}`}
 >
 <FileEdit className="h-3.5 w-3.5 text-amber-600"/>
 Draft
 </span>
 );
 case"ready_for_review":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-800 ${className}`}
 >
 <Clock className="h-3.5 w-3.5 text-blue-600"/>
 Ready for Review
 </span>
 );
 case"approved":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-800 ${className}`}
 >
 <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600"/>
 Approved
 </span>
 );
 case"rejected":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-800 ${className}`}
 >
 <XCircle className="h-3.5 w-3.5 text-rose-600"/>
 Rejected
 </span>
 );
 case"superseded":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 ${className}`}
 >
 <RefreshCw className="h-3.5 w-3.5 text-slate-500"/>
 Superseded
 </span>
 );
 case"archived":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 ${className}`}
 >
 <Archive className="h-3.5 w-3.5 text-slate-500"/>
 Archived
 </span>
 );
 default:
 return (
 <span
 className={`inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 ${className}`}
 >
 {status}
 </span>
 );
 }
}
