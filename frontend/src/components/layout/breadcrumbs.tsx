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
      className="flex min-w-0 items-center gap-1 text-xs text-salesos-text-secondary overflow-hidden"
    >
      {/* Home — always shrink-0; short and must never be truncated */}
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
              displayName = overrideLabel || "Campaign";
            } else if (parentSegment === "accounts") {
              displayName = overrideLabel || "Account";
            } else if (parentSegment === "deliveries") {
              displayName = overrideLabel || "Delivery";
            } else if (parentSegment === "research") {
              displayName = overrideLabel || "Research";
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
          <div key={href + index} className="flex min-w-0 shrink items-center gap-1">
            {/* Separator: always visible, never shrinks */}
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-salesos-text-secondary/60" />
            {isLast ? (
              /* Final segment: truncates with ellipsis, surrenders space first */
              <span
                className="min-w-0 truncate font-medium text-salesos-text max-w-[90px] sm:max-w-[130px] md:max-w-[180px] lg:max-w-[260px] xl:max-w-[360px]"
                aria-current="page"
                title={displayName}
              >
                {displayName}
              </span>
            ) : (
              /* Intermediate segments: bounded, shrinkable, truncate if needed */
              <Link
                href={href}
                className="block min-w-0 shrink truncate hover:text-salesos-text transition-colors max-w-[70px] sm:max-w-[90px] md:max-w-[110px] lg:max-w-[140px] xl:max-w-[160px]"
                title={displayName}
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
