import Link from"next/link";
import type { ReactNode } from"react";

interface AuthCardProps {
 title: string;
 description?: string;
 children: ReactNode;
}

export function AuthCard({ title, description, children }: AuthCardProps) {
 return (
 <main className="grid min-h-screen place-items-center bg-salesos-surface-muted p-6">
 <div className="w-full max-w-sm">
 {/* Brand header */}
 <div className="mb-6 flex justify-center">
 <Link
 href="/"
 className="flex items-center gap-2 font-bold text-salesos-text"
 >
 <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-xs font-black text-white">
 OS
 </span>
 <span className="text-base tracking-tight">SalesOS</span>
 </Link>
 </div>

 {/* Card */}
 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-6 shadow-sm">
 <div className="mb-5 text-center">
 <h1 className="text-xl font-semibold text-salesos-text">{title}</h1>
 {description && (
 <p className="mt-1 text-sm text-salesos-text-secondary">{description}</p>
 )}
 </div>
 {children}
 </div>
 </div>
 </main>
 );
}
