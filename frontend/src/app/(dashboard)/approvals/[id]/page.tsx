"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import {
  fetchApprovalItem,
  approveApprovalItem,
  rejectApprovalItem,
  returnApprovalItemToDraft,
  type ApprovalItemDetail,
} from "@/lib/api/approvals";
import type { DraftStatus } from "@/lib/api/outreach";
import type { ResearchBrief } from "@/lib/api/research";
import { DraftStatusBadge } from "@/components/outreach/draft-status-badge";
import { DraftVersionHistory } from "@/components/outreach/draft-version-history";
import { ResearchContextCard } from "@/components/outreach/research-context-card";
import { ApprovalActionModal, type ApprovalActionType } from "@/components/approvals/approval-action-modal";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Sparkles,
  AlertCircle,
  ExternalLink,
  FileText,
  Clock,
  User,
  Building,
  Target,
  ShieldAlert,
} from "lucide-react";

interface ApprovalDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function ApprovalDetailPage({ params }: ApprovalDetailPageProps) {
  const { id: draftId } = use(params);
  const { activeWorkspace } = useWorkspace();
  const [detail, setDetail] = useState<ApprovalItemDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [modalAction, setModalAction] = useState<ApprovalActionType | null>(null);

  useEffect(() => {
    async function loadDetail() {
      if (!activeWorkspace || !draftId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await fetchApprovalItem(activeWorkspace.id, draftId);
        setDetail(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load approval item detail");
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [activeWorkspace, draftId]);

  async function handleConfirmAction(notes: string) {
    if (!activeWorkspace || !draftId || !modalAction) return;
    try {
      if (modalAction === "approve" || modalAction === "approve-and-send") {
        if (draft.status === "draft") {
          const { submitDraftForReview } = await import("@/lib/api/outreach");
          await submitDraftForReview(activeWorkspace.id, draftId);
        }
        await approveApprovalItem(activeWorkspace.id, draftId, notes);

        if (modalAction === "approve-and-send") {
          const { createDelivery } = await import("@/lib/api/deliveries");
          await createDelivery(activeWorkspace.id, draftId, undefined);
          setActionMessage("Draft approved and sent successfully");
        } else {
          setActionMessage("Draft approved successfully");
        }
      } else if (modalAction === "reject") {
        await rejectApprovalItem(activeWorkspace.id, draftId, notes);
        setActionMessage("Draft rejected");
      } else {
        await returnApprovalItemToDraft(activeWorkspace.id, draftId, notes);
        setActionMessage("Returned draft to editing state");
      }
      const updated = await fetchApprovalItem(activeWorkspace.id, draftId);
      setDetail(updated);
      setTimeout(() => setActionMessage(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        <div className="h-6 w-32 animate-pulse rounded bg-salesos-surface-muted"></div>
        <div className="h-24 animate-pulse rounded-lg bg-salesos-surface-muted border border-salesos-border"></div>
        <div className="h-64 animate-pulse rounded-lg bg-salesos-surface-muted border border-salesos-border"></div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <div className="rounded-lg border border-salesos-danger/20 bg-salesos-danger/10 p-6 text-center text-salesos-danger">
          <AlertCircle className="mx-auto h-8 w-8 text-salesos-danger mb-2" />
          <h3 className="text-base font-semibold">Error Loading Approval Item</h3>
          <p className="mt-1 text-xs">{error || "Item not found"}</p>
          <div className="mt-4">
            <Link href="/approvals" className="text-xs font-semibold text-salesos-brand underline">
              Return to Approval Queue
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const { draft, research_brief, evidence_sources, current_version } = detail;
  const review_history = detail.recent_history || detail.review_history || [];
  const isReadyForReview = draft.status === "ready_for_review" || (draft.status === "draft" && draft.current_body !== null);

  const contactName =
    detail.contact_name ||
    (detail.contact
      ? `${((detail.contact as Record<string, string>).first_name || "")} ${((detail.contact as Record<string, string>).last_name || "")}`.trim()
      : null) ||
    "Prospect";
  const contactTitle = ((detail.contact as Record<string, string>)?.title as string) || null;
  const accountName =
    detail.account_name ||
    ((detail.account as Record<string, string>)?.name as string) ||
    null;
  const accountDomain = ((detail.account as Record<string, string>)?.domain as string) || null;
  const campaignName =
    detail.campaign_name ||
    ((detail.campaign as Record<string, string>)?.name as string) ||
    draft.campaign_id;
  const targetSegment = ((detail.campaign as Record<string, string>)?.target_segment as string) || null;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      {/* Back Button */}
      <div>
        <Link
          href="/approvals"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-salesos-text-secondary hover:text-salesos-text transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Approval Queue</span>
        </Link>
      </div>

      {/* Zero Delivery & Safety Notice */}
      <div className="rounded-lg border border-blue-200 bg-blue-50/80 p-3.5 text-xs text-blue-900 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-blue-600 shrink-0" />
          <span>
            <strong>Send Safety:</strong> Safe to approve. No automatic emails will be sent.
          </span>
        </div>
      </div>

      {/* Feedback Banner */}
      {actionMessage && (
        <div className="flex items-center gap-2 rounded-lg border border-salesos-success/20 bg-salesos-success/10 p-3.5 text-xs font-semibold text-emerald-900">
          <CheckCircle2 className="h-4 w-4 text-salesos-success shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Main Header Banner */}
      <div className="rounded-lg border border-salesos-border bg-salesos-surface p-6 shadow-sm space-y-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0 space-y-1.5">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-bold tracking-tight text-salesos-text break-words">
                {draft.current_subject || "(Untitled Subject)"}
              </h1>
              <DraftStatusBadge status={draft.status as DraftStatus} />
              <span className="rounded bg-salesos-surface-muted px-2 py-0.5 text-xs font-mono text-salesos-text-secondary font-semibold">
                Version v{draft.current_version_number}
              </span>
            </div>
            <div className="flex items-center gap-x-4 gap-y-1 text-[13px] text-salesos-text-secondary flex-wrap">
              <span>Contact: <strong className="text-salesos-text">{contactName}</strong> ({contactTitle || "No Title"})</span>
              <span>Account: <strong className="text-salesos-text">{accountName || "N/A"}</strong></span>
              <span>Campaign: <strong className="text-salesos-text">{campaignName}</strong></span>
            </div>
          </div>

          {/* Decision Toolbar */}
          <div className="flex items-center gap-2 flex-wrap pt-1 lg:pt-0 shrink-0">
            {isReadyForReview && (
              <>
                <button
                  type="button"
                  onClick={() => setModalAction("approve-and-send")}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-salesos-brand px-3.5 py-2 text-xs font-semibold text-white hover:bg-salesos-brand-hover shadow-sm transition-colors cursor-pointer"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Approve & Send</span>
                </button>
                <button
                  type="button"
                  onClick={() => setModalAction("approve")}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-salesos-border bg-salesos-surface px-3 py-2 text-xs font-medium text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text shadow-2xs transition-colors cursor-pointer"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Approve Only</span>
                </button>
                <button
                  type="button"
                  onClick={() => setModalAction("reject")}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-salesos-danger/20 bg-salesos-danger/10 px-3 py-2 text-xs font-medium text-salesos-danger hover:bg-rose-100 transition-colors cursor-pointer"
                >
                  <XCircle className="h-3.5 w-3.5" />
                  <span>Reject</span>
                </button>
              </>
            )}

            {(isReadyForReview || draft.status === "rejected") && (
              <button
                type="button"
                onClick={() => setModalAction("return-to-draft")}
                className="inline-flex items-center gap-1.5 rounded-lg border border-amber-200 bg-salesos-warning/10 px-3 py-2 text-xs font-medium text-salesos-warning hover:bg-amber-100 transition-colors cursor-pointer"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Return to Draft</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: Email Content & Evidence */}
        <div className="space-y-6 lg:col-span-2">
          {/* Email Subject & Body Card */}
          <div className="rounded-lg border border-salesos-border bg-salesos-surface p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-salesos-border pb-3">
              <h2 className="text-sm font-semibold text-salesos-text flex items-center gap-2">
                <FileText className="h-4 w-4 text-salesos-text-secondary/60" />
                Outreach Message Preview
              </h2>
              <span className="text-xs font-mono text-salesos-text-secondary">v{draft.current_version_number}</span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wide text-salesos-text-secondary/60">Subject Line</label>
                <div className="mt-1 rounded-lg border border-salesos-border bg-salesos-surface-muted p-3 text-sm font-semibold text-salesos-text">
                  {draft.current_subject || "(No subject)"}
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wide text-salesos-text-secondary/60">Email Body</label>
                <div className="mt-1 whitespace-pre-wrap rounded-lg border border-salesos-border bg-salesos-surface-muted p-4 text-[13px] text-salesos-text leading-relaxed leading-relaxed min-h-[160px]">
                  {draft.current_body || "(No body content)"}
                </div>
              </div>
            </div>
          </div>

          {/* Research Brief Context */}
          {research_brief && Object.keys(research_brief).length > 0 && (
            <ResearchContextCard brief={research_brief as unknown as ResearchBrief} />
          )}

          {/* Evidence Sources */}
          {evidence_sources && evidence_sources.length > 0 && (
            <div className="rounded-lg border border-salesos-border bg-salesos-surface p-6 shadow-sm space-y-3">
              <h2 className="text-sm font-semibold text-salesos-text flex items-center gap-2">
                <FileText className="h-4 w-4 text-salesos-text-secondary/60" />
                Research Used ({evidence_sources.length})
              </h2>
              <div className="space-y-2.5">
                {evidence_sources.map((src, idx) => {
                  const title = (src.title as string) || "Evidence Source";
                  const url = (src.url as string) || null;
                  const snippet = (src.snippet as string) || null;
                  return (
                    <div key={idx} className="rounded-md border border-salesos-border bg-salesos-surface-muted p-3 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-salesos-text">{title}</span>
                        {url && (
                          <a
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-salesos-brand hover:underline"
                          >
                            <span>Visit Source</span>
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                      {snippet && <p className="text-salesos-text-secondary text-[13px] text-[11px] line-clamp-2">{snippet}</p>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Prospect/Account, AI Metadata & Audit */}
        <div className="space-y-6">
          {/* Prospect & Account Background */}
          <div className="rounded-lg border border-salesos-border bg-salesos-surface p-5 shadow-sm space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-salesos-text-secondary/60 flex items-center gap-1.5">
              <User className="h-3.5 w-3.5 text-salesos-text-secondary" />
              Prospect Context
            </h2>
            <div className="space-y-2 text-xs">
              <div>
                <span className="text-salesos-text-secondary">Name:</span>{" "}
                <strong className="text-salesos-text">{contactName}</strong>
              </div>
              {contactTitle && (
                <div>
                  <span className="text-salesos-text-secondary">Title:</span>{" "}
                  <span className="text-salesos-text">{contactTitle}</span>
                </div>
              )}
              {accountName && (
                <div className="pt-2 border-t border-salesos-border flex items-center gap-1.5">
                  <Building className="h-3.5 w-3.5 text-salesos-text-secondary/60 shrink-0" />
                  <span className="text-salesos-text-secondary">Account:</span>{" "}
                  <strong className="text-salesos-text">{accountName}</strong>
                  {accountDomain && (
                    <span className="text-[11px] font-mono text-salesos-text-secondary/60">({accountDomain})</span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Campaign Context */}
          {campaignName && (
            <div className="rounded-lg border border-salesos-border bg-salesos-surface p-5 shadow-sm space-y-2">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-salesos-text-secondary/60 flex items-center gap-1.5">
                <Target className="h-3.5 w-3.5 text-salesos-text-secondary" />
                Campaign Target
              </h2>
              <div className="text-xs space-y-1">
                <div className="font-semibold text-salesos-text">{campaignName}</div>
                {targetSegment && (
                  <div className="text-salesos-text-secondary text-[13px] text-[11px]">Segment: {targetSegment}</div>
                )}
              </div>
            </div>
          )}

          {/* AI Details */}
          {current_version?.provider && (
            <details className="rounded-lg border border-salesos-border bg-salesos-surface p-5 shadow-sm group">
              <summary className="text-xs font-semibold uppercase tracking-wider text-salesos-text-secondary flex items-center gap-1.5 cursor-pointer list-none">
                <Sparkles className="h-3.5 w-3.5 text-salesos-text-secondary" />
                AI Details
              </summary>
              <div className="mt-4 space-y-1 text-xs text-salesos-text-secondary">
                <div>Provider: <strong>{current_version.provider}</strong></div>
                <div>Model: <strong>{current_version.model || "llama-3.3-70b-versatile"}</strong></div>
                <div>Prompt Version: <strong>{current_version.prompt_version || "v1.0.0"}</strong></div>
                <div>Source: <strong>{current_version.generation_source}</strong></div>
              </div>
            </details>
          )}

          {/* Review Audit History Log */}
          <div className="rounded-lg border border-salesos-border bg-salesos-surface p-5 shadow-sm space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-salesos-text-secondary/60 flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-salesos-text-secondary" />
              Review History ({review_history.length})
            </h2>
            {review_history.length === 0 ? (
              <p className="text-xs text-salesos-text-secondary/60 italic">No review decisions logged yet.</p>
            ) : (
              <div className="space-y-2.5">
                {review_history.map((rev) => (
                  <div key={rev.id} className="rounded-md border border-salesos-border bg-salesos-surface-muted p-2.5 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span
                        className={`font-semibold capitalize text-[11px] ${
                          rev.decision === "approved"
                            ? "text-salesos-success"
                            : rev.decision === "rejected"
                            ? "text-salesos-danger"
                            : "text-salesos-warning"
                        }`}
                      >
                        {rev.decision.replace(/_/g, " ")} (v{rev.version_number})
                      </span>
                      <span className="text-[10px] text-salesos-text-secondary/60 font-mono">
                        {new Date(rev.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div className="text-[11px] text-salesos-text-secondary text-[13px]">Reviewer: {rev.reviewer_email || rev.reviewer_id}</div>
                    {rev.notes && <p className="text-[11px] text-salesos-text-secondary bg-salesos-surface p-1.5 rounded border border-salesos-border">{rev.notes}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Version Lineage Timeline */}
          {draft.versions && draft.versions.length > 0 && (
            <DraftVersionHistory versions={draft.versions} currentVersionNumber={draft.current_version_number} />
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      <ApprovalActionModal
        isOpen={modalAction !== null}
        actionType={modalAction}
        draftSubject={draft.current_subject || undefined}
        onClose={() => setModalAction(null)}
        onConfirm={handleConfirmAction}
      />
    </div>
  );
}
