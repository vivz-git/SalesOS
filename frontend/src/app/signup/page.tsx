"use client";

import { type FormEvent, useState } from"react";
import Link from"next/link";
import { useRouter } from"next/navigation";
import { CheckCircle2 } from"lucide-react";

import { AuthCard } from"@/components/auth/auth-card";
import { AuthDivider } from"@/components/auth/auth-divider";
import { GoogleButton } from"@/components/auth/google-button";
import { PasswordInput } from"@/components/auth/password-input";
import { PasswordStrength } from"@/components/auth/password-strength";
import { Button } from"@/components/ui/button";
import { createClient } from"@/lib/supabase/client";

function friendlySignupError(message: string): string {
 const lower = message.toLowerCase();
 if (lower.includes("user already registered")) {
 return"An account with this email already exists. Try signing in instead.";
 }
 if (lower.includes("password should be at least")) {
 return"Password must be at least 8 characters.";
 }
 if (lower.includes("unable to validate email address")) {
 return"Please enter a valid email address.";
 }
 return message;
}

export default function SignupPage() {
 const router = useRouter();
 const [password, setPassword] = useState("");
 const [error, setError] = useState<string | undefined>();
 const [loading, setLoading] = useState(false);
 const [emailSent, setEmailSent] = useState(false);
 const [sentEmail, setSentEmail] = useState("");

 async function handleSignup(event: FormEvent<HTMLFormElement>) {
 event.preventDefault();
 if (loading) return;

 const form = new FormData(event.currentTarget);
 const email = String(form.get("email"));
 const pw = String(form.get("password"));
 const confirm = String(form.get("confirm-password"));

 if (pw !== confirm) {
 setError("Passwords do not match.");
 return;
 }
 if (pw.length < 8) {
 setError("Password must be at least 8 characters.");
 return;
 }

 setLoading(true);
 setError(undefined);

 const supabase = createClient();
 const { data, error: authError } = await supabase.auth.signUp({
 email,
 password: pw,
 });

 if (authError) {
 setError(friendlySignupError(authError.message));
 setLoading(false);
 return;
 }

 // Email confirmation required (data.session is null until confirmed)
 if (data.user && !data.session) {
 setSentEmail(email);
 setEmailSent(true);
 return;
 }

 // Email confirmation disabled — session exists, go to dashboard
 router.replace("/");
 router.refresh();
 }

 if (emailSent) {
 return (
 <AuthCard
 title="Check your email"
 description={`We sent a confirmation link to ${sentEmail}`}
 >
 <div className="flex flex-col items-center gap-4 py-4 text-center">
 <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-50">
 <CheckCircle2 className="h-6 w-6 text-green-600"aria-hidden="true"/>
 </div>
 <p className="text-sm text-slate-500">
 Click the link in your email to activate your account. Check
 your spam folder if you don&apos;t see it within a few minutes.
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
 title="Create your account"
 description="Start your SalesOS journey today."
 >
 <GoogleButton />

 <AuthDivider />

 <form onSubmit={handleSignup} className="grid gap-4"noValidate>
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
 className="rounded-md border border-slate-200 px-3 py-2 text-sm outline-none placeholder:text-slate-400 disabled:opacity-50"
 />
 </div>

 <div className="grid gap-1">
 <label
 htmlFor="password"
 className="text-sm font-medium text-slate-700"
 >
 Password
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
 Creating account…
 </span>
 ) : (
"Create account"
 )}
 </Button>
 </form>

 <p className="mt-4 text-center text-sm text-slate-500">
 Already have an account?{""}
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
