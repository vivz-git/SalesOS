"use client";

import { useState } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { generateOutreachDraft, type OutreachDraft } from "@/lib/api/outreach";
import { Sparkles, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

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
      <Button
        type="button"
        onClick={handleGenerate}
        disabled={disabled || generating || !activeWorkspace}
        className={className}
        size="sm"
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
      </Button>

      {error && (
        <span className="flex items-center gap-1 text-[11px] font-medium text-rose-600">
          <AlertCircle className="h-3 w-3 shrink-0" />
          {error}
        </span>
      )}
    </div>
  );
}
