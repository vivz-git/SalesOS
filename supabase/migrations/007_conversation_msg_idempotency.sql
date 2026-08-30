-- migration file 007_conversation_msg_idempotency.sql

-- Deduplicate existing rows keeping the oldest one
DELETE FROM conversation_messages
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY workspace_id, provider_message_id
                   ORDER BY created_at ASC
               ) as row_num
        FROM conversation_messages
        WHERE provider_message_id IS NOT NULL
    ) t
    WHERE t.row_num > 1
);

-- Create partial unique index
CREATE UNIQUE INDEX IF NOT EXISTS uq_conversation_msg_provider
ON conversation_messages (workspace_id, provider_message_id)
WHERE provider_message_id IS NOT NULL;
