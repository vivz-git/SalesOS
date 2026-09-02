"use client";
import { Info } from "lucide-react";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Archive,
  ArrowLeft,
  Building2,
  Edit,
  ExternalLink,
  Linkedin,
  Mail,
  Phone,
  RotateCcw,
  Star,
  UserCheck,
} from "lucide-react";

import { fetchAccount, type Account } from "@/lib/api/accounts";
import { ContactForm } from "@/components/contacts/contact-form";
import { ContactStatusBadge } from "@/components/contacts/contact-status-badge";
import { ContactResearchSection } from "@/components/contacts/contact-research-section";
import { Button } from "@/components/ui/button";
import {
  archiveContact,
  fetchContact,
  restoreContact,
  updateContact,
  type Contact,
  type ContactCreatePayload,
} from "@/lib/api/contacts";
import { useWorkspace } from "@/lib/workspace-context";
import { createOutreachDraft, generateOutreachDraft } from "@/lib/api/outreach";
import { breadcrumbStore } from "@/lib/breadcrumb-store";

interface ContactDetailsProps {
  params: Promise<{ id: string }>;
}

export default function ContactDetailsPage({ params }: ContactDetailsProps) {
  const { id } = use(params);
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [contact, setContact] = useState<Contact | null>(null);
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (contact) {
      const fullName = `${contact.first_name || ""} ${contact.last_name || ""}`.trim();
      breadcrumbStore.setLabel(fullName || contact.email || "Prospect");
    }
    return () => {
      breadcrumbStore.setLabel(null);
    };
  }, [contact]);

  const loadContact = useCallback(async () => {
    if (!activeWorkspace || !id) return;
    try {
      setLoading(true);
      setError(null);
      const c = await fetchContact(activeWorkspace.id, id);
      setContact(c);

      if (c.account_id) {
        fetchAccount(activeWorkspace.id, c.account_id)
          .then(setAccount)
          .catch(() => setAccount(null));
      } else {
        setAccount(null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load contact details.");
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, id]);

  useEffect(() => {
    loadContact();
  }, [loadContact]);


  async function handleGenerateDraft() {
    if (!activeWorkspace || !contact) return;
    try {
      setActionLoading(true);
      const draft = await createOutreachDraft(activeWorkspace.id, {
        contact_id: contact.id,
        generation_source: "ai_generated",
      });
      await generateOutreachDraft(activeWorkspace.id, draft.id);
      router.push(`/approvals/${draft.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to generate draft.");
      setActionLoading(false);
    }
  }

  async function handleArchive() {
    if (!activeWorkspace || !contact) return;
    try {
      setActionLoading(true);
      const updated = await archiveContact(activeWorkspace.id, contact.id);
      setContact(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Archive failed.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRestore() {
    if (!activeWorkspace || !contact) return;
    try {
      setActionLoading(true);
      const updated = await restoreContact(activeWorkspace.id, contact.id);
      setContact(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Restore failed.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleEditSubmit(payload: ContactCreatePayload) {
    if (!activeWorkspace || !contact) return;
    const updated = await updateContact(activeWorkspace.id, contact.id, payload);
    setContact(updated);
    if (updated.account_id) {
      fetchAccount(activeWorkspace.id, updated.account_id)
        .then(setAccount)
        .catch(() => setAccount(null));
    } else {
      setAccount(null);
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-xl border bg-salesos-surface p-6 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-salesos-text-secondary">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
          <span>Loading contact profile...</span>
        </div>
      </div>
    );
  }

  if (error || !contact) {
    return (
      <div className="space-y-4">
        <Link
          href="/prospects"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-salesos-text-secondary hover:text-salesos-text"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Prospects</span>
        </Link>

        <div className="flex flex-col items-center justify-center rounded-xl border bg-salesos-surface p-8 text-center shadow-sm">
          <p className="text-sm font-semibold text-salesos-danger">{error || "Contact not found."}</p>
          <Button variant="outline" size="sm" onClick={() => router.push("/prospects")} className="mt-4">
            Return to Prospects
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href="/prospects"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-salesos-text-secondary hover:text-salesos-text"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Prospects</span>
        </Link>
      </div>

      <div className="rounded-xl border bg-salesos-surface p-6 shadow-sm space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between border-b pb-5">
          <div className="min-w-0 space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold tracking-tight text-salesos-text">
                {contact.first_name} {contact.last_name}
              </h1>
              {contact.is_primary && (
                <span className="inline-flex items-center gap-1 rounded-full bg-salesos-warning/10 px-2.5 py-0.5 text-xs font-semibold text-salesos-warning ring-1 ring-amber-600/20 ring-inset">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-500" />
                  Primary Contact
                </span>
              )}
            </div>

            {contact.title && (
              <p className="text-sm font-medium text-salesos-text-secondary">
                {contact.title} {contact.department ? `• ${contact.department}` : ""}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center lg:items-end lg:flex-col shrink-0">
            <div className="self-start sm:self-auto lg:self-end">
              <ContactStatusBadge status={contact.status} />
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Button
                variant="default"
                size="sm"
                onClick={handleGenerateDraft}
                disabled={actionLoading}
                className="flex items-center gap-1.5 bg-salesos-brand hover:bg-salesos-brand-hover text-white shadow-sm"
              >
                <Mail className="h-3.5 w-3.5" />
                <span>Generate Personalized Email</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(true)}
                disabled={actionLoading}
                className="flex items-center gap-1.5"
              >
                <Edit className="h-3.5 w-3.5" />
                <span>Edit Contact</span>
              </Button>

              {contact.status !== "archived" ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleArchive}
                  disabled={actionLoading}
                  className="flex items-center gap-1.5 text-salesos-danger border-salesos-danger/20 hover:bg-salesos-danger/10"
                >
                  <Archive className="h-3.5 w-3.5" />
                  <span>Archive</span>
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRestore}
                  disabled={actionLoading}
                  className="flex items-center gap-1.5 text-salesos-text-secondary hover:bg-salesos-surface-muted"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span>Restore Contact</span>
                </Button>
              )}
            </div>
          </div>
        </div>

        <ContactResearchSection
          contactId={contact.id}
          onGenerate={handleGenerateDraft}
          isGenerating={actionLoading}
        />

        <div className="grid gap-6 md:grid-cols-2">
          {/* Direct Communication Channels */}
          <div className="rounded-lg border bg-salesos-surface-muted p-5 space-y-3">
            <h2 className="text-xs font-semibold text-salesos-text-secondary uppercase tracking-wider">
              Communication Channels
            </h2>

            <div className="space-y-2 text-xs">
              <div>
                <span className="font-semibold text-salesos-text-secondary block">Work Email</span>
                {contact.email ? (
                  <a
                    href={`mailto:${contact.email}`}
                    className="text-salesos-brand hover:underline font-medium flex items-center gap-1 mt-0.5"
                  >
                    <Mail className="h-3.5 w-3.5 text-salesos-brand" />
                    <span>{contact.email}</span>
                  </a>
                ) : (
                  <span className="text-salesos-text-secondary/60">Not provided</span>
                )}
              </div>

              <div>
                <span className="font-semibold text-salesos-text-secondary block">Phone</span>
                {contact.phone ? (
                  <a
                    href={`tel:${contact.phone}`}
                    className="text-salesos-text font-medium flex items-center gap-1 mt-0.5"
                  >
                    <Phone className="h-3.5 w-3.5 text-salesos-text-secondary/60" />
                    <span>{contact.phone}</span>
                  </a>
                ) : (
                  <span className="text-salesos-text-secondary/60">Not provided</span>
                )}
              </div>

              <div>
                <span className="font-semibold text-salesos-text-secondary block">LinkedIn Profile</span>
                {contact.linkedin_url ? (
                  <a
                    href={contact.linkedin_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-salesos-brand hover:underline font-medium flex items-center gap-1 mt-0.5"
                  >
                    <Linkedin className="h-3.5 w-3.5 text-salesos-brand" />
                    <span>View LinkedIn Profile</span>
                    <ExternalLink className="h-3 w-3 text-indigo-400" />
                  </a>
                ) : (
                  <span className="text-salesos-text-secondary/60">Not provided</span>
                )}
              </div>
            </div>
          </div>

          {/* Associated Target Account */}
          <div className="rounded-lg border bg-salesos-surface-muted p-5 space-y-3">
            <h2 className="text-xs font-semibold text-salesos-text-secondary uppercase tracking-wider">
              Target Company Association
            </h2>

            {account ? (
              <Link
                href={`/accounts/${account.id}`}
                className="group block rounded-md border border-salesos-border bg-salesos-surface p-3 shadow-xs hover:border-salesos-border"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-salesos-text-secondary group-hover:text-salesos-text" />
                    <span className="text-sm font-bold text-salesos-text group-hover:text-salesos-text-secondary">
                      {account.name}
                    </span>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-salesos-text-secondary/60">
                    Status: {account.status}
                  </span>
                </div>
                {account.domain && (
                  <p className="mt-1 text-xs text-salesos-text-secondary">{account.domain}</p>
                )}
              </Link>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-md border border-dashed border-salesos-border p-4 text-center">
                <p className="text-xs font-medium text-salesos-text-secondary">No account currently assigned.</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditing(true)}
                  className="mt-2 text-xs"
                >
                  Assign Account
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-salesos-border bg-salesos-surface p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-salesos-text-secondary">
            <UserCheck className="h-4 w-4 text-salesos-text-secondary" />
            <span>Decision Maker Record</span>
          </div>
          <details className="mt-2 group">
            <summary className="text-[11px] font-medium text-salesos-text-secondary cursor-pointer hover:text-salesos-text list-none flex items-center gap-1">
              <Info className="h-3 w-3" />
              <span>Technical Details</span>
            </summary>
            <p className="mt-2 text-[11px] text-salesos-text-secondary/80 bg-salesos-surface-muted/50 p-2 rounded border border-salesos-border">
              Contact ID: <code className="font-mono">{contact.id}</code><br/>
              Workspace: {activeWorkspace?.name}<br/>
              Decision maker provenance is maintained across research workflows.
            </p>
          </details>
        </div>
      </div>

      {isEditing && (
        <ContactForm
          title="Edit Decision Maker Contact"
          initialData={contact}
          onSubmit={handleEditSubmit}
          onClose={() => setIsEditing(false)}
        />
      )}
    </div>
  );
}
