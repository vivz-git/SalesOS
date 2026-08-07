"use client";

import { useEffect, useState } from "react";
import { User } from "lucide-react";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { useWorkspace } from "@/lib/workspace-context";

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
    fetch("/api/v1/me", {
      headers: {
        "X-SalesOS-Workspace-Id": activeWorkspace.id,
      },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setIdentity(data);
      })
      .catch(() => undefined);
  }, [activeWorkspace]);

  return (
    <div className="flex items-center gap-3">
      {identity ? (
        <div className="flex items-center gap-2 text-xs">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-100 text-zinc-700">
            <User className="h-4 w-4" />
          </div>
          <div className="hidden flex-col sm:flex">
            <span className="font-medium text-zinc-900">{identity.email}</span>
            <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">
              Role: {identity.role}
            </span>
          </div>
        </div>
      ) : null}
      <SignOutButton />
    </div>
  );
}
