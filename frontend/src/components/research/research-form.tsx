"use client";

import { useEffect, useState } from"react";
import { X } from"lucide-react";

import { Button } from"@/components/ui/button";
import { fetchAccounts, type Account } from"@/lib/api/accounts";
import { fetchContacts, type Contact } from"@/lib/api/contacts";
import type { ResearchBriefCreatePayload } from"@/lib/api/research";
import { useWorkspace } from"@/lib/workspace-context";

interface ResearchFormProps {
 onSubmit: (payload: ResearchBriefCreatePayload) => Promise<void>;
 onClose: () => void;
 title: string;
}

export function ResearchForm({ onSubmit, onClose, title }: ResearchFormProps) {
 const { activeWorkspace } = useWorkspace();
 const [accountId, setAccountId] = useState("");
 const [contactId, setContactId] = useState("");
 const [summary, setSummary] = useState("");
 const [keyFindingsText, setKeyFindingsText] = useState("");

 const [accounts, setAccounts] = useState<Account[]>([]);
 const [contacts, setContacts] = useState<Contact[]>([]);
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState<string | null>(null);

 useEffect(() => {
 if (!activeWorkspace) return;
 fetchAccounts(activeWorkspace.id)
 .then(setAccounts)
 .catch(() => undefined);
 fetchContacts(activeWorkspace.id)
 .then(setContacts)
 .catch(() => undefined);
 }, [activeWorkspace]);

 async function handleSubmit(e: React.FormEvent) {
 e.preventDefault();
 if (!accountId) {
 setError("Please select a target company account.");
 return;
 }

 const keyFindings = keyFindingsText
 .split("\n")
 .map((line) => line.trim())
 .filter(Boolean);

 try {
 setLoading(true);
 setError(null);
 await onSubmit({
 account_id: accountId,
 contact_id: contactId || undefined,
 summary: summary.trim() || undefined,
 key_findings: keyFindings.length > 0 ? keyFindings : undefined,
 });
 onClose();
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to create research brief.");
 } finally {
 setLoading(false);
 }
 }

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
 <div className="w-full max-w-lg rounded-xl border bg-white p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
 <div className="flex items-center justify-between border-b pb-3">
 <h2 className="text-lg font-bold text-slate-900">{title}</h2>
 <button
 type="button"
 onClick={onClose}
 className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
 aria-label="Close modal"
 >
 <X className="h-5 w-5"/>
 </button>
 </div>

 {error && (
 <div className="rounded-md bg-red-50 p-3 text-xs font-medium text-red-700">
 {error}
 </div>
 )}

 <form onSubmit={handleSubmit} className="space-y-4">
 <div>
 <label htmlFor="brief-account"className="block text-xs font-semibold text-slate-700">
 Target Company Account <span className="text-red-500">*</span>
 </label>
 <select
 id="brief-account"
 required
 value={accountId}
 onChange={(e) => setAccountId(e.target.value)}
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 >
 <option value="">Select Target Account</option>
 {accounts.map((a) => (
 <option key={a.id} value={a.id}>
 {a.name} {a.domain ? `(${a.domain})` :""}
 </option>
 ))}
 </select>
 </div>

 <div>
 <label htmlFor="brief-contact"className="block text-xs font-semibold text-slate-700">
 Decision Maker Contact (Optional)
 </label>
 <select
 id="brief-contact"
 value={contactId}
 onChange={(e) => setContactId(e.target.value)}
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 >
 <option value="">No Contact Selected</option>
 {contacts.map((c) => (
 <option key={c.id} value={c.id}>
 {c.first_name} {c.last_name} {c.title ? `(${c.title})` :""}
 </option>
 ))}
 </select>
 </div>

 <div>
 <label htmlFor="brief-summary"className="block text-xs font-semibold text-slate-700">
 Executive Summary / Objective
 </label>
 <textarea
 id="brief-summary"
 rows={2}
 value={summary}
 onChange={(e) => setSummary(e.target.value)}
 placeholder="Outline research scope, goals, or preliminary intelligence notes..."
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>

 <div>
 <label htmlFor="brief-findings"className="block text-xs font-semibold text-slate-700">
 Initial Key Findings (One per line)
 </label>
 <textarea
 id="brief-findings"
 rows={3}
 value={keyFindingsText}
 onChange={(e) => setKeyFindingsText(e.target.value)}
 placeholder="e.g. Expanding engineering department in Q3&#10;Recent Series B funding announcement"
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>

 <div className="flex items-center justify-end gap-2 border-t pt-4">
 <Button type="button"variant="outline"onClick={onClose} disabled={loading}>
 Cancel
 </Button>
 <Button type="submit"disabled={loading}>
 {loading ?"Creating...":"Create Research Brief"}
 </Button>
 </div>
 </form>
 </div>
 </div>
 );
}
