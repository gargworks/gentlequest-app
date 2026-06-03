# GentleQuest Analytics Event Taxonomy

> **Version:** 1.0.0 — authored 2026-06-03  
> **Scope:** All analytics callsites in `ai_buddy_web/` as of commit `6657091c`  
> **DO NOT add new events or rename existing ones without updating this doc.**

---

## PII Findings (Items Requiring Review Before Next Release)

> [!NOTE]
> **FIXED (commit 2058e048) — `auth_magic_link_verified` previously logged `user_id` to Firebase Analytics.**  
> File: `lib/services/deep_link_service.dart:169`  
> The `user_id` field has been replaced with `auth_success: true`. No persistent identifier is logged.

> [!WARNING]
> **LOW — `leopard_access_granted` logs `code` to Firebase Analytics.**  
> File: `lib/features/leopard/widgets/leopard_access_gate.dart:50`  
> `code` is the string the user typed to unlock Leopard access. If the code is user-chosen and reused elsewhere it could be quasi-identifying. **Action:** verify the code is a fixed system string, not user-generated.

> [!WARNING]
> **LOW — `sse_exercise_parse_failed` logs `raw_keys` which may contain unexpected payload content.**  
> File: `lib/providers/chat_provider.dart:413`  
> `raw_keys` is derived from a parsed SSE chunk. If the SSE payload contains user-generated text as a key this could leak content. **Action:** verify `raw_keys` is bounded to enum-like SSE field names only.

---

## Alphabetical Event Index

| Event Name | Surface | File(s) |
|---|---|---|
| `app_open` | Firebase | `firebase_service.dart:142` |
| `auth_magic_link_requested` | Firebase | `auth/login_screen.dart:65` |
| `auth_magic_link_verified` | Firebase | `deep_link_service.dart:169` ✅ fixed |
| `auth_magic_link_verify_failed` | Firebase | `deep_link_service.dart:182` |
| `chat_message` | Firebase | `firebase_service.dart:247` |
| `chat_session_started` | Firebase | `chat_provider.dart:234` |
| `consent_changed` | Backend | `settings_screen.dart:246` |
| `content_shared` | Firebase | `deep_link_service.dart:213` |
| `crisis_alert_ack_failed` | Firebase | `alert_inbox_screen.dart:135,154` |
| `crisis_resource_accessed` | Firebase | `firebase_service.dart:253` |
| `daily_checkin_completed` | Backend | `wellness_dashboard_screen.dart:448` |
| `deep_link_opened` | Firebase | `deep_link_service.dart:73,101` |
| `exercise_completed` | Firebase | `firebase_service.dart:257` |
| `first_chat_message_sent` | Firebase | `chat_provider.dart:239` |
| `intervention_accepted` | Firebase | `interactive_chat_screen.dart:1074` |
| `intervention_offered` | Firebase | `chat_provider.dart:362` |
| `leopard_access_attempt` | Firebase | `leopard_access_gate.dart:40` |
| `leopard_access_granted` | Firebase | `leopard_access_gate.dart:50` ⚠️ LOW PII |
| `leopard_quest_generated` | Firebase | `leopard_shell.dart:57` |
| `leopard_quest_shared` | Firebase | `leopard_shell.dart:206` |
| `mood_tracked` | Firebase | `firebase_service.dart:240` |
| `quest_complete` | Backend | `wellness_dashboard_screen.dart:436,1429,1521` |
| `quest_completed` | Firebase | `quest_provider.dart:208` |
| `quest_progress` | Backend | `wellness_dashboard_screen.dart:1374` |
| `quest_reminder_fired` | Backend | `wellness_dashboard_screen.dart:920,3279` |
| `quest_start` | Backend | `wellness_dashboard_screen.dart:4145` |
| `quest_view` | Backend | `wellness_dashboard_screen.dart:3699,4027` |
| `sse_exercise_parse_failed` | Firebase | `chat_provider.dart:413` |

---

## Detailed Event Catalog

### `app_open` (Firebase)

- **Surface:** Firebase Analytics (`FirebaseService.logEvent`)
- **Fired from:** `lib/services/firebase_service.dart:142` — on `FirebaseService.init()` completion
- **When:** App cold-start, every time the app initializes Firebase
- **Metadata params:** _(none)_
- **PII risk:** NONE
- **Anonymity gate:** YES — `_anonymityOn` check in `logEvent`; suppressed when `kAnonymityModeKey=true`
- **Used by:** DAU/WAU/MAU baseline; Firebase Console "Active users" tile

---

### `auth_magic_link_requested` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/screens/auth/login_screen.dart:65`
- **When:** User submits email to request a sign-in magic link
- **Metadata params:** _(none)_
- **PII risk:** NONE — email is NOT included in this event
- **Anonymity gate:** YES
- **Used by:** Auth funnel conversion metric

---

### `auth_magic_link_verified` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/services/deep_link_service.dart:169`
- **When:** User clicks the magic link from email and token validation succeeds
- **Metadata params:**
  - `auth_success` (bool, always `true` — non-PII) — **Note:** previously logged `user_id` (persistent identifier); replaced with `auth_success: true` in commit `2058e048`
- **PII risk:** NONE (post-fix)
- **Anonymity gate:** YES
- **Used by:** Sign-in success rate metric

---

### `auth_magic_link_verify_failed` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/services/deep_link_service.dart:182`
- **When:** Magic link token validation fails (expired, already used, network error)
- **Metadata params:**
  - `reason` (string, error message from `AuthException.message` — verify no user data leaks into message)
- **PII risk:** LOW — verify `AuthException.message` contains only system-level error codes
- **Anonymity gate:** YES
- **Used by:** Auth failure debugging

---

### `chat_message` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/services/firebase_service.dart:247` via `logChatMessage()`
- **When:** Each individual chat message is sent (note: `chat_session_started` is the preferred funnel event)
- **Metadata params:**
  - `message_type` (string, e.g. 'user' or 'assistant')
- **PII risk:** NONE — message content is NOT included
- **Anonymity gate:** YES
- **Used by:** Engagement depth metric (messages per session)

---

### `chat_session_started` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/providers/chat_provider.dart:234`
- **When:** User sends their first message in an interactive chat session
- **Metadata params:**
  - `message_length` (int, character count of message — non-PII)
  - `is_first` (bool, whether this is user's first-ever chat message)
- **PII risk:** NONE — message content NOT included; only character count
- **Anonymity gate:** YES
- **Used by:** Session start funnel event; DAU engagement metric

---

### `consent_changed` (Backend `/api/analytics/log`)

- **Surface:** Backend ingest
- **Fired from:** `lib/screens/settings_screen.dart:246`
- **When:** User toggles analytics consent in Settings
- **Metadata params:**
  - `value` (bool, the new consent state — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES — note: if anonymity mode is on, this event is suppressed even if consent is toggled on. Consent UI is independent of anonymity mode.
- **Used by:** Consent tracking / regulatory compliance audit trail

---

### `content_shared` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/services/deep_link_service.dart:213`
- **When:** User receives content via a deep link share (type=mood or type=crisis)
- **Metadata params:**
  - `type` (string, 'mood' | 'crisis' | 'unknown' — non-PII)
  - `has_content` (bool — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Share feature engagement metric

---

### `crisis_alert_ack_failed` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/screens/alert_inbox_screen.dart:135` (network error path), `:154` (general error path)
- **When:** User attempts to acknowledge a crisis alert but the server-side ACK call fails
- **Metadata params:**
  - `alert_id` (string, internal alert UUID — non-PII)
  - `error` (string, error message — verify no PII leaks)
- **PII risk:** LOW — verify `error` string doesn't include user content
- **Anonymity gate:** YES
- **Used by:** Crisis alerting reliability monitoring

---

### `crisis_resource_accessed` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/services/firebase_service.dart:253` via `logCrisisResourceAccess()`
- **When:** User opens the crisis resources screen or activates a crisis resource
- **Metadata params:** _(none)_
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Safety feature engagement; regulatory reporting

---

### `daily_checkin_completed` (Backend)

- **Surface:** Backend `/api/analytics/log`
- **Fired from:** `lib/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart:448`
- **When:** User completes the quick daily check-in via the Today tab wellness card
- **Metadata params:**
  - `day_number` (int, days since account created — non-PII)
  - `date_utc` (string, ISO8601 timestamp — non-PII, no user identity)
  - `has_mood_data` (bool, always `true` — non-PII)
  - `completion_time_seconds` (int, approximate `2` — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES — `_isAnalyticsEnabled()` guards the backend call
- **Used by:** D1/D7/D30 retention metric; streak feature baseline

---

### `deep_link_opened` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:**
  - `lib/services/deep_link_service.dart:73` (web cold-start `/auth/verify` path, with `surface: 'web'`)
  - `lib/services/deep_link_service.dart:101` (native `_handleDeepLink` path)
- **When:** App receives a deep link (native or web)
- **Metadata params:**
  - `url` (string, path only — query params stripped before logging. **Note:** previously logged full URL including auth token; fixed in commit `2058e048` by calling `uri.replace(queryParameters: {}).toString()`)
  - `surface` (string, 'web' — only on `:73` path)
- **PII risk:** NONE (post-fix)
- **Anonymity gate:** YES
- **Used by:** Deep link funnel debugging

---

### `exercise_completed` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/services/firebase_service.dart:257` via `logExerciseCompleted()`
- **When:** User completes a guided exercise (breathing, grounding, etc.)
- **Metadata params:**
  - `exercise_type` (string, exercise category — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Exercise feature engagement; intervention effectiveness tracking

---

### `first_chat_message_sent` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/providers/chat_provider.dart:239`
- **When:** User sends their very first chat message ever (guarded by `isFirstMessage` flag stored in SharedPreferences)
- **Metadata params:**
  - `message_length` (int, character count — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** **Primary onboarding funnel event** — `app_open → first_chat_message_sent` is the key activation metric. Also used by proposed Firebase Funnel in Item 6.

---

### `intervention_accepted` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/screens/interactive_chat_screen.dart:1074`
- **When:** User taps "Accept" on an inline exercise/intervention card offered by the AI
- **Metadata params:**
  - `exercise_type` (string, intervention type — non-PII)
  - `source` (string, context identifier — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** `intervention_offered → intervention_accepted` conversion ratio dashboard tile

---

### `intervention_offered` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/providers/chat_provider.dart:362`
- **When:** AI response includes an exercise/intervention suggestion
- **Metadata params:**
  - `exercise_type` (string, intervention type — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Intervention offer rate; paired with `intervention_accepted` for acceptance ratio

---

### `leopard_access_attempt` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/features/leopard/widgets/leopard_access_gate.dart:40`
- **When:** User submits a code to attempt Leopard feature access
- **Metadata params:**
  - `code_entered` (string, the access code typed — **see LOW PII warning**)
- **PII risk:** LOW — if the code is a fixed system token this is non-PII. If user-chosen, it could be quasi-identifying. Verify before next release.
- **Anonymity gate:** YES
- **Used by:** Leopard feature beta access analytics

---

### `leopard_access_granted` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/features/leopard/widgets/leopard_access_gate.dart:50`
- **When:** User enters the correct code and is granted Leopard feature access
- **Metadata params:**
  - `code` (string, the correct access code — **LOW PII see above**)
- **PII risk:** LOW
- **Anonymity gate:** YES
- **Used by:** Leopard beta cohort tracking

---

### `leopard_quest_generated` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/features/leopard/leopard_shell.dart:57`
- **When:** AI generates a Leopard quest for the user
- **Metadata params:** _(check actual params at callsite — not listed in goal taxonomy; verify no content logged)_
- **PII risk:** NONE expected
- **Anonymity gate:** YES
- **Used by:** Leopard engagement metric

---

### `leopard_quest_shared` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/features/leopard/leopard_shell.dart:206`
- **When:** User shares a Leopard quest result
- **Metadata params:** _(verify at callsite)_
- **PII risk:** NONE expected
- **Anonymity gate:** YES
- **Used by:** Leopard virality metric

---

### `mood_tracked` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/services/firebase_service.dart:240` via `logMoodEntry()`
- **When:** User logs a mood entry
- **Metadata params:**
  - `mood_type` (string, mood category label — non-PII)
  - `mood_score` (int, 1-10 numeric score — non-PII)
- **PII risk:** NONE — mood type/score are not identifying
- **Anonymity gate:** YES
- **Used by:** Mood feature engagement; retention signal

---

### `quest_complete` (Backend) — THREE CALLSITES

> Note: Three distinct UI flows fire the same event name. Params are consistent but `tag` and `ui` fields differentiate the source.

- **Surface:** Backend `/api/analytics/log`
- **Fired from:**
  - `wellness_dashboard_screen.dart:436` — quick check-in (tag=`xp_awarded`, ui=`quick_checkin`)
  - `wellness_dashboard_screen.dart:1429` — timer-sheet "Complete now" button (tag=`complete_now`, ui=`timer_sheet`)
  - `wellness_dashboard_screen.dart:1521` — inline Today card complete (tag=`xp_awarded`, ui varies)
- **When:** User marks a quest as complete via any of the three UI paths
- **Metadata params:**
  - `quest_id` (string, internal UUID — non-PII)
  - `surface` (string, `'wellness_dashboard'` — non-PII)
  - `variant` (string, `'today'` — non-PII)
  - `tag` (string, `'xp_awarded'` or `'complete_now'` — non-PII)
  - `ts` (int, epoch ms — non-PII)
  - `success` (bool, always `true` — non-PII)
  - `progress` (float, always `1.0` — non-PII)
  - `ui` (string, UI component identifier — non-PII)
  - `source` (string, optional telemetry tag — non-PII, `:1521` path only)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Quest completion rate; retention metric; XP award verification

---

### `quest_completed` (Firebase) — distinct from `quest_complete` (Backend)

> ⚠️ **Naming collision risk:** `quest_complete` fires to backend; `quest_completed` fires to Firebase. These are different events with slightly different names. Both represent quest completion but on different surfaces.

- **Surface:** Firebase Analytics
- **Fired from:** `lib/providers/quest_provider.dart:208`
- **When:** Quest provider internally marks a quest completed
- **Metadata params:** _(verify at callsite — not fully listed in taxonomy spec)_
- **PII risk:** NONE expected
- **Anonymity gate:** YES
- **Used by:** Firebase-side quest completion funnel

---

### `quest_progress` (Backend)

- **Surface:** Backend `/api/analytics/log`
- **Fired from:** `wellness_dashboard_screen.dart:1374`
- **When:** User starts a timed quest (timer sheet opens — fires at `progress: 0.0`)
- **Metadata params:**
  - `quest_id` (string — non-PII)
  - `surface` (string — non-PII)
  - `variant` (string — non-PII)
  - `tag` (string, `'timer_start'` — non-PII)
  - `ts` (int, epoch ms — non-PII)
  - `progress` (float, `0.0` — non-PII)
  - `duration_ms` (int, configured duration — non-PII)
  - `ui` (string, `'timer_sheet'` — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Quest engagement funnel (start → complete)

---

### `quest_reminder_fired` (Backend) — TWO CALLSITES

- **Surface:** Backend `/api/analytics/log`
- **Fired from:**
  - `wellness_dashboard_screen.dart:920` (scheduled in-app notification)
  - `wellness_dashboard_screen.dart:3279` (explore-tab flow)
- **When:** In-app quest reminder notification is shown to the user
- **Metadata params:**
  - `quest_id` (string, optional — non-PII)
  - `surface` (string — non-PII)
  - `variant` (string — non-PII)
  - `tag` (string, `'fired'` — non-PII)
  - `ts` (int, epoch ms — non-PII)
  - `ui` (string, `'in_app'` — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Notification delivery and engagement metric

---

### `quest_start` (Backend)

- **Surface:** Backend `/api/analytics/log`
- **Fired from:** `wellness_dashboard_screen.dart:4145`
- **When:** User taps "I did this" on an Explore-tab quest card (intent to complete)
- **Metadata params:**
  - `quest_id` (string — non-PII)
  - `type` (string, quest type — non-PII)
  - `surface` (string — non-PII)
  - `variant` (string, `'explore'` — non-PII)
  - `ts` (int, epoch ms — non-PII)
  - `ui` (string, `'explore'` — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Explore tab engagement; `quest_start → quest_complete` funnel

---

### `quest_view` (Backend) — TWO CALLSITES

- **Surface:** Backend `/api/analytics/log`
- **Fired from:**
  - `wellness_dashboard_screen.dart:3699` — Explore tab switch (tag=`explore_tab`, ui=`tab_switch`)
  - `wellness_dashboard_screen.dart:4027` — Explore item impression (per-card impression tracking)
- **When:** User views the Explore tab or individual quest cards become visible
- **Metadata params:**
  - `quest_id` (string, `:4027` path only — non-PII)
  - `type` (string, `:4027` path only — non-PII)
  - `surface` (string — non-PII)
  - `variant` (string, `'explore'` — non-PII)
  - `tag` (string — non-PII)
  - `ts` (int, epoch ms — non-PII)
  - `ui` (string — non-PII)
- **PII risk:** NONE
- **Anonymity gate:** YES
- **Used by:** Content discovery metric; Explore tab engagement

---

### `sse_exercise_parse_failed` (Firebase)

- **Surface:** Firebase Analytics
- **Fired from:** `lib/providers/chat_provider.dart:413`
- **When:** SSE stream from backend delivers an exercise payload that fails client-side JSON parse
- **Metadata params:**
  - `error` (string, error message from exception — verify no user data)
  - `raw_keys` (list/string, keys from the raw SSE payload — **LOW PII concern: verify no content values logged**)
- **PII risk:** LOW — see PII findings section
- **Anonymity gate:** YES
- **Used by:** SSE parsing reliability monitoring; backend response format debugging

---

## By-Screen Index

| Screen / Module | Events |
|---|---|
| App boot (`firebase_service.dart`) | `app_open`, `mood_tracked`, `chat_message`, `crisis_resource_accessed`, `exercise_completed` |
| Auth / Login | `auth_magic_link_requested` |
| Deep Link Service | `deep_link_opened`, `auth_magic_link_verified`, `auth_magic_link_verify_failed`, `content_shared` |
| Chat Provider | `chat_session_started`, `first_chat_message_sent`, `intervention_offered`, `sse_exercise_parse_failed` |
| Interactive Chat Screen | `intervention_accepted` |
| Quest Provider | `quest_completed` |
| Leopard Shell | `leopard_quest_generated`, `leopard_quest_shared` |
| Leopard Access Gate | `leopard_access_attempt`, `leopard_access_granted` |
| Alert Inbox Screen | `crisis_alert_ack_failed` |
| Settings Screen | `consent_changed` |
| Wellness Dashboard Screen | `quest_complete`, `daily_checkin_completed`, `quest_reminder_fired`, `quest_progress`, `quest_view`, `quest_start` |

---

## Surface Summary

| Surface | Event Count | Consent Gate | Notes |
|---|---|---|---|
| Firebase Analytics | 20 | `_anonymityOn` check in `FirebaseService.logEvent` | All Firebase events suppressed when anonymity mode is on |
| Backend `/api/analytics/log` | 8 | `X-Analytics-Consent: true` header required + `_isAnalyticsEnabled()` prefs check | Events dropped on floor if consent header absent (returns 201 silently) |

_Total unique event names: 27 (plus `quest_complete` at backend has 3 callsites, `quest_view` and `quest_reminder_fired` have 2 each, `deep_link_opened` has 2)_
