import type { ResearchBrief } from"@/lib/api/research";
import { Sparkles, FileText, CheckCircle } from"lucide-react";

interface ResearchContextCardProps {
 brief?: ResearchBrief | null;
 loading?: boolean;
}

export function ResearchContextCard({ brief, loading }: ResearchContextCardProps) {
 if (loading) {
 return (
 <div className="animate-pulse rounded-xl border border-slate-200 bg-white p-4">
 <div className="h-4 w-1/3 rounded bg-slate-200 mb-2"></div>
 <div className="h-3 w-full rounded bg-slate-100 mb-1"></div>
 <div className="h-3 w-2/3 rounded bg-slate-100"></div>
 </div>
 );
 }

 if (!brief) {
 return (
 <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-4 text-center text-xs text-slate-500">
 No research brief context linked to this draft.
 </div>
 );
 }

 const confidencePct = brief.confidence_score !== null ? Math.round(brief.confidence_score * 100) : null;

 return (
 <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
 <Sparkles className="h-4 w-4 text-slate-400"/>
 <span>Research Used</span>
 </div>

 {confidencePct !== null && (
 <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700">
 <CheckCircle className="h-3 w-3 text-slate-500"/>
 {confidencePct}% Confidence
 </span>
 )}
 </div>

 {brief.summary && (
 <p className="text-[13px] leading-relaxed text-slate-600">
 {brief.summary}
 </p>
 )}

 {brief.key_findings && brief.key_findings.length > 0 && (
 <div className="space-y-1">
 <span className="text-[11px] font-semibold tracking-wider text-slate-600 uppercase">
 Key Findings
 </span>
 <ul className="list-disc list-inside space-y-0.5 text-[13px] text-slate-600">
 {brief.key_findings.map((finding, idx) => (
 <li key={idx} className="truncate">
 {finding}
 </li>
 ))}
 </ul>
 </div>
 )}

 {brief.confidence_reason && (
 <div className="flex items-start gap-1.5 text-[11px] text-slate-600 bg-slate-100 p-2 rounded-md">
 <FileText className="h-3.5 w-3.5 shrink-0 mt-0.5 text-slate-400"/>
 <span>{brief.confidence_reason}</span>
 </div>
 )}
 </div>
 );
}
