"use client";

import Link from"next/link";
import { usePathname } from"next/navigation";
import {
 CheckCircle2,
 ChevronLeft,
 ChevronRight,
 LayoutDashboard,
 Settings,
 Users,
 X,
 Inbox,
} from"lucide-react";

export interface NavItem {
 name: string;
 href: string;
 icon: React.ComponentType<{ className?: string }>;
}

export const NAVIGATION_ITEMS: NavItem[] = [
 { name:"Dashboard", href:"/", icon: LayoutDashboard },
 { name:"Prospects", href:"/prospects", icon: Users },
 { name:"Approvals", href:"/approvals", icon: CheckCircle2 },
 { name:"Inbox", href:"/inbox", icon: Inbox },
 { name:"Settings", href:"/settings", icon: Settings },
];

interface SidebarProps {
 collapsed: boolean;
 onToggleCollapse: () => void;
 mobileOpen: boolean;
 onCloseMobile: () => void;
}

export function Sidebar({
 collapsed,
 onToggleCollapse,
 mobileOpen,
 onCloseMobile,
}: SidebarProps) {
 const pathname = usePathname() ||"/";

 function isItemActive(href: string) {
 if (href ==="/") return pathname ==="/";
 return pathname.startsWith(href);
 }

 const content = (
 <div className="flex h-full flex-col justify-between py-4">
 <div>
 <div className="flex items-center justify-between px-4 pb-4">
 <Link href="/"className="flex items-center gap-2 font-bold text-slate-900">
 <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-xs font-black text-white">
 OS
 </span>
 {!collapsed && <span className="text-base tracking-tight">SalesOS</span>}
 </Link>

 <button
 type="button"
 onClick={onCloseMobile}
 className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 md:hidden"
 aria-label="Close menu"
 >
 <X className="h-5 w-5"/>
 </button>
 </div>

 <nav aria-label="Sidebar"className="mt-2 grid gap-1 px-2">
 {NAVIGATION_ITEMS.map((item) => {
 const Icon = item.icon;
 const active = isItemActive(item.href);

 return (
 <Link
 key={item.href}
 href={item.href}
 onClick={onCloseMobile}
 className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
 active
 ?"bg-accent text-white"
 :"text-slate-600 hover:bg-slate-100 hover:text-slate-900"
 }`}
 title={collapsed ? item.name : undefined}
 >
 <Icon className={`h-5 w-5 shrink-0 ${active ?"text-white":"text-slate-500 group-hover:text-slate-900"}`} />
 {!collapsed && <span>{item.name}</span>}
 </Link>
 );
 })}
 </nav>
 </div>

 <div className="hidden border-t border-slate-200 p-2 md:block">
 <button
 type="button"
 onClick={onToggleCollapse}
 className="flex w-full items-center justify-center rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
 aria-label={collapsed ?"Expand sidebar":"Collapse sidebar"}
 >
 {collapsed ? <ChevronRight className="h-5 w-5"/> : <ChevronLeft className="h-5 w-5"/>}
 </button>
 </div>
 </div>
 );

 return (
 <>
 {/* Desktop Sidebar */}
 <aside
 className={`hidden border-r border-slate-200 bg-white transition-all duration-300 md:block ${
 collapsed ?"w-16":"w-64"
 }`}
 >
 {content}
 </aside>

 {/* Mobile Drawer Overlay */}
 {mobileOpen && (
 <div className="fixed inset-0 z-40 md:hidden">
 <div
 className="fixed inset-0 bg-black/30 transition-opacity"
 onClick={onCloseMobile}
 />
 <aside className="relative z-50 h-full w-64 border-r border-slate-200 bg-white shadow-xl">
 {content}
 </aside>
 </div>
 )}
 </>
 );
}
