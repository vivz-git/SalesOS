"use client";

import { useState } from "react";
import type { DraftVersion } from "@/lib/api/outreach";
import { History, User, Bot, ChevronDown, ChevronUp } from "lucide-react";

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
      <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-center text-sm text-zinc-500">
        No version history recorded.
      </div>
    );
  }

  const sorted = [...versions].sort((a, b) => b.version_number - a.version_number);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900">
        <History className="h-4 w-4 text-zinc-500" />
        <span>Version Lineage ({versions.length})</span>
      </div>

      <div className="divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white">
        {sorted.map((ver) => {
          const isCurrent = ver.version_number === currentVersionNumber;
          const isExpanded = expandedId === ver.id;
          const isAi = ver.generation_source === "ai_generated" || ver.generation_source === "ai_assisted";

          return (
            <div key={ver.id} className="p-3.5 transition-colors hover:bg-zinc-50/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                      isCurrent ? "bg-zinc-900 text-white" : "bg-zinc-100 text-zinc-700"
                    }`}
                  >
                    v{ver.version_number}
                  </span>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-zinc-900">
                        {ver.subject || "(No subject)"}
                      </span>
                      {isCurrent && (
                        <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-emerald-800 uppercase">
                          Active
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                      <span className="inline-flex items-center gap-1">
                        {isAi ? <Bot className="h-3 w-3 text-purple-600" /> : <User className="h-3 w-3 text-zinc-400" />}
                        {ver.generation_source}
                      </span>
                      {ver.provider && (
                        <span>
                          • {ver.provider} {ver.model ? `(${ver.model})` : ""}
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
                      className="rounded px-2 py-1 text-xs font-medium text-zinc-600 hover:bg-zinc-200 hover:text-zinc-900"
                    >
                      View
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setExpandedId(isExpanded ? null : ver.id)}
                    className="rounded p-1 text-zinc-400 hover:text-zinc-600"
                    aria-label={isExpanded ? "Collapse version" : "Expand version"}
                  >
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="mt-3 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-800 whitespace-pre-wrap font-mono">
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
