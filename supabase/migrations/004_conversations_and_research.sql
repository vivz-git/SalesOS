-- Phase 4 Migration: Conversations, Research & Approval Audit Persistence

-- 1. Create Types
CREATE TYPE conversation_status AS ENUM ('active', 'needs_human_action', 'closed', 'opt_out');
CREATE TYPE conversation_direction AS ENUM ('inbound', 'outbound');
CREATE TYPE reply_state AS ENUM ('positive', 'objection', 'unsubscribe', 'question', 'ambiguous', 'not_applicable');
CREATE TYPE research_status AS ENUM ('pending', 'in_progress', 'completed', 'failed');
CREATE TYPE approval_decision_type AS ENUM ('approved', 'rejected', 'returned_to_draft');

-- 2. Create Tables

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    delivery_id UUID REFERENCES deliveries(id) ON DELETE SET NULL,
    status conversation_status NOT NULL DEFAULT 'active',
    current_reply_state reply_state,
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (workspace_id, contact_id)
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    direction conversation_direction NOT NULL DEFAULT 'inbound',
    sender_email VARCHAR(255) NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT,
    body TEXT,
    provider_message_id VARCHAR(255),
    delivery_id UUID REFERENCES deliveries(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (provider_message_id) -- INBOUND WEBHOOK IDEMPOTENCY
);

CREATE TABLE reply_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES conversation_messages(id) ON DELETE CASCADE,
    reply_state reply_state NOT NULL,
    confidence_score NUMERIC(4,3) DEFAULT 1.0,
    explanation TEXT,
    needs_human_action BOOLEAN NOT NULL DEFAULT FALSE,
    classified_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (message_id)
);

CREATE TABLE research_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    summary TEXT,
    key_findings JSONB,
    status research_status NOT NULL DEFAULT 'pending',
    confidence_score NUMERIC(4,3),
    confidence_reason TEXT,
    provider VARCHAR(100),
    model VARCHAR(100),
    prompt_version VARCHAR(50),
    generated_at TIMESTAMPTZ,
    token_usage INTEGER,
    estimated_cost NUMERIC(10,5),
    duration_ms INTEGER,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE research_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    brief_id UUID NOT NULL REFERENCES research_briefs(id) ON DELETE CASCADE,
    url VARCHAR(500),
    title VARCHAR(255),
    source_type VARCHAR(50) NOT NULL DEFAULT 'website',
    snippet TEXT,
    confidence NUMERIC(4,3) DEFAULT 1.0,
    raw_content_hash VARCHAR(128),
    retrieved_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE approval_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    draft_id UUID NOT NULL REFERENCES outreach_drafts(id) ON DELETE CASCADE,
    version_id UUID REFERENCES draft_versions(id) ON DELETE SET NULL,
    version_number INTEGER NOT NULL,
    reviewer_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    decision approval_decision_type NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    actor_type VARCHAR(50) NOT NULL,
    actor_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Indexes
CREATE INDEX idx_conversations_workspace_id ON conversations(workspace_id);
CREATE INDEX idx_conversation_messages_workspace_id ON conversation_messages(workspace_id);
CREATE INDEX idx_reply_classifications_workspace_id ON reply_classifications(workspace_id);
CREATE INDEX idx_research_briefs_workspace_id ON research_briefs(workspace_id);
CREATE INDEX idx_research_sources_workspace_id ON research_sources(workspace_id);
CREATE INDEX idx_approval_decisions_workspace_id ON approval_decisions(workspace_id);
CREATE INDEX idx_audit_events_workspace_id ON audit_events(workspace_id);

-- 4. Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE reply_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies for salesos_backend

-- conversations
CREATE POLICY "tenant_isolation_conversations_select" ON conversations FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_conversations_insert" ON conversations FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_conversations_update" ON conversations FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_conversations_delete" ON conversations FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- conversation_messages
CREATE POLICY "tenant_isolation_conversation_messages_select" ON conversation_messages FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_conversation_messages_insert" ON conversation_messages FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_conversation_messages_update" ON conversation_messages FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_conversation_messages_delete" ON conversation_messages FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- reply_classifications
CREATE POLICY "tenant_isolation_reply_classifications_select" ON reply_classifications FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_reply_classifications_insert" ON reply_classifications FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_reply_classifications_update" ON reply_classifications FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_reply_classifications_delete" ON reply_classifications FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- research_briefs
CREATE POLICY "tenant_isolation_research_briefs_select" ON research_briefs FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_research_briefs_insert" ON research_briefs FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_research_briefs_update" ON research_briefs FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_research_briefs_delete" ON research_briefs FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- research_sources
CREATE POLICY "tenant_isolation_research_sources_select" ON research_sources FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_research_sources_insert" ON research_sources FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_research_sources_update" ON research_sources FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_research_sources_delete" ON research_sources FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- approval_decisions
CREATE POLICY "tenant_isolation_approval_decisions_select" ON approval_decisions FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_approval_decisions_insert" ON approval_decisions FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_approval_decisions_update" ON approval_decisions FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_approval_decisions_delete" ON approval_decisions FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- audit_events
CREATE POLICY "tenant_isolation_audit_events_select" ON audit_events FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_audit_events_insert" ON audit_events FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_audit_events_update" ON audit_events FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_audit_events_delete" ON audit_events FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- 6. Grant Permissions to salesos_backend
GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversation_messages TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON reply_classifications TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON research_briefs TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON research_sources TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON approval_decisions TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON audit_events TO salesos_backend;
