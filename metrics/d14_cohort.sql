-- D14 retention cohort query for GentleQuest
--
-- Schema basis (verified against ~/gentlequest/models.py):
--   analytics_events(id, session_id, event_type, metadata JSONB, request_id, timestamp)
--   user_sessions(id, created_at, last_active, conversation_count, risk_level)
--
-- Identity model: GentleQuest does not require auth for most flows; the durable
-- user identity is `session_id` (a UUID from user_sessions). The client fires
-- Firebase first_open / session_start events that do NOT reach this server, so
-- there is no dedicated `first_open` row in analytics_events. The faithful
-- server-side proxy for "first opened the app" is the EARLIEST analytics_events
-- timestamp per session_id. "Returned on day 14" = any analytics_events row for
-- that session_id whose timestamp falls in the D14 calendar window
-- (cohort_date + 14 days, inclusive of that calendar day through +15 days to
-- capture the 24h window).
--
-- Parameter: :cohort_start (DATE) — the first_open date defining the cohort.
--   All session_ids whose earliest event falls on this date form the cohort.
--
-- Minimum cohort size: n >= 40. Below that, the reader script returns
-- verdict=INSUFFICIENT rather than a PASS/FAIL rate (small-n retention is
-- noise, not signal).

WITH first_open_per_session AS (
    -- Earliest analytics event per session_id = proxy for first_open.
    SELECT
        session_id,
        MIN(timestamp) AS first_open_ts
    FROM analytics_events
    WHERE session_id IS NOT NULL
    GROUP BY session_id
),
cohort AS (
    -- Users whose first_open falls on the cohort_start date.
    SELECT
        session_id,
        first_open_ts,
        DATE(first_open_ts) AS cohort_date
    FROM first_open_per_session
    WHERE DATE(first_open_ts) = :cohort_start
),
d14_returns AS (
    -- A cohort member "returned on D14" if they have ANY analytics_events row
    -- whose timestamp is >= first_open + 14 days AND < first_open + 15 days
    -- (the 24h window starting at the 14-day mark). Any event_type counts as
    -- activity — we are measuring presence, not a specific action.
    SELECT
        c.session_id
    FROM cohort c
    JOIN analytics_events ae
        ON ae.session_id = c.session_id
    WHERE ae.timestamp >= c.first_open_ts + INTERVAL '14 days'
      AND ae.timestamp <  c.first_open_ts + INTERVAL '15 days'
    GROUP BY c.session_id
)
SELECT
    c.cohort_date,
    COUNT(DISTINCT c.session_id)                       AS cohort_size,
    COUNT(DISTINCT r.session_id)                       AS d14_returned,
    CASE
        WHEN COUNT(DISTINCT c.session_id) = 0 THEN NULL
        ELSE ROUND(
            COUNT(DISTINCT r.session_id)::numeric
            / COUNT(DISTINCT c.session_id)::numeric,
            4
        )
    END                                                AS d14_rate
FROM cohort c
LEFT JOIN d14_returns r ON r.session_id = c.session_id
GROUP BY c.cohort_date;
