import { NextResponse, type NextRequest } from"next/server";

import { updateSession } from"@/lib/supabase/middleware";

/**
 * Routes that unauthenticated users may access freely.
 * /reset-password is public because the user arrives here from the
 * password-reset email callback with a recovery session already set.
 */
const PUBLIC_PATHS = new Set([
"/login",
"/signup",
"/forgot-password",
"/reset-password",
"/auth/callback",
]);

/**
 * Routes where an already-authenticated user should be redirected to the
 * dashboard. /reset-password is intentionally excluded: an authenticated
 * user with a recovery session must be allowed to update their password.
 */
const AUTH_REDIRECT_PATHS = new Set(["/login","/signup","/forgot-password"]);

export async function middleware(request: NextRequest) {
 const { authenticated, response } = await updateSession(request);
 const { pathname } = request.nextUrl;

 if (!authenticated && !PUBLIC_PATHS.has(pathname)) {
 const url = request.nextUrl.clone();
 url.pathname ="/login";
 return NextResponse.redirect(url);
 }

 if (authenticated && AUTH_REDIRECT_PATHS.has(pathname)) {
 const url = request.nextUrl.clone();
 url.pathname ="/";
 return NextResponse.redirect(url);
 }

 return response;
}

export const config = {
 matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
