-- Phase 3 Migration: Sequences, Jobs, Drafts, Deliveries

-- 1. Create Types

CREATE TYPE sequence_step_type AS ENUM ('first_touch', 'follow_up');
CREATE TYPE sequence_status AS ENUM ('pending_approval', 'active', 'paused', 'stopped', 'completed', 'failed');
CREATE TYPE job_status AS ENUM ('pending', 'running', 'failed', 'completed');
CREATE TYPE draft_status AS ENUM ('draft', 'ready_for_review', 'approved', 'rejected', 'superseded', 'archived');
CREATE TYPE draft_generation_source AS ENUM ('human', 'ai_generated', 'template', 'ai_assisted');
CREATE TYPE delivery_status AS ENUM ('queued', 'running', 'sent', 'delivered', 'failed', 'bounced', 'complained');

-- 2. Create Tables

CREATE TABLE sequence_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (campaign_id, version_number)
);

CREATE TABLE sequence_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_id UUID NOT NULL REFERENCES sequence_definitions(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    delay_days INTEGER NOT NULL DEFAULT 0,
    channel VARCHAR(50) NOT NULL DEFAULT 'email',
    step_type sequence_step_type NOT NULL DEFAULT 'first_touch',
    template_subject VARCHAR(255),
    template_body TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (sequence_id, step_number)
);

CREATE TABLE sequence_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    sequence_id UUID NOT NULL REFERENCES sequence_definitions(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    current_step_number INTEGER NOT NULL DEFAULT 1,
    status sequence_status NOT NULL DEFAULT 'pending_approval',
    stop_reason VARCHAR(255),
    next_step_due_at TIMESTAMPTZ,
    enrolled_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    enrolled_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (contact_id, campaign_id)
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    job_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status job_status NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Unique index to prevent duplicate jobs for the same enrollment step (while pending or running)
CREATE UNIQUE INDEX idx_unique_active_enrollment_step ON jobs ((payload->>'enrollment_id'), (payload->>'step_number')) WHERE status IN ('pending', 'running');

CREATE TABLE outreach_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    sequence_enrollment_id UUID REFERENCES sequence_enrollments(id) ON DELETE SET NULL,
    sequence_step_number INTEGER,
    research_brief_id UUID,
    current_version_id UUID,
    current_version_number INTEGER NOT NULL DEFAULT 1,
    current_subject VARCHAR(255),
    current_body TEXT,
    status draft_status NOT NULL DEFAULT 'draft',
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (sequence_enrollment_id, sequence_step_number)
);

CREATE TABLE draft_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    draft_id UUID NOT NULL REFERENCES outreach_drafts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL DEFAULT 1,
    subject VARCHAR(255),
    body TEXT NOT NULL,
    generation_source draft_generation_source NOT NULL DEFAULT 'human',
    provider VARCHAR(100),
    model VARCHAR(100),
    prompt_version VARCHAR(50),
    research_brief_id UUID,
    research_brief_version INTEGER,
    evidence_references JSONB,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (draft_id, version_number)
);

-- Add Foreign Key constraint for current_version_id now that draft_versions exists
ALTER TABLE outreach_drafts 
    ADD CONSTRAINT fk_outreach_drafts_current_version_id 
    FOREIGN KEY (current_version_id) REFERENCES draft_versions(id) ON DELETE SET NULL;

CREATE TABLE deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    draft_id UUID NOT NULL REFERENCES outreach_drafts(id) ON DELETE CASCADE,
    version_id UUID REFERENCES draft_versions(id) ON DELETE SET NULL,
    version_number INTEGER NOT NULL,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    body TEXT,
    provider VARCHAR(100) NOT NULL DEFAULT 'resend',
    provider_message_id VARCHAR(255),
    status delivery_status NOT NULL DEFAULT 'queued',
    idempotency_key VARCHAR(255) NOT NULL UNIQUE,
    error_message TEXT,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Indexes

CREATE INDEX idx_sequence_enrollments_workspace_id ON sequence_enrollments(workspace_id);
CREATE INDEX idx_sequence_enrollments_contact_id ON sequence_enrollments(contact_id);
CREATE INDEX idx_jobs_workspace_id ON jobs(workspace_id);
CREATE INDEX idx_jobs_polling ON jobs(status, available_at) WHERE status IN ('pending', 'failed');
CREATE INDEX idx_outreach_drafts_workspace_id ON outreach_drafts(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_draft_versions_workspace_id ON draft_versions(workspace_id);
CREATE INDEX idx_deliveries_workspace_id ON deliveries(workspace_id);

-- 4. Enable RLS

ALTER TABLE sequence_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sequence_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE sequence_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE draft_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies for salesos_backend

-- sequence_definitions
CREATE POLICY "tenant_isolation_sequence_definitions_select" ON sequence_definitions FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_sequence_definitions_insert" ON sequence_definitions FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_sequence_definitions_update" ON sequence_definitions FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_sequence_definitions_delete" ON sequence_definitions FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- sequence_steps
CREATE POLICY "tenant_isolation_sequence_steps_select" ON sequence_steps FOR SELECT TO salesos_backend
USING (sequence_id IN (SELECT id FROM sequence_definitions WHERE workspace_id = get_app_workspace_id()));
CREATE POLICY "tenant_isolation_sequence_steps_insert" ON sequence_steps FOR INSERT TO salesos_backend
WITH CHECK (sequence_id IN (SELECT id FROM sequence_definitions WHERE workspace_id = get_app_workspace_id()));
CREATE POLICY "tenant_isolation_sequence_steps_update" ON sequence_steps FOR UPDATE TO salesos_backend
USING (sequence_id IN (SELECT id FROM sequence_definitions WHERE workspace_id = get_app_workspace_id()))
WITH CHECK (sequence_id IN (SELECT id FROM sequence_definitions WHERE workspace_id = get_app_workspace_id()));
CREATE POLICY "tenant_isolation_sequence_steps_delete" ON sequence_steps FOR DELETE TO salesos_backend
USING (sequence_id IN (SELECT id FROM sequence_definitions WHERE workspace_id = get_app_workspace_id()));

-- sequence_enrollments
CREATE POLICY "tenant_isolation_sequence_enrollments_select" ON sequence_enrollments FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_sequence_enrollments_insert" ON sequence_enrollments FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_sequence_enrollments_update" ON sequence_enrollments FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_sequence_enrollments_delete" ON sequence_enrollments FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- jobs
CREATE POLICY "tenant_isolation_jobs_select" ON jobs FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_jobs_insert" ON jobs FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_jobs_update" ON jobs FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_jobs_delete" ON jobs FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- outreach_drafts
CREATE POLICY "tenant_isolation_outreach_drafts_select" ON outreach_drafts FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_outreach_drafts_insert" ON outreach_drafts FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_outreach_drafts_update" ON outreach_drafts FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_outreach_drafts_delete" ON outreach_drafts FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- draft_versions
CREATE POLICY "tenant_isolation_draft_versions_select" ON draft_versions FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_draft_versions_insert" ON draft_versions FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_draft_versions_update" ON draft_versions FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_draft_versions_delete" ON draft_versions FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- deliveries
CREATE POLICY "tenant_isolation_deliveries_select" ON deliveries FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_deliveries_insert" ON deliveries FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_deliveries_update" ON deliveries FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_deliveries_delete" ON deliveries FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- 6. Grant Permissions to salesos_backend
GRANT SELECT, INSERT, UPDATE, DELETE ON sequence_definitions TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON sequence_steps TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON sequence_enrollments TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON jobs TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON outreach_drafts TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON draft_versions TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON deliveries TO salesos_backend;
