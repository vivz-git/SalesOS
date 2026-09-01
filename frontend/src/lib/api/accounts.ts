import { request } from './client';
export type AccountStatus ="target"|"qualified"|"disqualified"|"archived";

export interface Account {
 id: string;
 workspace_id: string;
 campaign_id: string | null;
 name: string;
 domain: string | null;
 industry: string | null;
 employee_count: string | null;
 city: string | null;
 state: string | null;
 country: string | null;
 status: AccountStatus;
 created_by: string | null;
 created_at: string | null;
 updated_at: string | null;
 deleted_at: string | null;
}

export interface AccountCreatePayload {
 name: string;
 campaign_id?: string;
 domain?: string;
 industry?: string;
 employee_count?: string;
 city?: string;
 state?: string;
 country?: string;
 status?: AccountStatus;
}

export interface AccountUpdatePayload {
 name?: string;
 campaign_id?: string | null;
 domain?: string;
 industry?: string;
 employee_count?: string;
 city?: string;
 state?: string;
 country?: string;
 status?: AccountStatus;
}

export interface AccountFilterParams {
 campaign_id?: string;
 status?: string;
 search?: string;
 limit?: number;
 offset?: number;
}


export async function fetchAccounts(
 workspaceId: string,
 params: AccountFilterParams = {}
): Promise<Account[]> {
 const searchParams = new URLSearchParams();
 if (params.campaign_id) searchParams.set("campaign_id", params.campaign_id);
 if (params.status) searchParams.set("status", params.status);
 if (params.search) searchParams.set("search", params.search);
 if (params.limit !== undefined) searchParams.set("limit", params.limit.toString());
 if (params.offset !== undefined) searchParams.set("offset", params.offset.toString());

 const queryString = searchParams.toString();
 const url = `/api/v1/accounts${queryString ? `?${queryString}` :""}`;
 return request<Account[]>(url, workspaceId);
}

export async function fetchAccount(
 workspaceId: string,
 accountId: string
): Promise<Account> {
 return request<Account>(`/api/v1/accounts/${accountId}`, workspaceId);
}

export async function createAccount(
 workspaceId: string,
 payload: AccountCreatePayload
): Promise<Account> {
 return request<Account>(`/api/v1/accounts`, workspaceId, {
 method:"POST",
 body: JSON.stringify(payload),
 });
}

export async function updateAccount(
 workspaceId: string,
 accountId: string,
 payload: AccountUpdatePayload
): Promise<Account> {
 return request<Account>(`/api/v1/accounts/${accountId}`, workspaceId, {
 method:"PATCH",
 body: JSON.stringify(payload),
 });
}

export async function deleteAccount(
 workspaceId: string,
 accountId: string
): Promise<Account> {
 return request<Account>(`/api/v1/accounts/${accountId}`, workspaceId, {
 method:"DELETE",
 });
}

export async function archiveAccount(
 workspaceId: string,
 accountId: string
): Promise<Account> {
 return request<Account>(`/api/v1/accounts/${accountId}/actions/archive`, workspaceId, {
 method:"POST",
 });
}

export async function restoreAccount(
 workspaceId: string,
 accountId: string
): Promise<Account> {
 return request<Account>(`/api/v1/accounts/${accountId}/actions/restore`, workspaceId, {
 method:"POST",
 });
}
