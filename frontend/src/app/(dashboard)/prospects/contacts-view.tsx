"use client";

import { useCallback, useEffect, useState } from"react";
import Link from"next/link";
import {
 ChevronLeft,
 ChevronRight,
 Mail,
 Plus,
 Search,
 Star,
 Users,
} from"lucide-react";

import { ContactForm } from"@/components/contacts/contact-form";
import { ContactStatusBadge } from"@/components/contacts/contact-status-badge";
import { Button } from"@/components/ui/button";
import { fetchAccounts, type Account } from"@/lib/api/accounts";
import {
 createContact,
 fetchContacts,
 type Contact,
 type ContactCreatePayload,
} from"@/lib/api/contacts";
import { useWorkspace } from"@/lib/workspace-context";
import { createResearchBrief, triggerResearchJob } from"@/lib/api/research";

const PAGE_SIZE = 12;

const STATUS_TABS = [
 { label:"All", value:""},
 { label:"Active", value:"active"},
 { label:"Unresponsive", value:"unresponsive"},
 { label:"Opted Out", value:"opted_out"},
 { label:"Archived", value:"archived"},
];

export default function ContactsView() {
 const { activeWorkspace } = useWorkspace();
 const [contacts, setContacts] = useState<Contact[]>([]);
 const [accounts, setAccounts] = useState<Account[]>([]);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 const [statusFilter, setStatusFilter] = useState("");
 const [accountFilter, setAccountFilter] = useState("");
 const [searchQuery, setSearchQuery] = useState("");
 const [page, setPage] = useState(1);
 const [isModalOpen, setIsModalOpen] = useState(false);

 const loadAccounts = useCallback(async () => {
 if (!activeWorkspace) return;
 try {
 const data = await fetchAccounts(activeWorkspace.id);
 setAccounts(data);
 } catch {
 // Ignore account load failure fallback
 }
 }, [activeWorkspace]);

 const loadContacts = useCallback(async () => {
 if (!activeWorkspace) return;
 try {
 setLoading(true);
 setError(null);
 const data = await fetchContacts(activeWorkspace.id, {
 status: statusFilter || undefined,
 account_id: accountFilter || undefined,
 search: searchQuery || undefined,
 limit: PAGE_SIZE,
 offset: (page - 1) * PAGE_SIZE,
 });
 setContacts(data);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load contacts.");
 } finally {
 setLoading(false);
 }
 }, [activeWorkspace, statusFilter, accountFilter, searchQuery, page]);

 useEffect(() => {
 loadAccounts();
 }, [loadAccounts]);

 useEffect(() => {
 loadContacts();
 }, [loadContacts]);

 async function handleCreateContact(payload: ContactCreatePayload) {
 if (!activeWorkspace) return;
 const contact = await createContact(activeWorkspace.id, payload);

 if (contact.account_id) {
 try {
 const brief = await createResearchBrief(activeWorkspace.id, {
 account_id: contact.account_id,
 contact_id: contact.id,
 });
 await triggerResearchJob(activeWorkspace.id, brief.id);
 } catch (err) {
 console.error('Failed to automatically trigger research:', err);
 }
 }

 await loadContacts();
 }

 const accountMap = new Map(accounts.map((a) => [a.id, a]));

 return (
 <div className="space-y-6">
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
 <div>
 <h2 className="text-lg font-bold tracking-tight text-salesos-text">People</h2>
 <p className="mt-1 text-sm text-salesos-text-secondary">
 Decision-maker directory, job titles, departments, and primary account contacts.
 </p>
 </div>

 <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2"variant="primary">
 <Plus className="h-4 w-4"/>
 <span>New Contact</span>
 </Button>
 </div>

 <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-salesos-border pb-3">
 <div className="flex items-center gap-1 overflow-x-auto">
 {STATUS_TABS.map((tab) => {
 const isActive = statusFilter === tab.value;
 return (
 <button
 key={tab.value}
 type="button"
 onClick={() => {
 setStatusFilter(tab.value);
 setPage(1);
 }}
 className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
 isActive
 ?"bg-salesos-brand text-white"
 :"text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text"
 }`}
 >
 {tab.label}
 </button>
 );
 })}
 </div>

 <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
 <select
 value={accountFilter}
 onChange={(e) => {
 setAccountFilter(e.target.value);
 setPage(1);
 }}
 className="rounded-md border border-salesos-border px-3 py-1.5 text-[13px] text-salesos-text focus:border-salesos-focus focus:outline-none"
 >
 <option value="">All Accounts</option>
 {accounts.map((a) => (
 <option key={a.id} value={a.id}>
 {a.name}
 </option>
 ))}
 </select>

 <div className="relative w-full sm:w-56">
 <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-salesos-text-secondary/60"/>
 <input
 type="text"
 value={searchQuery}
 onChange={(e) => {
 setSearchQuery(e.target.value);
 setPage(1);
 }}
 placeholder="Search decision makers..."
 className="w-full rounded-md border border-salesos-border pl-8 pr-3 py-1.5 text-[13px] text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>
 </div>
 </div>

 {loading ? (
 <div className="flex h-48 w-full items-center justify-center rounded-lg border bg-salesos-surface p-6 shadow-sm">
 <div className="flex items-center gap-2 text-sm text-salesos-text-secondary">
 <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"/>
 <span>Loading decision makers...</span>
 </div>
 </div>
 ) : error ? (
 <div className="flex flex-col items-center justify-center rounded-lg border bg-salesos-surface p-6 text-center shadow-sm">
 <p className="text-sm font-medium text-salesos-danger">{error}</p>
 <Button variant="secondary"size="sm"onClick={loadContacts} className="mt-3">
 Retry
 </Button>
 </div>
 ) : contacts.length === 0 ? (
 <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-salesos-border bg-salesos-surface p-12 text-center shadow-sm">
 <div className="flex h-12 w-12 items-center justify-center rounded-full bg-salesos-surface-muted text-salesos-text-secondary">
 <Users className="h-6 w-6"/>
 </div>
 <h3 className="mt-4 text-sm font-bold text-salesos-text">No contacts found</h3>
 <p className="mt-1 text-[13px] text-salesos-text-secondary">
 {searchQuery || accountFilter
 ?"No contact matched your search or account filter."
 :"Get started by adding your first decision maker."}
 </p>
 {!searchQuery && !accountFilter && (
 <Button onClick={() => setIsModalOpen(true)} className="mt-4"size="sm"variant="primary">
 Create Contact
 </Button>
 )}
 </div>
 ) : (
 <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
 {contacts.map((contact) => {
 const linkedAccount = contact.account_id ? accountMap.get(contact.account_id) : null;
 return (
 <Link
 key={contact.id}
 href={`/contacts/${contact.id}`}
 className="group flex flex-col justify-between rounded-lg border border-salesos-border bg-salesos-surface p-5 shadow-xs transition-all hover:border-salesos-border hover:shadow-md"
 >
 <div>
 <div className="flex items-start justify-between gap-2">
 <div className="flex items-center gap-1.5">
 <h3 className="text-base font-bold text-salesos-text group-hover:text-salesos-text-secondary">
 {contact.first_name} {contact.last_name}
 </h3>
 {contact.is_primary && (
 <span title="Primary Contact">
 <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-500"/>
 </span>
 )}
 </div>
 <ContactStatusBadge status={contact.status} />
 </div>

 {contact.title && (
 <p className="mt-1 text-[13px] font-semibold text-salesos-text-secondary">{contact.title}</p>
 )}

 {linkedAccount && (
 <p className="mt-1 text-[13px] text-salesos-text-secondary font-medium">
 Company: {linkedAccount.name}
 </p>
 )}

 {contact.email && (
 <p className="mt-2 flex items-center gap-1 text-[13px] text-salesos-text-secondary">
 <Mail className="h-3.5 w-3.5 text-salesos-text-secondary/60 shrink-0"/>
 <span className="truncate">{contact.email}</span>
 </p>
 )}
 </div>

 <div className="mt-4 flex items-center justify-between border-t border-salesos-border pt-3 text-[11px] text-salesos-text-secondary/60">
 <span>View Details & Actions →</span>
 </div>
 </Link>
 );
 })}
 </div>
 )}

 {/* Pagination Controls */}
 <div className="flex items-center justify-between border-t border-salesos-border pt-4">
 <span className="text-[13px] text-salesos-text-secondary">
 Showing page <span className="font-semibold text-salesos-text">{page}</span>
 </span>
 <div className="flex items-center gap-2">
 <Button
 variant="secondary"
 size="sm"
 onClick={() => setPage((p) => Math.max(1, p - 1))}
 disabled={page === 1 || loading}
 className="flex items-center gap-1"
 >
 <ChevronLeft className="h-4 w-4"/>
 <span>Previous</span>
 </Button>
 <Button
 variant="secondary"
 size="sm"
 onClick={() => setPage((p) => p + 1)}
 disabled={contacts.length < PAGE_SIZE || loading}
 className="flex items-center gap-1"
 >
 <span>Next</span>
 <ChevronRight className="h-4 w-4"/>
 </Button>
 </div>
 </div>

 {isModalOpen && (
 <ContactForm
 title="Add Decision Maker Contact"
 onSubmit={handleCreateContact}
 onClose={() => setIsModalOpen(false)}
 />
 )}
 </div>
 );
}
