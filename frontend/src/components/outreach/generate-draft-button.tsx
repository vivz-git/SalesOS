"use client";

import { useState } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { generateOutreachDraft, type OutreachDraft } from "@/lib/api/outreach";
import { Sparkles, Loader2, AlertCircle } from "lucide-react";

interface GenerateDraftButtonProps {
  draftId: string;
  disabled?: boolean;
  onSuccess?: (updatedDraft: OutreachDraft) => void;
  className?: string;
}

export function GenerateDraftButton({
  draftId,
  disabled = false,
  onSuccess,
  className = "",
}: GenerateDraftButtonProps) {
  const { activeWorkspace } = useWorkspace();
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!activeWorkspace || !draftId) return;
    setGenerating(true);
    setError(null);

    try {
      const updated = await generateOutreachDraft(activeWorkspace.id, draftId);
      if (onSuccess) {
        onSuccess(updated);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "AI generation failed");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="inline-flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={handleGenerate}
        disabled={disabled || generating || !activeWorkspace}
        className={`inline-flex items-center gap-1.5 rounded-lg bg-purple-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-purple-700 transition-colors disabled:opacity-50 ${className}`}
      >
        {generating ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>Generating AI Draft...</span>
          </>
        ) : (
          <>
            <Sparkles className="h-3.5 w-3.5" />
            <span>Generate AI Draft</span>
          </>
        )}
      </button>

      {error && (
        <span className="flex items-center gap-1 text-[11px] font-medium text-rose-600">
          <AlertCircle className="h-3 w-3 shrink-0" />
          {error}
        </span>
      )}
    </div>
  );
}
