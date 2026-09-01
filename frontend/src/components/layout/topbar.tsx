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
 <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white px-4 shadow-sm md:px-6">
 <div className="flex items-center gap-3">
 <button
 type="button"
 onClick={onToggleMobileSidebar}
 className="rounded-md p-1.5 text-slate-600 hover:bg-slate-100 hover:text-slate-900 md:hidden"
 aria-label="Open mobile menu"
 >
 <Menu className="h-5 w-5"/>
 </button>

 <div className="hidden sm:block">
 <Breadcrumbs />
 </div>
 </div>

 <div className="flex items-center gap-4">
 <WorkspaceSwitcher />
 <div className="h-4 w-px bg-slate-200"/>
 <UserNav />
 </div>
 </header>
 );
}
