"use client";

import { useState } from "react";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Campaign, CampaignCreatePayload } from "@/lib/api/campaigns";

interface CampaignFormProps {
  initialData?: Campaign | null;
  onSubmit: (payload: CampaignCreatePayload) => Promise<void>;
  onClose: () => void;
  title: string;
}

export function CampaignForm({
  initialData,
  onSubmit,
  onClose,
  title,
}: CampaignFormProps) {
  const [name, setName] = useState(initialData?.name || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [targetSegment, setTargetSegment] = useState(initialData?.target_segment || "");
  const [icpDefinition, setIcpDefinition] = useState(initialData?.icp_definition || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Campaign name is required.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await onSubmit({
        name: name.trim(),
        description: description.trim() || undefined,
        target_segment: targetSegment.trim() || undefined,
        icp_definition: icpDefinition.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save campaign.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
      <div className="w-full max-w-lg rounded-xl border bg-white p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b pb-3">
          <h2 className="text-lg font-bold text-zinc-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 p-3 text-xs font-medium text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="campaign-name" className="block text-xs font-semibold text-zinc-700">
              Campaign Name <span className="text-red-500">*</span>
            </label>
            <input
              id="campaign-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Q3 SaaS Outbound"
              className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:border-zinc-900 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="target-segment" className="block text-xs font-semibold text-zinc-700">
              Target Segment
            </label>
            <input
              id="target-segment"
              type="text"
              value={targetSegment}
              onChange={(e) => setTargetSegment(e.target.value)}
              placeholder="e.g. Mid-Market B2B SaaS 50-200 ARR"
              className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:border-zinc-900 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-xs font-semibold text-zinc-700">
              Description
            </label>
            <textarea
              id="description"
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Strategic goals or team notes for this campaign..."
              className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:border-zinc-900 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="icp-definition" className="block text-xs font-semibold text-zinc-700">
              ICP & Messaging Brief
            </label>
            <textarea
              id="icp-definition"
              rows={3}
              value={icpDefinition}
              onChange={(e) => setIcpDefinition(e.target.value)}
              placeholder="Ideal Customer Profile guidelines, value props, and tone instructions..."
              className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:border-zinc-900 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t pt-4">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Save Campaign"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
