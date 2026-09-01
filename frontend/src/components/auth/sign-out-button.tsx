"use client";

import { useRouter } from"next/navigation";

import { Button } from"@/components/ui/button";
import { createClient } from"@/lib/supabase/client";

export function SignOutButton() {
 const router = useRouter();
 async function signOut() {
 await createClient().auth.signOut();
 router.replace("/login");
 router.refresh();
 }
 return <Button onClick={signOut} variant="outline">Sign out</Button>;
}
