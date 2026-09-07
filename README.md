# SalesOS

SalesOS is a multi-tenant, **approval-first AI sales operating system** for B2B outbound teams. It takes a campaign from **targeting to conversation** in one workflow instead of stitching together a CRM, research tools, AI copy generators, and email infrastructure.

**Live app:** https://sales-os-frontend-black.vercel.app
**Live API:** https://salesos-production-927e.up.railway.app/health

---

## What it does

**Campaign → Research → AI Outreach → Human Approval → Delivery → Reply Classification → CRM Sync → Reporting**

- **Multi-tenant workspaces** with workspace-scoped data access and role-based membership
- **Accounts & contacts** for managing outbound targets
- **Campaigns & sequences** for ICP definition and multi-step outreach cadences
- **AI-powered research** on accounts and decision-makers, run as a background job
- **AI outreach generation** (Groq-hosted LLM) with structured, versioned drafts
- **Approval queue** — no AI-generated message reaches a prospect without human sign-off
- **Email delivery tracking** through Resend, with webhook-driven status sync
- **Inbound reply handling** with automatic reply-state classification
- **HubSpot integration** for CRM synchronization
- **Weekly reports** for campaign and outreach performance
- **Google OAuth + email/password authentication** via Supabase Auth
- **Background worker** that claims and processes research/outreach/sequence jobs from a Postgres-backed queue

### Why it's different

SalesOS isn't another AI email writer. AI handles research and repetitive drafting; a human always reviews and approves what actually gets sent. That keeps outbound auditable instead of turning it into a black box.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Vitest |
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic Settings, pytest, mypy (strict), ruff |
| Database / Auth | Supabase (Postgres + Row-Level Security + Auth) |
| AI | Groq-hosted LLM (`llama-3.3-70b-versatile`) for research synthesis, outreach drafting, and reply classification |
| Integrations | Resend (email delivery + inbound webhooks), HubSpot CRM (OAuth v3) |
| Hosting | Vercel (frontend), Railway (backend, Docker) |

> Note: earlier docs referenced LangGraph for AI orchestration. The current implementation calls the Groq provider directly from a Postgres-backed job worker (`backend/app/worker.py`); `backend/app/workflows/` is a reserved-but-empty placeholder, not implemented.

```text
                   ┌──────────────────┐
                   │   Next.js App    │
                   │     Vercel       │
                   └────────┬─────────┘
                            │
                     Supabase Auth
                            │
                            ▼
                   ┌──────────────────┐
                   │   FastAPI API    │
                   │     Railway      │
                   └────────┬─────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
     PostgreSQL      Background Worker    Integrations
      Supabase         (Groq LLM)       Resend / HubSpot
```

---

## Repository structure

```text
frontend/    Next.js app (App Router), components, API client, tests
backend/     FastAPI app, adapters (Groq/Resend/HubSpot), async worker, pytest suite
supabase/    Migrations and RLS policies (system of record for schema)
scripts/     Operational scripts, incl. e2e_validation_test.py / prod_smoke_test.py
docs/        Supporting engineering docs
PRD.md, ARCHITECTURE.md, DATABASE.md, API_SPEC.md, AGENTS.md   Canonical product/engineering references
```

---

## Getting started locally

Prerequisites: Node 20+, pnpm, Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker (for local Supabase).

```bash
# 1. Install dependencies
pnpm install
cd backend && uv sync && cd ..

# 2. Start local Supabase (Postgres + Auth), then apply migrations
npx supabase start
npx supabase db reset

# 3. Configure environment
cp .env.example .env    # fill in the Supabase URL/keys printed by `supabase start`

# 4. Run backend and frontend (separate terminals)
cd backend && uv run python run_local.py     # http://127.0.0.1:8000
pnpm dev                                     # http://127.0.0.1:3000
```

Docker Compose (`docker-compose.yml`) is also available to run both services against an `.env` file.

---

## Testing

```bash
# Backend — pytest, ruff, mypy (strict)
cd backend
uv run pytest
uv run ruff check .
uv run mypy app

# Frontend — typecheck, lint, unit tests, production build
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

### Last verified run (this session)

| Check | Result |
|---|---|
| Backend `pytest` | **52 passed, 6 skipped, 0 failed** (skips are integration tests that need a live local Supabase Postgres at `127.0.0.1:54322`, unavailable in this sandbox) |
| Backend `ruff check` | All checks passed |
| Backend `mypy` (strict) | Success — no issues in 32 source files |
| Frontend `tsc --noEmit` | Clean |
| Frontend `eslint` | 0 errors, 4 warnings (missing `useEffect` deps — cosmetic) |
| Frontend `vitest` | **113 passed** across 25 test files |
| Frontend `next build` | Production build succeeded, all 24 routes compiled/pre-rendered |
| Local smoke test | Started backend (`/health` → 200) and frontend dev server; confirmed public auth pages (`/login`, `/signup`) return 200, protected dashboard routes (`/inbox`, `/reports`, `/approvals`, `/campaigns`) correctly 307-redirect unauthenticated users to `/login`, and an unauthenticated `GET /v1/accounts` correctly returns 401 rather than crashing |

The repo also ships two real end-to-end scripts under `scripts/`:
- `e2e_validation_test.py` — full flow (auth → workspace → campaign → account/contact → research job → AI draft → approval → delivery → inbound reply → sequence enrollment → reports) plus cross-tenant isolation checks, run against a **local** Supabase stack.
- `prod_smoke_test.py` — the same authenticated flow run against the **live production** API/Supabase.

Neither was executed in this session: the local one needs `supabase start` (Docker is available but wasn't spun up), and the prod one writes permanent test data into your live production database — run it deliberately, not as part of routine verification, especially not right before a demo.

---

## Project status — is it finished / demo-ready?

**Yes, for a demo.** Every automated check that can run without live third-party credentials is green: backend tests/lint/types, frontend tests/lint/types, and a clean production build. The app is deployed and reachable (Vercel + Railway), auth gating works correctly, and the API rejects unauthenticated requests properly instead of erroring.

What "finished" doesn't mean here — things to know before a live demo or resume claim:

- **Live-data coverage is asserted, not proven, by this session.** The 6 skipped backend tests and the two `scripts/*.py` E2E flows are the tests that actually exercise a full request against a real Postgres/Supabase instance; none ran here. Before a real demo, run `supabase start` once and execute `scripts/e2e_validation_test.py` locally (or `prod_smoke_test.py` against a *staging*, not production, environment) to confirm the full click-path with real data.
- **Demo the golden path in a browser once, live, beforehand:** sign up → create workspace → create campaign → add account/contact → generate research → generate/approve an outreach draft → simulate an inbound reply → view weekly report. This session verified the app *boots and routes correctly*, not that every screen renders pixel-perfect with real data — do that pass yourself or ask for a browser-driven check.
- **AI/email/CRM integrations degrade gracefully but need real keys to demo fully.** `GROQ_API_KEY`, `RESEND_API_KEY`, and `HUBSPOT_CLIENT_ID/SECRET` must be set in the deployed environment for outreach generation, real email delivery, and CRM sync to work end-to-end — confirm these are configured in Railway before presenting.
- **README/architecture drift:** this file previously described AI orchestration via LangGraph; that folder is an empty placeholder. Fixed here to describe what's actually implemented (a direct Groq adapter call from the background worker).
- **Repo hygiene:** one-off `fix_*.py` / `update_*.py` / `check_*.py` patch scripts and a generated `graphify-out/` cache directory from prior UI-polish sessions have been removed from the repo root and are now git-ignored.

### Resume-ready framing

This is a legitimate full-stack, multi-tenant SaaS project worth listing: a typed FastAPI backend with async SQLAlchemy, strict mypy, RLS-based tenant isolation, a background job worker, and three real external integrations (Groq, Resend, HubSpot); a Next.js 15 / React 19 frontend with a real test suite; and a deployed, reachable production instance (Vercel + Railway). It's substantive enough to talk through in an interview — the approval-gate design, RLS-based multi-tenancy, and the async job worker are the parts worth highlighting.
