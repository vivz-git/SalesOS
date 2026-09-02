"use client";

import { useEffect, useState } from"react";
import { User } from"lucide-react";

import { SignOutButton } from"@/components/auth/sign-out-button";
import { useWorkspace } from"@/lib/workspace-context";
import { createClient } from"@/lib/supabase/client";

interface UserIdentity {
 user_id: string;
 email: string | null;
 workspace_id: string;
 role: string;
}

export function UserNav() {
 const { activeWorkspace } = useWorkspace();
 const [identity, setIdentity] = useState<UserIdentity | null>(null);

 useEffect(() => {
 if (!activeWorkspace) return;

 async function fetchIdentity() {
 const supabase = createClient();
 const { data: { session } } = await supabase.auth.getSession();

 const headers = new Headers();
 headers.set("X-SalesOS-Workspace-Id", activeWorkspace!.id);
 if (session?.access_token) {
 headers.set("Authorization", `Bearer ${session.access_token}`);
 }

 try {
 const res = await fetch("/api/v1/me", { headers });
 if (res.ok) {
 const data = await res.json();
 setIdentity(data);
 }
 } catch {
 // ignore
 }
 }

 fetchIdentity();
 }, [activeWorkspace]);

  return (
    <div className="flex shrink-0 items-center gap-2 sm:gap-3">
      {identity ? (
        <div className="flex min-w-0 items-center gap-2 text-xs">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-salesos-surface-muted text-salesos-text-secondary">
            <User className="h-4 w-4" />
          </div>
          <div className="hidden flex-col min-w-0 sm:flex">
            <span className="truncate font-medium text-salesos-text max-w-[130px] md:max-w-[180px] lg:max-w-none">
              {identity.email}
            </span>
            <span className="truncate text-[10px] font-semibold text-salesos-text-secondary uppercase tracking-wider">
              Role: {identity.role}
            </span>
          </div>
        </div>
      ) : null}
      <SignOutButton />
    </div>
  );
}
