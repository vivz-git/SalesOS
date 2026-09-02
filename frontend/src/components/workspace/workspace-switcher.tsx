"use client";

import { useState, type ChangeEvent } from"react";

import { Button } from"@/components/ui/button";
import { useWorkspace } from"@/lib/workspace-context";

export function WorkspaceSwitcher() {
 const { workspaces, activeWorkspace, setActiveWorkspaceId, createWorkspace } = useWorkspace();
 const [isCreating, setIsCreating] = useState(false);
 const [newWorkspaceName, setNewWorkspaceName] = useState("");
 const [error, setError] = useState<string | null>(null);

 function handleSelect(e: ChangeEvent<HTMLSelectElement>) {
 const val = e.target.value;
 if (val ==="__new__") {
 setIsCreating(true);
 } else {
 setActiveWorkspaceId(val);
 }
 }

 async function handleCreateSubmit(e: React.FormEvent) {
 e.preventDefault();
 setError(null);
 if (!newWorkspaceName.trim()) return;
 try {
 await createWorkspace(newWorkspaceName.trim());
 setNewWorkspaceName("");
 setIsCreating(false);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to create workspace");
 }
 }

 return (
 <div className="flex shrink-0 items-center gap-2">
 <select
 aria-label="Select workspace"
 className="h-8 max-w-[120px] sm:max-w-[160px] md:max-w-[200px] lg:max-w-[240px] truncate rounded-md border border-salesos-border bg-salesos-surface px-2.5 py-1 text-xs sm:text-sm font-medium text-salesos-text shadow-2xs focus:border-salesos-focus focus:outline-none"
 value={activeWorkspace?.id ||""}
 onChange={handleSelect}
 >
 {workspaces.map((ws) => (
 <option key={ws.id} value={ws.id}>
 {ws.name}
 </option>
 ))}
 <option value="__new__">+ Create New Workspace</option>
 </select>

 {isCreating && (
 <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
 <div className="w-full max-w-md rounded-lg bg-salesos-surface p-6 shadow-xl">
 <h2 className="text-lg font-semibold text-salesos-text">Create New Workspace</h2>
 <form onSubmit={handleCreateSubmit} className="mt-4 grid gap-4">
 <div>
 <label className="block text-sm font-medium text-salesos-text-secondary">
 Workspace Name
 </label>
 <input
 type="text"
 required
 value={newWorkspaceName}
 onChange={(e) => setNewWorkspaceName(e.target.value)}
 placeholder="e.g. Acme Sales Team"
 className="mt-1 w-full rounded-md border p-2 text-sm"
 />
 </div>
 {error && <p className="text-xs text-salesos-danger"role="alert">{error}</p>}
 <div className="flex justify-end gap-2">
 <Button
 type="button"
 variant="outline"
 onClick={() => {
 setIsCreating(false);
 setError(null);
 }}
 >
 Cancel
 </Button>
 <Button type="submit">Create Workspace</Button>
 </div>
 </form>
 </div>
 </div>
 )}
 </div>
 );
}
