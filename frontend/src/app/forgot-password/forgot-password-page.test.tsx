import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ForgotPasswordPage from "./page";

const { mockResetPasswordForEmail } = vi.hoisted(() => ({
  mockResetPasswordForEmail: vi.fn(),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [k: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      resetPasswordForEmail: mockResetPasswordForEmail,
    },
  }),
}));

describe("ForgotPasswordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window, "location", {
      value: { origin: "http://localhost:3000" },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders forgot password form with email field and send button", () => {
    render(<ForgotPasswordPage />);

    expect(
      screen.getByRole("heading", { name: /forgot password/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /send reset link/i }),
    ).toBeInTheDocument();
  });

  it("renders back to sign in link", () => {
    render(<ForgotPasswordPage />);
    const link = screen.getByRole("link", { name: /sign in/i });
    expect(link).toHaveAttribute("href", "/login");
  });

  it("shows success state after sending reset link", async () => {
    mockResetPasswordForEmail.mockResolvedValueOnce({ error: null });

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.submit(
      screen
        .getByRole("button", { name: /send reset link/i })
        .closest("form")!,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /check your email/i }),
      ).toBeInTheDocument();
    });

    expect(mockResetPasswordForEmail).toHaveBeenCalledWith(
      "user@example.com",
      expect.objectContaining({
        redirectTo: expect.stringContaining("/reset-password"),
      }),
    );
  });

  it("passes correct redirectTo through /auth/callback", async () => {
    mockResetPasswordForEmail.mockResolvedValueOnce({ error: null });

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.submit(
      screen
        .getByRole("button", { name: /send reset link/i })
        .closest("form")!,
    );

    await waitFor(() => {
      expect(mockResetPasswordForEmail).toHaveBeenCalledWith(
        "user@example.com",
        {
          redirectTo:
            "http://localhost:3000/auth/callback?next=/reset-password",
        },
      );
    });
  });

  it("displays error when reset email fails", async () => {
    mockResetPasswordForEmail.mockResolvedValueOnce({
      error: { message: "Unable to send email" },
    });

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.submit(
      screen
        .getByRole("button", { name: /send reset link/i })
        .closest("form")!,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /unable to send email/i,
    );
  });
});
