"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  FileSearch,
  PlayCircle,
  User,
} from "lucide-react";

import { EvidenceViewer } from "@/components/research/evidence-viewer";
import { ResearchStatusBadge } from "@/components/research/research-status-badge";
import { SourceViewer } from "@/components/research/source-viewer";
import { Button } from "@/components/ui/button";
import { fetchAccount, type Account } from "@/lib/api/accounts";
import { fetchContact, type Contact } from "@/lib/api/contacts";
import {
  fetchResearchBrief,
  fetchResearchSources,
  triggerResearchJob,
  type ResearchBrief,
  type ResearchJob,
  type ResearchSource,
} from "@/lib/api/research";
import { useWorkspace } from "@/lib/workspace-context";

interface ResearchDetailsProps {
  params: Promise<{ id: string }>;
}

export default function ResearchDetailsPage({ params }: ResearchDetailsProps) {
  const { id } = use(params);
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [brief, setBrief] = useState<ResearchBrief | null>(null);
  const [sources, setSources] = useState<ResearchSource[]>([]);
  const [account, setAccount] = useState<Account | null>(null);
  const [contact, setContact] = useState<Contact | null>(null);
  const [activeJob, setActiveJob] = useState<ResearchJob | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const loadBriefData = useCallback(async () => {
    if (!activeWorkspace || !id) return;
    try {
      setLoading(true);
      setError(null);
      const b = await fetchResearchBrief(activeWorkspace.id, id);
      setBrief(b);

      const srcs = await fetchResearchSources(activeWorkspace.id, id).catch(() => []);
      setSources(srcs);

      if (b.account_id) {
        fetchAccount(activeWorkspace.id, b.account_id)
          .then(setAccount)
          .catch(() => setAccount(null));
      }
      if (b.contact_id) {
        fetchContact(activeWorkspace.id, b.contact_id)
          .then(setContact)
          .catch(() => setContact(null));
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load research brief.");
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, id]);

  useEffect(() => {
    loadBriefData();
  }, [loadBriefData]);

  async function handleTriggerJob() {
    if (!activeWorkspace || !brief) return;
    try {
      setActionLoading(true);
      const job = await triggerResearchJob(activeWorkspace.id, brief.id);
      setActiveJob(job);
      const updatedBrief = await fetchResearchBrief(activeWorkspace.id, brief.id);
      setBrief(updatedBrief);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Job execution trigger failed.");
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-xl border bg-salesos-surface p-6 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-salesos-text-secondary">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
          <span>Loading intelligence brief...</span>
        </div>
      </div>
    );
  }

  if (error || !brief) {
    return (
      <div className="space-y-4">
        <Link
          href="/research"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-salesos-text-secondary hover:text-salesos-text"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Research Briefs</span>
        </Link>

        <div className="flex flex-col items-center justify-center rounded-xl border bg-salesos-surface p-8 text-center shadow-sm">
          <p className="text-sm font-semibold text-salesos-danger">{error || "Research brief not found."}</p>
          <Button variant="outline" size="sm" onClick={() => router.push("/research")} className="mt-4">
            Return to Briefs Directory
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href="/research"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-salesos-text-secondary hover:text-salesos-text"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Research Briefs</span>
        </Link>
      </div>

      <div className="rounded-xl border bg-salesos-surface p-6 shadow-sm space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-salesos-text">
                {account ? `${account.name} Research Brief` : "Company Research Brief"}
              </h1>
              <ResearchStatusBadge status={brief.status} />
            </div>
            {contact && (
              <p className="mt-1 text-xs font-semibold text-salesos-text-secondary">
                Decision Maker Focus: {contact.first_name} {contact.last_name} ({contact.title || "Target Contact"})
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleTriggerJob}
              disabled={actionLoading || brief.status === "in_progress"}
              className="flex items-center gap-1.5 bg-salesos-brand hover:bg-salesos-brand-hover text-white"
            >
              <PlayCircle className="h-4 w-4" />
              <span>{actionLoading ? "Enqueuing..." : "Run Research Pipeline"}</span>
            </Button>
          </div>
        </div>

        {activeJob && (
          <div className="rounded-lg border border-salesos-brand/20 bg-salesos-brand-subtle p-4 text-xs text-salesos-brand flex items-center justify-between">
            <div>
              <span className="font-bold block">Background Job Enqueued:</span>
              <span>Job ID: {activeJob.id} • Status: {activeJob.status}</span>
            </div>
            <ResearchStatusBadge status={activeJob.status} />
          </div>
        )}

        {/* Associated Entity Links */}
        <div className="grid gap-4 sm:grid-cols-2">
          {account && (
            <Link
              href={`/accounts/${account.id}`}
              className="group flex items-center justify-between rounded-lg border border-salesos-border bg-salesos-surface-muted p-3 hover:border-salesos-border"
            >
              <div className="flex items-center gap-2 text-xs font-semibold text-salesos-text">
                <Building2 className="h-4 w-4 text-salesos-text-secondary group-hover:text-salesos-text" />
                <span>{account.name}</span>
              </div>
              <span className="text-[11px] text-salesos-text-secondary/60">View Account →</span>
            </Link>
          )}

          {contact && (
            <Link
              href={`/contacts/${contact.id}`}
              className="group flex items-center justify-between rounded-lg border border-salesos-border bg-salesos-surface-muted p-3 hover:border-salesos-border"
            >
              <div className="flex items-center gap-2 text-xs font-semibold text-salesos-text">
                <User className="h-4 w-4 text-salesos-text-secondary group-hover:text-salesos-text" />
                <span>{contact.first_name} {contact.last_name}</span>
              </div>
              <span className="text-[11px] text-salesos-text-secondary/60">View Decision Maker →</span>
            </Link>
          )}
        </div>

        {/* Evidence & Source Viewers */}
        <EvidenceViewer brief={brief} />

        <SourceViewer sources={sources} />

        <div className="rounded-lg border border-salesos-border bg-salesos-surface p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-salesos-text-secondary">
            <FileSearch className="h-4 w-4 text-salesos-text-secondary" />
            <span>Audit-Ready Provenance Record</span>
          </div>
          <p className="mt-1 text-xs text-salesos-text-secondary">
            Brief ID: <code className="rounded bg-salesos-surface-muted px-1 py-0.5">{brief.id}</code> • Workspace:{" "}
            <span className="font-semibold text-salesos-text">{activeWorkspace?.name}</span>. Research evidence is append-only for auditability.
          </p>
        </div>
      </div>
    </div>
  );
}
