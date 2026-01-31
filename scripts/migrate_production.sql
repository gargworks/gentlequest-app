-- Migration to add missing columns for Agentic Wellness Interventions and Quests
-- Table: chat_messages
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'none';
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS resources TEXT;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS message_type VARCHAR(50) DEFAULT 'text';

-- Table: quests
ALTER TABLE quests ADD COLUMN IF NOT EXISTS target INTEGER DEFAULT 1;

-- Table: sessions (Added 2026-01-21)
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS conversation_count INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'low';

-- Table: resources (Added 2026-01-21)
ALTER TABLE resources ADD COLUMN IF NOT EXISTS university_id INTEGER;
ALTER TABLE resources ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Table: intervention_outcomes (Ensuring all agentic fields are present)
ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS exercise_type VARCHAR(50);
ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS time_spent_seconds INTEGER;
ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS mood_before INTEGER;
ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS mood_after INTEGER;
