import { type NextRequest, NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  if (code) (await createClient()).auth.exchangeCodeForSession(code);
  return NextResponse.redirect(new URL("/", request.url));
}
