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
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-success/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-success border border-salesos-success/20 ${className}`}>
 <Play className="h-3 w-3 text-salesos-success"/>
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
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-warning/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-warning border border-amber-200 ${className}`}>
 <Pause className="h-3 w-3 text-salesos-warning"/>
 <span>Paused</span>
 </span>
 );
 case"stopped":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-danger/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-danger border border-salesos-danger/20 ${className}`}>
 <Square className="h-3 w-3 text-salesos-danger"/>
 <span>Stopped</span>
 </span>
 );
 case"completed":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-brand-subtle px-2.5 py-0.5 text-xs font-semibold text-salesos-brand border border-salesos-brand/20 ${className}`}>
 <CheckCircle2 className="h-3 w-3 text-salesos-brand"/>
 <span>Completed</span>
 </span>
 );
 case"failed":
 default:
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-surface-muted px-2.5 py-0.5 text-xs font-semibold text-salesos-text-secondary ${className}`}>
 <AlertTriangle className="h-3 w-3 text-salesos-text-secondary"/>
 <span className="capitalize">{status.replace(/_/g,"")}</span>
 </span>
 );
 }
}
