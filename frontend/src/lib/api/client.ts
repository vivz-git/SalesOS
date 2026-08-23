import { createClient } from "@/lib/supabase/client";

export async function request<T>(
  url: string,
  workspaceId: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("X-SalesOS-Workspace-Id", workspaceId);
  headers.set("Content-Type", "application/json");

  try {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      headers.set("Authorization", `Bearer ${session.access_token}`);
    }
  } catch (err) {
    // Suppress auth client initialization errors if running outside browser context,
    // though this helper should primarily be called from client-side hooks.
    console.warn("Failed to get Supabase session for API request", err);
  }

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
