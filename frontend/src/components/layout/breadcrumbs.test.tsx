import { cleanup, render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { Breadcrumbs } from "./breadcrumbs";

let mockPathname = "/campaigns";
let mockOverride: string | null = null;

vi.mock("@/lib/breadcrumb-store", () => ({
  useBreadcrumbOverride: () => mockOverride,
}));

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

describe("Breadcrumbs Component", () => {
  beforeEach(() => {
    mockPathname = "/campaigns";
    mockOverride = null;
  });

  afterEach(() => {
    cleanup();
  });

  it("renders home and current route segment accurately", () => {
    render(<Breadcrumbs />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Campaigns")).toBeInTheDocument();
  });

  it("hides raw conversation UUID and displays Thread", () => {
    mockPathname = "/conversations/9202bba44f6f4ef49e38b5d274e3af83";
    render(<Breadcrumbs />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Conversations")).toBeInTheDocument();
    expect(screen.getByText("Thread")).toBeInTheDocument();
    expect(screen.queryByText("9202bba44f6f4ef49e38b5d274e3af83")).not.toBeInTheDocument();
  });

  it("displays prospect name instead of contact UUID when override is set", () => {
    mockPathname = "/contacts/d3b07384-d113-4632-a548-067f975cf643";
    mockOverride = "Alex Buyer";
    render(<Breadcrumbs />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Prospects")).toBeInTheDocument();
    expect(screen.getByText("Alex Buyer")).toBeInTheDocument();
    expect(screen.queryByText("d3b07384-d113-4632-a548-067f975cf643")).not.toBeInTheDocument();
  });

  it("hides raw approval draft UUID and displays Review", () => {
    mockPathname = "/approvals/b8c38827-0245-42cf-9b37-2900742f5341";
    render(<Breadcrumbs />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Approvals")).toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(screen.queryByText("b8c38827-0245-42cf-9b37-2900742f5341")).not.toBeInTheDocument();
  });
});
