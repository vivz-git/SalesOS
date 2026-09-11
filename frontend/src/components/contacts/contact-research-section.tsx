"use client";

import { useEffect, useState, useCallback } from"react";
import {
 createResearchBrief,
 fetchResearchBriefs,
 triggerResearchJob,
 type ResearchBrief,
} from"@/lib/api/research";
import { useWorkspace } from"@/lib/workspace-context";
import { Button } from"@/components/ui/button";
import { AlertCircle, BrainCircuit, CheckCircle2, FileText, Loader2, Search, Sparkles, XCircle } from"lucide-react";

interface ContactResearchSectionProps {
 contactId: string;
 accountId?: string | null;
 onGenerate?: () => void;
 isGenerating?: boolean;
}

export function ContactResearchSection({
 contactId,
 accountId,
 onGenerate,
 isGenerating = false,
}: ContactResearchSectionProps) {
 const { activeWorkspace } = useWorkspace();
 const [briefs, setBriefs] = useState<ResearchBrief[]>([]);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);
 const [isTriggering, setIsTriggering] = useState(false);

 const loadResearch = useCallback(async (isInitial = false) => {
 if (!activeWorkspace) return;
 try {
 if (isInitial) setLoading(true);
 setError(null);
 const data = await fetchResearchBriefs(activeWorkspace.id, { contact_id: contactId, limit: 1 });
 setBriefs(data);
 } catch (err: unknown) {
 if (isInitial) {
 setError(err instanceof Error ? err.message :"Failed to load research.");
 }
 } finally {
 if (isInitial) setLoading(false);
 }
 }, [activeWorkspace, contactId]);

 useEffect(() => {
 loadResearch(true);
 }, [loadResearch]);

 const brief = briefs[0];
 const isResearching = brief?.status ==="pending"|| brief?.status ==="in_progress";
 const isCompleted = brief?.status ==="completed";
 const isFailed = brief?.status ==="failed";
 const hasResearch = !!brief;

 // Poll while research job is active
 useEffect(() => {
 if (!isResearching) return;
 const interval = setInterval(() => {
 loadResearch(false);
 }, 3000);
 return () => clearInterval(interval);
 }, [isResearching, loadResearch]);

 const canResearch = hasResearch || !!accountId;

 async function handleResearch() {
 if (!activeWorkspace || isTriggering || isResearching) return;
 try {
 setIsTriggering(true);
 setError(null);
 // Reuse the existing brief when there is one; the app supports re-running a
 // brief's pipeline, so never create a duplicate brief for this contact.
 let briefId = brief?.id;
 if (!briefId) {
 if (!accountId) {
 setError("Assign a target company account to this contact before running research.");
 return;
 }
 const created = await createResearchBrief(activeWorkspace.id, {
 account_id: accountId,
 contact_id: contactId,
 });
 briefId = created.id;
 }
 await triggerResearchJob(activeWorkspace.id, briefId);
 await loadResearch(false);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Job execution trigger failed.");
 } finally {
 setIsTriggering(false);
 }
 }

 if (loading) {
 return (
 <div className="flex h-32 w-full items-center justify-center rounded-xl border bg-salesos-surface p-6 shadow-sm">
 <div className="flex items-center gap-2 text-sm text-salesos-text-secondary">
 <Loader2 className="h-4 w-4 animate-spin"/>
 <span>Loading research...</span>
 </div>
 </div>
 );
 }

 if (error) {
 return (
 <div className="flex flex-col items-center justify-center rounded-xl border bg-salesos-surface p-6 shadow-sm text-center">
 <AlertCircle className="h-6 w-6 text-red-500 mb-2"/>
 <p className="text-sm font-medium text-salesos-danger">{error}</p>
 <Button variant="outline"size="sm"onClick={() => loadResearch(true)} className="mt-4">
 Try Again
 </Button>
 </div>
 );
 }

 return (
 <div className="rounded-xl border bg-salesos-surface p-6 shadow-sm space-y-4">
 <div className="flex items-center justify-between border-b pb-4">
 <div className="flex items-center gap-2">
 <BrainCircuit className="h-5 w-5 text-salesos-brand"/>
 <h2 className="text-lg font-semibold text-salesos-text">AI Research & Outreach</h2>
 </div>
 {hasResearch && (
 <div className="flex items-center gap-2">
 {isResearching && (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 ring-1 ring-blue-600/20 ring-inset">
 <Loader2 className="h-3 w-3 animate-spin"/>
 Researching...
 </span>
 )}
 {isCompleted && (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-success/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-success ring-1 ring-emerald-600/20 ring-inset">
 <CheckCircle2 className="h-3 w-3"/>
 Research Completed
 </span>
 )}
 {isFailed && (
 <span className="inline-flex items-center gap-1.5 rounded-full bg-salesos-warning/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-warning ring-1 ring-amber-600/20 ring-inset">
 <XCircle className="h-3 w-3"/>
 Research Incomplete
 </span>
 )}
 </div>
 )}
 </div>

 {!hasResearch && (
 <div className="flex flex-col items-center justify-center py-6 text-center">
 <FileText className="h-8 w-8 text-salesos-text-secondary/40 mb-3"/>
 <p className="text-sm font-medium text-salesos-text">No research available yet</p>
 <p className="text-xs text-salesos-text-secondary mt-1 mb-4 max-w-sm">
 Trigger a research job to gather intelligence on this contact to personalize your outreach.
 </p>
 </div>
 )}

 {hasResearch && (
 <div className="space-y-4">
 {brief.summary && (
 <div>
 <h3 className="text-xs font-semibold text-salesos-text-secondary uppercase tracking-wider mb-2">Executive Summary</h3>
 <p className="text-sm text-salesos-text-secondary leading-relaxed bg-salesos-surface-muted p-4 rounded-lg border">{brief.summary}</p>
 </div>
 )}

 {brief.key_findings && brief.key_findings.length > 0 && (
 <div>
 <h3 className="text-xs font-semibold text-salesos-text-secondary uppercase tracking-wider mb-2">Key Findings</h3>
 <ul className="space-y-2">
 {brief.key_findings.map((finding, idx) => (
 <li key={idx} className="flex gap-2 text-sm text-salesos-text-secondary">
 <span className="text-salesos-brand mt-0.5">•</span>
 <span>{finding}</span>
 </li>
 ))}
 </ul>
 </div>
 )}
 </div>
 )}

 <div className="pt-2 border-t mt-4 flex justify-end">
 <div className="flex w-full max-w-xl flex-col gap-3 sm:flex-row">
 <Button
 onClick={handleResearch}
 disabled={isResearching || isTriggering || isGenerating || !canResearch}
 title={
 canResearch
 ? undefined
 :"Assign a target company account to this contact before running research."
 }
 variant="outline"
 className="flex-1 flex items-center gap-2"
 >
 {isTriggering || isResearching ? (
 <>
 <Loader2 className="h-4 w-4 animate-spin"/>
 <span>Researching...</span>
 </>
 ) : (
 <>
 <Search className="h-4 w-4"/>
 <span>Research Prospect</span>
 </>
 )}
 </Button>

 <Button
 onClick={onGenerate}
 disabled={isResearching || isGenerating}
 className="flex-1 flex items-center gap-2 bg-salesos-brand hover:bg-salesos-brand-hover text-white"
 >
 {isGenerating ? (
 <>
 <Loader2 className="h-4 w-4 animate-spin"/>
 <span>Generating Email...</span>
 </>
 ) : (
 <>
 <Sparkles className="h-4 w-4"/>
 <span>Generate Personalized Email</span>
 </>
 )}
 </Button>
 </div>
 </div>
 </div>
 );
}