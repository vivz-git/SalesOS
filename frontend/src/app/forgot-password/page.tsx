"use client";

import { type FormEvent, useState } from"react";
import Link from"next/link";
import { CheckCircle2 } from"lucide-react";

import { AuthCard } from"@/components/auth/auth-card";
import { Button } from"@/components/ui/button";
import { createClient } from"@/lib/supabase/client";

export default function ForgotPasswordPage() {
 const [email, setEmail] = useState("");
 const [error, setError] = useState<string | undefined>();
 const [loading, setLoading] = useState(false);
 const [sent, setSent] = useState(false);

 async function handleSubmit(event: FormEvent<HTMLFormElement>) {
 event.preventDefault();
 if (loading) return;

 setLoading(true);
 setError(undefined);

 const supabase = createClient();
 const { error: authError } = await supabase.auth.resetPasswordForEmail(
 email,
 {
 // After the user clicks the link Supabase sends, they land at
 // /auth/callback which exchanges the code for a recovery session and
 // then redirects to /reset-password via the ?next= param.
 redirectTo: `${window.location.origin}/auth/callback?next=/reset-password`,
 },
 );

 if (authError) {
 setError(authError.message);
 setLoading(false);
 return;
 }

 setSent(true);
 }

 if (sent) {
 return (
 <AuthCard
 title="Check your email"
 description={`We sent a password reset link to ${email}`}
 >
 <div className="flex flex-col items-center gap-4 py-4 text-center">
 <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-50">
 <CheckCircle2 className="h-6 w-6 text-green-600"aria-hidden="true"/>
 </div>
 <p className="text-sm text-slate-500">
 Click the link in your email to reset your password. Check your
 spam folder if you don&apos;t see it within a few minutes.
 </p>
 <Link
 href="/login"
 className="text-sm font-medium text-slate-900 hover:underline"
 >
 Back to sign in
 </Link>
 </div>
 </AuthCard>
 );
 }

 return (
 <AuthCard
 title="Forgot password"
 description="Enter your email and we'll send you a reset link."
 >
 <form onSubmit={handleSubmit} className="grid gap-4"noValidate>
 <div className="grid gap-1">
 <label
 htmlFor="email"
 className="text-sm font-medium text-slate-700"
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
 value={email}
 onChange={(e) => setEmail(e.target.value)}
 className="rounded-md border border-slate-200 px-3 py-2 text-sm outline-none placeholder:text-slate-400 disabled:opacity-50"
 />
 </div>

 {error && (
 <p className="text-sm text-red-600"role="alert">
 {error}
 </p>
 )}

 <Button type="submit"disabled={loading} className="w-full">
 {loading ? (
 <span className="flex items-center gap-2">
 <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"/>
 Sending…
 </span>
 ) : (
"Send reset link"
 )}
 </Button>
 </form>

 <p className="mt-4 text-center text-sm text-slate-500">
 Remember your password?{""}
 <Link
 href="/login"
 className="font-medium text-slate-900 hover:underline"
 >
 Sign in
 </Link>
 </p>
 </AuthCard>
 );
}
