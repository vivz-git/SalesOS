"use client";

import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { useWorkspace } from "@/lib/workspace-context";

export function WorkspaceOnboarding() {
  const { createWorkspace } = useWorkspace();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      await createWorkspace(name.trim());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create workspace");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center p-6 bg-zinc-50">
      <div className="w-full max-w-md rounded-xl border bg-white p-8 shadow-sm">
        <div className="text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            Welcome to SalesOS
          </h1>
          <p className="mt-2 text-sm text-zinc-600">
            Create your first workspace to start setting up campaigns and prospecting workflows.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            Workspace Name
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Acme Corp Outbound"
              className="rounded-md border p-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none"
            />
          </label>

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Get Started"}
          </Button>
        </form>
      </div>
    </main>
  );
}
