-- SalesOS Phase 1 Infrastructure Migration
-- Establishes RLS context helper functions and least-privilege backend role strategy

-- ROLE STRATEGY (Do not execute without password rotation):
-- To enforce least-privilege, the application DATABASE_URL must connect
-- using a dedicated role, NOT postgres or service_role.
--
-- DO $$
-- BEGIN
--   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'salesos_backend') THEN
--     CREATE ROLE salesos_backend WITH LOGIN PASSWORD '<injected_by_ops>';
--   END IF;
-- END
-- $$;
-- 
-- Ensure the role lacks BYPASSRLS and SUPERUSER privileges.

CREATE OR REPLACE FUNCTION get_app_user_id() RETURNS uuid AS $$
BEGIN
    RETURN NULLIF(current_setting('salesos.app_user_id', true), '')::uuid;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_app_workspace_id() RETURNS uuid AS $$
BEGIN
    RETURN NULLIF(current_setting('salesos.app_workspace_id', true), '')::uuid;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
