import type { EnrollmentStatus } from"@/lib/api/sequences";
import { Play, Pause, Square, CheckCircle2, Clock, AlertTriangle } from"lucide-react";

interface SequenceStatusBadgeProps {
 status: EnrollmentStatus;
 className?: string;
}

export function SequenceStatusBadge({ status, className =""}: SequenceStatusBadgeProps) {
 switch (status) {
 case"active":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200 ${className}`}>
 <Play className="h-3 w-3 text-emerald-600"/>
 <span>Active</span>
 </span>
 );
 case"pending_approval":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200 ${className}`}>
 <Clock className="h-3 w-3 text-blue-600"/>
 <span>Pending Approval</span>
 </span>
 );
 case"paused":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800 border border-amber-200 ${className}`}>
 <Pause className="h-3 w-3 text-amber-600"/>
 <span>Paused</span>
 </span>
 );
 case"stopped":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-semibold text-red-700 border border-red-200 ${className}`}>
 <Square className="h-3 w-3 text-red-600"/>
 <span>Stopped</span>
 </span>
 );
 case"completed":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 border border-indigo-200 ${className}`}>
 <CheckCircle2 className="h-3 w-3 text-indigo-600"/>
 <span>Completed</span>
 </span>
 );
 case"failed":
 default:
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700 ${className}`}>
 <AlertTriangle className="h-3 w-3 text-slate-500"/>
 <span className="capitalize">{status.replace(/_/g,"")}</span>
 </span>
 );
 }
}
