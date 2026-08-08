import type { ResearchBrief } from "@/lib/api/research";
import { Sparkles, FileText, CheckCircle } from "lucide-react";

interface ResearchContextCardProps {
  brief?: ResearchBrief | null;
  loading?: boolean;
}

export function ResearchContextCard({ brief, loading }: ResearchContextCardProps) {
  if (loading) {
    return (
      <div className="animate-pulse rounded-xl border border-zinc-200 bg-white p-4">
        <div className="h-4 w-1/3 rounded bg-zinc-200 mb-2"></div>
        <div className="h-3 w-full rounded bg-zinc-100 mb-1"></div>
        <div className="h-3 w-2/3 rounded bg-zinc-100"></div>
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-300 bg-zinc-50/50 p-4 text-center text-xs text-zinc-500">
        No research brief context linked to this draft.
      </div>
    );
  }

  const confidencePct = brief.confidence_score !== null ? Math.round(brief.confidence_score * 100) : null;

  return (
    <div className="rounded-xl border border-purple-200 bg-purple-50/40 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-purple-950">
          <Sparkles className="h-4 w-4 text-purple-600" />
          <span>Research Context</span>
        </div>

        {confidencePct !== null && (
          <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-semibold text-purple-800">
            <CheckCircle className="h-3 w-3 text-purple-600" />
            {confidencePct}% Confidence
          </span>
        )}
      </div>

      {brief.summary && (
        <p className="text-xs leading-relaxed text-zinc-700">
          {brief.summary}
        </p>
      )}

      {brief.key_findings && brief.key_findings.length > 0 && (
        <div className="space-y-1">
          <span className="text-[11px] font-semibold tracking-wider text-purple-900 uppercase">
            Key Intelligence Findings
          </span>
          <ul className="list-disc list-inside space-y-0.5 text-xs text-zinc-700">
            {brief.key_findings.map((finding, idx) => (
              <li key={idx} className="truncate">
                {finding}
              </li>
            ))}
          </ul>
        </div>
      )}

      {brief.confidence_reason && (
        <div className="flex items-start gap-1.5 text-[11px] text-purple-800/80 bg-purple-100/50 p-2 rounded-lg">
          <FileText className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <span>{brief.confidence_reason}</span>
        </div>
      )}
    </div>
  );
}
