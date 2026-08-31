"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import {
  fetchConversations,
  ingestInboundReply,
  type Conversation,
  type ReplyState,
} from "@/lib/api/conversations";
import { ReplyClassificationBadge } from "@/components/conversations/reply-classification-badge";
import {
  MessageSquare,
  Search,
  RefreshCw,
  Eye,
  AlertCircle,
  ShieldAlert,
  Inbox,
  Send,
  Plus,
  CheckCircle2,
  Loader2,
  X,
} from "lucide-react";

export function RepliesTab() {
  const { activeWorkspace } = useWorkspace();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [replyStateFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Simulated Inbound Test Drawer state
  const [showSimulateModal, setShowSimulateModal] = useState<boolean>(false);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [simSender, setSimSender] = useState<string>("alex.buyer@targetcompany.com");
  const [simSubject, setSimSubject] = useState<string>("Re: SalesOS Demo Inquiry");
  const [simBody, setSimBody] = useState<string>("Sounds great! Are you free for a call on Thursday at 2pm?");

  const loadData = useCallback(async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchConversations(activeWorkspace.id, {
        status: statusFilter,
        reply_state: replyStateFilter,
        search: searchQuery,
      });
      setConversations(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load conversations");
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, statusFilter, replyStateFilter, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleSimulateInbound(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!activeWorkspace || simulating) return;
    setSimulating(true);
    setModalError(null);
    try {
      const conv = await ingestInboundReply(activeWorkspace.id, {
        sender_email: simSender,
        recipient_email: "sales@mycompany.com",
        subject: simSubject,
        body: simBody,
      });
      setShowSimulateModal(false);
      const stateLabel = conv?.current_reply_state
        ? ` as "${conv.current_reply_state.replace(/_/g, " ")}"`
        : "";
      setSuccessMsg(`Inbound prospect reply was successfully ingested and classified${stateLabel}.`);
      await loadData();
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err.message : "Failed to ingest inbound test reply");
    } finally {
      setSimulating(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 flex items-center gap-2">
            <MessageSquare className="h-6 w-6 text-purple-600" />
            <span>Conversations Inbox</span>
          </h1>
          <p className="mt-1 text-xs text-zinc-500">
            Prospect reply tracking, automated intent classification, opt-outs, and human escalation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setModalError(null);
              setShowSimulateModal(true);
            }}
            className="inline-flex items-center gap-1.5 rounded-lg bg-purple-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-purple-700 transition-colors shadow-2xs"
          >
            <Plus className="h-4 w-4" />
            <span>Simulate Inbound Reply</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4 shadow-2xs md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {[
            { id: "all", label: "All Threads" },
            { id: "needs_human_action", label: "Needs Review" },
            { id: "active", label: "Active" },
            { id: "opt_out", label: "Opt-Outs" },
            { id: "closed", label: "Closed" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors whitespace-nowrap ${
                statusFilter === tab.id
                  ? "bg-purple-100 text-purple-900"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1 md:w-56">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-zinc-400" />
            <input
              type="text"
              placeholder="Search prospects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadData()}
              className="w-full rounded-lg border border-zinc-200 bg-zinc-50 pl-8 pr-3 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:bg-white focus:outline-hidden"
            />
          </div>

          <button
            onClick={loadData}
            className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-900"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800">
          <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-900 font-semibold shadow-2xs">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Conversation Thread Table */}
      <div className="rounded-xl border border-zinc-200 bg-white shadow-2xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-zinc-400">Loading conversation threads...</div>
        ) : conversations.length === 0 ? (
          <div className="p-12 text-center text-xs text-zinc-500 space-y-2">
            <Inbox className="mx-auto h-8 w-8 text-zinc-300" />
            <p className="font-semibold text-zinc-800">No Conversations Found</p>
            <p className="text-zinc-400">Inbound email replies from target contacts will appear here.</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs text-zinc-700">
            <thead className="border-b border-zinc-200 bg-zinc-50 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              <tr>
                <th className="px-4 py-3">Prospect</th>
                <th className="px-4 py-3">Account</th>
                <th className="px-4 py-3">Intent Classification</th>
                <th className="px-4 py-3">Thread Status</th>
                <th className="px-4 py-3">Last Message</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {conversations.map((conv) => (
                <tr key={conv.id} className="hover:bg-zinc-50/80 transition-colors">
                  <td className="px-4 py-3.5">
                    <div className="font-semibold text-zinc-900">{conv.contact_name || "Unknown Prospect"}</div>
                    <div className="text-[11px] text-zinc-500">{conv.contact_email || conv.contact_id}</div>
                  </td>
                  <td className="px-4 py-3.5 font-medium text-zinc-800">
                    {conv.account_name || "Target Account"}
                  </td>
                  <td className="px-4 py-3.5">
                    <ReplyClassificationBadge state={conv.current_reply_state as ReplyState} />
                  </td>
                  <td className="px-4 py-3.5 capitalize">
                    {conv.status === "needs_human_action" ? (
                      <span className="inline-flex items-center gap-1 rounded bg-orange-100 px-2 py-0.5 text-xs font-semibold text-orange-800">
                        <AlertCircle className="h-3 w-3" /> Needs Review
                      </span>
                    ) : conv.status === "opt_out" ? (
                      <span className="inline-flex items-center gap-1 rounded bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-800">
                        <ShieldAlert className="h-3 w-3" /> Opt-Out
                      </span>
                    ) : (
                      <span className="rounded bg-zinc-100 px-2 py-0.5 text-xs font-semibold text-zinc-700 capitalize">
                        {conv.status}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 font-mono text-[11px] text-zinc-500">
                    {new Date(conv.last_message_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <Link
                      href={`/conversations/${conv.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-purple-600 hover:text-purple-900 hover:underline"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      <span>View Thread</span>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Inbound Test Modal */}
      {showSimulateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <Send className="h-5 w-5 text-purple-600" />
                <h3 className="text-base font-bold text-zinc-900">
                  Simulate Inbound Prospect Reply
                </h3>
              </div>
              <button
                type="button"
                onClick={() => !simulating && setShowSimulateModal(false)}
                disabled={simulating}
                className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 disabled:opacity-50"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-xs text-zinc-500">
              Test inbound reply ingestion and automatic intent classification.
            </p>

            <form onSubmit={handleSimulateInbound} className="space-y-4">
              <div className="space-y-3 text-xs">
                <div>
                  <label className="font-semibold text-zinc-700">Sender Email</label>
                  <input
                    type="email"
                    value={simSender}
                    onChange={(e) => setSimSender(e.target.value)}
                    disabled={simulating}
                    required
                    className="mt-1 w-full rounded-lg border border-zinc-200 p-2 text-xs disabled:bg-zinc-50"
                  />
                </div>

                <div>
                  <label className="font-semibold text-zinc-700">Subject</label>
                  <input
                    type="text"
                    value={simSubject}
                    onChange={(e) => setSimSubject(e.target.value)}
                    disabled={simulating}
                    required
                    className="mt-1 w-full rounded-lg border border-zinc-200 p-2 text-xs disabled:bg-zinc-50"
                  />
                </div>

                <div>
                  <label className="font-semibold text-zinc-700">Reply Message Body</label>
                  <textarea
                    rows={3}
                    value={simBody}
                    onChange={(e) => setSimBody(e.target.value)}
                    disabled={simulating}
                    required
                    className="mt-1 w-full rounded-lg border border-zinc-200 p-2 text-xs disabled:bg-zinc-50"
                  />
                </div>
              </div>

              {modalError && (
                <div className="flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-800">
                  <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
                  <span>{modalError}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSimulateModal(false)}
                  disabled={simulating}
                  className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-100 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={simulating}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-purple-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-purple-700 transition-colors disabled:opacity-50"
                >
                  {simulating ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    <span>Ingest & Classify Reply</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
