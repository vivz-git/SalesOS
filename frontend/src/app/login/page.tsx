"use client";

import { type FormEvent, useState, Suspense } from"react";
import Link from"next/link";
import { useRouter, useSearchParams } from"next/navigation";

import { AuthCard } from"@/components/auth/auth-card";
import { AuthDivider } from"@/components/auth/auth-divider";
import { GoogleButton } from"@/components/auth/google-button";
import { PasswordInput } from"@/components/auth/password-input";
import { Button } from"@/components/ui/button";
import { createClient } from"@/lib/supabase/client";

function friendlyError(message: string): string {
 const lower = message.toLowerCase();
 if (lower.includes("invalid login credentials") || lower.includes("invalid credentials")) {
 return"Incorrect email or password. Please try again.";
 }
 if (lower.includes("email not confirmed")) {
 return"Please confirm your email address before signing in.";
 }
 if (lower.includes("too many requests")) {
 return"Too many sign-in attempts. Please wait a moment and try again.";
 }
 return message;
}

function LoginForm() {
 const router = useRouter();
 const searchParams = useSearchParams();
 const urlError = searchParams.get("error");

 const [error, setError] = useState<string | undefined>(
 urlError ? friendlyError(urlError) : undefined,
 );
 const [loading, setLoading] = useState(false);

 async function signIn(event: FormEvent<HTMLFormElement>) {
 event.preventDefault();
 if (loading) return;

 setLoading(true);
 setError(undefined);

 const form = new FormData(event.currentTarget);
 const { error: authError } = await createClient().auth.signInWithPassword({
 email: String(form.get("email")),
 password: String(form.get("password")),
 });

 if (authError) {
 setError(friendlyError(authError.message));
 setLoading(false);
 return;
 }

 router.replace("/");
 router.refresh();
 }

 return (
 <AuthCard
 title="Welcome back"
 description="Sign in to your SalesOS account"
 >
 <GoogleButton />

 <AuthDivider />

 <form onSubmit={signIn} className="grid gap-4"noValidate>
 <div className="grid gap-1">
 <label
 htmlFor="email"
 className="text-sm font-medium text-salesos-text-secondary"
 >
 Email
 </label>
 <input
 id="email"
 name="email"
 type="email"
 required
 autoComplete="email"
 disabled={loading}
 placeholder="you@company.com"
 className="rounded-md border border-salesos-border px-3 py-2 text-sm outline-none placeholder:text-salesos-text-secondary/60 disabled:opacity-50"
 />
 </div>

 <div className="grid gap-1">
 <div className="flex items-center justify-between">
 <label
 htmlFor="password"
 className="text-sm font-medium text-salesos-text-secondary"
 >
 Password
 </label>
 <Link
 href="/forgot-password"
 className="text-xs text-salesos-text-secondary hover:text-salesos-text"
 >
 Forgot password?
 </Link>
 </div>
 <PasswordInput
 id="password"
 name="password"
 required
 autoComplete="current-password"
 disabled={loading}
 placeholder="••••••••"
 />
 </div>

 {error && (
 <p className="text-sm text-salesos-danger"role="alert">
 {error}
 </p>
 )}

 <Button type="submit"disabled={loading} className="w-full">
 {loading ? (
 <span className="flex items-center gap-2">
 <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"/>
 Signing in…
 </span>
 ) : (
"Sign in"
 )}
 </Button>
 </form>

 <p className="mt-4 text-center text-sm text-salesos-text-secondary">
 Don&apos;t have an account?{""}
 <Link
 href="/signup"
 className="font-medium text-salesos-text hover:underline"
 >
 Create one
 </Link>
 </p>
 </AuthCard>
 );
}

export default function LoginPage() {
 return (
 <Suspense
 fallback={
 <div className="flex min-h-screen items-center justify-center bg-salesos-surface-muted">
 <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"/>
 </div>
 }
 >
 <LoginForm />
 </Suspense>
 );
}
