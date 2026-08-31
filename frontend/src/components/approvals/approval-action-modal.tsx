"use client";

import { useState } from "react";
import { CheckCircle2, XCircle, RotateCcw, Loader2, X } from "lucide-react";

export type ApprovalActionType = "approve" | "reject" | "return-to-draft" | "approve-and-send";

interface ApprovalActionModalProps {
  isOpen: boolean;
  actionType: ApprovalActionType | null;
  draftSubject?: string;
  onClose: () => void;
  onConfirm: (notes: string) => Promise<void>;
}

export function ApprovalActionModal({
  isOpen,
  actionType,
  draftSubject,
  onClose,
  onConfirm,
}: ApprovalActionModalProps) {
  const [notes, setNotes] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !actionType) return null;

  const config = {
    approve: {
      title: "Approve Outreach Draft",
      description: "This will mark the draft as approved. No external delivery or email sending will occur.",
      badgeColor: "bg-emerald-100 text-emerald-800 border-emerald-200",
      btnColor: "bg-emerald-600 hover:bg-emerald-700 text-white",
      icon: CheckCircle2,
      btnLabel: "Confirm Approval",
    },
    "approve-and-send": {
      title: "Approve & Send Outreach",
      description: "Approve this draft and immediately queue it for external email delivery.",
      badgeColor: "bg-purple-100 text-purple-800 border-purple-200",
      btnColor: "bg-purple-600 hover:bg-purple-700 text-white",
      icon: CheckCircle2,
      btnLabel: "Approve & Send",
    },
    reject: {
      title: "Reject Outreach Draft",
      description: "Mark this draft as rejected. The draft will remain in audit history.",
      badgeColor: "bg-rose-100 text-rose-800 border-rose-200",
      btnColor: "bg-rose-600 hover:bg-rose-700 text-white",
      icon: XCircle,
      btnLabel: "Confirm Rejection",
    },
    "return-to-draft": {
      title: "Return to Draft / Request Revision",
      description: "Return this item to draft state so sales reps or AI can generate further revisions.",
      badgeColor: "bg-amber-100 text-amber-800 border-amber-200",
      btnColor: "bg-amber-600 hover:bg-amber-700 text-white",
      icon: RotateCcw,
      btnLabel: "Return to Draft",
    },
  }[actionType];

  const IconComponent = config.icon;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onConfirm(notes);
      setNotes("");
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
      <div className="w-full max-w-lg rounded-xl border border-zinc-200 bg-white p-6 shadow-xl space-y-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <div className={`rounded-lg border p-2 ${config.badgeColor}`}>
              <IconComponent className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-zinc-900">{config.title}</h2>
              <p className="text-xs text-zinc-500">{config.description}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {draftSubject && (
          <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-3">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-zinc-400 block mb-0.5">
              Target Draft
            </span>
            <p className="text-xs font-semibold text-zinc-800 truncate">{draftSubject}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="notes" className="text-xs font-semibold text-zinc-700">
              Reviewer Notes / Feedback (Optional)
            </label>
            <textarea
              id="notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add optional review feedback or rejection reason..."
              className="w-full rounded-lg border border-zinc-300 p-2.5 text-xs text-zinc-900 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none"
            />
          </div>

          {error && (
            <div className="rounded-lg bg-rose-50 border border-rose-200 p-2.5 text-xs font-medium text-rose-700">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="rounded-lg border border-zinc-300 px-3.5 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold shadow-xs transition-colors ${config.btnColor} disabled:opacity-50`}
            >
              {submitting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <span>{config.btnLabel}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
