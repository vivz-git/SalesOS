"use client";

import { useWorkspace } from "@/lib/workspace-context";

export default function DashboardHomePage() {
  const { activeWorkspace } = useWorkspace();

  return (
    <div className="space-y-6">
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
          Dashboard Overview
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Welcome to SalesOS. Autonomous outbound preparation with human-controlled sending.
        </p>

        {activeWorkspace && (
          <div className="mt-6 rounded-lg border bg-zinc-50 p-4">
            <p className="text-sm font-medium text-zinc-900">Active Workspace</p>
            <p className="mt-1 text-xs text-zinc-600">
              Name: <span className="font-semibold text-zinc-900">{activeWorkspace.name}</span> • Slug:{" "}
              <code className="rounded bg-zinc-200 px-1 py-0.5">{activeWorkspace.slug}</code>
            </p>
            <p className="mt-1 text-[11px] text-zinc-400">
              Workspace ID: {activeWorkspace.id}
            </p>
          </div>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Campaign Briefs
          </p>
          <p className="mt-2 text-2xl font-bold text-zinc-900">0</p>
          <p className="mt-1 text-xs text-zinc-500">Campaign brief placeholder</p>
        </div>
        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Pending Approvals
          </p>
          <p className="mt-2 text-2xl font-bold text-zinc-900">0</p>
          <p className="mt-1 text-xs text-zinc-500">Approval queue placeholder</p>
        </div>
        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Target Accounts
          </p>
          <p className="mt-2 text-2xl font-bold text-zinc-900">0</p>
          <p className="mt-1 text-xs text-zinc-500">Target list placeholder</p>
        </div>
      </div>
    </div>
  );
}
