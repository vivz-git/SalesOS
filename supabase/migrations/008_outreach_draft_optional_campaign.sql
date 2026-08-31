-- Migration: Make campaign_id optional in outreach_drafts
ALTER TABLE outreach_drafts ALTER COLUMN campaign_id DROP NOT NULL;

ALTER TABLE outreach_drafts DROP CONSTRAINT outreach_drafts_campaign_id_fkey;
ALTER TABLE outreach_drafts ADD CONSTRAINT outreach_drafts_campaign_id_fkey
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL;
