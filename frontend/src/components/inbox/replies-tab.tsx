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
import { Button } from "@/components/ui/button";

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
    <div className="space-y-6">
      {/* Filter Toolbar */}
      <div className="flex flex-col gap-3 rounded-xl border border-salesos-border bg-salesos-surface p-4 shadow-2xs md:flex-row md:items-center md:justify-between">
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
              type="button"
              onClick={() => setStatusFilter(tab.id)}
              aria-pressed={statusFilter === tab.id}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-salesos-focus ${
                statusFilter === tab.id
                  ? "bg-salesos-brand-subtle text-salesos-brand"
                  : "text-salesos-text-secondary hover:bg-salesos-surface-muted"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1 md:w-56">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-salesos-text-secondary/60" />
            <input
              type="text"
              placeholder="Search prospects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadData()}
              className="w-full rounded-lg border border-salesos-border bg-salesos-surface-muted pl-8 pr-3 py-1.5 text-xs text-salesos-text focus:border-slate-400 focus:bg-salesos-surface focus:outline-none"
            />
          </div>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={loadData}
            aria-label="Refresh threads"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-salesos-danger/20 bg-salesos-danger/10 p-4 text-xs text-salesos-danger">
          <AlertCircle className="h-4 w-4 text-salesos-danger shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-salesos-success/20 bg-salesos-success/10 p-4 text-xs text-emerald-900 font-semibold shadow-2xs">
          <CheckCircle2 className="h-4 w-4 text-salesos-success shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Conversation Thread Table */}
      <div className="rounded-xl border border-salesos-border bg-salesos-surface shadow-2xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-salesos-text-secondary/60">Loading conversation threads...</div>
        ) : conversations.length === 0 ? (
          <div className="p-12 text-center text-xs text-salesos-text-secondary space-y-2">
            <Inbox className="mx-auto h-8 w-8 text-salesos-text-secondary/40" />
            <p className="font-semibold text-salesos-text">No Conversations Found</p>
            <p className="text-salesos-text-secondary/60">Inbound email replies from target contacts will appear here.</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs text-salesos-text-secondary">
            <thead className="border-b border-salesos-border bg-salesos-surface-muted text-[11px] font-semibold uppercase tracking-wider text-salesos-text-secondary">
              <tr>
                <th className="px-4 py-3">Prospect</th>
                <th className="px-4 py-3">Account</th>
                <th className="px-4 py-3">Intent Classification</th>
                <th className="px-4 py-3">Thread Status</th>
                <th className="px-4 py-3">Last Message</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-salesos-border">
              {conversations.map((conv) => (
                <tr key={conv.id} className="hover:bg-salesos-surface-muted/80 transition-colors">
                  <td className="px-4 py-3.5">
                    <div className="font-semibold text-salesos-text">{conv.contact_name || "Unknown Prospect"}</div>
                    <div className="text-[11px] text-salesos-text-secondary">{conv.contact_email || conv.contact_id}</div>
                  </td>
                  <td className="px-4 py-3.5 font-medium text-salesos-text">
                    {conv.account_name || "Target Account"}
                  </td>
                  <td className="px-4 py-3.5">
                    <ReplyClassificationBadge state={conv.current_reply_state as ReplyState} />
                  </td>
                  <td className="px-4 py-3.5 capitalize whitespace-nowrap">
                    {conv.status === "needs_human_action" ? (
                      <span className="inline-flex items-center gap-1 rounded bg-orange-100 px-2 py-0.5 text-xs font-semibold text-orange-800">
                        <AlertCircle className="h-3 w-3" /> Needs Review
                      </span>
                    ) : conv.status === "opt_out" ? (
                      <span className="inline-flex items-center gap-1 rounded bg-rose-100 px-2 py-0.5 text-xs font-semibold text-salesos-danger">
                        <ShieldAlert className="h-3 w-3" /> Opt-Out
                      </span>
                    ) : (
                      <span className="rounded bg-salesos-surface-muted px-2 py-0.5 text-xs font-semibold text-salesos-text-secondary capitalize">
                        {conv.status}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 font-mono text-[11px] text-salesos-text-secondary whitespace-nowrap">
                    {new Date(conv.last_message_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <Link
                      href={`/conversations/${conv.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-salesos-brand hover:text-salesos-brand-hover hover:underline"
                    >
                      <Eye className="h-3.5 w-3.5" aria-hidden="true" />
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
          <div className="w-full max-w-md rounded-xl border border-salesos-border bg-salesos-surface p-6 shadow-xl space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <Send className="h-5 w-5 text-salesos-brand" aria-hidden="true" />
                <h3 className="text-base font-bold text-salesos-text">
                  Simulate Inbound Prospect Reply
                </h3>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => !simulating && setShowSimulateModal(false)}
                disabled={simulating}
                aria-label="Close modal"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </Button>
            </div>
            <p className="text-xs text-salesos-text-secondary">
              Test inbound reply ingestion and automatic intent classification.
            </p>

            <form onSubmit={handleSimulateInbound} className="space-y-4">
              <div className="space-y-3 text-xs">
                <div>
                  <label className="font-semibold text-salesos-text-secondary">Sender Email</label>
                  <input
                    type="email"
                    value={simSender}
                    onChange={(e) => setSimSender(e.target.value)}
                    disabled={simulating}
                    required
                    className="mt-1 w-full rounded-lg border border-salesos-border p-2 text-xs disabled:bg-salesos-surface-muted"
                  />
                </div>

                <div>
                  <label className="font-semibold text-salesos-text-secondary">Subject</label>
                  <input
                    type="text"
                    value={simSubject}
                    onChange={(e) => setSimSubject(e.target.value)}
                    disabled={simulating}
                    required
                    className="mt-1 w-full rounded-lg border border-salesos-border p-2 text-xs disabled:bg-salesos-surface-muted"
                  />
                </div>

                <div>
                  <label className="font-semibold text-salesos-text-secondary">Reply Message Body</label>
                  <textarea
                    rows={3}
                    value={simBody}
                    onChange={(e) => setSimBody(e.target.value)}
                    disabled={simulating}
                    required
                    className="mt-1 w-full rounded-lg border border-salesos-border p-2 text-xs disabled:bg-salesos-surface-muted"
                  />
                </div>
              </div>

              {modalError && (
                <div className="flex items-center gap-2 rounded-lg border border-salesos-danger/20 bg-salesos-danger/10 p-2.5 text-xs text-salesos-danger">
                  <AlertCircle className="h-4 w-4 text-salesos-danger shrink-0" />
                  <span>{modalError}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSimulateModal(false)}
                  disabled={simulating}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="default"
                  size="sm"
                  disabled={simulating}
                >
                  {simulating ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    <span>Ingest & Classify Reply</span>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
