# GentleQuest Backend Analytics Ingest Audit

> **Version:** 1.0.0 — authored 2026-06-03  
> **Auditor:** Antigravity (agy) — Item 4 of analytics goal `relay_20260603T155332Z_cc_gq_to_agy_analytics_goal_v131`  
> **Verdict:** KEEP — endpoint is live, persists to Neon Postgres, has retention policy and downstream consumers.

---

## Endpoint Details

| Field | Value |
|---|---|
| **URL** | `https://app.gentlequest.app/api/analytics/log` |
| **Method** | `POST` |
| **Rate limit** | 120 req/min |
| **Auth required** | None (public) — but requires `X-Analytics-Consent: true` header to persist |
| **Response (success)** | `201 {"ok": true}` |
| **Response (no consent header)** | `201 {"ok": true}` (silent no-op — same status, no persistence) |
| **Response (invalid event_type)** | `400 {"error": "Invalid event_type"}` |
| **Response (server error)** | `500 {"error": "Failed to log analytics"}` |

### Live Verification

```
curl -sI -X POST "https://app.gentlequest.app/api/analytics/log" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"test","metadata":{}}'
# Result: HTTP/2 201 (verified 2026-06-03T16:07:52Z)
```

---

## Backend Handler

- **File:** `routes/analytics_routes.py:18`
- **Blueprint:** `analytics_bp` registered at `/api/analytics/log`
- **Server:** Werkzeug/3.11.15 on Render (confirmed via `x-render-origin-server` header)

### Handler Logic (summary)

1. **Consent check:** If `X-Analytics-Consent` header ≠ `"true"` → return 201 (silent no-op, nothing persisted)
2. **Event type validation:** Strips whitespace; max 64 chars; allowlist of characters `[a-zA-Z0-9_.:-]`
3. **Metadata sanitization:** Only these keys accepted: `action, label, screen, source, value, count, duration_ms, success, code, provider, quest_id, tag, surface, variant, ts, progress, ui` — all other keys silently dropped. Values capped at 200 chars.
4. **Session association:** `_get_or_create_session()` attaches a session ID (from `X-Session-ID` header via `SessionManager`)
5. **Persistence:** Inserts `AnalyticsEvent` ORM record and commits to Neon Postgres via SQLAlchemy

---

## Persistence Target

| Field | Value |
|---|---|
| **Database** | Neon Postgres (production) |
| **Model** | `AnalyticsEvent` (defined in `models.py`) |
| **Fields stored** | `session_id`, `event_type`, `event_metadata` (JSON), `request_id`, `timestamp` |
| **PII stored?** | NO — session_id is an anonymous UUID; email/device IDs explicitly excluded |
| **Retention** | Configurable via `ANALYTICS_RETENTION_DAYS` env var. Admin purge available at `POST /api/admin/purge` (token-gated). Default: until account deletion (per privacy policy). |

---

## Related Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/analytics/recent` | GET | Read recent events (for debugging). No auth — consider adding read protection. |
| `/api/analytics/overview` | GET | Aggregated intervention stats (last N days) |
| `/api/analytics/interventions` | GET | Detailed intervention effectiveness breakdown |
| `/api/analytics/user/<session_id>` | GET | Per-session engagement + best intervention recommendation |
| `/api/analytics/function-calling` | GET | Gemini function-calling vs keyword fallback stats |

---

## Downstream Consumers

| Consumer | Source | What it reads |
|---|---|---|
| `GET /api/analytics/overview` | `providers/analytics.py:get_intervention_stats` | Aggregated stats from `AnalyticsEvent` + intervention outcome tables |
| `GET /api/analytics/interventions` | `providers/analytics.py:get_completion_rates_by_type` | Completion rates, mood improvement deltas, recommendations |
| `GET /api/analytics/user/<id>` | `providers/analytics.py:get_user_engagement_metrics` | Per-session engagement scores |
| Admin purge cron | `helpers/mood_helpers.py:_purge_old_data_inner` | Deletes events older than `ANALYTICS_RETENTION_DAYS` |
| Health check | `routes/health.py:112` | Lists `/api/analytics/log` as a monitored endpoint |

---

## Mobile Client Wiring

The Flutter app calls this endpoint via `lib/services/analytics_service.dart:logAnalyticsEvent()`:

```dart
// Only fires when:
// 1. Anonymity mode is OFF (SharedPreferences kAnonymityModeKey = false)
// 2. Analytics consent is ON (SharedPreferences _analyticsConsentKey = true)
// Headers sent:
//   X-Session-ID: <session UUID from SessionManager>
//   X-Analytics-Consent: true
//   X-Request-ID: req-<timestamp>-<random>
```

**Consent double-gate:** Client only sends the `X-Analytics-Consent: true` header when the user has explicitly opted in. The server also checks for this header as a second gate. If either gate fails, no data is stored.

---

## Findings and Recommendations

> [!TIP]
> **KEEP** — The endpoint is live, correctly architected (no PII in, consent-double-gated, Postgres-persisted with retention policy). No action needed on the endpoint itself.

> [!NOTE]
> **LOW:** `GET /api/analytics/recent` has no authentication. Any unauthenticated request can read recent event types and metadata. Event types/metadata contain no PII (by design), but consider adding a read token for defense in depth before any public-facing dashboard is built on top.

> [!NOTE]
> **LOW:** The `metadata` allowlist in `analytics_routes.py:47-51` does not include some params that mobile callsites send (e.g., `day_number`, `date_utc`, `has_mood_data`, `completion_time_seconds` from `daily_checkin_completed`). These are silently dropped. This is SAFE (no bad data persisted) but means the backend has less data than Firebase for these events. Aligning the allowlist would improve backend analytics granularity.

> [!WARNING]
> **MEDIUM:** No aggregation dashboard currently consumes `analytics_event` table directly for the Firebase-equivalent events (app_open, first_chat_message_sent etc. — those go to Firebase only). The backend stores quest/wellness events only. A future unified analytics dashboard would need to either pull from Firebase BigQuery export OR reconcile both sources. Not blocking current release.
