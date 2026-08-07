# SalesOS Agent Guide

## 1. Project Purpose

SalesOS is a multi-tenant, approval-first AI sales employee for B2B outbound teams. Preserve customer control, explainability, and auditability in every change.

## 2. Repository Structure

- `frontend/` — Next.js 15, TypeScript, Tailwind CSS, and shadcn/ui application.
- `backend/` — FastAPI application, domain services, integration adapters, and workers.
- `supabase/` — database migrations, RLS policies, and Supabase configuration.
- `prompts/` — versioned AI prompt assets and evaluations.
- `scripts/` — operational and development scripts.
- `docs/` — supporting product and engineering documentation.
- Root documents — canonical product, architecture, data, and API decisions.

## 3. Required Reading Before Coding

Read these in order before changing implementation:

1. `PRD.md` — product scope and MVP boundaries.
2. `ARCHITECTURE.md` — system boundaries and deployment responsibilities.
3. `DATABASE.md` — data ownership, lifecycle, and RLS requirements.
4. `API_SPEC.md` — API contract and integration behavior.

Read the relevant directory for local instructions and existing patterns before editing it.

## 4. Coding Standards

- Use TypeScript in the frontend and typed Python in the backend.
- Prefer small, cohesive modules with explicit inputs, outputs, and errors.
- Validate all external input at service boundaries.
- Keep UI components accessible and use established design-system primitives.
- Keep business rules out of presentation components and provider adapters.
- Add comments only for non-obvious decisions; keep code self-explanatory.

## 5. Architecture Principles

- FastAPI is the authoritative application control plane; clients do not enforce business policy.
- Supabase Postgres is the system of record; use durable state for workflows and external operations.
- Run research, generation, delivery, sync, and reporting asynchronously; make jobs observable and retry-safe.
- Treat LangGraph outputs as untrusted until schema-validated and persisted with provenance.
- Preserve the approval gate: no external message may bypass current, valid human approval.
- Encapsulate HubSpot, Resend, and model-provider behavior behind adapters.

## 6. Naming Conventions

- Use `snake_case` for Python, database fields, API JSON fields, and API route parameters.
- Use `PascalCase` for TypeScript components, types, and classes; use `camelCase` for TypeScript values and functions.
- Use plural, lowercase resource names in API routes; use explicit `/actions/{verb}` routes for governed commands.
- Name IDs with a descriptive suffix where clarity helps (for example, `workspace_id`, `campaign_id`).
- Name state values as stable lowercase strings; do not infer state from timestamps or booleans.

## 7. Testing Expectations

- Test changed behavior at the lowest useful layer and add regression coverage for defects.
- Cover authorization, tenant isolation, state transitions, idempotency, and provider failure paths for backend changes.
- Cover user-visible loading, error, and confirmed-state behavior for frontend changes.
- Use contract tests for API and provider adapters; do not call live production providers in automated tests.
- Run the relevant checks before handoff and report what was run and any limitations.

## 8. Security Rules

- Enforce workspace scope and role authorization on every read and write.
- Preserve and test RLS for tenant-owned data; never rely on frontend filtering for isolation.
- Never expose service credentials, provider tokens, secrets, or raw sensitive payloads to clients or logs.
- Verify inbound webhook signatures and deduplicate provider events.
- Re-check suppression, policy, approval, and eligibility immediately before external delivery.
- Append audit events for material user, system, agent, provider, and administrative actions; never rewrite history.

## 9. Rules for Modifying Code

- Make the smallest change that satisfies the requested behavior and preserves documented contracts.
- Do not change product scope, API semantics, schema ownership, or approval behavior without updating the canonical document first or alongside the implementation.
- Use migrations for schema changes; do not modify applied migrations.
- Keep external effects idempotent, transactional where possible, and observable when asynchronous.
- Maintain backward compatibility within the current API major version.
- Do not remove tests, security controls, audit events, or error handling to simplify a change.

## 10. Rules for Future AI Agents

- Inspect existing code and relevant canonical documents before proposing or making changes.
- State assumptions when requirements are ambiguous; do not silently expand scope.
- Do not invent alternate architecture or bypass established boundaries without an explicit decision.
- Preserve unrelated user changes in a dirty worktree.
- Prefer evidence-backed conclusions; verify changes proportionally to risk.
- Keep documentation concise and link to the canonical file instead of duplicating it.
