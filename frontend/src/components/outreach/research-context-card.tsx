import type { ResearchBrief } from"@/lib/api/research";
import { Sparkles, FileText, CheckCircle } from"lucide-react";

interface ResearchContextCardProps {
 brief?: ResearchBrief | null;
 loading?: boolean;
}

export function ResearchContextCard({ brief, loading }: ResearchContextCardProps) {
 if (loading) {
 return (
 <div className="animate-pulse rounded-xl border border-salesos-border bg-salesos-surface p-4">
 <div className="h-4 w-1/3 rounded bg-salesos-border mb-2"></div>
 <div className="h-3 w-full rounded bg-salesos-surface-muted mb-1"></div>
 <div className="h-3 w-2/3 rounded bg-salesos-surface-muted"></div>
 </div>
 );
 }

 if (!brief) {
 return (
 <div className="rounded-xl border border-dashed border-salesos-border bg-salesos-surface-muted/50 p-4 text-center text-xs text-salesos-text-secondary">
 No research brief context linked to this draft.
 </div>
 );
 }

 const confidencePct = brief.confidence_score !== null ? Math.round(brief.confidence_score * 100) : null;

 return (
 <div className="rounded-lg border border-salesos-border bg-salesos-surface-muted p-4 space-y-3">
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2 text-sm font-semibold text-salesos-text">
 <Sparkles className="h-4 w-4 text-salesos-info"/>
 <span>Research Used</span>
 </div>

 {confidencePct !== null && (
 <span className="inline-flex items-center gap-1 rounded-full bg-salesos-surface-muted px-2 py-0.5 text-[11px] font-medium text-salesos-text-secondary">
 <CheckCircle className="h-3 w-3 text-salesos-text-secondary"/>
 {confidencePct}% Confidence
 </span>
 )}
 </div>

 {brief.summary && (
 <p className="text-[13px] leading-relaxed text-salesos-text-secondary">
 {brief.summary}
 </p>
 )}

 {brief.key_findings && brief.key_findings.length > 0 && (
 <div className="space-y-1">
 <span className="text-[11px] font-semibold tracking-wider text-salesos-text-secondary uppercase">
 Key Findings
 </span>
 <ul className="list-disc list-inside space-y-0.5 text-[13px] text-salesos-text-secondary">
 {brief.key_findings.map((finding, idx) => (
 <li key={idx} className="truncate">
 {finding}
 </li>
 ))}
 </ul>
 </div>
 )}

 {brief.confidence_reason && (
 <div className="flex items-start gap-1.5 text-[11px] text-salesos-text-secondary bg-salesos-surface-muted p-2 rounded-md">
 <FileText className="h-3.5 w-3.5 shrink-0 mt-0.5 text-salesos-info"/>
 <span>{brief.confidence_reason}</span>
 </div>
 )}
 </div>
 );
}
