"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { MessageSquare, Send, Inbox as InboxIcon } from "lucide-react";
import { RepliesTab } from "@/components/inbox/replies-tab";
import { SentTab } from "@/components/inbox/sent-tab";

function InboxContent() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");
  const [activeTab, setActiveTab] = useState<"replies" | "sent">("replies");

  useEffect(() => {
    if (tabParam === "sent") {
      setActiveTab("sent");
    } else if (tabParam === "replies") {
      setActiveTab("replies");
    }
  }, [tabParam]);

  return (
    <>
      <div className="flex border-b border-zinc-200">
        <button
          onClick={() => setActiveTab("replies")}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "replies"
              ? "border-purple-600 text-purple-700"
              : "border-transparent text-zinc-500 hover:text-zinc-700 hover:border-zinc-300"
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          Replies
        </button>
        <button
          onClick={() => setActiveTab("sent")}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "sent"
              ? "border-purple-600 text-purple-700"
              : "border-transparent text-zinc-500 hover:text-zinc-700 hover:border-zinc-300"
          }`}
        >
          <Send className="h-4 w-4" />
          Sent
        </button>
      </div>

      <div className="mt-6">
        {activeTab === "replies" ? <RepliesTab /> : <SentTab />}
      </div>
    </>
  );
}

export default function InboxPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 flex items-center gap-2">
            <InboxIcon className="h-6 w-6 text-purple-600" />
            <span>Inbox</span>
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            Unified view of prospect replies and outbound sent emails.
          </p>
        </div>
      </div>

      <Suspense fallback={<div className="p-4 text-xs text-zinc-500">Loading inbox...</div>}>
        <InboxContent />
      </Suspense>
    </div>
  );
}
