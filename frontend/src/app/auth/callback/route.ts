import { type NextRequest, NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

/**
 * Validates that a redirect destination is a safe, same-origin relative path.
 * Prevents open redirect attacks.
 */
function safeNextPath(next: string | null): string {
  if (
    next &&
    next.startsWith("/") &&
    !next.startsWith("//") &&
    !next.includes(":")
  ) {
    return next;
  }
  return "/";
}

export async function GET(request: NextRequest) {
  const { searchParams, origin } = request.nextUrl;

  // Surface OAuth provider errors to the user.
  const oauthError = searchParams.get("error");
  const oauthErrorDescription = searchParams.get("error_description");
  if (oauthError) {
    const url = new URL("/login", origin);
    url.searchParams.set(
      "error",
      oauthErrorDescription ?? oauthError,
    );
    return NextResponse.redirect(url);
  }

  const code = searchParams.get("code");
  if (code) {
    const supabase = await createClient();
    const { error: exchangeError } =
      await supabase.auth.exchangeCodeForSession(code);
    if (exchangeError) {
      const url = new URL("/login", origin);
      url.searchParams.set("error", exchangeError.message);
      return NextResponse.redirect(url);
    }
  }

  // Honour an optional ?next= param (e.g. /auth/callback?next=/reset-password
  // sent by the forgot-password flow). Validate to prevent open redirects.
  const next = safeNextPath(searchParams.get("next"));
  return NextResponse.redirect(new URL(next, origin));
}
