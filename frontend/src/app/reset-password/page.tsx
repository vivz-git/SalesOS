"use client";

import { type FormEvent, useEffect, useState } from"react";
import Link from"next/link";
import { useRouter } from"next/navigation";
import { CheckCircle2 } from"lucide-react";

import { AuthCard } from"@/components/auth/auth-card";
import { PasswordInput } from"@/components/auth/password-input";
import { PasswordStrength } from"@/components/auth/password-strength";
import { Button } from"@/components/ui/button";
import { createClient } from"@/lib/supabase/client";

type PageState ="checking"|"no-session"|"ready"|"success";

export default function ResetPasswordPage() {
 const router = useRouter();
 const [pageState, setPageState] = useState<PageState>("checking");
 const [password, setPassword] = useState("");
 const [confirm, setConfirm] = useState("");
 const [error, setError] = useState<string | undefined>();
 const [loading, setLoading] = useState(false);

 useEffect(() => {
 async function checkRecoverySession() {
 const supabase = createClient();
 const {
 data: { session },
 } = await supabase.auth.getSession();
 setPageState(session ?"ready":"no-session");
 }
 checkRecoverySession();
 }, []);

 async function handleSubmit(event: FormEvent<HTMLFormElement>) {
 event.preventDefault();
 if (loading) return;

 if (password !== confirm) {
 setError("Passwords do not match.");
 return;
 }
 if (password.length < 8) {
 setError("Password must be at least 8 characters.");
 return;
 }

 setLoading(true);
 setError(undefined);

 const supabase = createClient();
 const { error: authError } = await supabase.auth.updateUser({ password });

 if (authError) {
 setError(authError.message);
 setLoading(false);
 return;
 }

 setPageState("success");
 // Sign out the recovery session so the user logs in fresh
 await supabase.auth.signOut();
 setTimeout(() => router.replace("/login"), 2500);
 }

 if (pageState ==="checking") {
 return (
 <AuthCard title="Reset password">
 <div className="flex items-center justify-center py-10"aria-busy="true">
 <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"/>
 </div>
 </AuthCard>
 );
 }

 if (pageState ==="no-session") {
 return (
 <AuthCard
 title="Link expired"
 description="Your password reset link has expired or is invalid."
 >
 <div className="flex flex-col items-center gap-3 py-2 text-center">
 <p className="text-sm text-slate-500">
 Request a new link and try again.
 </p>
 <Link
 href="/forgot-password"
 className="text-sm font-medium text-slate-900 hover:underline"
 >
 Request new reset link
 </Link>
 </div>
 </AuthCard>
 );
 }

 if (pageState ==="success") {
 return (
 <AuthCard
 title="Password updated"
 description="Your password has been updated. Redirecting you to sign in…"
 >
 <div className="flex flex-col items-center gap-4 py-4 text-center">
 <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-50">
 <CheckCircle2 className="h-6 w-6 text-green-600"aria-hidden="true"/>
 </div>
 </div>
 </AuthCard>
 );
 }

 return (
 <AuthCard
 title="Set new password"
 description="Choose a strong password for your account."
 >
 <form onSubmit={handleSubmit} className="grid gap-4"noValidate>
 <div className="grid gap-1">
 <label
 htmlFor="password"
 className="text-sm font-medium text-slate-700"
 >
 New password
 </label>
 <PasswordInput
 id="password"
 name="password"
 required
 autoComplete="new-password"
 disabled={loading}
 placeholder="••••••••"
 value={password}
 onChange={(e) => setPassword(e.target.value)}
 />
 <PasswordStrength password={password} />
 </div>

 <div className="grid gap-1">
 <label
 htmlFor="confirm-password"
 className="text-sm font-medium text-slate-700"
 >
 Confirm password
 </label>
 <PasswordInput
 id="confirm-password"
 name="confirm-password"
 required
 autoComplete="new-password"
 disabled={loading}
 placeholder="••••••••"
 value={confirm}
 onChange={(e) => setConfirm(e.target.value)}
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
 Updating…
 </span>
 ) : (
"Update password"
 )}
 </Button>
 </form>
 </AuthCard>
 );
}
