import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResearchStatusBadge } from "./research-status-badge";

describe("ResearchStatusBadge Component", () => {
  it("renders pending status badge correctly", () => {
    render(<ResearchStatusBadge status="pending" />);
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("renders in_progress status badge correctly", () => {
    render(<ResearchStatusBadge status="in_progress" />);
    expect(screen.getByText("In Progress")).toBeInTheDocument();
  });

  it("renders completed status badge correctly", () => {
    render(<ResearchStatusBadge status="completed" />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("renders failed status badge correctly", () => {
    render(<ResearchStatusBadge status="failed" />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });
});
