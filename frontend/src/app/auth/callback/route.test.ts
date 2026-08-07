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
    const request = new NextRequest("http://localhost:3000/auth/callback?code=test-auth-code");
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
});
