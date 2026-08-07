import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "./page";

const { mockReplace, mockRefresh, mockSignInWithPassword } = vi.hoisted(() => ({
  mockReplace: vi.fn(),
  mockRefresh: vi.fn(),
  mockSignInWithPassword: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    refresh: mockRefresh,
  }),
}));

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      signInWithPassword: mockSignInWithPassword,
    },
  }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders login form and submits credentials successfully", async () => {
    mockSignInWithPassword.mockResolvedValueOnce({ error: null });

    render(<LoginPage />);

    expect(screen.getByRole("heading", { name: /sign in to salesos/i })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "password123" } });
    fireEvent.submit(screen.getByRole("button", { name: /sign in/i }).closest("form")!);

    await waitFor(() => {
      expect(mockSignInWithPassword).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "password123",
      });
      expect(mockReplace).toHaveBeenCalledWith("/");
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  it("displays error message on failed sign in", async () => {
    mockSignInWithPassword.mockResolvedValueOnce({ error: { message: "Invalid login credentials" } });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "wrongpassword" } });
    fireEvent.submit(screen.getByRole("button", { name: /sign in/i }).closest("form")!);

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid login credentials");
    expect(mockReplace).not.toHaveBeenCalled();
  });
});
