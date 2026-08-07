# SalesOS Product Requirements Document

**Product:** SalesOS  
**Category:** AI Sales Employee for B2B outbound teams  
**Status:** MVP definition  
**Principle:** Autonomous preparation; human-controlled sending.

## 1. Vision

SalesOS is the AI Sales Employee for B2B companies: a trusted teammate that turns an ideal-customer profile into well-researched, personalized outbound opportunities—without replacing the judgment, brand voice, or control of the sales team.

Sales teams should spend their time in conversations with qualified buyers, not assembling prospect lists, reading company websites, drafting first touches, chasing follow-ups, or manually updating CRM records. SalesOS owns that repetitive operating layer and makes every action inspectable, approval-gated, and measurable.

## 2. Problem Statement

Modern B2B outbound is expensive, fragmented, and difficult to scale with quality. Reps must move between data sources, LinkedIn, company websites, inboxes, sequencing tools, and CRMs. The result is inconsistent research, generic messages, incomplete CRM data, and limited visibility into what is actually working.

Existing tools either provide data without execution, automate execution without sufficient context, or force teams to sacrifice personalization for volume. Leaders need pipeline creation that is repeatable and auditable; reps need leverage, not another dashboard.

SalesOS solves this by converting a campaign brief into a reviewed, CRM-connected outbound workflow: research, relevance, copy, sequencing, approval, execution, and reporting.

## 3. Target Customers

### Primary customer

B2B SaaS and technology-enabled service companies with 5–100 go-to-market employees, a defined ideal customer profile, and an outbound motion led by founders, SDRs, AEs, or demand-generation teams.

### Early-adopter profile

- Selling products with annual contract values typically above $10,000.
- Using a CRM such as HubSpot or Salesforce.
- Running outbound email and/or LinkedIn-led prospecting.
- Feeling constrained by SDR capacity, research quality, or CRM hygiene.
- Willing to keep a human in the approval loop while automation earns trust.

### Buyer

VP Sales, Head of Growth, Revenue Operations leader, or founder. The buyer is accountable for pipeline efficiency, team productivity, and brand/reputational risk.

## 4. User Personas

### Sales Leader

Owns pipeline targets and outbound quality. Needs confidence that campaigns align with positioning, segments, and guardrails; wants clear performance and activity reporting.

### Account Executive / SDR

Owns prospect conversations and revenue outcomes. Needs high-quality account context, fast-to-review drafts, timely follow-ups, and less administrative work.

### Revenue Operations Manager

Owns the sales systems and data integrity. Needs reliable CRM sync, configurable fields and ownership rules, campaign governance, and complete auditability.

### Founder / GTM Generalist

Often runs early sales personally. Needs a way to create a credible outbound motion without hiring a full outbound team or compromising the founder’s voice.

## 5. Core Features

### 5.1 Campaign workspace

Users define an ICP, target segment, value proposition, offer, tone, exclusions, and desired call to action. SalesOS turns this brief into a campaign with explicit operating rules.

### 5.2 Company research

For each target account, SalesOS builds a concise research profile from approved sources: company description, industry, size, recent signals, likely business priorities, and reasons the account matches the campaign.

### 5.3 Decision-maker research

SalesOS identifies relevant buying roles and produces a contact brief containing role relevance, publicly available professional context, and suggested personalization angles. It must distinguish verified facts from model-generated inferences.

### 5.4 Personalized outreach generation

SalesOS drafts channel-appropriate outreach grounded in the account and contact brief. Every message includes traceable research inputs and can be edited, regenerated, or rejected by a user.

### 5.5 Follow-up sequence generation

SalesOS proposes a multi-step follow-up sequence with message variants, timing, stop conditions, and a campaign-specific CTA. The system pauses or stops sequences when a reply, opt-out, or configured CRM event occurs.

### 5.6 Approval queue

No external message is sent without explicit human approval in the MVP. Users can approve, edit and approve, reject, or bulk-approve only within configured campaign guardrails. Approval history is retained.

### 5.7 CRM synchronization

SalesOS creates or updates contacts, accounts, activities, campaign membership, and relevant engagement data in the connected CRM. Syncs should be idempotent, visible, and recoverable when fields conflict.

### 5.8 Conversation tracking

SalesOS centralizes sent messages, replies, contact status, and next recommended action. It detects key response states such as interested, not now, referral, unsubscribe, and out of office, while routing ambiguous cases to a human.

### 5.9 Audit log and governance

Every material action is recorded: research sources, generated content, edits, approvals, sends, CRM updates, automated classifications, and failures. Administrators can review who did what and when.

### 5.10 Weekly reporting

SalesOS sends a digest of pipeline activity and learning: accounts researched, contacts activated, approval rate, sends, replies, positive replies, meetings, sequence performance, and recommended campaign changes.

## 6. User Journey

1. A sales leader connects the CRM, configures sender identity and approval rules, and creates a campaign from an ICP and offer.
2. SalesOS imports or receives a target-account list, validates eligibility, and researches each company and relevant decision makers.
3. The user reviews account briefs and removes unsuitable accounts or contacts.
4. SalesOS generates personalized first-touch messages and follow-up sequences, with evidence behind each personalization claim.
5. The user works through the approval queue—editing, approving, or rejecting drafts. Approved messages are queued for delivery within campaign rules.
6. SalesOS records sends and CRM activity, tracks replies, halts the appropriate sequence steps, and surfaces conversations requiring a human response.
7. The team reviews weekly performance, learns which segments and messages are effective, and refines future campaigns.

## 7. MVP Scope

The MVP proves a single high-value loop: **campaign brief → researched prospects → approved personalized email → CRM activity → reply visibility → weekly report**.

Included:

- One workspace with role-based admin and contributor access.
- Campaign creation for a supplied account/contact list.
- Company and contact research briefs using supported public data sources.
- AI-generated personalized email first touches and a three-step email follow-up sequence.
- Draft-level citation/evidence display and manual editing.
- Mandatory per-message human approval before sending.
- Email sending through one supported connected mailbox or approved sending provider.
- HubSpot integration for contacts, companies, notes/activities, and campaign-related status.
- Reply ingestion and basic reply-state classification with human escalation.
- Immutable audit log for generation, approval, send, and CRM-sync events.
- In-product and email weekly report.

MVP quality bar:

- A user can understand why a prospect was selected and why a message was written.
- A user can prevent any message from being sent before it leaves the system.
- CRM records remain attributable, deduplicated, and operationally useful.
- Failures are visible; silent drops are unacceptable.

## 8. Out of Scope

- Fully autonomous sending or autonomous response handling.
- Calling, voicemail, SMS, WhatsApp, or social-network message delivery.
- Building or reselling a proprietary global prospect database.
- Replacing the CRM, sales engagement platform, or customer support system.
- Complex deal forecasting, quote generation, contract workflows, or revenue intelligence.
- Multi-language content generation and localization beyond English.
- Advanced deliverability infrastructure, inbox warm-up, or send-volume optimization.
- Native Salesforce integration in the first release.
- Custom workflow builders and arbitrary third-party integrations.

## 9. Success Metrics

### North-star metric

**Human-approved, qualified outbound conversations per active workspace per week.** A qualified conversation is a positive reply, referral to a relevant buyer, or booked meeting, as confirmed by the user or CRM state.

### Product adoption

- At least 60% of newly created workspaces launch their first approved campaign within seven days.
- At least 50% of weekly active workspaces approve and send outreach in three of four weeks.
- Median time from campaign creation to first approved message is under 30 minutes.

### Quality and trust

- At least 70% of generated drafts are approved with only light or no editing.
- Less than 2% of approved drafts are rejected due to factual or personalization errors.
- 100% of sends and CRM mutations have an auditable event trail.
- Zero messages are sent without the required approval.

### Business impact

- Active customers generate a positive-reply rate at or above their pre-SalesOS outbound baseline within 60 days.
- Users report at least a 50% reduction in manual research and first-draft time per prospect.
- At least 20% of active workspaces convert to paid within the first defined pilot cohort.

## 10. Future Roadmap

### Phase 1: Earn trust

Improve research accuracy, personalization controls, campaign collaboration, HubSpot depth, and reporting. Introduce team-level style guides, reusable campaign templates, and granular approval policies.

### Phase 2: Expand channels and intelligence

Add Salesforce, additional email and enrichment providers, LinkedIn-assisted workflows where permitted, stronger buying-signal detection, A/B testing, and account prioritization.

### Phase 3: Guided autonomy

Allow customers to opt into constrained automation for low-risk actions: auto-enriching CRM records, automatically scheduling approved sequence steps, and suggested response drafts. Automation remains policy-bound, reversible, and fully logged.

### Phase 4: AI revenue operating system

Extend from outbound execution into territory planning, account orchestration, multithreaded buying-committee engagement, learning across campaigns, and executive-level pipeline recommendations. SalesOS becomes the system that continuously turns market signals into responsible sales action.
