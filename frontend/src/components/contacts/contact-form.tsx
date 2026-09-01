"use client";

import { useEffect, useState } from"react";
import { X } from"lucide-react";

import { Button } from"@/components/ui/button";
import { fetchAccounts, type Account } from"@/lib/api/accounts";
import type { Contact, ContactCreatePayload, ContactStatus } from"@/lib/api/contacts";
import { useWorkspace } from"@/lib/workspace-context";

interface ContactFormProps {
 initialData?: Contact | null;
 onSubmit: (payload: ContactCreatePayload) => Promise<void>;
 onClose: () => void;
 title: string;
}

export function ContactForm({
 initialData,
 onSubmit,
 onClose,
 title,
}: ContactFormProps) {
 const { activeWorkspace } = useWorkspace();
 const [firstName, setFirstName] = useState(initialData?.first_name ||"");
 const [lastName, setLastName] = useState(initialData?.last_name ||"");
 const [accountId, setAccountId] = useState(initialData?.account_id ||"");
 const [email, setEmail] = useState(initialData?.email ||"");
 const [phone, setPhone] = useState(initialData?.phone ||"");
 const [jobTitle, setJobTitle] = useState(initialData?.title ||"");
 const [department, setDepartment] = useState(initialData?.department ||"");
 const [linkedinUrl, setLinkedinUrl] = useState(initialData?.linkedin_url ||"");
 const [isPrimary, setIsPrimary] = useState(initialData?.is_primary || false);
 const [status, setStatus] = useState<ContactStatus>(initialData?.status ||"active");

 const [accounts, setAccounts] = useState<Account[]>([]);
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState<string | null>(null);

 useEffect(() => {
 if (!activeWorkspace) return;
 fetchAccounts(activeWorkspace.id)
 .then(setAccounts)
 .catch(() => undefined);
 }, [activeWorkspace]);

 async function handleSubmit(e: React.FormEvent) {
 e.preventDefault();
 if (!firstName.trim() || !lastName.trim()) {
 setError("First name and last name are required.");
 return;
 }

 try {
 setLoading(true);
 setError(null);
 await onSubmit({
 first_name: firstName.trim(),
 last_name: lastName.trim(),
 account_id: accountId || undefined,
 email: email.trim() || undefined,
 phone: phone.trim() || undefined,
 title: jobTitle.trim() || undefined,
 department: department.trim() || undefined,
 linkedin_url: linkedinUrl.trim() || undefined,
 is_primary: isPrimary,
 status,
 });
 onClose();
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to save contact.");
 } finally {
 setLoading(false);
 }
 }

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
 <div className="w-full max-w-lg rounded-xl border bg-salesos-surface p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
 <div className="flex items-center justify-between border-b pb-3">
 <h2 className="text-lg font-bold text-salesos-text">{title}</h2>
 <button
 type="button"
 onClick={onClose}
 className="rounded-md p-1 text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text"
 aria-label="Close modal"
 >
 <X className="h-5 w-5"/>
 </button>
 </div>

 {error && (
 <div className="rounded-md bg-salesos-danger/10 p-3 text-xs font-medium text-salesos-danger">
 {error}
 </div>
 )}

 <form onSubmit={handleSubmit} className="space-y-4">
 <div className="grid gap-4 sm:grid-cols-2">
 <div>
 <label htmlFor="first-name"className="block text-xs font-semibold text-salesos-text-secondary">
 First Name <span className="text-red-500">*</span>
 </label>
 <input
 id="first-name"
 type="text"
 required
 value={firstName}
 onChange={(e) => setFirstName(e.target.value)}
 placeholder="e.g. Jane"
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>

 <div>
 <label htmlFor="last-name"className="block text-xs font-semibold text-salesos-text-secondary">
 Last Name <span className="text-red-500">*</span>
 </label>
 <input
 id="last-name"
 type="text"
 required
 value={lastName}
 onChange={(e) => setLastName(e.target.value)}
 placeholder="e.g. Doe"
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>
 </div>

 <div>
 <label htmlFor="contact-account"className="block text-xs font-semibold text-salesos-text-secondary">
 Target Company Account
 </label>
 <select
 id="contact-account"
 value={accountId}
 onChange={(e) => setAccountId(e.target.value)}
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 >
 <option value="">No Account Assigned</option>
 {accounts.map((a) => (
 <option key={a.id} value={a.id}>
 {a.name} {a.domain ? `(${a.domain})` :""}
 </option>
 ))}
 </select>
 </div>

 <div className="grid gap-4 sm:grid-cols-2">
 <div>
 <label htmlFor="contact-email"className="block text-xs font-semibold text-salesos-text-secondary">
 Work Email
 </label>
 <input
 id="contact-email"
 type="email"
 value={email}
 onChange={(e) => setEmail(e.target.value)}
 placeholder="e.g. jane.doe@acme.com"
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>

 <div>
 <label htmlFor="contact-phone"className="block text-xs font-semibold text-salesos-text-secondary">
 Phone Number
 </label>
 <input
 id="contact-phone"
 type="text"
 value={phone}
 onChange={(e) => setPhone(e.target.value)}
 placeholder="e.g. +1-555-0199"
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>
 </div>

 <div className="grid gap-4 sm:grid-cols-2">
 <div>
 <label htmlFor="contact-title"className="block text-xs font-semibold text-salesos-text-secondary">
 Job Title
 </label>
 <input
 id="contact-title"
 type="text"
 value={jobTitle}
 onChange={(e) => setJobTitle(e.target.value)}
 placeholder="e.g. VP of Engineering"
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>

 <div>
 <label htmlFor="contact-department"className="block text-xs font-semibold text-salesos-text-secondary">
 Department
 </label>
 <input
 id="contact-department"
 type="text"
 value={department}
 onChange={(e) => setDepartment(e.target.value)}
 placeholder="e.g. Engineering"
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>
 </div>

 <div>
 <label htmlFor="contact-linkedin"className="block text-xs font-semibold text-salesos-text-secondary">
 LinkedIn Profile URL
 </label>
 <input
 id="contact-linkedin"
 type="text"
 value={linkedinUrl}
 onChange={(e) => setLinkedinUrl(e.target.value)}
 placeholder="e.g. https://linkedin.com/in/janedoe"
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>

 <div className="grid gap-4 sm:grid-cols-2">
 <div>
 <label htmlFor="contact-status"className="block text-xs font-semibold text-salesos-text-secondary">
 Status
 </label>
 <select
 id="contact-status"
 value={status}
 onChange={(e) => setStatus(e.target.value as ContactStatus)}
 className="mt-1 block w-full rounded-md border border-salesos-border px-3 py-2 text-sm text-salesos-text focus:border-salesos-focus focus:outline-none"
 >
 <option value="active">Active</option>
 <option value="unresponsive">Unresponsive</option>
 <option value="opted_out">Opted Out</option>
 <option value="archived">Archived</option>
 </select>
 </div>

 <div className="flex items-center gap-2 pt-5">
 <input
 id="is-primary"
 type="checkbox"
 checked={isPrimary}
 onChange={(e) => setIsPrimary(e.target.checked)}
 className="h-4 w-4 rounded border-salesos-border text-salesos-text"
 />
 <label htmlFor="is-primary"className="text-xs font-semibold text-salesos-text-secondary">
 Primary Account Contact
 </label>
 </div>
 </div>

 <div className="flex items-center justify-end gap-2 border-t pt-4">
 <Button type="button"variant="outline"onClick={onClose} disabled={loading}>
 Cancel
 </Button>
 <Button type="submit"disabled={loading}>
 {loading ?"Saving...":"Save Contact"}
 </Button>
 </div>
 </form>
 </div>
 </div>
 );
}
