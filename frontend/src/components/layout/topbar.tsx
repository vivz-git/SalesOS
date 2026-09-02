"use client";

import { Menu } from"lucide-react";

import { Breadcrumbs } from"@/components/layout/breadcrumbs";
import { UserNav } from"@/components/layout/user-nav";
import { WorkspaceSwitcher } from"@/components/workspace/workspace-switcher";

interface TopbarProps {
 onToggleMobileSidebar: () => void;
}

export function Topbar({ onToggleMobileSidebar }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between gap-2 border-b border-salesos-border bg-salesos-surface px-4 shadow-sm md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onToggleMobileSidebar}
          className="shrink-0 rounded-md p-1.5 text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text md:hidden"
          aria-label="Open mobile menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="hidden min-w-0 sm:block">
          <Breadcrumbs />
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-3 md:gap-4">
        <WorkspaceSwitcher />
        <div className="h-4 w-px shrink-0 bg-salesos-border" />
        <UserNav />
      </div>
    </header>
  );
}
