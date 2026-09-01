"use client";

import { useState } from "react";
import { Send, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DeliveryActionModalProps {
  isOpen: boolean;
  draftSubject?: string;
  realProspectEmail?: string;
  isApproved?: boolean;
  onClose: () => void;
  onConfirm: (testRecipientEmail: string | null) => Promise<void>;
}

export function DeliveryActionModal({
  isOpen,
  draftSubject,
  realProspectEmail,
  isApproved = true,
  onClose,
  onConfirm,
}: DeliveryActionModalProps) {
  const [testEmail, setTestEmail] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      // If no test email is provided, send null to use the real prospect email
      await onConfirm(testEmail.trim() || null);
      setTestEmail("");
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Delivery failed");
    } finally {
      setSubmitting(false);
    }
  }

  const isSendingToRealProspect = testEmail.trim() === "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-xl space-y-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg border p-2 bg-indigo-50 text-indigo-700 border-indigo-200">
              <Send className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {isApproved ? "Send Outbound Email" : "Approve & Send Outbound Email"}
              </h2>
              <p className="text-xs text-slate-500">
                {isApproved ? "Dispatch this approved draft via Resend." : "Approve this draft and dispatch it via Resend."}
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            disabled={submitting}
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {draftSubject && (
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 space-y-1">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 block mb-0.5">
              Draft & Recipient
            </span>
            <p className="text-xs font-semibold text-slate-800 truncate">{draftSubject}</p>
            {realProspectEmail && (
              <p className="text-xs text-slate-500">Target prospect: <span className="font-mono text-slate-700">{realProspectEmail}</span></p>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="testEmail" className="text-xs font-semibold text-slate-700">
              Test Recipient Email (Optional)
            </label>
            <p className="text-[11px] text-slate-500 pb-1">
              If provided, the email will be sent to this address instead of the real prospect. Useful for safe production testing.
            </p>
            <input
              id="testEmail"
              type="email"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              placeholder="e.g. you@yourdomain.com"
              className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>

          {isSendingToRealProspect && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800">
              <span className="font-semibold block mb-1">Attention: Live Dispatch</span>
              You have not entered a test email. Clicking confirm will dispatch this email to the real prospect immediately.
            </div>
          )}

          {error && (
            <div className="rounded-lg bg-rose-50 border border-rose-200 p-2.5 text-xs font-medium text-rose-700">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2.5 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="default"
              size="sm"
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Sending...</span>
                </>
              ) : (
                <span>Confirm {isSendingToRealProspect ? "Live Send" : "Test Send"}</span>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
