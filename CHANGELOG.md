# Changelog

All notable changes to GentleQuest (ai-mental-health-assistant) are documented here.

## [1.6.0] — 2026-08-13

Design milestone: the five "Fable-level" features, plus a full design-token cleanup.

### Added
- **Companion creature** — persistent CustomPainter-drawn companion with growth stages.
- **Return after absence** — the companion's breathing continues mid-cycle on return; no "welcome back" banner, no decay, no guilt.
- **Silent witness** — companion moves into the chat surface; breathe / settle / stay states, with heavy-language detection driving settle.
- **Crisis re-entry surface** — history aged to 82%, plain "LAST NIGHT" datestamp, no crisis banner, no "how are you feeling?".
- **Anti-dashboard weekly letter** — the weekly review rewritten as prose ("Dear you,"); no charts, no scores. Includes a no-data state and a fragment-picker for sharing a single line.
- **Shared solitude** — body doubling reframed as a room: ambient breathing glows, no clock, no participant count, no bell.
- **Onboarding vow** — five paced lines with designed silences; "Begin", not "Get Started".
- **"Yours" tab** — surfaces five previously unreachable screens.
- Chat error and offline states.

### Changed
- Rebuilt the shipped Flutter web bundle (`static/`), which had been stale at 1.3.0 since May while source moved to 1.6.0.

### Fixed
- Emerald-palette cleanup: deleted `theme_helper.dart` and migrated ~20 files onto `GQColors` tokens.
- 1px RenderFlex overflow in the shareable mood card.
- `/api/health` split into a lightweight check plus `/api/health/full`; the old handler queried Postgres on every Render health probe, holding the Neon compute awake continuously.
- Terminal `compliance_result` events emitted on five previously silent paths (cached-region allow/block, GPS disabled, permission denied, unverified error).
- Platform insight no longer reports "iOS dominates" on an exactly even split.

## [1.5.2] — 2026-08-04

### Changed
- Compliance unblock for IL / UT / WA following legal research; see `docs/legal/STATE_BLOCK_DECISION_2026-08-04.md`. Restores access for ~23.9M people (24.1% of blocked traffic).

## [1.5.0] — 2026-07-03

The ADHD update.

### Added
- Low-stim "quiet mode" (`LowStimService`, `low_stim_mode.dart`).
- ADHD-path onboarding step.
- Body doubling (first iteration).
- Clinical crisis detection wired into the live chat path, escalation-only and flag-gated.

### Fixed
- Age attestation corrected to 18+ and the under-18 path restored.

## [1.4.0] — 2026-06-12

### Added
- Play Age Signals integration.
- Texas SB 2420 compliance work.

### Fixed
- Synthetic-QA BLOCKER burndown.

## [1.3.2] — 2026-06-04

### Added
- Quest exercise launchers.

### Fixed
- Splash screen; crisis copy.

## [1.0.0-phase-I] — 2026-04-18

Milestone: Backend modularization + production readiness + Phase F–I features.

### Added
- **Mood Insights Dashboard** (`/insights`, `/api/insights/*`): weekly trend, keyword buckets, heatmap, quest correlation, personalized next steps — session-scoped, rate-limited.
- **Quest Gamification** (`/api/quests/*`): rule-based quest matcher, daily quests, start tracking, streaks, achievements.
- **Counselor Alert Triage** (`/api/alerts/*`): triage state machine, audit trail, filtered history, real-time SSE stream with counselor auth gating.
- **Crisis Escalation v2** (`/api/crisis/*`): country-aware resources, Twilio SMS client with circuit breaker (env-gated, disabled by default), admin-gated 24h check-in, privacy guarantees.
- **Structured JSON logging** with Sentry PII scrubbing.
- **Graceful shutdown** via signal handlers.
- **Post-deploy smoke tests** + GitHub Actions PR workflow (`.github/workflows/test_on_pr.yml`).
- **Idempotent migrations** for `triage_state` column and `crisis_escalations` table.

### Changed
- `app.py` slimmed from monolith to ≤300 lines via Flask app factory + modular blueprints under `routes/`.
- AI provider failover chain consolidated.
- Background task execution extracted from request path.

### Fixed
- `requirements.txt` typo (`requirements.txts` → `requests`).
- Country code key case mismatch in crisis resources.

### Security
- Twilio circuit breaker disabled-by-default; explicit env vars required to enable.
- Counselor SSE stream gated by counselor auth.
- Crisis admin check-in gated by admin token.

### Infrastructure
- New test suites: `test_helpers_insights.py`, `test_routes_insights.py`, `test_helpers_quest_matcher.py`, `test_routes_quests.py`, `test_helpers_alert_triage.py`, `test_routes_alerts.py`, `test_twilio_client.py`, `test_routes_crisis.py`.

See PR [#4](https://github.com/eidetic-works/ai-mental-health-assistant/pull/4).
