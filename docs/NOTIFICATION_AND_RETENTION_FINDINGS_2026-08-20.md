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

## 4. Retention is genuinely near zero — and this is NOT an instrumentation artifact

Session lifespan across all 265 distinct `session_id`s ever recorded
(`analytics_events`, direct production query):

| span between first and last event | sessions |
|---|---|
| < 1 hour | **263 (99.2%)** |
| < 1 day | 1 |
| ≥ 14 days | 1 |

The obvious hypothesis — "`session_id` regenerates per launch, so returns are undetectable
by construction" — was **checked and refuted**. `SessionManager.getOrCreateSessionId()`
(`lib/services/session_manager.dart:47-57`) resolves in-memory → persisted secure storage →
create-only-if-absent. The id persists across relaunches.

**So the data means what it says: users open GentleQuest once and do not come back.**

Caveat, honestly stated: persistence is strongest on native. On web, secure storage degrades
to browser storage, which incognito/clearing wipes — so the web slice of this number is
softer than the native slice. That weakens the precision, not the direction.

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
- The real finding is §4. A notification does not fix a product people do not return to.
  The roadmap's own middle band already grants one automatic 4-week extension to 2026-11-05;
  reading the gate honestly and taking that beats a rushed release chasing ~9% of the
  denominator.

## Still unverified

- Whether the local `app-release.aab` (1.6.0+26081301) is byte-identical to the build live
  on Play. The manifest evidence is from a local build artifact; identity with the shipped
  binary is an inference, though the version/build string matches the live listing.
- Whether any D14 cohort member has an email on file — load-bearing for the only
  store-release-free channel that already works (SendGrid, `routes/auth.py:117-163`).
- iOS runtime behaviour of the missing `UNUserNotificationCenter.current().delegate` in
  `AppDelegate.swift`. The plugin registers via `addApplicationDelegate`, so forwarding may
  still work. Not determinable without a device.
