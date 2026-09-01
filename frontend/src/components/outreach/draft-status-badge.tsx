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
 className={`inline-flex items-center gap-1.5 rounded-md bg-salesos-warning/10 px-2 py-0.5 text-[11px] font-medium text-salesos-warning ${className}`}
 >
 <FileEdit className="h-3.5 w-3.5 text-salesos-warning"/>
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
 className={`inline-flex items-center gap-1.5 rounded-md bg-salesos-success/10 px-2 py-0.5 text-[11px] font-medium text-salesos-success ${className}`}
 >
 <CheckCircle2 className="h-3.5 w-3.5 text-salesos-success"/>
 Approved
 </span>
 );
 case"rejected":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-salesos-danger/10 px-2 py-0.5 text-[11px] font-medium text-salesos-danger ${className}`}
 >
 <XCircle className="h-3.5 w-3.5 text-salesos-danger"/>
 Rejected
 </span>
 );
 case"superseded":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-salesos-surface-muted px-2 py-0.5 text-[11px] font-medium text-salesos-text-secondary ${className}`}
 >
 <RefreshCw className="h-3.5 w-3.5 text-salesos-text-secondary"/>
 Superseded
 </span>
 );
 case"archived":
 return (
 <span
 className={`inline-flex items-center gap-1.5 rounded-md bg-salesos-surface-muted px-2 py-0.5 text-[11px] font-medium text-salesos-text-secondary ${className}`}
 >
 <Archive className="h-3.5 w-3.5 text-salesos-text-secondary"/>
 Archived
 </span>
 );
 default:
 return (
 <span
 className={`inline-flex items-center rounded-md bg-salesos-surface-muted px-2 py-0.5 text-[11px] font-medium text-salesos-text-secondary ${className}`}
 >
 {status}
 </span>
 );
 }
}
