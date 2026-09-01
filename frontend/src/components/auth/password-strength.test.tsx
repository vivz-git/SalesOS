import { cleanup, render, screen } from"@testing-library/react";
import { afterEach, describe, expect, it } from"vitest";

import {
 getPasswordStrength,
 PasswordStrength,
} from"./password-strength";

describe("getPasswordStrength", () => {
 it("returns score 0 and empty label for empty password", () => {
 const result = getPasswordStrength("");
 expect(result.score).toBe(0);
 expect(result.label).toBe("");
 });

 it("scores 1 (Weak) for only lowercase, short password", () => {
 // only lowercase: 1 point
 const result = getPasswordStrength("abc");
 expect(result.score).toBe(1);
 expect(result.label).toBe("Weak");
 });

 it("scores 2 (Fair) for lowercase + uppercase", () => {
 const result = getPasswordStrength("Abc");
 expect(result.score).toBe(2);
 expect(result.label).toBe("Fair");
 });

 it("scores 4 (Strong) for length>=8 + upper + lower + number", () => {
 const result = getPasswordStrength("Password1");
 expect(result.score).toBe(4);
 expect(result.label).toBe("Strong");
 });

 it("scores 5 (Strong) for all criteria met", () => {
 const result = getPasswordStrength("MyP@ssword1!");
 expect(result.score).toBe(5);
 expect(result.label).toBe("Strong");
 });
});

describe("PasswordStrength component", () => {
 afterEach(() => {
 cleanup();
 });

 it("renders nothing when password is empty", () => {
 const { container } = render(<PasswordStrength password=""/>);
 expect(container.firstChild).toBeNull();
 });

 it("renders Weak label for simple short password", () => {
 render(<PasswordStrength password="abc"/>);
 expect(screen.getByText(/weak/i)).toBeInTheDocument();
 });

 it("renders Strong label for complex password", () => {
 render(<PasswordStrength password="MyP@ssword1!"/>);
 expect(screen.getByText(/strong/i)).toBeInTheDocument();
 });

 it("renders strength bar segments", () => {
 render(<PasswordStrength password="TestPass"/>);
 // aria-label includes the strength
 const region = screen.getByLabelText(/password strength/i);
 expect(region).toBeInTheDocument();
 });
});
