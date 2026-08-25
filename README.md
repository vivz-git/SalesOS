SalesOS

SalesOS is a multi-tenant B2B sales platform built to take an outbound campaign from **targeting to conversation** in one workflow.

Instead of stitching together a CRM, research tools, AI copy generators, approval tools, and email infrastructure, SalesOS brings the core workflow into one place — with a human approval step before anything is sent.

**Live:** https://sales-os-frontend-black.vercel.app

---

## What it does

SalesOS follows this flow:

**Campaign → Research → AI Outreach → Human Approval → Delivery → Reply Classification → CRM Sync → Reporting**

### Core features

- **Multi-tenant workspaces** with workspace-scoped data access
- **Accounts & contacts** for managing outbound targets
- **Campaigns & sequences** for defining ICP and outreach strategy
- **AI-powered research** for accounts and decision-makers
- **AI outreach generation** with structured drafts and personalization
- **Approval queue** so humans review AI-generated outreach before delivery
- **Email delivery tracking** through Resend
- **Inbound reply handling** with reply-state classification
- **HubSpot integration** for CRM synchronization
- **Reports** for campaign and outreach performance
- **Google OAuth + email/password authentication**
- **Background job processing** for research and outreach workflows

---

## Why SalesOS is different

The goal is not to build another AI email writer.

SalesOS is designed as an **approval-first sales operating system**: AI handles research and repetitive work, while the user keeps control over what actually gets sent.

That makes the system useful for real outbound workflows without turning the sales process into a black box.

---

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
     PostgreSQL         AI / Workers      Integrations
      Supabase           LangGraph        Resend / HubSpot
