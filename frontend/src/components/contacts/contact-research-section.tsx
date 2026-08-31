"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchResearchBriefs, type ResearchBrief } from "@/lib/api/research";
import { useWorkspace } from "@/lib/workspace-context";
import { Button } from "@/components/ui/button";
import { AlertCircle, BrainCircuit, CheckCircle2, FileText, Loader2, Sparkles, XCircle } from "lucide-react";

interface ContactResearchSectionProps {
  contactId: string;
  onGenerate?: () => void;
  isGenerating?: boolean;
}

export function ContactResearchSection({
  contactId,
  onGenerate,
  isGenerating = false,
}: ContactResearchSectionProps) {
  const { activeWorkspace } = useWorkspace();
  const [briefs, setBriefs] = useState<ResearchBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadResearch = useCallback(async (isInitial = false) => {
    if (!activeWorkspace) return;
    try {
      if (isInitial) setLoading(true);
      setError(null);
      const data = await fetchResearchBriefs(activeWorkspace.id, { contact_id: contactId, limit: 1 });
      setBriefs(data);
    } catch (err: unknown) {
      if (isInitial) {
        setError(err instanceof Error ? err.message : "Failed to load research.");
      }
    } finally {
      if (isInitial) setLoading(false);
    }
  }, [activeWorkspace, contactId]);

  useEffect(() => {
    loadResearch(true);
  }, [loadResearch]);

  const brief = briefs[0];
  const isResearching = brief?.status === "pending" || brief?.status === "in_progress";
  const isCompleted = brief?.status === "completed";
  const isFailed = brief?.status === "failed";
  const hasResearch = !!brief;

  // Poll while research job is active
  useEffect(() => {
    if (!isResearching) return;
    const interval = setInterval(() => {
      loadResearch(false);
    }, 3000);
    return () => clearInterval(interval);
  }, [isResearching, loadResearch]);

  if (loading) {
    return (
      <div className="flex h-32 w-full items-center justify-center rounded-xl border bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Loading research...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border bg-white p-6 shadow-sm text-center">
        <AlertCircle className="h-6 w-6 text-red-500 mb-2" />
        <p className="text-sm font-medium text-red-600">{error}</p>
        <Button variant="outline" size="sm" onClick={() => loadResearch(true)} className="mt-4">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-indigo-500" />
          <h2 className="text-lg font-semibold text-zinc-900">AI Research & Outreach</h2>
        </div>
        {hasResearch && (
          <div className="flex items-center gap-2">
            {isResearching && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 ring-1 ring-blue-600/20 ring-inset">
                <Loader2 className="h-3 w-3 animate-spin" />
                Researching...
              </span>
            )}
            {isCompleted && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-600/20 ring-inset">
                <CheckCircle2 className="h-3 w-3" />
                Research Completed
              </span>
            )}
            {isFailed && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 ring-1 ring-amber-600/20 ring-inset">
                <XCircle className="h-3 w-3" />
                Research Incomplete
              </span>
            )}
          </div>
        )}
      </div>

      {!hasResearch && (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <FileText className="h-8 w-8 text-zinc-300 mb-3" />
          <p className="text-sm font-medium text-zinc-900">No research available yet</p>
          <p className="text-xs text-zinc-500 mt-1 mb-4 max-w-sm">
            Trigger a research job to gather intelligence on this contact to personalize your outreach.
          </p>
        </div>
      )}

      {hasResearch && (
        <div className="space-y-4">
          {brief.summary && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Executive Summary</h3>
              <p className="text-sm text-zinc-700 leading-relaxed bg-zinc-50 p-4 rounded-lg border">{brief.summary}</p>
            </div>
          )}

          {brief.key_findings && brief.key_findings.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Key Findings</h3>
              <ul className="space-y-2">
                {brief.key_findings.map((finding, idx) => (
                  <li key={idx} className="flex gap-2 text-sm text-zinc-700">
                    <span className="text-indigo-500 mt-0.5">•</span>
                    <span>{finding}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="pt-2 border-t mt-4 flex justify-end">
        <Button
          onClick={onGenerate}
          disabled={isResearching || isGenerating}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Generating Email...</span>
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              <span>Generate Personalized Email</span>
            </>
          )}
        </Button>
      </div>
    </div>
  );
}