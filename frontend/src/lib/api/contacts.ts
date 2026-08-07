export type ContactStatus = "active" | "unresponsive" | "opted_out" | "archived";

export interface Contact {
  id: string;
  workspace_id: string;
  account_id: string | null;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  title: string | null;
  department: string | null;
  linkedin_url: string | null;
  is_primary: boolean;
  status: ContactStatus;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
}

export interface ContactCreatePayload {
  first_name: string;
  last_name: string;
  account_id?: string;
  email?: string;
  phone?: string;
  title?: string;
  department?: string;
  linkedin_url?: string;
  is_primary?: boolean;
  status?: ContactStatus;
}

export interface ContactUpdatePayload {
  first_name?: string;
  last_name?: string;
  account_id?: string | null;
  email?: string;
  phone?: string;
  title?: string;
  department?: string;
  linkedin_url?: string;
  is_primary?: boolean;
  status?: ContactStatus;
}

export interface ContactFilterParams {
  account_id?: string;
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

async function request<T>(
  url: string,
  workspaceId: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("X-SalesOS-Workspace-Id", workspaceId);
  headers.set("Content-Type", "application/json");

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchContacts(
  workspaceId: string,
  params: ContactFilterParams = {}
): Promise<Contact[]> {
  const searchParams = new URLSearchParams();
  if (params.account_id) searchParams.set("account_id", params.account_id);
  if (params.status) searchParams.set("status", params.status);
  if (params.search) searchParams.set("search", params.search);
  if (params.limit !== undefined) searchParams.set("limit", params.limit.toString());
  if (params.offset !== undefined) searchParams.set("offset", params.offset.toString());

  const queryString = searchParams.toString();
  const url = `/api/v1/contacts${queryString ? `?${queryString}` : ""}`;
  return request<Contact[]>(url, workspaceId);
}

export async function fetchContact(
  workspaceId: string,
  contactId: string
): Promise<Contact> {
  return request<Contact>(`/api/v1/contacts/${contactId}`, workspaceId);
}

export async function createContact(
  workspaceId: string,
  payload: ContactCreatePayload
): Promise<Contact> {
  return request<Contact>(`/api/v1/contacts`, workspaceId, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateContact(
  workspaceId: string,
  contactId: string,
  payload: ContactUpdatePayload
): Promise<Contact> {
  return request<Contact>(`/api/v1/contacts/${contactId}`, workspaceId, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteContact(
  workspaceId: string,
  contactId: string
): Promise<Contact> {
  return request<Contact>(`/api/v1/contacts/${contactId}`, workspaceId, {
    method: "DELETE",
  });
}

export async function archiveContact(
  workspaceId: string,
  contactId: string
): Promise<Contact> {
  return request<Contact>(`/api/v1/contacts/${contactId}/actions/archive`, workspaceId, {
    method: "POST",
  });
}

export async function restoreContact(
  workspaceId: string,
  contactId: string
): Promise<Contact> {
  return request<Contact>(`/api/v1/contacts/${contactId}/actions/restore`, workspaceId, {
    method: "POST",
  });
}
