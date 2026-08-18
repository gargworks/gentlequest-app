-- Pooled D14 retention cohort query for GentleQuest.
--
-- Companion to d14_cohort.sql. That query returns one row per calendar
-- first-open date; the Stage-1 exit gate in BILLION_DOLLAR_ROADMAP.md
-- instead defines ONE cohort spanning the whole 2026-08-15->09-24 window
-- ("D14 retention >=15 pct on the 2026-08-15->09-24 first_open cohort, n>=40").
-- A single day rarely hits n>=40 on its own; the gate is pooled by design.
--
-- Same identity model and D14 definition as d14_cohort.sql: first_open is
-- proxied by the earliest analytics_events row per session_id; "returned on
-- D14" is any event 14-15 days after that session's own first_open (not a
-- fixed calendar date -- each session gets its own 14-day mark).
--
-- Parameters: :range_start, :range_end (DATE, inclusive) -- the window of
-- first-open dates that define the pooled cohort.

WITH first_open_per_session AS (
    SELECT
        session_id,
        MIN(timestamp) AS first_open_ts
    FROM analytics_events
    WHERE session_id IS NOT NULL
    GROUP BY session_id
),
cohort AS (
    SELECT
        session_id,
        first_open_ts
    FROM first_open_per_session
    WHERE DATE(first_open_ts) BETWEEN :range_start AND :range_end
),
d14_returns AS (
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
    COUNT(DISTINCT c.session_id)                       AS cohort_size,
    COUNT(DISTINCT r.session_id)                        AS d14_returned,
    -- Eligible = cohort members who HAVE actually reached their own D14
    -- mark (first_open + 14 days <= now). The rate is computed over this
    -- subset, never over the full cohort_size -- a member whose 14-day mark
    -- hasn't arrived yet is neither returned nor churned, and folding them
    -- into the denominator manufactures a fake low rate out of members who
    -- simply haven't had the chance to return.
    COUNT(DISTINCT c.session_id) FILTER (
        WHERE c.first_open_ts + INTERVAL '14 days' <= NOW()
    )                                                  AS eligible_size,
    CASE
        WHEN COUNT(DISTINCT c.session_id) FILTER (
            WHERE c.first_open_ts + INTERVAL '14 days' <= NOW()
        ) = 0 THEN NULL
        ELSE ROUND(
            COUNT(DISTINCT r.session_id)::numeric
            / COUNT(DISTINCT c.session_id) FILTER (
                WHERE c.first_open_ts + INTERVAL '14 days' <= NOW()
            )::numeric,
            4
        )
    END                                                AS d14_rate,
    COUNT(DISTINCT c.session_id) FILTER (
        WHERE c.first_open_ts + INTERVAL '14 days' > NOW()
    )                                                  AS not_yet_eligible
FROM cohort c
LEFT JOIN d14_returns r ON r.session_id = c.session_id;
