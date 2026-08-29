"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import {
  fetchConversationDetail,
  reclassifyConversation,
  updateConversationStatus,
  type Conversation,
  type ReplyState,
  type ConversationStatus,
} from "@/lib/api/conversations";
import { ReplyClassificationBadge } from "@/components/conversations/reply-classification-badge";
import {
  ArrowLeft,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  Edit3,
  Sparkles,
  } from "lucide-react";

interface ConversationDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function ConversationDetailPage({ params }: ConversationDetailPageProps) {
  const { id: conversationId } = use(params);
  const { activeWorkspace } = useWorkspace();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [overrideState, setOverrideState] = useState<ReplyState>("interested");

  useEffect(() => {
    async function loadData() {
      if (!activeWorkspace || !conversationId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await fetchConversationDetail(activeWorkspace.id, conversationId);
        setConversation(res);
        if (res.current_reply_state) {
          setOverrideState(res.current_reply_state);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load conversation thread");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [activeWorkspace, conversationId]);

  async function handleReclassify() {
    if (!activeWorkspace || !conversationId) return;
    try {
      const updated = await reclassifyConversation(
        activeWorkspace.id,
        conversationId,
        overrideState,
        "Manually reclassified by user"
      );
      setConversation(updated);
      setActionMsg(`Reclassified thread as ${overrideState}`);
      setTimeout(() => setActionMsg(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reclassify");
    }
  }

  async function handleStatusChange(newStatus: ConversationStatus) {
    if (!activeWorkspace || !conversationId) return;
    try {
      const updated = await updateConversationStatus(activeWorkspace.id, conversationId, newStatus);
      setConversation(updated);
      setActionMsg(`Thread status updated to ${newStatus}`);
      setTimeout(() => setActionMsg(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div className="h-6 w-32 animate-pulse rounded bg-zinc-200"></div>
        <div className="h-48 animate-pulse rounded-xl bg-zinc-100 border border-zinc-200"></div>
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800">
          <AlertCircle className="mx-auto h-8 w-8 text-rose-600 mb-2" />
          <h3 className="text-base font-semibold">Conversation Thread Not Found</h3>
          <p className="mt-1 text-xs">{error || "Unable to locate conversation record"}</p>
          <div className="mt-4">
            <Link href="/conversations" className="text-xs font-semibold text-purple-700 underline">
              Return to Conversations Inbox
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Back Button */}
      <div>
        <Link
          href="/conversations"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500 hover:text-zinc-900 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Inbox</span>
        </Link>
      </div>

      {actionMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 text-xs font-semibold text-emerald-900">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Main Header Banner */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-2xs space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-bold tracking-tight text-zinc-900">
                {conversation.contact_name || "Prospect Thread"}
              </h1>
              <ReplyClassificationBadge state={conversation.current_reply_state} />
              <span className="rounded bg-zinc-100 px-2 py-0.5 text-xs font-mono text-zinc-700 font-semibold capitalize">
                Status: {conversation.status.replace(/_/g, " ")}
              </span>
            </div>
            <p className="text-xs text-zinc-500">
              Contact Email: <strong className="text-zinc-900">{conversation.contact_email}</strong> • Account: <strong className="text-zinc-900">{conversation.account_name || "N/A"}</strong>
            </p>
          </div>

          {/* Status Actions */}
          <div className="flex items-center gap-2 flex-wrap shrink-0">
            {conversation.status === "needs_human_action" && (
              <button
                onClick={() => handleStatusChange("active")}
                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 transition-colors"
              >
                Mark Resolved / Active
              </button>
            )}
            {conversation.status !== "closed" && (
              <button
                onClick={() => handleStatusChange("closed")}
                className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-100 transition-colors"
              >
                Close Thread
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: Message History Timeline */}
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-2xs space-y-4">
            <h2 className="text-sm font-semibold text-zinc-900 flex items-center gap-2 border-b border-zinc-100 pb-3">
              <MessageSquare className="h-4 w-4 text-purple-600" />
              <span>Conversation History ({conversation.messages.length})</span>
            </h2>

            <div className="space-y-4">
              {conversation.messages.map((msg) => {
                const isInbound = msg.direction === "inbound";
                return (
                  <div
                    key={msg.id}
                    className={`rounded-xl border p-4 text-xs space-y-2 ${
                      isInbound
                        ? "border-purple-200 bg-purple-50/40"
                        : "border-zinc-200 bg-zinc-50/60"
                    }`}
                  >
                    <div className="flex items-center justify-between border-b border-zinc-100 pb-2">
                      <span className="font-semibold text-zinc-900">
                        {isInbound ? `Inbound Reply from ${msg.sender_email}` : `Outbound Sent to ${msg.recipient_email}`}
                      </span>
                      <span className="font-mono text-[10px] text-zinc-400">
                        {new Date(msg.created_at).toLocaleString()}
                      </span>
                    </div>

                    <div>
                      <span className="font-semibold text-zinc-700">Subject: </span>
                      <span className="text-zinc-900">{msg.subject}</span>
                    </div>

                    <div className="whitespace-pre-wrap text-zinc-800 leading-relaxed bg-white p-3 rounded-lg border border-zinc-100">
                      {msg.body}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Intent Classification & Override */}
        <div className="space-y-6">
          {/* Classification Provenance Card */}
          {conversation.last_classification && (
            <div className="rounded-xl border border-purple-200 bg-purple-50/70 p-5 shadow-2xs space-y-3 text-xs">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-purple-900 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-purple-600" />
                <span>Intent Classification Context</span>
              </h2>

              <div className="space-y-1.5 text-purple-950 font-mono text-[11px]">
                <div>
                  State: <strong className="capitalize">{conversation.last_classification.reply_state}</strong>
                </div>
                <div>
                  Confidence: <strong>{Math.round(conversation.last_classification.confidence_score * 100)}%</strong>
                </div>
                <div className="pt-1 text-[11px] text-purple-900 font-sans italic bg-purple-100/60 p-2 rounded">
                  &quot;{conversation.last_classification.explanation}&quot;
                </div>
              </div>
            </div>
          )}

          {/* Reclassify Intent Dropdown */}
          <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs space-y-3 text-xs">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <Edit3 className="h-3.5 w-3.5 text-zinc-500" />
              <span>Manual Reclassification</span>
            </h2>

            <div className="space-y-2">
              <select
                value={overrideState}
                onChange={(e) => setOverrideState(e.target.value as ReplyState)}
                className="w-full rounded-lg border border-zinc-200 bg-zinc-50 p-2 text-xs text-zinc-900 focus:border-purple-500 focus:bg-white focus:outline-hidden"
              >
                <option value="interested">Interested</option>
                <option value="not_now">Not Now</option>
                <option value="referral">Referral</option>
                <option value="unsubscribe">Opt-Out / Unsubscribe</option>
                <option value="out_of_office">Out of Office</option>
                <option value="ambiguous">Needs Review (Ambiguous)</option>
              </select>

              <button
                type="button"
                onClick={handleReclassify}
                className="w-full rounded-lg bg-zinc-900 py-1.5 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors"
              >
                Update Classification
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-2">
            <ShieldAlert className="h-4 w-4 text-blue-600 shrink-0 mt-0.5" />
            <span>
              Human escalation boundary: Inbound replies do not trigger automatic email sends.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
