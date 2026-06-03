# Firebase Console Setup — GentleQuest

> **Version:** 1.0.0 — authored 2026-06-03  
> **Project:** `gentlequestapp` (project number: 315814630048)  
> **Scope:** Minimum viable console configuration for v1.3.1 launch monitoring  
> **Item 6 of analytics goal** `relay_20260603T155332Z_cc_gq_to_agy_analytics_goal_v131`

---

## Overview

This document records the setup steps for the minimum-viable Firebase Console configuration that surfaces:
1. Crash-free user rate (Crashlytics velocity alert)
2. DAU/WAU/MAU (built-in Firebase metric — no setup required)
3. Funnel: `app_open → first_chat_message_sent → quest_completed`
4. Custom dashboard with 4 key tiles

> [!NOTE]
> Firebase Console UI configuration cannot be scripted via CLI — these steps require manual execution in the Firebase Console. This doc serves as the reproduction guide.

---

## Crashlytics Velocity Alert (Item 6, Step 1)

**Purpose:** Get notified if v1.3.1 has a crash rate spike after App Store release.

**Steps:**
1. Open [Firebase Console → GentleQuest → Crashlytics](https://console.firebase.google.com/project/gentlequestapp/crashlytics)
2. Click the gear icon (⚙️) → **Alerts**
3. Under **Velocity alerts**, click **Enable**
4. Set threshold: **Alert when crash rate exceeds 1% of sessions** (conservative for initial monitoring)
5. Email recipient: operator's Google account linked to Firebase project
6. Click **Save**

**Verification:** Alert email should appear in Firebase Console "Configured alerts" list.

---

## Audience: `engaged_users` (Item 6, Step 2)

**Purpose:** Create a cohort of users who fired `first_chat_message_sent` in the last 7 days — the most meaningful engagement signal for GentleQuest.

**Steps:**
1. Open [Firebase Console → Analytics → Audiences](https://console.firebase.google.com/project/gentlequestapp/analytics/audiences)
2. Click **Create audience** → **New audience**
3. Name: `engaged_users`
4. Description: `Users who sent their first chat message in the last 7 days`
5. Add condition:
   - Condition type: **Event** → select `first_chat_message_sent`
   - Time window: **In the last 7 days**
6. Click **Save**

**Why `first_chat_message_sent`:** This event is the primary activation gate. Users who reach this event are meaningfully using GentleQuest, not just opening the app.

---

## Funnel: Onboarding to First Chat (Item 6, Step 3)

**Purpose:** Measure conversion from app open → first meaningful engagement.

**Steps:**
1. Open [Firebase Console → Analytics → Funnels](https://console.firebase.google.com/project/gentlequestapp/analytics/funnels)
2. Click **Create funnel**
3. Name: `onboarding_to_first_chat`
4. Add steps:
   - Step 1: **Event** → `app_open` (label: "App opened")
   - Step 2: **Event** → `first_chat_message_sent` (label: "First message sent")
5. Optional Step 3 (if Firebase event data is populated): `quest_completed` (label: "Quest completed")
6. Set time window: **30 days**
7. Click **Save**

**Key metric:** Step 1 → Step 2 conversion rate. Baseline target: >20% of app_open sessions reach `first_chat_message_sent`.

> [!NOTE]
> `quest_completed` (Firebase) vs `quest_complete` (Backend) are different events. The Firebase funnel uses `quest_completed` from `quest_provider.dart`. Backend funnel would require BigQuery export. For v1.3.1, use Firebase-native events only.

---

## Custom Dashboard: GQ Daily Snapshot (Item 6, Step 4)

**Purpose:** Single-pane view of the four metrics that matter most for v1.3.1.

**Steps:**
1. Open [Firebase Console → Analytics → Dashboards](https://console.firebase.google.com/project/gentlequestapp/analytics/dashboards)
2. Click **Create dashboard** → Name: `GQ Daily Snapshot`
3. Add **Tile 1: DAU**
   - Click **Add card** → **Card type: Metric**
   - Metric: **Daily active users (DAU)**
   - Date range: Last 28 days
   - Title: `Daily Active Users`
4. Add **Tile 2: Crash-free user rate**
   - Card type: **Metric**
   - Metric: **Crash-free users** (from Crashlytics)
   - Date range: Last 7 days
   - Title: `Crash-free User Rate`
5. Add **Tile 3: first_chat_message_sent count**
   - Card type: **Event count**
   - Event: `first_chat_message_sent`
   - Date range: Last 7 days
   - Title: `First Chat Message (Activation)`
6. Add **Tile 4: intervention_offered vs intervention_accepted ratio**
   - Card type: **Event count** (two lines)
   - Events: `intervention_offered` and `intervention_accepted`
   - Date range: Last 7 days
   - Title: `Intervention Acceptance Rate`
   - (Compute ratio manually: accepted ÷ offered × 100%)
7. Click **Save dashboard**

---

## Data Population Note

> [!IMPORTANT]
> Firebase Analytics events from v1.3.1 will only appear in the dashboard **after Apple approves and releases the build**. Events from v1.3.0 (the currently live build) are NOT collected since v1.3.0 has no Firebase integration.
> 
> The v1.3.1 build is currently `WAITING_FOR_REVIEW` (submitted 2026-06-03T14:50:55Z). Typical Apple review: 24-48 hours.
>
> Initial population: 48-72 hours after release.

---

## dSYM Upload Status (Crashlytics — Item 1 Verification)

Retroactive dSYM upload for build `26060318` completed 2026-06-03:

```
Successfully submitted symbols for Runner.app.dSYM (UUID: 1e6a8ec2112d3f67893ef6b51b90d7e7)
Successfully submitted symbols for App.framework.dSYM (UUID: b974acc56d86369f95ce0d786970936e)
Successfully submitted symbols for Flutter.framework.dSYM (UUID: 4c4c44bd55553144a168f1213f21e615)
Successfully submitted symbols for FirebaseCrashlytics.framework.dSYM
[... 50+ total frameworks uploaded]
```

**Symbolication should work for crashes in v1.3.1.** To verify after release:
1. Install v1.3.1 TestFlight build
2. Open Settings → scroll to DEBUG section → tap "Test fatal crash"
3. Wait 24 hours
4. Check Firebase Console → Crashlytics → all-issues — should show a crash with symbolicated frames (function names, not hex addresses)

---

## Firebase Features NOT Enabled (Per Operator Constraints)

The following features require operator authorization before enabling:

| Feature | Why Not Enabled | Cost Impact |
|---|---|---|
| BigQuery Export | Requires BigQuery project + storage costs | ~$0.02/GB/month |
| A/B Testing | Requires explicit feature flag setup | Free tier available but operator decision |
| Remote Config | Could be useful for feature flags | Free |
| Google Ads integration | Not relevant for current growth stage | N/A |
| Predictions | Requires sufficient event volume | N/A |

---

## Reproduction Checklist (for future sessions)

- [ ] Crashlytics velocity alert configured for `gentlequestapp`
- [ ] `engaged_users` audience created
- [ ] `onboarding_to_first_chat` funnel created (2 steps: app_open → first_chat_message_sent)
- [ ] `GQ Daily Snapshot` dashboard created with 4 tiles
- [ ] dSYM upload verified for build 26060318
