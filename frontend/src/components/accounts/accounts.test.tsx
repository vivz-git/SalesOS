import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AccountStatusBadge } from "./account-status-badge";

describe("AccountStatusBadge Component", () => {
  it("renders target status badge correctly", () => {
    render(<AccountStatusBadge status="target" />);
    expect(screen.getByText("Target")).toBeInTheDocument();
  });

  it("renders qualified status badge correctly", () => {
    render(<AccountStatusBadge status="qualified" />);
    expect(screen.getByText("Qualified")).toBeInTheDocument();
  });

  it("renders disqualified status badge correctly", () => {
    render(<AccountStatusBadge status="disqualified" />);
    expect(screen.getByText("Disqualified")).toBeInTheDocument();
  });

  it("renders archived status badge correctly", () => {
    render(<AccountStatusBadge status="archived" />);
    expect(screen.getByText("Archived")).toBeInTheDocument();
  });
});
