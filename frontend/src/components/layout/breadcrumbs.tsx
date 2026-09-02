"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";
import { useBreadcrumbOverride } from "@/lib/breadcrumb-store";

const ROUTE_NAME_MAP: Record<string, string> = {
  dashboard: "Dashboard",
  campaigns: "Campaigns",
  accounts: "Accounts",
  contacts: "Prospects",
  prospects: "Prospects",
  approvals: "Approvals",
  conversations: "Conversations",
  inbox: "Inbox",
  reports: "Reports",
  settings: "Settings",
  outreach: "Outreach",
  research: "Research",
  deliveries: "Deliveries",
};

function isIdSegment(segment: string): boolean {
  return (
    /^[0-9a-fA-F]{32}$/.test(segment) ||
    /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(segment) ||
    (/^[0-9a-fA-F-]{16,}$/.test(segment) && !ROUTE_NAME_MAP[segment.toLowerCase()])
  );
}

export function Breadcrumbs() {
  const pathname = usePathname() || "/";
  const segments = pathname.split("/").filter(Boolean);
  const overrideLabel = useBreadcrumbOverride();

  return (
    <nav
      aria-label="Breadcrumb"
      className="flex min-w-0 items-center gap-1 text-xs text-salesos-text-secondary"
    >
      <Link
        href="/"
        className="flex shrink-0 items-center gap-1 hover:text-salesos-text transition-colors"
      >
        <Home className="h-3.5 w-3.5" />
        <span>Home</span>
      </Link>

      {segments.map((segment, index) => {
        const isLast = index === segments.length - 1;
        const parentSegment = index > 0 ? segments[index - 1] : "";
        const isId = isIdSegment(segment);

        let displayName = ROUTE_NAME_MAP[segment];

        if (!displayName) {
          if (isLast && overrideLabel) {
            displayName = overrideLabel;
          } else if (isId || parentSegment === "conversations") {
            if (parentSegment === "conversations") {
              displayName = overrideLabel || "Thread";
            } else if (parentSegment === "contacts" || parentSegment === "prospects") {
              displayName = overrideLabel || "Prospect";
            } else if (parentSegment === "approvals") {
              displayName = overrideLabel || "Review";
            } else if (parentSegment === "campaigns") {
              displayName = overrideLabel || "Campaign Detail";
            } else if (parentSegment === "accounts") {
              displayName = overrideLabel || "Account Detail";
            } else if (parentSegment === "deliveries") {
              displayName = overrideLabel || "Delivery Detail";
            } else if (parentSegment === "research") {
              displayName = overrideLabel || "Research Detail";
            } else {
              displayName = overrideLabel || "Details";
            }
          } else {
            displayName =
              segment.charAt(0).toUpperCase() +
              segment.slice(1).replace(/-/g, " ");
          }
        } else if (isLast && overrideLabel) {
          displayName = overrideLabel;
        }

        let href = `/${segments.slice(0, index + 1).join("/")}`;
        if (segment === "contacts") {
          href = "/prospects";
        }

        return (
          <div key={href + index} className="flex min-w-0 items-center gap-1">
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-salesos-text-secondary/60" />
            {isLast ? (
              <span
                className="truncate font-medium text-salesos-text max-w-[120px] md:max-w-[160px] lg:max-w-[320px] xl:max-w-none"
                aria-current="page"
                title={displayName}
              >
                {displayName}
              </span>
            ) : (
              <Link
                href={href}
                className="shrink-0 hover:text-salesos-text transition-colors"
              >
                {displayName}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
