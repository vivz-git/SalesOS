"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string>();

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const { error } = await createClient().auth.signInWithPassword({
      email: String(form.get("email")),
      password: String(form.get("password")),
    });
    if (error) return setError(error.message);
    router.replace("/");
    router.refresh();
  }

  return (
    <main className="grid min-h-screen place-items-center p-6">
      <form className="grid w-full max-w-sm gap-4" onSubmit={signIn}>
        <h1 className="text-xl font-semibold">Sign in to SalesOS</h1>
        <label className="grid gap-1 text-sm">Email<input required name="email" type="email" className="rounded-md border p-2" /></label>
        <label className="grid gap-1 text-sm">Password<input required name="password" type="password" className="rounded-md border p-2" /></label>
        {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
        <Button type="submit">Sign in</Button>
      </form>
    </main>
  );
}
