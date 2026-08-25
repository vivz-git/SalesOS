import { NextRequest } from "next/server";
import { describe, expect, it, vi } from "vitest";

import { GET } from "./route";

const { mockExchangeCodeForSession } = vi.hoisted(() => ({
  mockExchangeCodeForSession: vi.fn(),
}));

vi.mock("@/lib/supabase/server", () => ({
  createClient: vi.fn().mockResolvedValue({
    auth: {
      exchangeCodeForSession: mockExchangeCodeForSession,
    },
  }),
}));

describe("OAuth Callback Route Handler", () => {
  it("exchanges code for session when code parameter is present", async () => {
    mockExchangeCodeForSession.mockResolvedValueOnce({ error: null });
    const request = new NextRequest(
      "http://localhost:3000/auth/callback?code=test-auth-code",
    );
    const response = await GET(request);

    expect(mockExchangeCodeForSession).toHaveBeenCalledWith("test-auth-code");
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("http://localhost:3000/");
  });

  it("redirects to home without code exchange when code is missing", async () => {
    mockExchangeCodeForSession.mockClear();
    const request = new NextRequest("http://localhost:3000/auth/callback");
    const response = await GET(request);

    expect(mockExchangeCodeForSession).not.toHaveBeenCalled();
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("http://localhost:3000/");
  });

  it("redirects to /login with error when OAuth error param is present", async () => {
    const request = new NextRequest(
      "http://localhost:3000/auth/callback?error=access_denied&error_description=User+cancelled+the+flow",
    );
    const response = await GET(request);

    expect(mockExchangeCodeForSession).not.toHaveBeenCalled();
    expect(response.status).toBe(307);
    const location = response.headers.get("location")!;
    expect(location).toContain("/login");
    expect(location).toContain("error=");
    expect(location).toContain("User+cancelled");
  });

  it("redirects to /login with error when code exchange fails", async () => {
    mockExchangeCodeForSession.mockResolvedValueOnce({
      error: { message: "Code has expired or already been used" },
    });
    const request = new NextRequest(
      "http://localhost:3000/auth/callback?code=bad-code",
    );
    const response = await GET(request);

    expect(response.status).toBe(307);
    const location = response.headers.get("location")!;
    expect(location).toContain("/login");
    expect(location).toContain("error=");
  });

  it("redirects to custom ?next= path after successful code exchange", async () => {
    mockExchangeCodeForSession.mockResolvedValueOnce({ error: null });
    const request = new NextRequest(
      "http://localhost:3000/auth/callback?code=good-code&next=/reset-password",
    );
    const response = await GET(request);

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/reset-password",
    );
  });

  it("ignores unsafe ?next= value and redirects to /", async () => {
    mockExchangeCodeForSession.mockResolvedValueOnce({ error: null });
    const request = new NextRequest(
      "http://localhost:3000/auth/callback?code=good-code&next=https://evil.com",
    );
    const response = await GET(request);

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("http://localhost:3000/");
  });
});
