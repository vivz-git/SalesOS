"use client";

import { useState } from"react";
import ContactsView from"./contacts-view";
import AccountsView from"./accounts-view";

export default function ProspectsPage() {
 const [activeTab, setActiveTab] = useState<"contacts"|"accounts">("contacts");

 return (
 <div className="space-y-6 max-w-6xl mx-auto p-6">
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-salesos-border pb-4">
 <div>
 <h1 className="text-2xl font-bold tracking-tight text-salesos-text">
 Prospects
 </h1>
 <p className="mt-1 text-sm text-salesos-text-secondary">
 Manage your decision makers and target accounts.
 </p>
 </div>

 <div className="flex items-center gap-2 rounded-lg bg-salesos-surface-muted p-1">
 <button
 onClick={() => setActiveTab("contacts")}
 className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
 activeTab ==="contacts"
 ?"bg-salesos-surface text-salesos-text shadow-sm"
 :"text-salesos-text-secondary hover:text-salesos-text"
 }`}
 >
 People
 </button>
 <button
 onClick={() => setActiveTab("accounts")}
 className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
 activeTab ==="accounts"
 ?"bg-salesos-surface text-salesos-text shadow-sm"
 :"text-salesos-text-secondary hover:text-salesos-text"
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
