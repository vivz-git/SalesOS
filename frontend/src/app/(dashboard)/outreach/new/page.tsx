"use client";

import { useEffect, useState } from"react";
import Link from"next/link";
import { useRouter } from"next/navigation";
import { useWorkspace } from"@/lib/workspace-context";
import { createOutreachDraft, generateOutreachDraft } from"@/lib/api/outreach";
import { fetchCampaigns, type Campaign } from"@/lib/api/campaigns";
import { fetchContacts, type Contact } from"@/lib/api/contacts";
import { fetchResearchBriefs, type ResearchBrief } from"@/lib/api/research";
import { ArrowLeft, Send, FileText, AlertCircle } from"lucide-react";

export default function NewOutreachDraftPage() {
 const router = useRouter();
 const { activeWorkspace } = useWorkspace();

 const [campaigns, setCampaigns] = useState<Campaign[]>([]);
 const [contacts, setContacts] = useState<Contact[]>([]);
 const [researchBriefs, setResearchBriefs] = useState<ResearchBrief[]>([]);

 const [selectedCampaignId, setSelectedCampaignId] = useState<string>("");
 const [selectedContactId, setSelectedContactId] = useState<string>("");
 const [selectedBriefId, setSelectedBriefId] = useState<string>("");

 const [loadingData, setLoadingData] = useState<boolean>(true);
 const [submitting, setSubmitting] = useState<boolean>(false);
 const [error, setError] = useState<string | null>(null);

 useEffect(() => {
 async function loadFormOptions() {
 if (!activeWorkspace) return;
 setLoadingData(true);
 setError(null);
 try {
 const [camps, conts, briefs] = await Promise.all([
 fetchCampaigns(activeWorkspace.id),
 fetchContacts(activeWorkspace.id),
 fetchResearchBriefs(activeWorkspace.id),
 ]);
 setCampaigns(camps);
 setContacts(conts);
 setResearchBriefs(briefs);
 if (camps.length > 0) setSelectedCampaignId(camps[0].id);
 if (conts.length > 0) setSelectedContactId(conts[0].id);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to load campaigns/contacts data");
 } finally {
 setLoadingData(false);
 }
 }
 loadFormOptions();
 }, [activeWorkspace]);

 async function handleSubmit(e: React.FormEvent) {
 e.preventDefault();
 if (!activeWorkspace) return;
 if (!selectedCampaignId || !selectedContactId) {
 setError("Campaign and Contact are required.");
 return;
 }

 setSubmitting(true);
 setError(null);

 try {
 const created = await createOutreachDraft(activeWorkspace.id, {
 campaign_id: selectedCampaignId,
 contact_id: selectedContactId,
 research_brief_id: selectedBriefId || undefined,
 body:"",
 });

 // Auto-generate the draft using available context
 await generateOutreachDraft(activeWorkspace.id, created.id);

 router.push(`/outreach/${created.id}`);
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to create outreach draft");
 setSubmitting(false);
 }
 }

 return (
 <div className="mx-auto max-w-4xl space-y-6 p-6">
 {/* Back button */}
 <div>
 <Link
 href="/outreach"
 className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors focus:outline-none rounded-sm"
 >
 <ArrowLeft className="h-4 w-4"/>
 Back to Outreach Drafts
 </Link>
 </div>

 {/* Header */}
 <div>
 <h1 className="text-2xl font-bold tracking-tight text-slate-900">Create Outreach Draft</h1>
 <p className="mt-1 text-sm text-slate-500">
 Prepare a new message draft for a prospect. Messages are stored as drafts for human review.
 </p>
 </div>

 {error && (
 <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
 <AlertCircle className="h-5 w-5 text-red-600 shrink-0"/>
 <span>{error}</span>
 </div>
 )}

 {/* Form */}
 <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
 <div className="grid gap-6 sm:grid-cols-2">
 {/* Campaign Selector */}
 <div className="space-y-2">
 <label htmlFor="campaign_select"className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
 Campaign <span className="text-red-500">*</span>
 </label>
 <select
 id="campaign_select"
 value={selectedCampaignId}
 onChange={(e) => setSelectedCampaignId(e.target.value)}
 disabled={loadingData}
 className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
 required
 >
 {campaigns.length === 0 ? (
 <option value="">No campaigns available</option>
 ) : (
 campaigns.map((c) => (
 <option key={c.id} value={c.id}>
 {c.name} ({c.status})
 </option>
 ))
 )}
 </select>
 </div>

 {/* Contact Selector */}
 <div className="space-y-2">
 <label htmlFor="contact_select"className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
 Contact <span className="text-red-500">*</span>
 </label>
 <select
 id="contact_select"
 value={selectedContactId}
 onChange={(e) => setSelectedContactId(e.target.value)}
 disabled={loadingData}
 className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
 required
 >
 {contacts.length === 0 ? (
 <option value="">No contacts available</option>
 ) : (
 contacts.map((ct) => (
 <option key={ct.id} value={ct.id}>
 {ct.first_name} {ct.last_name} {ct.title ? `— ${ct.title}` :""}
 </option>
 ))
 )}
 </select>
 </div>
 </div>

 {/* Research Brief Selector (Optional) */}
 <div className="space-y-2">
 <label htmlFor="brief_select"className="flex items-center gap-1.5 text-xs font-semibold text-slate-900 uppercase tracking-wider">
 <FileText className="h-3.5 w-3.5 text-slate-500"/>
 Attach Research Brief (Optional)
 </label>
 <select
 id="brief_select"
 value={selectedBriefId}
 onChange={(e) => setSelectedBriefId(e.target.value)}
 disabled={loadingData}
 className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
 >
 <option value="">No research brief attached</option>
 {researchBriefs.map((b) => (
 <option key={b.id} value={b.id}>
 Brief {b.id.slice(0, 8)}... {b.summary ? `— ${b.summary.slice(0, 50)}...` :""}
 </option>
 ))}
 </select>
 </div>

 {/* Submit Actions */}
 <div className="flex items-center justify-end gap-3 border-t border-slate-200 pt-4">
 <Link
 href="/outreach"
 className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 focus:outline-none"
 >
 Cancel
 </Link>
 <button
 type="submit"
 disabled={submitting || loadingData}
 className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-xs font-semibold text-accent-foreground hover:bg-accent-hover disabled:opacity-50 focus:outline-none"
 >
 <Send className="h-3.5 w-3.5"/>
 {submitting ?"Generating Draft...":"Generate Draft"}
 </button>
 </div>
 </form>
 </div>
 );
}
