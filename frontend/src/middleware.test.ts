import { NextRequest, NextResponse } from "next/server";
import { describe, expect, it, vi } from "vitest";

import { updateSession } from "@/lib/supabase/middleware";
import { middleware } from "@/middleware";

vi.mock("@/lib/supabase/middleware", () => ({
  updateSession: vi.fn(),
}));

describe("Auth Middleware", () => {
  it("redirects unauthenticated user from protected route to /login", async () => {
    vi.mocked(updateSession).mockResolvedValueOnce({
      response: NextResponse.next(),
      authenticated: false,
    });

    const request = new NextRequest("http://localhost:3000/");
    const response = await middleware(request);

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("http://localhost:3000/login");
  });

  it("allows unauthenticated user to access public route /login", async () => {
    const mockRes = NextResponse.next();
    vi.mocked(updateSession).mockResolvedValueOnce({
      response: mockRes,
      authenticated: false,
    });

    const request = new NextRequest("http://localhost:3000/login");
    const response = await middleware(request);

    expect(response).toBe(mockRes);
  });

  it("redirects authenticated user from /login to /", async () => {
    vi.mocked(updateSession).mockResolvedValueOnce({
      response: NextResponse.next(),
      authenticated: true,
    });

    const request = new NextRequest("http://localhost:3000/login");
    const response = await middleware(request);

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("http://localhost:3000/");
  });

  it("allows authenticated user to access protected route", async () => {
    const mockRes = NextResponse.next();
    vi.mocked(updateSession).mockResolvedValueOnce({
      response: mockRes,
      authenticated: true,
    });

    const request = new NextRequest("http://localhost:3000/");
    const response = await middleware(request);

    expect(response).toBe(mockRes);
  });
});
