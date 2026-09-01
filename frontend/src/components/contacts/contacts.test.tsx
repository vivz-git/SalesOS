import { render, screen } from"@testing-library/react";
import { describe, expect, it } from"vitest";

import { ContactStatusBadge } from"./contact-status-badge";

describe("ContactStatusBadge Component", () => {
 it("renders active status badge correctly", () => {
 render(<ContactStatusBadge status="active"/>);
 expect(screen.getByText("Active")).toBeInTheDocument();
 });

 it("renders unresponsive status badge correctly", () => {
 render(<ContactStatusBadge status="unresponsive"/>);
 expect(screen.getByText("Unresponsive")).toBeInTheDocument();
 });

 it("renders opted out status badge correctly", () => {
 render(<ContactStatusBadge status="opted_out"/>);
 expect(screen.getByText("Opted Out")).toBeInTheDocument();
 });

 it("renders archived status badge correctly", () => {
 render(<ContactStatusBadge status="archived"/>);
 expect(screen.getByText("Archived")).toBeInTheDocument();
 });
});
