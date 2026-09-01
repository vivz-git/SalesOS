import { render, screen } from"@testing-library/react";
import { describe, expect, it } from"vitest";

import { CampaignStatusBadge } from"./campaign-status-badge";

describe("CampaignStatusBadge Component", () => {
 it("renders draft status badge correctly", () => {
 render(<CampaignStatusBadge status="draft"/>);
 expect(screen.getByText("Draft")).toBeInTheDocument();
 });

 it("renders active status badge correctly", () => {
 render(<CampaignStatusBadge status="active"/>);
 expect(screen.getByText("Active")).toBeInTheDocument();
 });

 it("renders paused status badge correctly", () => {
 render(<CampaignStatusBadge status="paused"/>);
 expect(screen.getByText("Paused")).toBeInTheDocument();
 });

 it("renders archived status badge correctly", () => {
 render(<CampaignStatusBadge status="archived"/>);
 expect(screen.getByText("Archived")).toBeInTheDocument();
 });
});
