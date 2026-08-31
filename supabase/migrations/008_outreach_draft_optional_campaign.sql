-- Migration: Make campaign_id optional in outreach_drafts
ALTER TABLE outreach_drafts ALTER COLUMN campaign_id DROP NOT NULL;
