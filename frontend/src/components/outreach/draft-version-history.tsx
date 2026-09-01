"use client";

import { useState } from"react";
import type { DraftVersion } from"@/lib/api/outreach";
import { History, User, Bot, ChevronDown, ChevronUp } from"lucide-react";

interface DraftVersionHistoryProps {
 versions: DraftVersion[];
 currentVersionNumber: number;
 onSelectVersion?: (version: DraftVersion) => void;
}

export function DraftVersionHistory({
 versions,
 currentVersionNumber,
 onSelectVersion,
}: DraftVersionHistoryProps) {
 const [expandedId, setExpandedId] = useState<string | null>(null);

 if (!versions || versions.length === 0) {
 return (
 <div className="rounded-lg border border-dashed border-salesos-border p-4 text-center text-sm text-salesos-text-secondary">
 No version history recorded.
 </div>
 );
 }

 const sorted = [...versions].sort((a, b) => b.version_number - a.version_number);

 return (
 <div className="space-y-3">
 <div className="flex items-center gap-2 text-sm font-semibold text-salesos-text">
 <History className="h-4 w-4 text-salesos-text-secondary"/>
 <span>Version Lineage ({versions.length})</span>
 </div>

 <div className="divide-y divide-slate-200 rounded-xl border border-salesos-border bg-salesos-surface">
 {sorted.map((ver) => {
 const isCurrent = ver.version_number === currentVersionNumber;
 const isExpanded = expandedId === ver.id;
 const isAi = ver.generation_source ==="ai_generated"|| ver.generation_source ==="ai_assisted";

 return (
 <div key={ver.id} className="p-3.5 transition-colors hover:bg-salesos-surface-muted/50">
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2.5">
 <span
 className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
 isCurrent ?"bg-slate-900 text-white":"bg-salesos-surface-muted text-salesos-text-secondary"
 }`}
 >
 v{ver.version_number}
 </span>

 <div>
 <div className="flex items-center gap-2">
 <span className="text-sm font-medium text-salesos-text">
 {ver.subject ||"(No subject)"}
 </span>
 {isCurrent && (
 <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-salesos-success uppercase">
 Active
 </span>
 )}
 </div>
 <div className="flex items-center gap-2 text-xs text-salesos-text-secondary">
 <span className="inline-flex items-center gap-1">
 {isAi ? <Bot className="h-3 w-3 text-salesos-text-secondary"/> : <User className="h-3 w-3 text-salesos-text-secondary/60"/>}
 {ver.generation_source}
 </span>
 {ver.provider && (
 <span>
 • {ver.provider} {ver.model ? `(${ver.model})` :""}
 </span>
 )}
 {ver.created_at && (
 <span>• {new Date(ver.created_at).toLocaleString()}</span>
 )}
 </div>
 </div>
 </div>

 <div className="flex items-center gap-2">
 {onSelectVersion && !isCurrent && (
 <button
 type="button"
 onClick={() => onSelectVersion(ver)}
 className="rounded px-2 py-1 text-xs font-medium text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text"
 >
 View
 </button>
 )}
 <button
 type="button"
 onClick={() => setExpandedId(isExpanded ? null : ver.id)}
 className="rounded p-1 text-salesos-text-secondary/60 hover:text-salesos-text-secondary"
 aria-label={isExpanded ?"Collapse version":"Expand version"}
 >
 {isExpanded ? <ChevronUp className="h-4 w-4"/> : <ChevronDown className="h-4 w-4"/>}
 </button>
 </div>
 </div>

 {isExpanded && (
 <div className="mt-3 rounded-lg border border-salesos-border bg-salesos-surface-muted p-3 text-xs text-salesos-text whitespace-pre-wrap font-mono">
 {ver.body}
 </div>
 )}
 </div>
 );
 })}
 </div>
 </div>
 );
}
