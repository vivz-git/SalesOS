# SalesOS API Specification

**API style:** Versioned REST over HTTPS  
**Primary implementation:** FastAPI  
**Consumers:** SalesOS Web (Next.js 15), future desktop and mobile clients, approved internal workers, and verified third-party webhooks  
**Design principle:** One authoritative, tenant-safe control plane for every user and system action.

## 1. API Design Principles

### API-first, client-neutral contract

The FastAPI service is the public application contract. The Next.js web app is a client of this API, not a privileged implementation shortcut. Future desktop and mobile clients use the same authenticated, versioned resources and command endpoints.

### Resource-oriented reads; explicit commands for consequential actions

Standard reads and low-risk updates use resource-oriented REST patterns. Operations that create external effects or move governed state—approval, delivery scheduling, campaign activation, CRM synchronization, credential rotation, and workflow retry—use explicit command endpoints. This makes intent clear, simplifies authorization, and produces a reliable audit trail.

### Approval-first external actions

No client can directly invoke Resend, HubSpot, LangGraph, or GPT-4.1 mini through the SalesOS API. The API validates policy, authorization, research state, suppression state, and approval requirements before it creates a durable job or external-operation request. The send path requires an active valid approval for the exact draft version.

### Tenant-safe by design

Each request has one resolved active workspace. The API derives tenant scope from the authenticated subject and verified membership; it never trusts a caller-supplied tenant ID as authority. All resources, errors, jobs, events, and idempotency keys are scoped to this workspace.

### Predictable and observable behavior

Requests are validated against typed schemas. Responses have stable envelopes, timestamps use ISO 8601 UTC, identifiers are opaque, and errors are machine-readable. Every consequential request carries or receives a correlation identifier suitable for support and audit investigation.

### Asynchronous for long-running work

Research, generation, CRM synchronization, provider reconciliation, scheduled sends, and report generation return quickly with a job or workflow reference. Clients observe durable status rather than maintaining fragile long-lived HTTP connections.

## 2. Authentication Flow

Supabase Auth is the identity provider. FastAPI is the resource server and policy enforcement point.

### User authentication

1. A Web, desktop, or mobile client authenticates through Supabase Auth using a supported method.
2. Supabase returns an authenticated session and short-lived access token.
3. The client sends the token as a bearer credential to the SalesOS API over HTTPS.
4. FastAPI validates token signature, expiry, issuer, and audience, then resolves the authenticated user profile.
5. FastAPI resolves the active workspace from an explicit workspace context only after verifying an active membership and role.
6. The API performs endpoint-level authorization and tenant scoping before reading or writing data.

### Workspace context

Clients select an active workspace through a dedicated workspace-selection mechanism or a well-defined request header. The selected workspace is treated as a request preference, not proof of access. Every request is rejected if the user lacks active membership.

### Service and worker authentication

Internal Railway services and LangGraph workers authenticate with dedicated, least-privilege service identities. They call only internal/protected API paths or use narrowly scoped database access. Service credentials are never present in browser, desktop, or mobile builds.

### Integration credentials

HubSpot OAuth tokens and Resend credentials are stored and used server-side only. The API exposes connection state and authorization initiation/completion outcomes, never raw secrets or refresh tokens.

### Authorization roles

The API enforces workspace roles defined in the database architecture: Owner, Admin, Manager, Contributor, and Viewer. Permission checks are operation-specific; for example, viewing a draft, editing a draft, approving a draft, and changing an approval policy are independently authorized.

## 3. REST API Structure

The external API is namespaced beneath a stable base path:

`https://api.salesos.example/v1`

Routes use lowercase plural nouns, hyphenated multiword segments, and opaque IDs. The API uses JSON request and response bodies unless a documented export/download endpoint specifies another content type.

### Resource patterns

| Intent | Pattern | Example |
| --- | --- | --- |
| List a collection | `GET /v1/{resources}` | `GET /v1/campaigns` |
| Retrieve a resource | `GET /v1/{resources}/{id}` | `GET /v1/campaigns/{campaign_id}` |
| Create a resource | `POST /v1/{resources}` | `POST /v1/target-lists` |
| Replace/edit allowed fields | `PATCH /v1/{resources}/{id}` | `PATCH /v1/campaigns/{campaign_id}` |
| Soft-delete a resource | `DELETE /v1/{resources}/{id}` | `DELETE /v1/target-lists/{list_id}` |
| Execute a governed command | `POST /v1/{resources}/{id}/actions/{action}` | `POST /v1/approval-requests/{id}/actions/approve` |
| Retrieve a subresource | `GET /v1/{resources}/{id}/{subresource}` | `GET /v1/campaigns/{campaign_id}/metrics` |

Nested routes are used only where the parent relationship materially constrains a collection. Each child retains a canonical top-level endpoint when it needs independent lookup, permissioning, or lifecycle management.

### Control plane versus provider endpoints

The product API exposes SalesOS resources and normalized status, not raw provider APIs. For example, it exposes a HubSpot connection and sync runs, rather than passing through arbitrary HubSpot requests; it exposes delivery status and email events, rather than Resend account management.

## 4. Versioning Strategy

SalesOS uses major path versioning, beginning with `/v1`. A major version changes only when compatibility cannot be preserved. Additive fields, new optional endpoints, new enum values with documented safe handling, and new optional filters may be introduced within the current version.

### Compatibility commitments

- Existing response fields keep their meaning and type throughout a major version.
- Clients must ignore unknown JSON fields and safely handle documented new enum values.
- Required request fields are not introduced into existing commands without a new version or a backward-compatible default.
- Deprecated fields and routes receive documentation, migration guidance, and a published sunset date before removal.
- Webhook event schemas are independently versioned in the event payload, so endpoint transport changes do not silently break consumers.

FastAPI-generated OpenAPI documentation is published per major version. The OpenAPI description is the contract source for SDK generation, client validation, and contract testing; it does not expose internal worker-only endpoints or secrets.

## 5. Endpoint Groups

The following groups define the initial public application surface. Specific field schemas are maintained in the versioned OpenAPI contract and product documentation.

### Identity and workspace

- `GET /v1/me` — authenticated user profile and available workspace memberships.
- `GET /v1/workspaces` — workspaces accessible to the authenticated user.
- `GET /v1/workspaces/{workspace_id}` — workspace configuration visible to the caller.
- `PATCH /v1/workspaces/{workspace_id}` — update authorized workspace settings.
- `GET /v1/workspace-policies` and `PATCH /v1/workspace-policies` — read/update approval, sending, and retention controls.
- `GET /v1/memberships`, `POST /v1/memberships`, `PATCH /v1/memberships/{membership_id}` — membership administration for authorized roles.

### Campaigns and targeting

- `GET, POST /v1/campaigns` and `GET, PATCH, DELETE /v1/campaigns/{campaign_id}` — campaign lifecycle and configuration.
- `POST /v1/campaigns/{campaign_id}/actions/activate` — validates readiness and starts campaign execution.
- `POST /v1/campaigns/{campaign_id}/actions/pause` and `/actions/resume` — controlled operational state changes.
- `GET, POST /v1/target-lists` and `GET, PATCH, DELETE /v1/target-lists/{target_list_id}` — reusable or campaign-scoped prospect collections.
- `GET, POST /v1/target-lists/{target_list_id}/items` — list membership and eligibility review.
- `POST /v1/target-lists/{target_list_id}/actions/import` — asynchronous CSV/provider import; returns a job reference.
- `GET /v1/target-list-items/{item_id}` and `POST /v1/target-list-items/{item_id}/actions/exclude` — individual eligibility control.

### Accounts, contacts, and research

- `GET, POST /v1/accounts`; `GET, PATCH, DELETE /v1/accounts/{account_id}` — account records and lifecycle.
- `GET, POST /v1/contacts`; `GET, PATCH, DELETE /v1/contacts/{contact_id}` — decision-maker records and lifecycle.
- `GET /v1/accounts/{account_id}/research-briefs` and `GET /v1/contacts/{contact_id}/research-briefs` — research history.
- `GET /v1/research-briefs/{brief_id}` — brief, provenance, review state, and source references allowed for the caller.
- `POST /v1/accounts/{account_id}/actions/research` and `POST /v1/contacts/{contact_id}/actions/research` — enqueue research workflows.
- `POST /v1/research-briefs/{brief_id}/actions/accept` or `/actions/reject` — human review of a generated brief where policy requires it.
- `GET, POST /v1/suppressions` and `DELETE /v1/suppressions/{suppression_id}` — compliance and do-not-contact controls; removal is fully audited.

### Sequences, drafts, and approvals

- `GET, POST /v1/sequences`; `GET, PATCH /v1/sequences/{sequence_id}` — versioned sequence configuration.
- `GET /v1/sequence-enrollments` and `GET /v1/sequence-enrollments/{enrollment_id}` — contact progression through a sequence.
- `POST /v1/sequence-enrollments/{enrollment_id}/actions/pause`, `/actions/resume`, and `/actions/stop` — governed enrollment control.
- `GET /v1/outreach-drafts` and `GET /v1/outreach-drafts/{draft_id}` — drafts, evidence, and current lifecycle state.
- `POST /v1/outreach-drafts/{draft_id}/actions/generate` — enqueue a new draft version.
- `POST /v1/outreach-drafts/{draft_id}/actions/revise` — create a human-authored or AI-assisted revision; never overwrites a prior version.
- `POST /v1/outreach-drafts/{draft_id}/actions/request-approval` — creates an approval work item for the selected version.
- `GET /v1/approval-requests` and `GET /v1/approval-requests/{approval_request_id}` — filterable approval queue and request detail.
- `POST /v1/approval-requests/{approval_request_id}/actions/approve`, `/actions/reject`, `/actions/revoke`, and `/actions/escalate` — immutable approval decisions.

### Delivery, conversations, and reporting

- `GET /v1/deliveries` and `GET /v1/deliveries/{delivery_id}` — approved delivery lifecycle and provider-normalized status.
- `POST /v1/deliveries/{delivery_id}/actions/cancel` — cancel a queued delivery when policy permits.
- `GET /v1/conversations` and `GET /v1/conversations/{conversation_id}` — conversation inbox and thread detail.
- `POST /v1/conversations/{conversation_id}/actions/assign` — assign human ownership.
- `POST /v1/conversations/{conversation_id}/actions/classify` — enqueue bounded reclassification, subject to policy.
- `GET /v1/reports/weekly` — current workspace weekly report and historical report list.
- `GET /v1/reports/weekly/{report_id}` — a specific persisted report and metric snapshot.
- `POST /v1/reports/weekly/actions/generate` — enqueue an on-demand report if the caller is authorized.

### Integrations

- `GET /v1/integrations` — connection status and supported providers.
- `POST /v1/integrations/hubspot/actions/authorize` — begins secure HubSpot OAuth authorization.
- `POST /v1/integrations/hubspot/actions/disconnect` — revokes/disables the connection under an authorized policy.
- `GET /v1/integrations/hubspot/sync-runs` and `GET /v1/integrations/hubspot/sync-runs/{sync_run_id}` — sync history and granular outcomes.
- `POST /v1/integrations/hubspot/actions/sync` — enqueue an authorized, scoped CRM synchronization.
- `GET /v1/integrations/resend` — configured sending status and verified sender-domain state, with no secret material.

### Jobs, workflows, audit, and exports

- `GET /v1/jobs` and `GET /v1/jobs/{job_id}` — caller-visible background job lifecycle.
- `GET /v1/workflows` and `GET /v1/workflows/{workflow_id}` — LangGraph run status, safe artifacts, and failure summaries.
- `POST /v1/jobs/{job_id}/actions/retry` and `POST /v1/workflows/{workflow_id}/actions/retry` — controlled retry of eligible failed work.
- `GET /v1/audit-events` and `GET /v1/audit-events/{audit_event_id}` — role-limited immutable event history.
- `POST /v1/exports` — asynchronous workspace-scoped export request.
- `GET /v1/exports/{export_id}` — export status and authorized short-lived download reference.

## 6. Request / Response Standards

### Transport and representation

- HTTPS is mandatory. HTTP requests redirect or fail outside trusted local development.
- Requests and responses use `application/json; charset=utf-8`, except documented file upload/download flows.
- Field names use `snake_case`; route segments use lowercase kebab case where multiword.
- Timestamps use ISO 8601 in UTC. Dates without time use ISO 8601 date format.
- IDs are opaque strings; clients must not infer creation time, tenant, or resource type from them.
- Clients pass a generated `Idempotency-Key` header on all retryable create and command requests that could have a material effect.
- Clients may supply `X-Request-ID`; the server returns a correlation identifier in every response.

### Success response shape

Single-resource responses return the resource in a stable `data` object. Collection responses return `data` plus a `pagination` object. Action responses return the updated resource when work completed synchronously or an `operation`/job reference when work is asynchronous.

Every resource representation includes at least its opaque `id`, lifecycle `status` where applicable, `created_at`, `updated_at`, and relevant version/concurrency metadata. Sensitive fields are excluded by default and exposed only through specifically authorized, documented representations.

### Mutations and concurrency

PATCH requests are partial updates to fields explicitly documented as mutable. Revisions of message content, research, policies, and sequences create new versions rather than overwriting history. Clients send a resource version or conditional request token for user-edited resources; conflicting updates return a conflict response with enough metadata for the client to refresh and resolve intentionally.

### Async command response

An accepted long-running command returns `202 Accepted` with a durable operation reference, current state, and links or identifiers for status retrieval. It does not promise eventual success; clients must inspect terminal status and user-visible error detail.

## 7. Error Handling

Errors follow a consistent machine-readable envelope. Responses never expose stack traces, secrets, provider credentials, or raw model prompts to untrusted clients.

Each error includes a stable `code`, human-readable `message`, HTTP `status`, request/correlation identifier, and optionally structured field errors, a retryability indicator, and a safe documentation link. A user-facing client should display an actionable message while recording the correlation identifier for support.

### HTTP status semantics

| Status | Meaning in SalesOS |
| --- | --- |
| `400` | Invalid command or malformed request that cannot be interpreted. |
| `401` | Missing, invalid, expired, or unverifiable authentication. |
| `403` | Authenticated caller lacks workspace membership, role, or policy permission. |
| `404` | Resource is absent or intentionally undiscoverable to the caller. |
| `409` | Version conflict, invalid state transition, duplicate idempotency conflict, or concurrent modification. |
| `410` | Resource was permanently removed or a short-lived action/download reference expired. |
| `422` | Request schema is valid but business validation fails, such as attempting approval without required evidence. |
| `429` | Applicable rate, concurrency, or quota limit exceeded. |
| `500` | Unexpected server error; a correlation ID is provided. |
| `502` / `503` / `504` | Temporary provider, dependency, or capacity failure; clients should use documented retry guidance. |

State-transition failures identify the blocking condition in a safe, normalized code, such as `approval_required`, `approval_expired`, `suppressed_recipient`, `campaign_not_active`, `integration_unavailable`, or `resource_version_conflict`.

## 8. Pagination

All potentially unbounded collections use cursor pagination. The default ordering is stable and documented per endpoint, usually newest-first by a timestamp plus opaque ID tie-breaker.

### Query contract

- `limit` requests a page size within endpoint-specific bounds; the API applies a conservative default and maximum.
- `cursor` is an opaque continuation token from the previous response; clients must not construct or parse it.
- Responses include `next_cursor` when additional results exist and may include `previous_cursor` only where bidirectional navigation is supported.
- Filters and sorting are endpoint-specific and documented. The cursor encodes the effective ordering/filter context; changing filters or sort requires starting a new traversal.
- Time-range filtering is supported for high-volume activity endpoints such as audit events, email events, and jobs.

Offset pagination is avoided for operational datasets because concurrent writes would produce duplicates and gaps. Exact total counts are omitted by default on high-volume collections; when available, they are explicitly labeled as exact or estimated.

## 9. Rate Limiting

Rate limits protect customer data, provider accounts, model spend, and system availability. Limits are enforced at the API gateway/application layer by authenticated principal, workspace, endpoint class, and IP where appropriate.

### Limit categories

- **Read limits:** high enough for normal interactive clients, with burst protection.
- **Write limits:** lower than reads, including per-resource concurrency safeguards.
- **Expensive command limits:** strict per-workspace budgets for research, generation, report generation, exports, and CRM syncs.
- **Authentication limits:** IP and identity-based protection against credential abuse.
- **Webhook limits:** provider-specific validation and backpressure, separate from end-user quotas.

Responses advertise applicable limit metadata and include `Retry-After` on `429` responses. Idempotent retries after temporary network failures are accepted safely; rate limiting never becomes a reason to create duplicate sends, CRM writes, or workflow runs.

Workspace plans and policies may define higher quotas, but all limits retain system-level caps. Model and provider consumption is attributed to the initiating workspace and surfaced through product telemetry.

## 10. Webhooks

### Inbound provider webhooks

FastAPI exposes dedicated, non-user-facing endpoints for verified providers:

- `POST /v1/webhooks/resend` — delivery, bounce, complaint, and related email lifecycle events.
- `POST /v1/webhooks/hubspot` — authorized CRM changes and OAuth lifecycle events where supported.

These endpoints are not authenticated with user bearer tokens. They verify provider signatures, enforce timestamp/replay protections, apply request-size limits, record an immutable receipt, deduplicate by provider event identifier, and enqueue asynchronous processing. A valid receipt response means the event was durably accepted, not necessarily fully processed.

### Outbound customer webhooks

Outbound customer webhooks are not an MVP requirement. When introduced, customers subscribe to tenant-scoped event types through an integration connection. Deliveries are signed, versioned, retried with exponential backoff, idempotently identified, and observable through a webhook-delivery log. Events include minimal necessary data and respect workspace retention/privacy settings.

### Event schema principles

Webhook payloads include `event_id`, `event_type`, `occurred_at`, `workspace_id` when appropriate, a schema version, and a minimal resource reference or snapshot. Consumers must treat delivery as at-least-once and deduplicate by event ID.

## 11. Background Job APIs

The API represents background work as durable job and workflow resources. It never asks a UI client to poll provider APIs or run agent tasks locally.

### Job lifecycle

A command that requires asynchronous work returns a job reference and, when applicable, a parent LangGraph workflow reference. Jobs expose states such as `queued`, `scheduled`, `running`, `waiting_for_input`, `succeeded`, `failed`, `cancelled`, and `dead_lettered`. Workflow state adds graph-specific progress, checkpoint, and approval-wait context.

### Client capabilities

Authorized clients can:

- Query jobs/workflows by current state, resource subject, campaign, and time range.
- Read safe progress and error summaries, including the relevant correlation ID.
- Retry an eligible failed item under the same tenant and policy scope.
- Cancel a queued or safely cancellable job where the operation has not produced an irreversible external effect.
- Subscribe through Supabase Realtime or a future client notification layer for state updates, while using REST as the authoritative source of truth.

Clients cannot alter queue priority, inject arbitrary agent tools/prompt content, forge workflow transitions, or bypass approval by manipulating a job. Internal worker-only diagnostic details are withheld from normal client representations.

## 12. Security

### Transport, identity, and authorization

- Enforce TLS, secure HTTP headers, CORS allowlists, request-size limits, schema validation, and safe response encoding.
- Validate Supabase JWTs on every authenticated API request and resolve active workspace membership server-side.
- Apply role, resource ownership, campaign policy, and current-state checks for each write command.
- Use Supabase PostgreSQL RLS as database-level defense in depth; the API does not rely on frontend filtering for tenant isolation.

### Secret and data protection

- Keep Supabase service credentials, HubSpot tokens, Resend credentials, and GPT-4.1 mini API credentials server-side in managed secret storage.
- Encrypt integration credentials at rest and return only connection metadata to clients.
- Redact sensitive data from API logs, audit summaries, telemetry, error messages, and model-call observability.
- Generate short-lived, scoped links for any exports or stored artifacts; never expose broad storage credentials.

### Business-action protection

- Require current, valid approval for the exact outbound draft version before creating a sendable delivery.
- Re-check suppression, campaign status, sender policy, recipient eligibility, and approval validity immediately before provider submission.
- Use idempotency keys and transactional state guards to prevent duplicate sends and CRM mutations.
- Verify all provider webhooks and record immutable receipts before processing.
- Treat research content and inbound external text as untrusted; constrain agent tools, validate structured model output, and prevent prompt content from changing authorization or execution policy.

### Observability and incident response

The API produces structured logs, metrics, traces, and immutable audit events with correlation IDs. Security-relevant events include failed authorization, suspicious rate-limit behavior, credential-connection changes, policy changes, approval decisions, delivery commands, and provider signature failures. Operational access uses least privilege and is separately audited.

## 13. Future API Evolution

The initial API supports the approval-first email MVP while preserving room for a broader revenue platform.

- Publish typed SDKs generated from the versioned OpenAPI contract for Web, desktop, mobile, and partner developers.
- Introduce API keys and OAuth client credentials for approved server-to-server integrations, with granular workspace scopes, rotation, and auditability.
- Add Salesforce and other CRM adapters behind the existing integration, mapping, and sync-run resources.
- Add channel-specific APIs for calling, SMS, calendar, and social-assisted workflows only with channel-appropriate consent, approval, and audit controls.
- Add outbound customer webhooks, event subscriptions, and a developer portal with replay/testing facilities.
- Add bulk command APIs that use explicit selection snapshots, dry-run validation, bounded batch sizes, asynchronous execution, and per-item results.
- Add enterprise controls for SSO/SAML, SCIM, custom roles, data residency, customer-managed encryption, legal holds, and advanced retention policies.
- Evolve policy-based automation through explicit policy-evaluation records; no automation path should be opaque or bypass tenant governance.

The API’s lasting contract is that any authorized SalesOS client can understand the state of an outbound action, request allowable work, observe its outcome, and audit why it occurred—without receiving direct access to the systems that perform risky external actions.
