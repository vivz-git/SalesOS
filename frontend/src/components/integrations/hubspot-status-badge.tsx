import type { ConnectionStatus } from"@/lib/api/hubspot";
import { CheckCircle2, XCircle, AlertCircle } from"lucide-react";

interface HubspotStatusBadgeProps {
 status: ConnectionStatus;
 className?: string;
}

export function HubspotStatusBadge({ status, className =""}: HubspotStatusBadgeProps) {
 switch (status) {
 case"connected":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-success/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-success border border-salesos-success/20 ${className}`}>
 <CheckCircle2 className="h-3 w-3 text-salesos-success"/>
 <span>Connected</span>
 </span>
 );
 case"disconnected":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-surface-muted px-2.5 py-0.5 text-xs font-semibold text-salesos-text-secondary ${className}`}>
 <XCircle className="h-3 w-3 text-salesos-text-secondary/60"/>
 <span>Disconnected</span>
 </span>
 );
 case"error":
 default:
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-salesos-danger/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-danger border border-salesos-danger/20 ${className}`}>
 <AlertCircle className="h-3 w-3 text-salesos-danger"/>
 <span>Connection Error</span>
 </span>
 );
 }
}
