# SalesOS

SalesOS is an approval-first AI sales operating system that unifies B2B targeting, account research, outreach generation, and CRM synchronization into a single governed workflow.

**Live App:** https://sales-os-frontend-black.vercel.app

## What it does

**Prospect → Research → AI Outreach → Human Approval → Delivery → Reply Classification → CRM / Reporting**

AI handles account research and drafts personalized outreach in the background, but no email is sent without human review. SalesOS keeps outbound messaging governed, auditable, and aligned with pipeline goals.

- **Prospect & Account Management:** Organize target accounts, contacts, and ICP criteria.
- **Automated Research:** Synthesize company context and decision-maker signals via background jobs.
- **AI-Personalized Outreach:** Generate structured, versioned email drafts using Groq-hosted LLMs.
- **Human Approval Gate:** Review, edit, approve, or reject drafts before delivery.
- **Delivery Tracking:** Send emails via Resend with webhook-driven delivery and engagement status.
- **Reply Classification:** Categorize inbound prospect responses automatically into actionable intent states.
- **HubSpot CRM Integration:** Sync contacts, engagements, and outreach lifecycle stages bidirectionally.
- **Performance Reporting:** Track campaign velocity, approval rates, and outreach conversions.

## Architecture

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

FastAPI acts as the authoritative control plane managing multi-tenant state and RLS in PostgreSQL, while an asynchronous worker handles background research, Groq generation, and third-party delivery/sync.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic, pytest, mypy |
| Database / Auth | Supabase (PostgreSQL, Row-Level Security, Auth) |
| AI | Groq LLM (`llama-3.3-70b-versatile`) |
| Integrations | Resend (email delivery + webhooks), HubSpot CRM (OAuth v3) |
| Hosting | Vercel (frontend), Railway (backend, Docker) |

## Results

Evaluated using the application's real code paths (reply classifier, draft/approval workflow, test suites) on synthetic benchmark datasets. Full reproducible evaluation: [`backend/evaluation/`](backend/evaluation/).

| Metric | Result | Context |
|---|---|---|
| Reply-intent classification | **86.8%** (33/38 correct) | Tested on 38 labeled B2B reply scenarios |
| Human approval outcomes | **7 as-is / 6 with edits / 5 rejected** | 18 synthetic prospects run through the review rubric |
| Backend test suite | **58 passed** (77.4% line coverage) | `pytest` + `pytest-cov` across domain and service layers |
| Frontend test suite | **113 passed** across 25 files | `vitest` covering components, hooks, and routing |
| Human effort comparison | **~15–20 min manual vs. ~2–3 min review** | **ESTIMATE:** manual research & drafting vs. SalesOS review |

- **Synthetic evaluation:** Metrics are derived from synthetic test datasets and rubric evaluations, not production benchmarks.
- **Classifier boundary:** The rule-based classifier handles 8 intent categories; misses reflect realistic phrasing variations not matched by current pattern rules.
- **Workflow verification:** Approval distributions confirm end-to-end draft lifecycle and review controls rather than live production copy quality.

## Run locally

```bash
# 1. Install dependencies
pnpm install
cd backend && uv sync && cd ..

# 2. Start local Supabase & apply migrations
npx supabase start
npx supabase db reset

# 3. Configure environment
cp .env.example .env

# 4. Start backend
cd backend && uv run python run_local.py    # http://127.0.0.1:8000

# 5. Start frontend
pnpm dev                                    # http://127.0.0.1:3000
```

## Testing

Verified across 58 backend tests (77.4% coverage) and 113 frontend tests.

```bash
# Backend (pytest, ruff, mypy strict)
cd backend
uv run pytest
uv run ruff check .
uv run mypy app

# Frontend (typecheck, lint, vitest, build)
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

## Known limitations

- **Local Supabase requirement:** Several live-data integration tests require a running local Supabase Postgres instance.
- **Provider credentials:** Full external email delivery, LLM generation, and CRM sync require active Resend, Groq, and HubSpot credentials.
- **Rule-based classifier:** The reply classifier uses pattern matching and has known phrasing/paraphrase blind spots compared to semantic models.
- **Synthetic evaluation data:** Reported metrics reflect synthetic test fixtures rather than live production outbound campaigns.
- **Production smoke testing:** `scripts/prod_smoke_test.py` writes real test data and should only be executed deliberately.
