# SalesOS

SalesOS is a **multi-tenant B2B sales platform** that uses AI to take outbound work from **prospect research to conversation** in one workflow.

Instead of switching between a CRM, research tools, AI writing tools, approval screens, and email infrastructure, SalesOS brings the core workflow into one place — with **human approval before anything is sent**.

**Live:** https://sales-os-frontend-black.vercel.app

## What it does

SalesOS follows a simple workflow:

**Prospect → Research → AI Outreach → Human Review → Send → Reply → Classification**

### Core features

- **Multi-tenant workspaces** with workspace-scoped data access
- **Accounts and contacts** for managing prospects
- **Campaigns and sequences** for outbound planning
- **AI research** for companies and decision-makers
- **AI-generated personalized outreach** based on prospect context
- **Human approval workflow** before email delivery
- **Email delivery tracking** with Resend
- **Inbound reply handling and intent classification**
- **HubSpot CRM integration**
- **Reports** for outreach activity and performance
- **Google OAuth and email/password authentication**
- **Background workers** for research and outreach jobs

## Why SalesOS?

SalesOS is not just an AI email writer.

The goal is to automate the repetitive parts of sales work while keeping the user in control of important actions.

For example:

Add Prospect
↓
Research
↓
Generate Personalized Email
↓
Human Review
↓
Approve & Send
↓
Track Delivery
↓
Receive Reply
↓
Classify Intent

The AI can **prepare** the work, but it does not get the final authority to send an email on its own.

## Architecture

## Architecture

```text
                    ┌─────────────────────┐
                    │   Next.js Frontend  │
                    │       Vercel        │
                    └──────────┬──────────┘
                               │
                         Supabase Auth
                               │
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI API     │
                    │       Railway       │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌─────────────┐
       │ Supabase   │   │ LangGraph  │   │ Integrations│
       │ PostgreSQL │   │ AI Workers │   │ Resend      │
       │    + RLS   │   │            │   │ HubSpot     │
       └────────────┘   └────────────┘   └─────────────┘

## Tech Stack

**Frontend:** Next.js, React, TypeScript, Tailwind CSS

**Backend:** FastAPI, Python

**Database & Auth:** Supabase, PostgreSQL, Row Level Security

**AI & Workflows:** LangGraph, LLM-based research and outreach generation

**Integrations:** Resend, HubSpot

**Deployment:** Vercel, Railway

## Engineering Highlights

- Human-in-the-loop approval before external email delivery
- Multi-tenant workspace isolation
- Background processing for AI research and outreach workflows
- Versioned outreach drafts and approval states
- Idempotent email delivery flow
- Automated frontend and backend testing
- Responsive production UI

## Project Goal

SalesOS is built as a **production-style AI workflow system**: simple for the user on the surface, while the underlying system handles AI orchestration, state transitions, integrations, and safety controls.
