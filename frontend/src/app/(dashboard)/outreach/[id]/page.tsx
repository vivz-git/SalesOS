"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import {
  fetchOutreachDraft,
  reviseOutreachDraft,
  submitDraftForReview,
  approveDraft,
  rejectDraft,
  archiveDraft,
  type OutreachDraft,
  type DraftStatus,
} from "@/lib/api/outreach";
import { fetchResearchBrief, type ResearchBrief } from "@/lib/api/research";
import { fetchContact, type Contact } from "@/lib/api/contacts";
import { DraftStatusBadge } from "@/components/outreach/draft-status-badge";
import { DraftVersionHistory } from "@/components/outreach/draft-version-history";
import { ResearchContextCard } from "@/components/outreach/research-context-card";
import { GenerateDraftButton } from "@/components/outreach/generate-draft-button";
import { DeliveryActionModal } from "@/components/deliveries/delivery-action-modal";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  XCircle,
  Archive,
  Edit3,
  Save,
  X,
  AlertCircle,
  FileText,
  Send,
} from "lucide-react";

interface DraftDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function DraftDetailPage({ params }: DraftDetailPageProps) {
  const { id: draftId } = use(params);
  const { activeWorkspace } = useWorkspace();

  const [draft, setDraft] = useState<OutreachDraft | null>(null);
  const [researchBrief, setResearchBrief] = useState<ResearchBrief | null>(null);
  const [contact, setContact] = useState<Contact | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [deliveryModalOpen, setDeliveryModalOpen] = useState<boolean>(false);

  // Edit / Revise Mode State
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editSubject, setEditSubject] = useState<string>("");
  const [editBody, setEditBody] = useState<string>("");
  const [savingRevision, setSavingRevision] = useState<boolean>(false);

  async function loadDraftData() {
    if (!activeWorkspace || !draftId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOutreachDraft(activeWorkspace.id, draftId);
      setDraft(data);
      setEditSubject(data.current_subject || "");
      setEditBody(data.current_body || "");

      if (data.research_brief_id) {
        fetchResearchBrief(activeWorkspace.id, data.research_brief_id)
          .then(setResearchBrief)
          .catch(() => setResearchBrief(null));
      }

      if (data.contact_id) {
        fetchContact(activeWorkspace.id, data.contact_id)
          .then(setContact)
          .catch(() => setContact(null));
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load outreach draft");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDraftData();
  }, [activeWorkspace, draftId]);

  async function handleSaveRevision(e: React.FormEvent) {
    e.preventDefault();
    if (!activeWorkspace || !draft) return;
    if (!editBody.trim()) {
      setError("Message body cannot be empty.");
      return;
    }

    setSavingRevision(true);
    setError(null);
    try {
      const updated = await reviseOutreachDraft(activeWorkspace.id, draft.id, {
        subject: editSubject.trim() || undefined,
        body: editBody.trim(),
        generation_source: "human",
      });

      setDraft(updated);
      setIsEditing(false);
      setActionMessage(`Created revision version v${updated.current_version_number}`);
      setTimeout(() => setActionMessage(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save revision");
    } finally {
      setSavingRevision(false);
    }
  }

  async function handleStatusAction(action: "submit" | "approve" | "reject" | "archive") {
    if (!activeWorkspace || !draft) return;
    setError(null);
    try {
      let updated: OutreachDraft;
      if (action === "submit") {
        updated = await submitDraftForReview(activeWorkspace.id, draft.id);
        setActionMessage("Submitted draft for review");
      } else if (action === "approve") {
        updated = await approveDraft(activeWorkspace.id, draft.id);
        setActionMessage("Approved draft");
      } else if (action === "reject") {
        updated = await rejectDraft(activeWorkspace.id, draft.id);
        setActionMessage("Rejected draft");
      } else {
        updated = await archiveDraft(activeWorkspace.id, draft.id);
        setActionMessage("Archived draft");
      }

      setDraft(updated);
      setTimeout(() => setActionMessage(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : `Failed to ${action} draft`);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        <div className="h-6 w-32 animate-pulse rounded bg-salesos-surface-muted"></div>
        <div className="h-24 animate-pulse rounded-xl bg-salesos-surface-muted"></div>
        <div className="h-64 animate-pulse rounded-xl bg-salesos-surface-muted"></div>
      </div>
    );
  }

  if (error && !draft) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <div className="rounded-xl border border-salesos-danger/20 bg-salesos-danger/10 p-6 text-center text-salesos-danger">
          <AlertCircle className="mx-auto h-8 w-8 text-salesos-danger mb-2" />
          <h3 className="text-base font-semibold">Error Loading Draft</h3>
          <p className="mt-1 text-xs">{error}</p>
          <div className="mt-4">
            <Link href="/outreach" className="text-xs font-semibold underline">
              Return to Outreach Drafts
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!draft) return null;

  const isArchived = draft.status === "archived";
  const isApproved = draft.status === "approved";

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      {/* Back button */}
      <div>
        <Link
          href="/outreach"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-salesos-text-secondary hover:text-salesos-text transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Outreach Drafts
        </Link>
      </div>

      {/* Action Notification Message */}
      {actionMessage && (
        <div className="flex items-center justify-between rounded-xl border border-salesos-success/20 bg-salesos-success/10 p-3.5 text-xs font-semibold text-emerald-900">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-salesos-success shrink-0" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-salesos-success hover:text-emerald-950">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-salesos-danger/20 bg-salesos-danger/10 p-4 text-xs font-semibold text-salesos-danger">
          <AlertCircle className="h-4 w-4 text-salesos-danger shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="rounded-xl border border-salesos-border bg-salesos-surface p-6 shadow-2xs space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-bold tracking-tight text-salesos-text">
                {draft.current_subject || "(Untitled Subject)"}
              </h1>
              <DraftStatusBadge status={draft.status as DraftStatus} />
              <span className="rounded bg-salesos-surface-muted px-2 py-0.5 text-xs font-mono text-salesos-text-secondary">
                Current Version: v{draft.current_version_number}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-salesos-text-secondary flex-wrap">
              <span>Campaign: <span className="font-mono text-salesos-text-secondary">{draft.campaign_id}</span></span>
              <span>Contact: <span className="font-mono text-salesos-text-secondary">{draft.contact_id}</span></span>
            </div>
          </div>

          {/* Governed Action Buttons & AI Trigger */}
          <div className="flex items-center gap-2 flex-wrap shrink-0">
            {!isArchived && !isApproved && (
              <GenerateDraftButton
                draftId={draft.id}
                onSuccess={(updated) => {
                  setDraft(updated);
                  setActionMessage(`Generated AI Outreach Draft (v${updated.current_version_number})`);
                  setTimeout(() => setActionMessage(null), 4000);
                }}
              />
            )}

            {(draft.status === "draft" || draft.status === "rejected") && (
              <button
                type="button"
                onClick={() => handleStatusAction("submit")}
                className="inline-flex items-center gap-1.5 rounded-lg bg-salesos-brand px-3 py-1.5 text-xs font-semibold text-white hover:bg-salesos-brand-hover transition-colors"
              >
                <Clock className="h-3.5 w-3.5" />
                Submit for Review
              </button>
            )}

            {(draft.status === "ready_for_review" || draft.status === "draft") && (
              <>
                <button
                  type="button"
                  onClick={() => setDeliveryModalOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-salesos-brand px-3 py-1.5 text-xs font-semibold text-white hover:bg-salesos-brand-hover transition-colors"
                >
                  <Send className="h-3.5 w-3.5" />
                  Approve & Send
                </button>
                <button
                  type="button"
                  onClick={() => handleStatusAction("reject")}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-salesos-danger/20 bg-salesos-danger/10 px-3 py-1.5 text-xs font-semibold text-salesos-danger hover:bg-rose-100 transition-colors"
                >
                  <XCircle className="h-3.5 w-3.5" />
                  Reject
                </button>
              </>
            )}

            {isApproved && (
              <button
                type="button"
                onClick={() => setDeliveryModalOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-lg bg-salesos-brand px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-salesos-brand-hover shadow-sm transition-colors"
              >
                <Send className="h-3.5 w-3.5" />
                <span>Send Outbound Email</span>
              </button>
            )}

            {!isArchived && (
              <button
                type="button"
                onClick={() => handleStatusAction("archive")}
                className="inline-flex items-center gap-1.5 rounded-lg border border-salesos-border px-3 py-1.5 text-xs font-semibold text-salesos-text-secondary hover:bg-salesos-surface-muted transition-colors"
              >
                <Archive className="h-3.5 w-3.5" />
                Archive
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Grid: Content + Side Context */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Draft Content / Revision Editor */}
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-xl border border-salesos-border bg-salesos-surface p-6 shadow-2xs space-y-4">
            <div className="flex items-center justify-between border-b border-salesos-border pb-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-salesos-text-secondary" />
                <h2 className="text-sm font-semibold text-salesos-text">Message Content (v{draft.current_version_number})</h2>
              </div>

              {!isEditing && !isArchived && !isApproved && (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="inline-flex items-center gap-1 rounded-lg border border-salesos-border px-2.5 py-1 text-xs font-semibold text-salesos-text-secondary hover:bg-salesos-surface-muted"
                >
                  <Edit3 className="h-3.5 w-3.5 text-salesos-text-secondary" />
                  Revise Content
                </button>
              )}
            </div>

            {isEditing ? (
              <form onSubmit={handleSaveRevision} className="space-y-4">
                <div className="space-y-1">
                  <label htmlFor="edit_subject" className="text-xs font-semibold text-salesos-text-secondary">Subject</label>
                  <input
                    id="edit_subject"
                    type="text"
                    value={editSubject}
                    onChange={(e) => setEditSubject(e.target.value)}
                    className="w-full rounded-lg border border-salesos-border p-2 text-xs text-salesos-text focus:border-salesos-focus focus:outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label htmlFor="edit_body" className="text-xs font-semibold text-salesos-text-secondary">Message Body</label>
                  <textarea
                    id="edit_body"
                    rows={10}
                    value={editBody}
                    onChange={(e) => setEditBody(e.target.value)}
                    className="w-full rounded-lg border border-salesos-border p-3 text-xs font-mono text-salesos-text focus:border-salesos-focus focus:outline-none"
                    required
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="rounded-lg border border-salesos-border px-3 py-1.5 text-xs font-semibold text-salesos-text-secondary hover:bg-salesos-surface-muted"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingRevision}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                  >
                    <Save className="h-3.5 w-3.5" />
                    {savingRevision ? "Saving New Version..." : "Save Revision (Create v" + (draft.current_version_number + 1) + ")"}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3">
                {draft.current_subject && (
                  <div>
                    <span className="text-[11px] font-semibold tracking-wider text-salesos-text-secondary uppercase">Subject</span>
                    <p className="text-sm font-medium text-salesos-text mt-0.5">{draft.current_subject}</p>
                  </div>
                )}

                <div>
                  <span className="text-[11px] font-semibold tracking-wider text-salesos-text-secondary uppercase">Body</span>
                  <div className="mt-1 rounded-lg border border-salesos-border bg-salesos-surface-muted/70 p-4 text-xs font-mono text-salesos-text whitespace-pre-wrap leading-relaxed">
                    {draft.current_body || "(Empty message content)"}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Version Lineage */}
          <div className="rounded-xl border border-salesos-border bg-salesos-surface p-6 shadow-2xs">
            <DraftVersionHistory
              versions={draft.versions || []}
              currentVersionNumber={draft.current_version_number}
            />
          </div>
        </div>

        {/* Right Column: Research Context */}
        <div className="space-y-6">
          <ResearchContextCard brief={researchBrief} />
        </div>
      </div>

      {deliveryModalOpen && draft && (
        <DeliveryActionModal
          isOpen={deliveryModalOpen}
          draftSubject={draft.current_subject || "(Untitled Subject)"}
          realProspectEmail={contact?.email || undefined}
          isApproved={isApproved}
          onClose={() => setDeliveryModalOpen(false)}
          onConfirm={async (testRecipientEmail) => {
            if (!activeWorkspace) return;

            // Chain approve and send
            if (draft.status !== "approved") {
              await approveDraft(activeWorkspace.id, draft.id);
            }

            const { createDelivery } = await import("@/lib/api/deliveries");
            const delivery = await createDelivery(
              activeWorkspace.id,
              draft.id,
              testRecipientEmail || undefined
            );

            // Reload the draft data to reflect the new approved status
            loadDraftData();

            setActionMessage(`Draft approved & email delivery initiated (${delivery.status})!`);
            setTimeout(() => setActionMessage(null), 5000);
          }}
        />
      )}
    </div>
  );
}
