"use client";

import Link from"next/link";
import { usePathname } from"next/navigation";
import { ChevronRight, Home } from"lucide-react";

const ROUTE_NAME_MAP: Record<string, string> = {
 dashboard:"Dashboard",
 campaigns:"Campaigns",
 accounts:"Accounts",
 contacts:"Contacts",
 approvals:"Approval Queue",
 conversations:"Conversations",
 reports:"Reports",
 settings:"Settings",
};

export function Breadcrumbs() {
 const pathname = usePathname() ||"/";
 const segments = pathname.split("/").filter(Boolean);

 return (
 <nav aria-label="Breadcrumb"className="flex items-center gap-1 text-xs text-salesos-text-secondary">
 <Link
 href="/"
 className="flex items-center gap-1 hover:text-salesos-text transition-colors"
 >
 <Home className="h-3.5 w-3.5"/>
 <span>Home</span>
 </Link>

 {segments.map((segment, index) => {
 const href = `/${segments.slice(0, index + 1).join("/")}`;
 const isLast = index === segments.length - 1;
 const displayName =
 ROUTE_NAME_MAP[segment] ||
 segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g,"");

 return (
 <div key={href} className="flex items-center gap-1">
 <ChevronRight className="h-3.5 w-3.5 text-salesos-text-secondary/60"/>
 {isLast ? (
 <span className="font-medium text-salesos-text"aria-current="page">
 {displayName}
 </span>
 ) : (
 <Link href={href} className="hover:text-salesos-text transition-colors">
 {displayName}
 </Link>
 )}
 </div>
 );
 })}
 </nav>
 );
}
