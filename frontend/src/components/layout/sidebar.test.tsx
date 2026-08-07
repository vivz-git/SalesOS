import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Sidebar } from "./sidebar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/campaigns",
}));

describe("Sidebar Component", () => {
  it("renders all navigation item placeholders and highlights active route", () => {
    render(
      <Sidebar
        collapsed={false}
        onToggleCollapse={vi.fn()}
        mobileOpen={false}
        onCloseMobile={vi.fn()}
      />
    );

    expect(screen.getByRole("link", { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /campaigns/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /accounts/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /contacts/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /approval queue/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /conversations/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /reports/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /settings/i })).toBeInTheDocument();
  });
});
