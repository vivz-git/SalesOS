"use client";

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
      <div className="flex h-64 w-full items-center justify-center rounded-xl border bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-slate-500">
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
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Prospects</span>
        </Link>

        <div className="flex flex-col items-center justify-center rounded-xl border bg-white p-8 text-center shadow-sm">
          <p className="text-sm font-semibold text-red-600">{error || "Contact not found."}</p>
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
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Prospects</span>
        </Link>
      </div>

      <div className="rounded-xl border bg-white p-6 shadow-sm space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                {contact.first_name} {contact.last_name}
              </h1>
              {contact.is_primary && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800 ring-1 ring-amber-600/20 ring-inset">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-500" />
                  Primary Contact
                </span>
              )}
              <ContactStatusBadge status={contact.status} />
            </div>

            {contact.title && (
              <p className="mt-1 text-sm font-medium text-slate-600">
                {contact.title} {contact.department ? `• ${contact.department}` : ""}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">

            <Button
              variant="default"
              size="sm"
              onClick={handleGenerateDraft}
              disabled={actionLoading}
              className="flex items-center gap-1.5 bg-accent hover:bg-accent-hover text-white"
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
                className="flex items-center gap-1.5 text-red-600 border-red-200 hover:bg-red-50"
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
                className="flex items-center gap-1.5 text-slate-700"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Restore Contact</span>
              </Button>
            )}
          </div>
        </div>

        <ContactResearchSection
          contactId={contact.id}
          onGenerate={handleGenerateDraft}
          isGenerating={actionLoading}
        />

        <div className="grid gap-6 md:grid-cols-2">
          {/* Direct Communication Channels */}
          <div className="rounded-lg border bg-slate-50 p-5 space-y-3">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Communication Channels
            </h2>

            <div className="space-y-2 text-xs">
              <div>
                <span className="font-semibold text-slate-500 block">Work Email</span>
                {contact.email ? (
                  <a
                    href={`mailto:${contact.email}`}
                    className="text-indigo-600 hover:underline font-medium flex items-center gap-1 mt-0.5"
                  >
                    <Mail className="h-3.5 w-3.5 text-indigo-500" />
                    <span>{contact.email}</span>
                  </a>
                ) : (
                  <span className="text-slate-400">Not provided</span>
                )}
              </div>

              <div>
                <span className="font-semibold text-slate-500 block">Phone</span>
                {contact.phone ? (
                  <a
                    href={`tel:${contact.phone}`}
                    className="text-slate-900 font-medium flex items-center gap-1 mt-0.5"
                  >
                    <Phone className="h-3.5 w-3.5 text-slate-400" />
                    <span>{contact.phone}</span>
                  </a>
                ) : (
                  <span className="text-slate-400">Not provided</span>
                )}
              </div>

              <div>
                <span className="font-semibold text-slate-500 block">LinkedIn Profile</span>
                {contact.linkedin_url ? (
                  <a
                    href={contact.linkedin_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-indigo-600 hover:underline font-medium flex items-center gap-1 mt-0.5"
                  >
                    <Linkedin className="h-3.5 w-3.5 text-indigo-500" />
                    <span>View LinkedIn Profile</span>
                    <ExternalLink className="h-3 w-3 text-indigo-400" />
                  </a>
                ) : (
                  <span className="text-slate-400">Not provided</span>
                )}
              </div>
            </div>
          </div>

          {/* Associated Target Account */}
          <div className="rounded-lg border bg-slate-50 p-5 space-y-3">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Target Company Association
            </h2>

            {account ? (
              <Link
                href={`/accounts/${account.id}`}
                className="group block rounded-md border border-slate-200 bg-white p-3 shadow-xs hover:border-slate-300"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-slate-600 group-hover:text-slate-900" />
                    <span className="text-sm font-bold text-slate-900 group-hover:text-slate-700">
                      {account.name}
                    </span>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Status: {account.status}
                  </span>
                </div>
                {account.domain && (
                  <p className="mt-1 text-xs text-slate-500">{account.domain}</p>
                )}
              </Link>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-md border border-dashed border-slate-300 p-4 text-center">
                <p className="text-xs font-medium text-slate-500">No account currently assigned.</p>
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

        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <UserCheck className="h-4 w-4 text-slate-500" />
            <span>Decision Maker Record</span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Contact ID: <code className="rounded bg-slate-100 px-1 py-0.5">{contact.id}</code> • Workspace:{" "}
            <span className="font-semibold text-slate-900">{activeWorkspace?.name}</span>. Decision maker provenance is maintained across research workflows.
          </p>
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
