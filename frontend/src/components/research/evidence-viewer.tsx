import { CheckCircle2, Cpu, HelpCircle, ShieldCheck } from"lucide-react";

import type { ResearchBrief } from"@/lib/api/research";

interface EvidenceViewerProps {
 brief: ResearchBrief;
}

export function EvidenceViewer({ brief }: EvidenceViewerProps) {
 const confidencePercent =
 brief.confidence_score !== null && brief.confidence_score !== undefined
 ? Math.round(brief.confidence_score * 100)
 : null;

 return (
 <div className="space-y-6">
 {/* Executive Summary */}
 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-5 shadow-xs space-y-2">
 <h3 className="text-xs font-bold uppercase tracking-wider text-salesos-text-secondary">
 Executive Summary
 </h3>
 <p className="text-sm text-salesos-text leading-relaxed">
 {brief.summary ||"No executive summary available for this research brief."}
 </p>
 </div>

 {/* Confidence Score & Explanation */}
 <div className="rounded-xl border border-salesos-border bg-salesos-surface-muted p-5 space-y-3">
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2">
 <ShieldCheck className="h-4 w-4 text-salesos-success"/>
 <h3 className="text-xs font-bold uppercase tracking-wider text-salesos-text-secondary">
 Confidence Evaluation
 </h3>
 </div>
 {confidencePercent !== null ? (
 <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-salesos-success">
 {confidencePercent}% Confidence Score
 </span>
 ) : (
 <span className="text-xs text-salesos-text-secondary/60 font-medium">Score Pending</span>
 )}
 </div>

 {brief.confidence_reason ? (
 <div className="rounded-lg border border-emerald-100 bg-salesos-surface p-3 text-xs text-salesos-text-secondary">
 <span className="font-semibold text-salesos-text block mb-0.5">Evaluation Reason:</span>
 {brief.confidence_reason}
 </div>
 ) : (
 <p className="text-xs text-salesos-text-secondary italic">
 Confidence explanation will be generated upon research pipeline execution.
 </p>
 )}
 </div>

 {/* Key Findings List */}
 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-5 shadow-xs space-y-3">
 <h3 className="text-xs font-bold uppercase tracking-wider text-salesos-text-secondary">
 Structured Key Findings
 </h3>

 {brief.key_findings && brief.key_findings.length > 0 ? (
 <ul className="space-y-2">
 {brief.key_findings.map((finding, idx) => (
 <li key={idx} className="flex items-start gap-2.5 text-xs text-salesos-text">
 <CheckCircle2 className="h-4 w-4 text-salesos-brand shrink-0 mt-0.5"/>
 <span>{finding}</span>
 </li>
 ))}
 </ul>
 ) : (
 <div className="flex items-center gap-2 text-xs text-salesos-text-secondary/60 italic">
 <HelpCircle className="h-4 w-4"/>
 <span>No key findings extracted yet.</span>
 </div>
 )}
 </div>

 {/* AI Provenance Metadata */}
 {(brief.provider || brief.model || brief.prompt_version || brief.generated_at) && (
 <div className="rounded-xl border border-salesos-border bg-salesos-surface-muted p-4 space-y-2">
 <div className="flex items-center gap-2 text-xs font-bold text-salesos-text-secondary">
 <Cpu className="h-4 w-4 text-salesos-text-secondary"/>
 <span>AI Audit Metadata</span>
 </div>
 <div className="grid grid-cols-2 gap-2 text-[11px] text-salesos-text-secondary sm:grid-cols-4">
 {brief.provider && (
 <div>
 <span className="font-medium text-salesos-text-secondary/60 block">Provider</span>
 <span className="font-semibold text-salesos-text">{brief.provider}</span>
 </div>
 )}
 {brief.model && (
 <div>
 <span className="font-medium text-salesos-text-secondary/60 block">Model</span>
 <span className="font-semibold text-salesos-text">{brief.model}</span>
 </div>
 )}
 {brief.prompt_version && (
 <div>
 <span className="font-medium text-salesos-text-secondary/60 block">Prompt Version</span>
 <span className="font-semibold text-salesos-text">{brief.prompt_version}</span>
 </div>
 )}
 {brief.token_usage !== null && (
 <div>
 <span className="font-medium text-salesos-text-secondary/60 block">Token Usage</span>
 <span className="font-semibold text-salesos-text">{brief.token_usage} tokens</span>
 </div>
 )}
 </div>
 </div>
 )}
 </div>
 );
}
