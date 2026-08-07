"use client";

import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { WorkspaceProvider } from "@/lib/workspace-context";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <WorkspaceProvider>
      <AppShell>{children}</AppShell>
    </WorkspaceProvider>
  );
}
