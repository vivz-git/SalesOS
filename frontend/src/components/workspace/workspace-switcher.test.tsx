import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceSwitcher } from "./workspace-switcher";

const mockSetActiveWorkspaceId = vi.fn();
const mockCreateWorkspace = vi.fn();

vi.mock("@/lib/workspace-context", () => ({
  useWorkspace: () => ({
    workspaces: [
      { id: "ws-1", name: "Acme Corp", slug: "acme-corp" },
      { id: "ws-2", name: "Beta LLC", slug: "beta-llc" },
    ],
    activeWorkspace: { id: "ws-1", name: "Acme Corp", slug: "acme-corp" },
    setActiveWorkspaceId: mockSetActiveWorkspaceId,
    createWorkspace: mockCreateWorkspace,
  }),
}));

describe("WorkspaceSwitcher Component", () => {
  it("renders workspace switcher dropdown with accessible options", () => {
    render(<WorkspaceSwitcher />);

    const select = screen.getByRole("combobox", { name: /select workspace/i });
    expect(select).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Acme Corp" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Beta LLC" })).toBeInTheDocument();
  });
});
