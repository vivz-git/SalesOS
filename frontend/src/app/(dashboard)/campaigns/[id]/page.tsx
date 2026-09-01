"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Archive,
  ArrowLeft,
  CheckCircle,
  Edit,
  PauseCircle,
  PlayCircle,
  RotateCcw,
} from "lucide-react";

import { CampaignForm } from "@/components/campaigns/campaign-form";
import { CampaignStatusBadge } from "@/components/campaigns/campaign-status-badge";
import { Button } from "@/components/ui/button";
import {
  activateCampaign,
  archiveCampaign,
  fetchCampaign,
  pauseCampaign,
  restoreCampaign,
  updateCampaign,
  type Campaign,
  type CampaignCreatePayload,
} from "@/lib/api/campaigns";
import { useWorkspace } from "@/lib/workspace-context";

import { SequenceBuilder } from "@/components/sequences/sequence-builder";
import {
  fetchCampaignSequence,
  type SequenceDefinition,
} from "@/lib/api/sequences";

interface CampaignDetailsProps {
  params: Promise<{ id: string }>;
}

export default function CampaignDetailsPage({ params }: CampaignDetailsProps) {
  const { id } = use(params);
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [sequence, setSequence] = useState<SequenceDefinition | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const loadCampaign = useCallback(async () => {
    if (!activeWorkspace || !id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await fetchCampaign(activeWorkspace.id, id);
      setCampaign(data);
      try {
        const seqData = await fetchCampaignSequence(activeWorkspace.id, id);
        setSequence(seqData);
      } catch {
        // Fallback silently if sequence loading fails
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load campaign details.");
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, id]);

  useEffect(() => {
    loadCampaign();
  }, [loadCampaign]);

  async function handleStatusAction(
    actionFn: (wsId: string, campaignId: string) => Promise<Campaign>
  ) {
    if (!activeWorkspace || !campaign) return;
    try {
      setActionLoading(true);
      const updated = await actionFn(activeWorkspace.id, campaign.id);
      setCampaign(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Status update failed.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleEditSubmit(payload: CampaignCreatePayload) {
    if (!activeWorkspace || !campaign) return;
    const updated = await updateCampaign(activeWorkspace.id, campaign.id, payload);
    setCampaign(updated);
  }

  if (loading) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-xl border bg-salesos-surface p-6 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-salesos-text-secondary">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
          <span>Loading campaign details...</span>
        </div>
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="space-y-4">
        <Link
          href="/campaigns"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-salesos-text-secondary hover:text-salesos-text"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Campaigns</span>
        </Link>

        <div className="flex flex-col items-center justify-center rounded-xl border bg-salesos-surface p-8 text-center shadow-sm">
          <p className="text-sm font-semibold text-salesos-danger">{error || "Campaign not found."}</p>
          <Button variant="outline" size="sm" onClick={() => router.push("/campaigns")} className="mt-4">
            Return to Campaigns List
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href="/campaigns"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-salesos-text-secondary hover:text-salesos-text"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Campaigns</span>
        </Link>
      </div>

      <div className="rounded-xl border bg-salesos-surface p-6 shadow-sm space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-salesos-text">{campaign.name}</h1>
              <CampaignStatusBadge status={campaign.status} />
            </div>
            {campaign.target_segment && (
              <p className="mt-1 text-sm font-medium text-salesos-text-secondary">
                Target Segment: {campaign.target_segment}
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
              disabled={actionLoading}
              className="flex items-center gap-1.5"
            >
              <Edit className="h-3.5 w-3.5" />
              <span>Edit</span>
            </Button>

            {campaign.status !== "active" && campaign.status !== "archived" && (
              <Button
                size="sm"
                onClick={() => handleStatusAction(activateCampaign)}
                disabled={actionLoading}
                className="flex items-center gap-1.5 bg-salesos-brand hover:bg-salesos-brand-hover text-white"
              >
                <PlayCircle className="h-3.5 w-3.5" />
                <span>Activate</span>
              </Button>
            )}

            {campaign.status === "active" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleStatusAction(pauseCampaign)}
                disabled={actionLoading}
                className="flex items-center gap-1.5 text-salesos-warning border-amber-300 hover:bg-salesos-warning/10"
              >
                <PauseCircle className="h-3.5 w-3.5" />
                <span>Pause</span>
              </Button>
            )}

            {campaign.status !== "archived" ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleStatusAction(archiveCampaign)}
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
                onClick={() => handleStatusAction(restoreCampaign)}
                disabled={actionLoading}
                className="flex items-center gap-1.5 text-salesos-text-secondary"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Restore Draft</span>
              </Button>
            )}
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-2">
            <h2 className="text-xs font-semibold text-salesos-text-secondary uppercase tracking-wider">
              Description & Notes
            </h2>
            <div className="rounded-lg border bg-salesos-surface-muted p-4 text-sm text-salesos-text-secondary min-h-24">
              {campaign.description || "No campaign description provided."}
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-xs font-semibold text-salesos-text-secondary uppercase tracking-wider">
              ICP & Messaging Brief
            </h2>
            <div className="rounded-lg border bg-salesos-surface-muted p-4 text-sm text-salesos-text-secondary min-h-24">
              {campaign.icp_definition || "No ICP definition provided."}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-salesos-border bg-salesos-surface p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-salesos-text-secondary">
            <CheckCircle className="h-4 w-4 text-salesos-text-secondary" />
            <span>Governed Execution Boundary</span>
          </div>
          <p className="mt-1 text-xs text-salesos-text-secondary">
            Campaign ID: <code className="rounded bg-salesos-surface-muted px-1 py-0.5">{campaign.id}</code> • Status:{" "}
            <span className="font-semibold capitalize text-salesos-text">{campaign.status}</span>. External outreach dispatch is protected by human approval gates.
          </p>
        </div>

        {/* Sequence Builder & Step Touchpoint Configuration */}
        {activeWorkspace && sequence && (
          <SequenceBuilder
            workspaceId={activeWorkspace.id}
            campaignId={campaign.id}
            initialSequence={sequence}
            onSaved={(updated) => setSequence(updated)}
          />
        )}
      </div>

      {isEditing && (
        <CampaignForm
          title="Edit Campaign Details"
          initialData={campaign}
          onSubmit={handleEditSubmit}
          onClose={() => setIsEditing(false)}
        />
      )}
    </div>
  );
}
