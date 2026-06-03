# GentleQuest Privacy Disclosure Audit

> **Version:** 1.0.0 — authored 2026-06-03  
> **Auditor:** Antigravity (agy) — Item 5 of analytics goal `relay_20260603T155332Z_cc_gq_to_agy_analytics_goal_v131`  
> **Scope:** v1.3.1 (build 26060318, now WAITING_FOR_REVIEW in App Store)  
> **v1.3.1 release notes claim:** _"Firebase Crashlytics so we can fix bugs without you having to report them; Privacy-respecting analytics (no personal data, just app-level usage)"_

---

## Severity Legend

| Severity | Meaning |
|---|---|
| BLOCKER | Claim is false or compliance risk — operator must act before App Store approval |
| HIGH | Disclosure gap — should be resolved in v1.3.2 |
| LOW | Minor drift or improvement opportunity |
| OK | Aligned — no action needed |

---

## 3-Column Comparison Matrix

| Category | ASC App Privacy (declared for v1.3.0) | In-App Privacy Policy (`assets/legal/privacy.md`) | Actual Collection (from EVENT_TAXONOMY.md + BACKEND_INGEST_AUDIT.md) | Severity |
|---|---|---|---|---|
| **Crash Data** | Diagnostics → Crash logs, performance data (Crashlytics) — Collected, Not linked to user, Not used for tracking | "Crash logs — sent to Firebase Crashlytics. No PII; IP addresses truncated to /24 (IPv4) or /48 (IPv6) before storage." Retention: 90 days (Firebase default). | ✅ Confirmed: Crashlytics enabled (mobile only), `setCrashlyticsCollectionEnabled(!kDebugMode)` — no personal data in crash reports | OK |
| **Analytics / Usage Data** | Usage Data → App interaction events — Collected, Not linked to user, Not used for tracking | "Analytics events — event type, anonymized metadata, timestamp — suppressed entirely when Anonymity Mode is on" | ✅ Confirmed: 27 event types catalogued; no direct PII fields except HIGH concern in `auth_magic_link_verified` (see below) | HIGH |
| **Identifiers** | Identifiers → Anonymous session ID (UUID) — Collected, Not linked to user, Not used for tracking | "Anonymous session ID — a UUID generated per device. Regenerable via Settings → Reset Session. Not linked to name, email, or device hardware ID." | ✅ Confirmed: `SessionManager.getOrCreateSessionId()` generates UUID; `X-Session-ID` header sent with backend events | OK |
| **Health & Fitness** | Health & Fitness → Mental health data — Collected, Not linked to user, Not used for tracking | "Mood entries (mood score, label, timestamp). Clinical assessments (PHQ-9 / GAD-7)." | ✅ Confirmed: `mood_tracked` logs `mood_type` + `mood_score` — non-identifying. Clinical assessment data NOT in analytics events. | OK |
| **User Content** | User Content → Journal entries, chat messages — Collected, Not linked to user | "Journal entries, chat history stored server-side during session" | ✅ Confirmed: NO message content in any analytics event. `chat_session_started` logs only `message_length` (char count). | OK |
| **Location** | Location → Coarse — US state or country | "Region — US state or country-level, used for compliance gating. We never store your precise location." | ✅ Confirmed: No location params in any analytics events. Coarse region used for server-side crisis-line routing only. | OK |
| **IDFA / Device Tracking** | NOT COLLECTED (declared) | "NOT collected: Device hardware identifiers (IDFA, IDFV, Android Advertising ID)" | ✅ Confirmed: `kTrackingStatus` not requested. Firebase Analytics configured without IDFA collection. `Info.plist` has no `NSUserTrackingUsageDescription` key (no ATT prompt). | OK |
| **Firebase Analytics — explicit naming** | Not explicitly named as "Firebase Analytics" in ASC form (declared under "Usage Data" category generically) | ✅ Named explicitly: "Firebase Analytics events are suppressed for your session" (in Anonymity Mode section). Anonymity Mode section correctly describes the suppression behavior. | Firebase Analytics v11.6.0 in use | LOW |
| **Crashlytics — retention period** | Not stated in ASC form | ✅ States: "Crash logs (Crashlytics) — 90 days (Firebase default)" | Firebase default 90-day retention confirmed by Google docs. | OK |
| **auth_magic_link_verified `user_id` field** | NOT disclosed — `user_id` (internal UUID) is logged to Firebase Analytics but not mentioned in any disclosure | Not mentioned | `user_id` in `deep_link_service.dart:169` sent to Firebase Analytics — could constitute a persistent identifier linked to usage data | HIGH |
| **deep_link_opened URL with auth token** | NOT disclosed | Not mentioned | `uri.toString()` logged at `deep_link_service.dart:73` includes full URL with auth token in query params | HIGH |

---

## Findings by Severity

### BLOCKER
None identified. The core privacy claim ("no personal data, just app-level usage") holds for the vast majority of events. The HIGH findings below should be resolved in v1.3.2.

---

### HIGH — Requires resolution in v1.3.2

#### H1: `auth_magic_link_verified` logs `user_id` to Firebase Analytics

- **Event:** `auth_magic_link_verified`
- **File:** `lib/services/deep_link_service.dart:169`
- **Param:** `user_id` — internal UUID from `AuthService.instance.verifyToken(rawToken).id`
- **Risk:** This UUID is a persistent identifier that links auth success events to a specific account across sessions. Firebase Analytics may associate this with device data. This potentially contradicts "Not linked to user" declaration.
- **Action:** Remove `user_id` from the event parameters. Replace with `auth_success: true` (non-identifying). Alternatively, log a one-way hash of the user_id that cannot be reversed.
- **PR needed:** Yes — fix in `lib/services/deep_link_service.dart:169` before v1.3.2

#### H2: `deep_link_opened` logs full URL including auth token

- **Event:** `deep_link_opened`
- **File:** `lib/services/deep_link_service.dart:73`
- **Param:** `url` = `uri.toString()` — on auth verify paths this includes `?token=<raw_token>` in the URL
- **Risk:** Auth tokens are single-use server-side, but logging them to Firebase Analytics creates a record. If Firebase's data is ever accessed (even by Firebase support), tokens would appear in event history. Low exploitability but a hygiene issue.
- **Action:** Before logging, strip query parameters: `uri.replace(queryParameters: {}).toString()`. Log only the path component.
- **PR needed:** Yes — fix in `lib/services/deep_link_service.dart:73` before v1.3.2

---

### LOW — Improvement opportunities

#### L1: Firebase Analytics not explicitly named in ASC App Privacy form

- **Current state:** ASC form declares "Usage Data → App interaction events" generically
- **Better state:** Add "Firebase Analytics by Google" as the data provider name in the App Privacy details
- **Action:** Operator to review ASC App Privacy form details section (third-party SDK disclosure)
- **Operator action required:** Yes (ASC form is operator-only access)

#### L2: Privacy Policy could be more explicit about Firebase Analytics vs Backend

- **Current state:** Privacy policy references "Firebase Analytics events" correctly in Anonymity Mode section
- **Better state:** Add a "Third-party SDKs" section listing Firebase Analytics (Google) and Firebase Crashlytics (Google) with links to their privacy policies
- **Action:** Add to `assets/legal/privacy.md` in v1.3.2

#### L3: `leopard_access_attempt` + `leopard_access_granted` log `code` field

- **Current state:** Access code logged to Firebase Analytics
- **Risk:** Low if `code` is a fixed system token (non-PII). If user-chosen, it could be quasi-identifying.
- **Action:** Verify the Leopard access code is NOT user-generated. If it is, replace `code` with `code_length` (int) or similar non-identifying proxy.

---

## iOS ATT (App Tracking Transparency) Status

**Status: NOT REQUIRED — correctly configured**

- No `NSUserTrackingUsageDescription` key in `Info.plist`
- No IDFA collection configured in Firebase Analytics
- No cross-app tracking
- No data sharing with data brokers
- ASC "Do you track users?" → **No** (correctly answered)

This means Apple will NOT prompt users with the ATT "Allow tracking?" dialog, which is the correct behavior for GentleQuest.

---

## ASC App Privacy — Reproduction Guide

> The following is the recommended ASC App Privacy configuration for v1.3.1 (does not change from v1.3.0):

```
Health & Fitness > Mental health data
  - Collected: YES
  - Linked to identity: NO
  - Used for tracking: NO

User Content > Chat messages, journal entries
  - Collected: YES
  - Linked to identity: NO
  - Used for tracking: NO

Diagnostics > Crash data, performance data
  - Collected: YES
  - Linked to identity: NO
  - Used for tracking: NO

Identifiers > Anonymous device/session identifier
  - Collected: YES
  - Linked to identity: NO
  - Used for tracking: NO

Usage Data > App interaction events
  - Collected: YES
  - Linked to identity: NO
  - Used for tracking: NO

Location > Coarse (country/state)
  - Collected: YES
  - Linked to identity: NO
  - Used for tracking: NO

Tracking: NO
```

---

## Action Items Summary

| ID | Severity | Action | Owner | PR |
|---|---|---|---|---|
| H1 | HIGH | Remove `user_id` from `auth_magic_link_verified` event | Antigravity | Next PR |
| H2 | HIGH | Strip query params from `deep_link_opened` URL before logging | Antigravity | Next PR |
| L1 | LOW | Add Firebase SDK names to ASC App Privacy third-party section | Operator | ASC form |
| L2 | LOW | Add "Third-party SDKs" section to privacy policy | Antigravity | v1.3.2 PR |
| L3 | LOW | Verify Leopard `code` is non-PII; scrub if user-generated | Antigravity | v1.3.2 PR |
