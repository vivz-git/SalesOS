"use client";

import { useEffect, useState } from "react";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { WorkspaceOnboarding } from "@/components/workspace/workspace-onboarding";
import { WorkspaceSwitcher } from "@/components/workspace/workspace-switcher";
import { useWorkspace, WorkspaceProvider } from "@/lib/workspace-context";

interface UserIdentity {
  user_id: string;
  email: string | null;
  workspace_id: string;
  role: string;
}

function WorkspaceDashboardContent() {
  const { workspaces, activeWorkspace, loading } = useWorkspace();
  const [identity, setIdentity] = useState<UserIdentity | null>(null);

  useEffect(() => {
    if (!activeWorkspace) return;
    fetch("/api/v1/me", {
      headers: {
        "X-SalesOS-Workspace-Id": activeWorkspace.id,
      },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setIdentity(data);
      })
      .catch(() => undefined);
  }, [activeWorkspace]);

  if (loading) {
    return (
      <main className="grid min-h-screen place-items-center p-6">
        <p className="text-sm text-zinc-500">Loading workspace...</p>
      </main>
    );
  }

  if (workspaces.length === 0) {
    return <WorkspaceOnboarding />;
  }

  return (
    <div className="min-h-screen bg-zinc-50 font-sans">
      <header className="border-b bg-white px-6 py-4 shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-lg font-bold text-zinc-900">SalesOS</span>
            <WorkspaceSwitcher />
          </div>

          <div className="flex items-center gap-4">
            {identity && (
              <div className="flex items-center gap-2 text-xs">
                <span className="font-medium text-zinc-700">{identity.email}</span>
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 font-semibold text-zinc-800 uppercase tracking-wider text-[10px]">
                  {identity.role}
                </span>
              </div>
            )}
            <SignOutButton />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl p-6">
        {activeWorkspace ? (
          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <h1 className="text-xl font-semibold text-zinc-900">{activeWorkspace.name}</h1>
            <p className="mt-1 text-sm text-zinc-500">Slug: {activeWorkspace.slug}</p>
            <div className="mt-6 rounded-lg bg-zinc-50 border p-4">
              <p className="text-sm font-medium text-zinc-700">Protected Workspace Foundation</p>
              <p className="mt-1 text-xs text-zinc-500">
                Workspace ID: {activeWorkspace.id} • Verified via FastAPI backend header authorization.
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-zinc-600">Please select or create a workspace.</p>
        )}
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <WorkspaceProvider>
      <WorkspaceDashboardContent />
    </WorkspaceProvider>
  );
}
