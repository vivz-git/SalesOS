"use client";

import { useState } from"react";
import ContactsView from"./contacts-view";
import AccountsView from"./accounts-view";

export default function ProspectsPage() {
 const [activeTab, setActiveTab] = useState<"contacts"|"accounts">("contacts");

 return (
 <div className="space-y-6 max-w-6xl mx-auto p-6">
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4">
 <div>
 <h1 className="text-2xl font-bold tracking-tight text-slate-900">
 Prospects
 </h1>
 <p className="mt-1 text-sm text-slate-500">
 Manage your decision makers and target accounts.
 </p>
 </div>

 <div className="flex items-center gap-2 rounded-lg bg-slate-100 p-1">
 <button
 onClick={() => setActiveTab("contacts")}
 className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
 activeTab ==="contacts"
 ?"bg-white text-slate-900 shadow-sm"
 :"text-slate-600 hover:text-slate-900"
 }`}
 >
 People
 </button>
 <button
 onClick={() => setActiveTab("accounts")}
 className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
 activeTab ==="accounts"
 ?"bg-white text-slate-900 shadow-sm"
 :"text-slate-600 hover:text-slate-900"
 }`}
 >
 Companies
 </button>
 </div>
 </div>

 {activeTab ==="contacts"? <ContactsView /> : <AccountsView />}
 </div>
 );
}
