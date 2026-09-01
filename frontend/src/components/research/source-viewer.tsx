import { ExternalLink, FileText, Globe, Hash } from"lucide-react";

import type { ResearchSource } from"@/lib/api/research";

interface SourceViewerProps {
 sources: ResearchSource[];
}

export function SourceViewer({ sources }: SourceViewerProps) {
 if (!sources || sources.length === 0) {
 return (
 <div className="rounded-xl border border-dashed border-salesos-border bg-salesos-surface p-6 text-center shadow-xs">
 <p className="text-xs font-medium text-salesos-text-secondary">No source provenance records attached yet.</p>
 </div>
 );
 }

 return (
 <div className="space-y-3">
 <div className="flex items-center justify-between">
 <h3 className="text-xs font-bold uppercase tracking-wider text-salesos-text-secondary">
 Source Provenance & Audit Citations ({sources.length})
 </h3>
 <span className="text-[10px] font-semibold text-salesos-success bg-salesos-success/10 px-2 py-0.5 rounded-full">
 Append-Only Immutable Log
 </span>
 </div>

 <div className="divide-y rounded-xl border border-salesos-border bg-salesos-surface shadow-xs">
 {sources.map((source) => (
 <div key={source.id} className="p-4 space-y-2 text-xs">
 <div className="flex items-start justify-between gap-2">
 <div className="flex items-center gap-2">
 <Globe className="h-4 w-4 text-salesos-text-secondary/60 shrink-0"/>
 <span className="font-bold text-salesos-text">
 {source.title ||"Untitled Source Provenance"}
 </span>
 <span className="rounded bg-salesos-surface-muted px-1.5 py-0.5 text-[10px] font-semibold text-salesos-text-secondary uppercase">
 {source.source_type}
 </span>
 </div>
 <span className="text-[10px] font-semibold text-salesos-text-secondary/60">
 Confidence: Math.round(source.confidence * 100)%
 </span>
 </div>

 {source.snippet && (
 <p className="text-salesos-text-secondary text-xs italic bg-salesos-surface-muted rounded p-2 border border-salesos-border">
 &quot;{source.snippet}&quot;
 </p>
 )}

 <div className="flex flex-wrap items-center justify-between gap-2 border-t border-salesos-border pt-2 text-[11px] text-salesos-text-secondary/60">
 <div className="flex items-center gap-3">
 {source.url && (
 <a
 href={source.url}
 target="_blank"
 rel="noreferrer"
 className="flex items-center gap-1 font-medium text-salesos-brand hover:underline"
 >
 <span>{source.url}</span>
 <ExternalLink className="h-3 w-3"/>
 </a>
 )}
 {source.raw_content_hash && (
 <span className="flex items-center gap-1 font-mono text-[10px] text-salesos-text-secondary/60">
 <Hash className="h-3 w-3"/>
 <span>{source.raw_content_hash}</span>
 </span>
 )}
 </div>

 {source.retrieved_at && (
 <div className="flex items-center gap-1">
 <FileText className="h-3 w-3 text-salesos-text-secondary/60"/>
 <span>
 Retrieved: {new Date(source.retrieved_at).toLocaleString()}
 </span>
 </div>
 )}
 </div>
 </div>
 ))}
 </div>
 </div>
 );
}
