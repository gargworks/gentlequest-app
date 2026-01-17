-- Database Optimization Script for GentleQuest
-- Run with: psql mental_health < scripts/database_optimization.sql

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Messages table (chat history queries)
CREATE INDEX IF NOT EXISTS idx_messages_session_timestamp 
ON messages(session_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
ON messages(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_messages_risk_level 
ON messages(risk_level) 
WHERE risk_level IN ('high', 'crisis');

-- Mood entries (mood history and analytics)
CREATE INDEX IF NOT EXISTS idx_mood_entries_session_timestamp 
ON mood_entries(session_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_mood_entries_timestamp 
ON mood_entries(timestamp DESC);

-- Clinical assessments (outcome tracking)
CREATE INDEX IF NOT EXISTS idx_clinical_assessments_session_timestamp 
ON clinical_assessments(session_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_clinical_assessments_type_timestamp 
ON clinical_assessments(assessment_type, timestamp DESC);

-- Crisis detections (safety monitoring)
CREATE INDEX IF NOT EXISTS idx_crisis_detections_session_timestamp 
ON crisis_detections(session_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_crisis_detections_risk_timestamp 
ON crisis_detections(risk_level, timestamp DESC);

-- Sessions (cleanup and analytics)
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity 
ON sessions(last_activity DESC);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at 
ON sessions(created_at DESC);

-- Analytics events (reporting)
CREATE INDEX IF NOT EXISTS idx_analytics_events_session_timestamp 
ON analytics_events(session_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_events_type_timestamp 
ON analytics_events(event_type, timestamp DESC);

-- ============================================================================
-- QUERY OPTIMIZATION
-- ============================================================================

-- Analyze tables to update statistics
ANALYZE messages;
ANALYZE mood_entries;
ANALYZE clinical_assessments;
ANALYZE crisis_detections;
ANALYZE sessions;
ANALYZE analytics_events;

-- Vacuum to reclaim space and update statistics
VACUUM ANALYZE messages;
VACUUM ANALYZE mood_entries;
VACUUM ANALYZE clinical_assessments;

-- ============================================================================
-- MONITORING VIEWS
-- ============================================================================

-- Daily active users
CREATE OR REPLACE VIEW v_daily_active_users AS
SELECT 
    DATE(timestamp) as date,
    COUNT(DISTINCT session_id) as dau,
    COUNT(*) as total_messages
FROM messages
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Weekly active users
CREATE OR REPLACE VIEW v_weekly_active_users AS
SELECT 
    DATE_TRUNC('week', timestamp) as week,
    COUNT(DISTINCT session_id) as wau,
    COUNT(*) as total_messages
FROM messages
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '90 days'
GROUP BY DATE_TRUNC('week', timestamp)
ORDER BY week DESC;

-- Crisis events summary
CREATE OR REPLACE VIEW v_crisis_summary AS
SELECT 
    DATE(sent_at) as date,
    severity,
    COUNT(*) as count,
    SUM(CASE WHEN acknowledged_at IS NULL THEN 1 ELSE 0 END) as pending,
    AVG(EXTRACT(EPOCH FROM (COALESCE(acknowledged_at, CURRENT_TIMESTAMP) - sent_at))/60) as avg_response_minutes
FROM counselor_alerts
WHERE sent_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY DATE(sent_at), severity
ORDER BY date DESC, severity;

-- Quest completion rates
CREATE OR REPLACE VIEW v_quest_completion_rates AS
SELECT 
    q.quest_type,
    q.week_number,
    q.year,
    COUNT(DISTINCT qp.session_id) as users_assigned,
    SUM(CASE WHEN qp.status = 'completed' THEN 1 ELSE 0 END) as completed,
    ROUND(100.0 * SUM(CASE WHEN qp.status = 'completed' THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT qp.session_id), 0), 2) as completion_rate
FROM quests q
LEFT JOIN quest_progress qp ON q.id = qp.quest_id
GROUP BY q.quest_type, q.week_number, q.year
ORDER BY q.year DESC, q.week_number DESC;

-- User engagement metrics
CREATE OR REPLACE VIEW v_user_engagement AS
SELECT 
    s.id as session_id,
    s.created_at,
    s.last_activity,
    COUNT(DISTINCT DATE(m.timestamp)) as days_active,
    COUNT(m.id) as total_messages,
    COALESCE(up.level, 1) as level,
    COALESCE(up.xp, 0) as xp,
    COALESCE(up.streak_days, 0) as streak_days
FROM sessions s
LEFT JOIN messages m ON s.id = m.session_id
LEFT JOIN user_profiles up ON s.id = up.session_id
WHERE s.last_activity > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY s.id, s.created_at, s.last_activity, up.level, up.xp, up.streak_days
ORDER BY s.last_activity DESC;

-- ============================================================================
-- CLEANUP QUERIES
-- ============================================================================

-- Delete old messages (>30 days)
DELETE FROM messages 
WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';

-- Delete inactive sessions (>14 days)
DELETE FROM sessions 
WHERE last_activity < CURRENT_TIMESTAMP - INTERVAL '14 days';

-- Delete old analytics events (>90 days)
DELETE FROM analytics_events 
WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- Delete old alerts (>90 days)
DELETE FROM counselor_alerts 
WHERE sent_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- ============================================================================
-- PERFORMANCE TUNING
-- ============================================================================

-- Increase shared_buffers for better caching (requires restart)
-- ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work_mem for complex queries
-- ALTER SYSTEM SET work_mem = '16MB';

-- Enable query plan caching
-- ALTER SYSTEM SET plan_cache_mode = 'force_generic_plan';

-- Reload configuration (if ALTER SYSTEM used)
-- SELECT pg_reload_conf();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check slow queries (requires pg_stat_statements)
SELECT 
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
