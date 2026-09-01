"use client";

import { useEffect, useState } from"react";
import { X } from"lucide-react";

import { Button } from"@/components/ui/button";
import type { Account, AccountCreatePayload, AccountStatus } from"@/lib/api/accounts";
import { fetchCampaigns, type Campaign } from"@/lib/api/campaigns";
import { useWorkspace } from"@/lib/workspace-context";

interface AccountFormProps {
 initialData?: Account | null;
 onSubmit: (payload: AccountCreatePayload) => Promise<void>;
 onClose: () => void;
 title: string;
}

export function AccountForm({
 initialData,
 onSubmit,
 onClose,
 title,
}: AccountFormProps) {
 const { activeWorkspace } = useWorkspace();
 const [name, setName] = useState(initialData?.name ||"");
 const [domain, setDomain] = useState(initialData?.domain ||"");
 const [industry, setIndustry] = useState(initialData?.industry ||"");
 const [employeeCount, setEmployeeCount] = useState(initialData?.employee_count ||"");
 const [city, setCity] = useState(initialData?.city ||"");
 const [country, setCountry] = useState(initialData?.country ||"");
 const [campaignId, setCampaignId] = useState(initialData?.campaign_id ||"");
 const [status, setStatus] = useState<AccountStatus>(initialData?.status ||"target");

 const [campaigns, setCampaigns] = useState<Campaign[]>([]);
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState<string | null>(null);

 useEffect(() => {
 if (!activeWorkspace) return;
 fetchCampaigns(activeWorkspace.id)
 .then(setCampaigns)
 .catch(() => undefined);
 }, [activeWorkspace]);

 async function handleSubmit(e: React.FormEvent) {
 e.preventDefault();
 if (!name.trim()) {
 setError("Account name is required.");
 return;
 }

 try {
 setLoading(true);
 setError(null);
 await onSubmit({
 name: name.trim(),
 domain: domain.trim() || undefined,
 industry: industry.trim() || undefined,
 employee_count: employeeCount.trim() || undefined,
 city: city.trim() || undefined,
 country: country.trim() || undefined,
 campaign_id: campaignId || undefined,
 status,
 });
 onClose();
 } catch (err: unknown) {
 setError(err instanceof Error ? err.message :"Failed to save account.");
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
 <label htmlFor="account-name"className="block text-xs font-semibold text-slate-700">
 Company Name <span className="text-red-500">*</span>
 </label>
 <input
 id="account-name"
 type="text"
 required
 value={name}
 onChange={(e) => setName(e.target.value)}
 placeholder="e.g. Acme Corp"
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>

 <div className="grid gap-4 sm:grid-cols-2">
 <div>
 <label htmlFor="account-domain"className="block text-xs font-semibold text-slate-700">
 Website Domain
 </label>
 <input
 id="account-domain"
 type="text"
 value={domain}
 onChange={(e) => setDomain(e.target.value)}
 placeholder="e.g. acme.com"
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>

 <div>
 <label htmlFor="account-campaign"className="block text-xs font-semibold text-slate-700">
 Assigned Campaign
 </label>
 <select
 id="account-campaign"
 value={campaignId}
 onChange={(e) => setCampaignId(e.target.value)}
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 >
 <option value="">No Campaign Assigned</option>
 {campaigns.map((c) => (
 <option key={c.id} value={c.id}>
 {c.name}
 </option>
 ))}
 </select>
 </div>
 </div>

 <div className="grid gap-4 sm:grid-cols-2">
 <div>
 <label htmlFor="account-industry"className="block text-xs font-semibold text-slate-700">
 Industry
 </label>
 <input
 id="account-industry"
 type="text"
 value={industry}
 onChange={(e) => setIndustry(e.target.value)}
 placeholder="e.g. B2B SaaS"
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>

 <div>
 <label htmlFor="account-employees"className="block text-xs font-semibold text-slate-700">
 Employee Count
 </label>
 <input
 id="account-employees"
 type="text"
 value={employeeCount}
 onChange={(e) => setEmployeeCount(e.target.value)}
 placeholder="e.g. 50-200"
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>
 </div>

 <div className="grid gap-4 sm:grid-cols-2">
 <div>
 <label htmlFor="account-city"className="block text-xs font-semibold text-slate-700">
 City
 </label>
 <input
 id="account-city"
 type="text"
 value={city}
 onChange={(e) => setCity(e.target.value)}
 placeholder="e.g. San Francisco"
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>

 <div>
 <label htmlFor="account-country"className="block text-xs font-semibold text-slate-700">
 Country
 </label>
 <input
 id="account-country"
 type="text"
 value={country}
 onChange={(e) => setCountry(e.target.value)}
 placeholder="e.g. USA"
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 />
 </div>
 </div>

 <div>
 <label htmlFor="account-status"className="block text-xs font-semibold text-slate-700">
 Account Status
 </label>
 <select
 id="account-status"
 value={status}
 onChange={(e) => setStatus(e.target.value as AccountStatus)}
 className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-900 focus:outline-none"
 >
 <option value="target">Target</option>
 <option value="qualified">Qualified</option>
 <option value="disqualified">Disqualified</option>
 <option value="archived">Archived</option>
 </select>
 </div>

 <div className="flex items-center justify-end gap-2 border-t pt-4">
 <Button type="button"variant="outline"onClick={onClose} disabled={loading}>
 Cancel
 </Button>
 <Button type="submit"disabled={loading}>
 {loading ?"Saving...":"Save Account"}
 </Button>
 </div>
 </form>
 </div>
 </div>
 );
}
