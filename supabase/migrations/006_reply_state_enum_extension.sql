-- Migration 006: Extend reply_state ENUM to support standard 6-state taxonomy and guarantee postgrest grants

ALTER TYPE reply_state ADD VALUE IF NOT EXISTS 'interested';
ALTER TYPE reply_state ADD VALUE IF NOT EXISTS 'not_now';
ALTER TYPE reply_state ADD VALUE IF NOT EXISTS 'referral';
ALTER TYPE reply_state ADD VALUE IF NOT EXISTS 'out_of_office';

-- Ensure PostgREST roles have appropriate table permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO postgres, service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
