"use client";

import { useState } from"react";
import { CheckCircle2, XCircle, RotateCcw, Loader2, X } from"lucide-react";
import { Button } from"@/components/ui/button";

export type ApprovalActionType ="approve"|"reject"|"return-to-draft"|"approve-and-send";

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
 title:"Approve Outreach Draft",
 description:"This will mark the draft as approved. No external delivery or email sending will occur.",
 badgeColor:"bg-emerald-100 text-emerald-800 border-emerald-200",
 btnVariant: "default",
 icon: CheckCircle2,
 btnLabel:"Confirm Approval",
 },
"approve-and-send": {
 title:"Approve & Send Outreach",
 description:"Approve this draft and immediately queue it for external email delivery.",
 badgeColor:"bg-indigo-100 text-indigo-800 border-indigo-200",
 btnVariant: "default",
 icon: CheckCircle2,
 btnLabel:"Approve & Send",
 },
 reject: {
 title:"Reject Outreach Draft",
 description:"Mark this draft as rejected. The draft will remain in audit history.",
 badgeColor:"bg-rose-100 text-rose-800 border-rose-200",
 btnVariant: "destructive",
 icon: XCircle,
 btnLabel:"Confirm Rejection",
 },
"return-to-draft": {
 title:"Return to Draft / Request Revision",
 description:"Return this item to draft state so sales reps or AI can generate further revisions.",
 badgeColor:"bg-amber-100 text-amber-800 border-amber-200",
 btnVariant: "secondary",
 icon: RotateCcw,
 btnLabel:"Return to Draft",
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
 setError(err instanceof Error ? err.message :"Action failed");
 } finally {
 setSubmitting(false);
 }
 }

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
 <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-xl space-y-5">
 <div className="flex items-start justify-between">
 <div className="flex items-center gap-2.5">
 <div className={`rounded-lg border p-2 ${config.badgeColor}`} aria-hidden="true">
 <IconComponent className="h-5 w-5"/>
 </div>
 <div>
 <h2 className="text-lg font-bold text-slate-900">{config.title}</h2>
 <p className="text-xs text-slate-500">{config.description}</p>
 </div>
 </div>
 <Button
 type="button"
 variant="ghost"
 size="icon"
 onClick={onClose}
 aria-label="Close modal"
 >
 <X className="h-5 w-5"aria-hidden="true"/>
 </Button>
 </div>

 {draftSubject && (
 <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
 <span className="text-[11px] font-medium uppercase tracking-wide text-slate-400 block mb-0.5">
 Target Draft
 </span>
 <p className="text-[13px] font-semibold text-slate-800 truncate">{draftSubject}</p>
 </div>
 )}

 <form onSubmit={handleSubmit} className="space-y-4">
 <div className="space-y-1.5">
 <label htmlFor="notes"className="text-xs font-semibold text-slate-700">
 Reviewer Notes / Feedback (Optional)
 </label>
 <textarea
 id="notes"
 rows={3}
 value={notes}
 onChange={(e) => setNotes(e.target.value)}
 placeholder="Add optional review feedback or rejection reason..."
 className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-slate-400 focus:outline-none"
 />
 </div>

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
 size="sm"
 disabled={submitting}
 variant={config.btnVariant as "default" | "destructive" | "secondary"}
 >
 {submitting ? (
 <>
 <Loader2 className="h-3.5 w-3.5 animate-spin"aria-hidden="true"/>
 <span>Processing...</span>
 </>
 ) : (
 <span>{config.btnLabel}</span>
 )}
 </Button>
 </div>
 </form>
 </div>
 </div>
 );
}
