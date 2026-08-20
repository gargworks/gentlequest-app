# Notification + retention findings — 2026-08-20

**Status: verified, unfixed.** Recorded because these were found in a working session and
would otherwise have existed only in an ephemeral relay thread.

Every claim below states how it was verified. Where something is inferred rather than
proven, it says so. Three separate wrong-object errors were made and caught during the
session that produced this document (a correct command run against the wrong repo's file,
twice, and a deploy-status check against a dead remote) — so treat any claim here without
a stated verification method as unverified.

---

## 1. Every scheduled local notification is undeliverable on Android

**Severity: high. Affects shipped builds, including a safety-adjacent feature.**

`flutter_local_notifications` 17.2.4 delivers `zonedSchedule` via an AlarmManager
`PendingIntent.getBroadcast` targeting
`com.dexterous.flutterlocalnotifications.ScheduledNotificationReceiver`. That receiver must
be declared by the **consuming app**. GentleQuest never declares it.

Verified three independent ways:

| Check | Result |
|---|---|
| `grep -E "receiver|BOOT_COMPLETED|dexterous" ai_buddy_web/android/app/src/main/AndroidManifest.xml` | only `POST_NOTIFICATIONS`; no `<receiver>`, no `RECEIVE_BOOT_COMPLETED` |
| plugin's real manifest: `~/.pub-cache/hosted/pub.dev/flutter_local_notifications-17.2.4/android/src/main/AndroidManifest.xml` | declares **only** `VIBRATE` + `POST_NOTIFICATIONS`. No receivers. |
| merged release manifest `ai_buddy_web/build/app/intermediates/merged_manifest/release/.../AndroidManifest.xml` | **zero** receivers of any kind |

The receivers *do* appear in the plugin's `example/android/app/src/main/AndroidManifest.xml`
— that is documentation showing consumers what they must declare. It is not merged into
consuming apps. Reading it and concluding "the plugin handles it" is the trap here.

**Consequence:** all five categories in `notification_service_impl.dart` (~1005 lines) are
silently dropped on Android — `dailyCheckin`, `worriedCheckin`, `weeklyReview`,
`streakNudge`, and **`crisisFollowup`**. The last is safety-adjacent in a mental-health app.

**Why this was never noticed:** the Settings "Send a test notification" button uses
`_plugin.show()` (`notification_service_impl.dart:357-374`), which fires immediately and
**bypasses the receiver entirely**. It works on Android while everything scheduled fails.
Anyone who QA'd notifications with that button would conclude the system was healthy.

**Fix (not applied):** declare in `ai_buddy_web/android/app/src/main/AndroidManifest.xml`
`ScheduledNotificationReceiver` and `ScheduledNotificationBootReceiver` (with
`BOOT_COMPLETED` / `MY_PACKAGE_REPLACED` / `QUICKBOOT_POWERON` intent filters), plus
`RECEIVE_BOOT_COMPLETED`. Do **not** add `SCHEDULE_EXACT_ALARM` / `USE_EXACT_ALARM` — all
call sites use `AndroidScheduleMode.inexactAllowWhileIdle`, and exact-alarm permissions
trigger Play policy review.

## 2. Notification taps route nowhere (all platforms)

`main.dart` `_handleNotificationPayload` matches only the bare strings `open_quest`,
`open_today`, `open_mood`, `open_talk` (`main.dart:80/96/109`) and falls through with no
`else`. Every scheduled payload is a URI — e.g.
`notification_service_impl.dart:459` `'gq://mood-log?source=push_daily'`, and similarly at
`:517`, `:598`, `:675`, `:808`. Even where a notification is delivered (iOS), tapping it
does nothing.

## 3. Server push is structurally dead — five independent breaks

Any one of these is sufficient. Verified individually:

1. **No client can obtain a token.** No `firebase_messaging` in `pubspec.yaml`/`pubspec.lock`;
   never present in any commit (`git log --all -S`).
2. **No client calls the registration endpoint.** `/api/user/push-tokens` appears only in
   `routes/push_tokens.py` and test files. The app has no push-token concept at all.
3. **Neither platform is provisioned.** `ios/Runner/Runner.entitlements` has only
   `associated-domains` — no `aps-environment`; no `UIBackgroundModes`. Android declares no
   `FirebaseMessagingService` and no messaging gradle dep.
4. **The backend could not send even with a valid token.** `apns2` and `firebase-admin` are
   in **no** requirements file (`grep -niE "apns|firebase" requirements.txt` → exit 1), and
   `Dockerfile:18-19` installs only `requirements.txt`.
5. **No credentials declared.** No `APNS_*` / `FCM_*` in `render.yaml`.

`push_tokens` has **0 rows in production** (verified by direct query). Note that the empty
table is a *symptom, not the break* — a table full of valid tokens would still send nothing,
because of break #4.

### 3a. Latent crash landmine in `services/push_delivery.py`

The imports sit **above** the config guards:
`:53-58` — `from apns2.payload import Payload` executes *before* the
`apns_not_configured` early-return; same shape at `:83-90` for `import firebase_admin`.
Neither `ImportError` is caught. So the graceful `*_not_configured` branches are
**unreachable dead code**: the first real token would raise `ModuleNotFoundError` and take
down the whole nightly job rather than degrade.

Compounding trap: `firebase_admin` **is** installed on the dev machine while absent from
every requirements file — so a local test of the Android path passes while the same code
would `ImportError` in the Docker image.

**Also note:** `push_delivery.py:123-125` silently `continue`s on `platform == "web"`.
Server push structurally excludes the majority of the user base (see §5).

## 4. Real app retention is UNKNOWN — the D14 instrument measures the wrong population

> **CORRECTED 2026-08-20, same day.** This section first claimed "retention is genuinely
> near zero — users open GentleQuest once and do not come back." **That claim was wrong**
> and is retracted. It was reached by ruling out one artifact (identity churn) and treating
> the survivor as proven, without running a positive control on the *population* being
> measured. A peer review asked "is a row written for every session, or only some?" — the
> right question, and it broke the claim. The corrected finding is below. The original
> error is left visible rather than quietly overwritten.

Session lifespan across all 265 distinct `session_id`s in `analytics_events` (direct
production query): **263 (99.2%) span under one hour**; 1 spans <1 day; 1 spans ≥14 days.

Two artifacts had to be ruled out before reading anything into that. Only one was.

**Artifact A — identity churn: RULED OUT.** `SessionManager.getOrCreateSessionId()`
(`lib/services/session_manager.dart:47-57`) resolves in-memory → persisted secure storage →
create-only-if-absent. `session_id` genuinely persists across relaunches, so returns are not
lost to id regeneration.

**Artifact B — wrong population: NOT ruled out. This is the real defect.**

```
events=313  distinct sessions=265  events/session=1.18
245 of 265 sessions (92%) have EXACTLY ONE event

event_type breakdown:
  cta_impression          206 events / 206 sessions   <-- landing-page marketing event
  compliance_ip_fallback   35 / 30
  compliance_passed        29 / 17
  first_chat_message       21 / 21
  web_app_open_from_cta    12 / 12
  chat_message              6 /  1
  cta_click                 4 /  4
```

**206 of 265 sessions (78%) exist solely because someone loaded a page carrying a CTA.**
Only **33 sessions** carry any real app-usage event at all.

`metrics/d14_cohort.sql` defines the cohort as *every* `session_id` whose earliest
`analytics_events` row lands on the cohort date — with no event-type filter and no platform
filter. So the D14 denominator is overwhelmingly **landing-page visitors who never installed
anything**. A web visitor who read a page and left is counted as a cohort member who "failed
to return on D14."

Worse, native app telemetry is barely present. Last 10 days: `first_chat_message` = 1,
`chat_message` = 1 — against 209 lifetime native installs (GA4 `first_open`: iOS 142 +
Android 67) and ~24 weekly actives. Whatever the native apps are doing, it is not landing in
this table in usable volume.

**Corrected verdict from `analytics_events`: INSUFFICIENT, not a value.** That instrument
measures something closer to landing-page bounce than app retention, and no data volume
fixes it.

### 4a. Re-measured properly via GA4 cohorts — the number is real now

Rather than leave it INSUFFICIENT, the sound path was built and run:
**`metrics/d14_cohort_ga4.py`** (new), using GA4's native cohort API on
`firstSessionDate`. Verified working 2026-08-20.

**Matured cohort, 2026-06-25 → 2026-07-25 (past D14, so scoreable):**

| platform | n | D1 | D7 | D14 |
|---|---|---|---|---|
| iOS | 3 | 0.0% | 0.0% | 0.0% |
| web | 87 | 0.0% | 0.0% | 0.0% |
| **ALL** | **90** | | | **0.0%** |

Only three return-visits exist across all 90 users, all before D6. **D14 = 0.0% on n=90.**
That is below the roadmap's own 7% *kill* line, not merely below the 15% pass bar.

**Gate window so far (2026-08-15 → present, post-1.6.0):** n=10, all web, **D1 = 10%**
(1 of 10) — the first non-zero D1 anywhere in the data. n=10 is far too small to read, and
the tool correctly returns INSUFFICIENT (49 days from maturity). Noted only because it is
the first movement, not as evidence 1.6.0 worked.

**Note on the epistemics, since it matters more than the number:** the original claim
("retention ~0%") and this one agree. The retraction in §4 was still correct and necessary
— a true conclusion reached through an invalid instrument is not knowledge, it is luck, and
it would have been indistinguishable from the many cases where the same reasoning produces
a wrong answer. The retraction is what produced the working instrument.

**Acquisition context (grim, and separate):** GA4 shows **zero** native newUsers in
2026-08-15→20; all 10 are web. Consistent with App Store Connect reporting 1 first-time
download across 90 days. Arrival is ~2/day and essentially all web, so the gate will be
measured on web traffic regardless of instrument — because that is who is actually arriving.

## 5. No notification lever can move the D14 gate

Platform mix (`metrics/analytics_latest.json`, 90d):
web 149 of 175 users (**85%**) — Linux 55, Windows 51, iOS 19, Mac 15, Android 9;
native iOS 16, native Android 10.

The D14 cohort query (`metrics/d14_cohort.sql`) counts server `session_id`s with **no
platform filter** — so web is fully in the denominator. Web receives no local notification
(`notification_service_web.dart` is entirely no-ops) and is explicitly skipped by server
push. Android is receiver-dead (§1). iOS notifications are opt-in and default-off
(`settings_screen.dart:163-165`, all toggles `?? false`), behind logging a first mood entry.

Maximum theoretical reach of any notification lever ≈ 15% of the gate's denominator;
realistic reach is single digits against a cohort of ~80.

Additional constraint: any client-side "first open" stamp only starts on the release build,
so the 2026-08-15 → ~08-27 sub-cohort is uncoverable by construction regardless of design.

---

## What follows from this

- Fix §1 and §2 as **repairs to four already-shipped broken features**, not as a retention
  lever. Do not book them against the D14 gate.
- Fix §3a regardless — it is cheap and it is a live landmine.
- Do **not** build server push for this gate: it costs more and reaches strictly fewer users
  than the local path.
- **The real finding is §4, and it is an instrumentation finding, not a product verdict.**
  Before anyone concludes anything about retention — good or bad — the D14 metric needs to be
  measured from GA4/Firebase rather than from `analytics_events`, whose population is ~78%
  landing-page traffic. Building a retention lever against the current number would be
  optimising against landing-page bounce.
- The roadmap's own middle band already grants one automatic 4-week extension to 2026-11-05.
  Taking it and rebuilding the measurement beats both a rushed release and a premature
  "retention is dead" conclusion.

## Still unverified

- Whether the local `app-release.aab` (1.6.0+26081301) is byte-identical to the build live
  on Play. The manifest evidence is from a local build artifact; identity with the shipped
  binary is an inference, though the version/build string matches the live listing.
- Whether any D14 cohort member has an email on file — load-bearing for the only
  store-release-free channel that already works (SendGrid, `routes/auth.py:117-163`).
- iOS runtime behaviour of the missing `UNUserNotificationCenter.current().delegate` in
  `AppDelegate.swift`. The plugin registers via `addApplicationDelegate`, so forwarding may
  still work. Not determinable without a device.
