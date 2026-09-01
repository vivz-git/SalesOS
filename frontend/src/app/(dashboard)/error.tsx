"use client";

import { useEffect } from"react";

import { Button } from"@/components/ui/button";

export default function DashboardError({
 error,
 reset,
}: {
 error: Error & { digest?: string };
 reset: () => void;
}) {
 useEffect(() => {
 // Log error to error monitoring service if needed
 }, [error]);

 return (
 <div className="flex flex-col items-center justify-center rounded-xl border bg-salesos-surface p-8 text-center shadow-sm">
 <h2 className="text-lg font-semibold text-salesos-text">Something went wrong</h2>
 <p className="mt-1 text-sm text-salesos-text-secondary">{error.message ||"An unexpected error occurred."}</p>
 <Button onClick={reset} className="mt-4">
 Try again
 </Button>
 </div>
 );
}
