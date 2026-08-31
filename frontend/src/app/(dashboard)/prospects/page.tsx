"use client";

import { useState } from "react";
import ContactsView from "./contacts-view";
import AccountsView from "./accounts-view";
import { Users, Building2 } from "lucide-react";

export default function ProspectsPage() {
  const [activeTab, setActiveTab] = useState<"contacts" | "accounts">("contacts");

  return (
    <div className="space-y-6 max-w-6xl mx-auto p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-zinc-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 flex items-center gap-2">
            <Users className="h-6 w-6 text-purple-600" />
            <span>Prospects</span>
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            Manage your decision makers and target accounts.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-lg bg-zinc-100 p-1">
          <button
            onClick={() => setActiveTab("contacts")}
            className={`flex items-center gap-2 rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "contacts"
                ? "bg-white text-zinc-900 shadow-sm"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            <Users className="h-4 w-4" />
            People
          </button>
          <button
            onClick={() => setActiveTab("accounts")}
            className={`flex items-center gap-2 rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "accounts"
                ? "bg-white text-zinc-900 shadow-sm"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            <Building2 className="h-4 w-4" />
            Companies
          </button>
        </div>
      </div>

      {activeTab === "contacts" ? <ContactsView /> : <AccountsView />}
    </div>
  );
}
