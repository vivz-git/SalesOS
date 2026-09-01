import type { DeliveryStatus } from"@/lib/api/deliveries";
import { CheckCircle2, Clock, Send, AlertTriangle, XCircle, ShieldAlert } from"lucide-react";

interface DeliveryStatusBadgeProps {
 status: DeliveryStatus;
 className?: string;
}

export function DeliveryStatusBadge({ status, className =""}: DeliveryStatusBadgeProps) {
 switch (status) {
 case"sent":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200 ${className}`}>
 <Send className="h-3 w-3 text-blue-600"/>
 <span>Sent (Submitted)</span>
 </span>
 );
 case"delivered":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-success/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-success border border-salesos-success/20 ${className}`}>
 <CheckCircle2 className="h-3 w-3 text-salesos-success"/>
 <span>Delivered</span>
 </span>
 );
 case"running":
 case"queued":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-warning/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-warning border border-amber-200 ${className}`}>
 <Clock className="h-3 w-3 text-salesos-warning"/>
 <span className="capitalize">{status}</span>
 </span>
 );
 case"bounced":
 case"complained":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-orange-50 px-2.5 py-0.5 text-xs font-semibold text-orange-800 border border-orange-200 ${className}`}>
 <AlertTriangle className="h-3 w-3 text-orange-600"/>
 <span className="capitalize">{status}</span>
 </span>
 );
 case"failed":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-danger/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-danger border border-salesos-danger/20 ${className}`}>
 <XCircle className="h-3 w-3 text-salesos-danger"/>
 <span>Failed</span>
 </span>
 );
 case"cancelled":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-surface-muted px-2.5 py-0.5 text-xs font-semibold text-salesos-text-secondary border border-salesos-border ${className}`}>
 <ShieldAlert className="h-3 w-3 text-salesos-text-secondary"/>
 <span>Cancelled</span>
 </span>
 );
 default:
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-surface-muted px-2.5 py-0.5 text-xs font-semibold text-salesos-text-secondary ${className}`}>
 <span className="capitalize">{status}</span>
 </span>
 );
 }
}
