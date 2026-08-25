import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SignupPage from "./page";

const { mockReplace, mockRefresh, mockSignUp, mockSignInWithOAuth } =
  vi.hoisted(() => ({
    mockReplace: vi.fn(),
    mockRefresh: vi.fn(),
    mockSignUp: vi.fn(),
    mockSignInWithOAuth: vi.fn(),
  }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace, refresh: mockRefresh }),
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
      signUp: mockSignUp,
      signInWithOAuth: mockSignInWithOAuth,
    },
  }),
}));

describe("SignupPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders signup form with all required fields and Google button", () => {
    render(<SignupPage />);

    expect(
      screen.getByRole("heading", { name: /create your account/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^confirm password$/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /continue with google/i }),
    ).toBeInTheDocument();
  });

  it("shows error when passwords do not match", async () => {
    render(<SignupPage />);

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "Password123!" },
    });
    fireEvent.change(screen.getByLabelText(/^confirm password$/i), {
      target: { value: "Different123!" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /create account/i }).closest("form")!,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /passwords do not match/i,
    );
    expect(mockSignUp).not.toHaveBeenCalled();
  });

  it("shows error when password is too short", async () => {
    render(<SignupPage />);

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "short" },
    });
    fireEvent.change(screen.getByLabelText(/^confirm password$/i), {
      target: { value: "short" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /create account/i }).closest("form")!,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /at least 8 characters/i,
    );
    expect(mockSignUp).not.toHaveBeenCalled();
  });

  it("shows email confirmation state when signup requires email verification", async () => {
    mockSignUp.mockResolvedValueOnce({
      data: {
        user: { id: "uid", email: "user@example.com" },
        session: null,
      },
      error: null,
    });

    render(<SignupPage />);

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "Password123!" },
    });
    fireEvent.change(screen.getByLabelText(/^confirm password$/i), {
      target: { value: "Password123!" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /create account/i }).closest("form")!,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /check your email/i }),
      ).toBeInTheDocument();
    });
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("redirects to dashboard when email confirmation is disabled (session returned)", async () => {
    mockSignUp.mockResolvedValueOnce({
      data: {
        user: { id: "uid" },
        session: { access_token: "tok" },
      },
      error: null,
    });

    render(<SignupPage />);

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "Password123!" },
    });
    fireEvent.change(screen.getByLabelText(/^confirm password$/i), {
      target: { value: "Password123!" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /create account/i }).closest("form")!,
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/");
    });
  });

  it("displays friendly error when email already registered", async () => {
    mockSignUp.mockResolvedValueOnce({
      data: { user: null, session: null },
      error: { message: "User already registered" },
    });

    render(<SignupPage />);

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "existing@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "Password123!" },
    });
    fireEvent.change(screen.getByLabelText(/^confirm password$/i), {
      target: { value: "Password123!" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /create account/i }).closest("form")!,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(/already exists/i);
  });
});
