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
 <span className={`inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200 ${className}`}>
 <CheckCircle2 className="h-3 w-3 text-emerald-600"/>
 <span>Connected</span>
 </span>
 );
 case"disconnected":
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 ${className}`}>
 <XCircle className="h-3 w-3 text-slate-400"/>
 <span>Disconnected</span>
 </span>
 );
 case"error":
 default:
 return (
 <span className={`inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 border border-rose-200 ${className}`}>
 <AlertCircle className="h-3 w-3 text-rose-600"/>
 <span>Connection Error</span>
 </span>
 );
 }
}
