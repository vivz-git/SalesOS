import { request } from "./client";

export interface ReportMetricsSnapshot {
  campaigns_count: number;
  accounts_researched_count: number;
  contacts_enrolled_count: number;
  drafts_generated_count: number;
  drafts_submitted_count: number;
  drafts_approved_count: number;
  approval_rate: number;
  emails_sent_count: number;
  emails_delivered_count: number;
  emails_bounced_count: number;
  emails_complained_count: number;
  delivery_rate: number;
  replies_received_count: number;
  reply_rate: number;
  interested_replies_count: number;
  interested_reply_rate: number;
  opt_out_replies_count: number;
  opt_out_rate: number;
  crm_synced_records_count: number;
}

export interface ReportRun {
  id: string;
  workspace_id: string;
  period_start: string;
  period_end: string;
  title: string;
  metrics_snapshot: ReportMetricsSnapshot;
  executive_summary: string;
  recommended_actions: string[];
  created_at: string;
}

export async function fetchWeeklyReportsList(
  workspaceId: string,
  limit: number = 10,
  offset: number = 0
): Promise<ReportRun[]> {
  return request<ReportRun[]>(
    `/v1/reports/weekly?limit=${limit}&offset=${offset}`,
    workspaceId
  );
}

export async function fetchWeeklyReportDetail(
  workspaceId: string,
  reportId: string
): Promise<ReportRun> {
  return request<ReportRun>(`/v1/reports/weekly/${reportId}`, workspaceId);
}

export async function generateWeeklyReport(workspaceId: string): Promise<ReportRun> {
  return request<ReportRun>("/v1/reports/weekly/actions/generate", workspaceId, {
    method: "POST",
  });
}
