-- Phase 2 Migration: Core Identity & CRM Schema

-- 1. Create Tables

CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TYPE membership_role AS ENUM ('owner', 'admin', 'manager', 'contributor', 'viewer');

CREATE TABLE memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role membership_role NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(workspace_id, user_id)
);

CREATE TYPE campaign_status AS ENUM ('draft', 'active', 'paused', 'archived');

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(1000),
    target_segment VARCHAR(255),
    icp_definition VARCHAR(2000),
    status campaign_status DEFAULT 'draft' NOT NULL,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TYPE account_status AS ENUM ('target', 'qualified', 'disqualified', 'archived');

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(100),
    employee_count VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    status account_status DEFAULT 'target' NOT NULL,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TYPE contact_status AS ENUM ('active', 'unresponsive', 'opted_out', 'archived');

CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    title VARCHAR(100),
    department VARCHAR(100),
    linkedin_url VARCHAR(255),
    is_primary BOOLEAN DEFAULT false NOT NULL,
    status contact_status DEFAULT 'active' NOT NULL,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

-- 2. Indexes

CREATE INDEX idx_memberships_user_id ON memberships(user_id);
CREATE INDEX idx_memberships_workspace_id ON memberships(workspace_id);
CREATE INDEX idx_campaigns_workspace_id ON campaigns(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_accounts_workspace_id ON accounts(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_contacts_workspace_id ON contacts(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_contacts_account_id ON contacts(account_id);

-- 3. Enable RLS

ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies for salesos_backend

-- Workspaces and Memberships (SELECT ONLY for backend role, insertion handled by REST admin_client)
CREATE POLICY "tenant_isolation_workspaces" ON workspaces FOR SELECT TO salesos_backend
USING (id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_memberships" ON memberships FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id() OR user_id = get_app_user_id());

-- Campaigns
CREATE POLICY "tenant_isolation_campaigns_select" ON campaigns FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_campaigns_insert" ON campaigns FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_campaigns_update" ON campaigns FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id())
WITH CHECK (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_campaigns_delete" ON campaigns FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- Accounts
CREATE POLICY "tenant_isolation_accounts_select" ON accounts FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_accounts_insert" ON accounts FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_accounts_update" ON accounts FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id())
WITH CHECK (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_accounts_delete" ON accounts FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- Contacts
CREATE POLICY "tenant_isolation_contacts_select" ON contacts FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_contacts_insert" ON contacts FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_contacts_update" ON contacts FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id())
WITH CHECK (workspace_id = get_app_workspace_id());

CREATE POLICY "tenant_isolation_contacts_delete" ON contacts FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- 5. GRANTS

GRANT SELECT ON workspaces TO salesos_backend;
GRANT SELECT ON memberships TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON campaigns TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON accounts TO salesos_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON contacts TO salesos_backend;
