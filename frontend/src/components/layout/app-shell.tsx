"use client";

import { useState, type ReactNode } from"react";

import { Sidebar } from"@/components/layout/sidebar";
import { Topbar } from"@/components/layout/topbar";
import { WorkspaceOnboarding } from"@/components/workspace/workspace-onboarding";
import { useWorkspace } from"@/lib/workspace-context";

export function AppShell({ children }: { children: ReactNode }) {
 const { workspaces, activeWorkspace, loading } = useWorkspace();
 const [collapsed, setCollapsed] = useState(false);
 const [mobileOpen, setMobileOpen] = useState(false);

 if (loading) {
 return (
 <main className="grid min-h-screen place-items-center bg-salesos-surface-muted p-6">
 <div className="flex items-center gap-2 text-sm text-salesos-text-secondary">
 <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"/>
 <span>Loading SalesOS workspace...</span>
 </div>
 </main>
 );
 }

 if (workspaces.length === 0) {
 return <WorkspaceOnboarding />;
 }

 return (
 <div className="flex min-h-screen bg-salesos-surface-muted font-sans text-salesos-text">
 <Sidebar
 collapsed={collapsed}
 onToggleCollapse={() => setCollapsed((prev) => !prev)}
 mobileOpen={mobileOpen}
 onCloseMobile={() => setMobileOpen(false)}
 />

 <div className="flex min-w-0 flex-1 flex-col">
 <Topbar onToggleMobileSidebar={() => setMobileOpen(true)} />

 <main className="flex-1 p-4 md:p-6">
 {activeWorkspace ? (
 children
 ) : (
 <div className="rounded-lg border border-salesos-border bg-salesos-surface p-6 shadow-sm">
 <p className="text-sm text-salesos-text-secondary">Please select or create a workspace.</p>
 </div>
 )}
 </main>
 </div>
 </div>
 );
}
