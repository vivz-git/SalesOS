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
  Globe,
  MapPin,
  Megaphone,
  RotateCcw,
} from "lucide-react";

import { AccountForm } from "@/components/accounts/account-form";
import { AccountStatusBadge } from "@/components/accounts/account-status-badge";
import { Button } from "@/components/ui/button";
import {
  archiveAccount,
  fetchAccount,
  restoreAccount,
  updateAccount,
  type Account,
  type AccountCreatePayload,
} from "@/lib/api/accounts";
import { fetchCampaign, type Campaign } from "@/lib/api/campaigns";
import { useWorkspace } from "@/lib/workspace-context";

interface AccountDetailsProps {
  params: Promise<{ id: string }>;
}

export default function AccountDetailsPage({ params }: AccountDetailsProps) {
  const { id } = use(params);
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [account, setAccount] = useState<Account | null>(null);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const loadAccount = useCallback(async () => {
    if (!activeWorkspace || !id) return;
    try {
      setLoading(true);
      setError(null);
      const acc = await fetchAccount(activeWorkspace.id, id);
      setAccount(acc);

      if (acc.campaign_id) {
        fetchCampaign(activeWorkspace.id, acc.campaign_id)
          .then(setCampaign)
          .catch(() => setCampaign(null));
      } else {
        setCampaign(null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load account details.");
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, id]);

  useEffect(() => {
    loadAccount();
  }, [loadAccount]);

  async function handleArchive() {
    if (!activeWorkspace || !account) return;
    try {
      setActionLoading(true);
      const updated = await archiveAccount(activeWorkspace.id, account.id);
      setAccount(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Archive failed.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRestore() {
    if (!activeWorkspace || !account) return;
    try {
      setActionLoading(true);
      const updated = await restoreAccount(activeWorkspace.id, account.id);
      setAccount(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Restore failed.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleEditSubmit(payload: AccountCreatePayload) {
    if (!activeWorkspace || !account) return;
    const updated = await updateAccount(activeWorkspace.id, account.id, payload);
    setAccount(updated);
    if (updated.campaign_id) {
      fetchCampaign(activeWorkspace.id, updated.campaign_id)
        .then(setCampaign)
        .catch(() => setCampaign(null));
    } else {
      setCampaign(null);
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-xl border bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-900 border-t-transparent" />
          <span>Loading company profile...</span>
        </div>
      </div>
    );
  }

  if (error || !account) {
    return (
      <div className="space-y-4">
        <Link
          href="/accounts"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-600 hover:text-zinc-900"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Accounts</span>
        </Link>

        <div className="flex flex-col items-center justify-center rounded-xl border bg-white p-8 text-center shadow-sm">
          <p className="text-sm font-semibold text-red-600">{error || "Account not found."}</p>
          <Button variant="outline" size="sm" onClick={() => router.push("/accounts")} className="mt-4">
            Return to Accounts List
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href="/accounts"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-600 hover:text-zinc-900"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Accounts</span>
        </Link>
      </div>

      <div className="rounded-xl border bg-white p-6 shadow-sm space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-zinc-900">{account.name}</h1>
              <AccountStatusBadge status={account.status} />
            </div>
            {account.domain && (
              <a
                href={`https://${account.domain}`}
                target="_blank"
                rel="noreferrer"
                className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:underline"
              >
                <Globe className="h-4 w-4 text-indigo-500" />
                <span>{account.domain}</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
              disabled={actionLoading}
              className="flex items-center gap-1.5"
            >
              <Edit className="h-3.5 w-3.5" />
              <span>Edit Account</span>
            </Button>

            {account.status !== "archived" ? (
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
                className="flex items-center gap-1.5 text-zinc-700"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Restore Account</span>
              </Button>
            )}
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Company Details */}
          <div className="rounded-lg border bg-zinc-50 p-5 space-y-3">
            <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Company Attributes
            </h2>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="font-semibold text-zinc-500 block">Industry</span>
                <span className="text-zinc-900 font-medium">
                  {account.industry || "Not specified"}
                </span>
              </div>

              <div>
                <span className="font-semibold text-zinc-500 block">Company Size</span>
                <span className="text-zinc-900 font-medium">
                  {account.employee_count ? `${account.employee_count} employees` : "Not specified"}
                </span>
              </div>

              <div className="col-span-2">
                <span className="font-semibold text-zinc-500 block">Location</span>
                <span className="text-zinc-900 font-medium flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5 text-zinc-400" />
                  {[account.city, account.state, account.country].filter(Boolean).join(", ") ||
                    "Location not specified"}
                </span>
              </div>
            </div>
          </div>

          {/* Assigned Campaign */}
          <div className="rounded-lg border bg-zinc-50 p-5 space-y-3">
            <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Campaign Association
            </h2>

            {campaign ? (
              <Link
                href={`/campaigns/${campaign.id}`}
                className="group block rounded-md border border-zinc-200 bg-white p-3 shadow-xs hover:border-zinc-300"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Megaphone className="h-4 w-4 text-zinc-600 group-hover:text-zinc-900" />
                    <span className="text-sm font-bold text-zinc-900 group-hover:text-zinc-700">
                      {campaign.name}
                    </span>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                    Status: {campaign.status}
                  </span>
                </div>
                {campaign.target_segment && (
                  <p className="mt-1 text-xs text-zinc-500">{campaign.target_segment}</p>
                )}
              </Link>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-md border border-dashed border-zinc-300 p-4 text-center">
                <p className="text-xs font-medium text-zinc-500">No campaign currently assigned.</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditing(true)}
                  className="mt-2 text-xs"
                >
                  Assign Campaign
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-zinc-700">
            <Building2 className="h-4 w-4 text-zinc-500" />
            <span>Target Account Profile</span>
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            Account ID: <code className="rounded bg-zinc-100 px-1 py-0.5">{account.id}</code> • Workspace:{" "}
            <span className="font-semibold text-zinc-900">{activeWorkspace?.name}</span>. Target company context is preserved across campaign pipelines.
          </p>
        </div>
      </div>

      {isEditing && (
        <AccountForm
          title="Edit Target Company"
          initialData={account}
          onSubmit={handleEditSubmit}
          onClose={() => setIsEditing(false)}
        />
      )}
    </div>
  );
}
