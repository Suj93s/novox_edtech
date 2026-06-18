-- Migration: Add module awareness to chat_sessions
ALTER TABLE chat_sessions 
ADD COLUMN IF NOT EXISTS module_id UUID REFERENCES novox_curriculum(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_chat_sessions_module_id ON chat_sessions(module_id);
