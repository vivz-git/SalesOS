import Link from "next/link";
import type { ReactNode } from "react";

interface AuthCardProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function AuthCard({ title, description, children }: AuthCardProps) {
  return (
    <main className="grid min-h-screen place-items-center bg-zinc-50 p-6">
      <div className="w-full max-w-sm">
        {/* Brand header */}
        <div className="mb-6 flex justify-center">
          <Link
            href="/"
            className="flex items-center gap-2 font-bold text-zinc-900"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-xs font-black text-white">
              OS
            </span>
            <span className="text-base tracking-tight">SalesOS</span>
          </Link>
        </div>

        {/* Card */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="mb-5 text-center">
            <h1 className="text-xl font-semibold text-zinc-900">{title}</h1>
            {description && (
              <p className="mt-1 text-sm text-zinc-500">{description}</p>
            )}
          </div>
          {children}
        </div>
      </div>
    </main>
  );
}
