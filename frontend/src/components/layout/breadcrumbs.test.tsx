import { render, screen } from"@testing-library/react";
import { describe, expect, it, vi } from"vitest";

import { Breadcrumbs } from"./breadcrumbs";

vi.mock("@/lib/breadcrumb-store", () => ({
  useBreadcrumbOverride: () => null,
}));

vi.mock("next/navigation", () => ({
 usePathname: () =>"/campaigns",
}));

describe("Breadcrumbs Component", () => {
 it("renders home and current route segment accurately", () => {
 render(<Breadcrumbs />);

 expect(screen.getByText("Home")).toBeInTheDocument();
 expect(screen.getByText("Campaigns")).toBeInTheDocument();
 });
});
