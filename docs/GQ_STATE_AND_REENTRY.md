# GentleQuest — live state + re-entry contract

Single source of truth for a cold session. Read this FIRST, then act.
The reasoning behind the plan (why each workstream exists, what was tried and retracted)
lives in `docs/plan/GQ_5WEEK_PLAN.md`.
Update the STATUS table and OPEN QUEUE in the same commit as any work you ship.

Last updated: 2026-09-03

---

## THE GOAL (one line)

Get GentleQuest to a **scorable D14 retention verdict** on a legitimate window,
by making activation real and measurable — without shipping anything false to users.

Criterion (A) installs is already **PASSED** (ADR-006, 353 installs). Do not chase installs.
Criterion (B) D14 ≥15%, n≥40 is the whole game. Everything else is in service of it.

---

## STATUS

| Area | State |
|---|---|
| Play internal track | `1.7.2+26090203` live — crisis fix, nav fix, funnel events, consent toggle |
| Play production | `26083001` (older) — promote is OPERATOR-ONLY |
| Backend (Render) | live at `f88c36a9`; **auto-deploy is OFF**, deploy manually via API |
| Committed but NOT in any build | weekly-review personalization, consent opt-out fix, lazy-tab test |
| iOS | **LAUNCH CONFIRMED by the operator on a real iPhone (iOS 26.1), 2026-09-04.** 1.7.3 (26090304) (Delivery c48b4f83). ROOT CAUSE of the black screen, found by comparing a known-good IPA: an **iOS SDK mismatch**. Xcode 26.5 links Runner against SDK **26.5**, but Flutter 3.32.8's engine is built against **18.2** — 8 major versions apart — so iOS 26 composites via a path that engine does not drive. Frames render (the app-switcher snapshot showed the splash perfectly) but never reach the display: black, no crash, no error. The working 1.2.1 IPA had Runner sdk 18.5 / engine 18.2 — MATCHED. Fix: **Flutter upgraded 3.32.8 -> 3.47.2** (engine sdk 26.2). Now Runner 26.5 / engine 26.2. 3.35.7 was tried first and its engine is still 18.2, so it would NOT have fixed this. Suite 421 pass, same 5 known failures, 0 analyze errors. |
| Android build | **1.7.3+26090301 LIVE on internal** 2026-09-03, verified via Play API (`internal: completed [26090301]`). Production untouched at `26083001`. Carries the welcome-screen instrumentation. Release script now exists: `scripts/play_upload_internal.py` (internal-only by construction). |
| Backend | **DEPLOYED 2026-09-03**, `de786fac`, dep-dacjalbm8hqs73b4s0eg, live. Smoke-verified in the wild: 3 events one session id -> `landing_sessions: 1`; a bot-UA event declaring `_ua_class:human` was REJECTED; `unclassified_sessions: 8` + `insufficient_data: true`. NOTE: Render says `autoDeploy: yes` but had not deployed since 2026-09-02 — the GitLab webhook is not firing. Deploy manually until that is fixed. |
| **Activation cliff — RELOCATED 2026-09-03** | The cliff is NOT at chat. Re-measured with `totalUsers` (was `eventCount`): 34 installs → 35 session_start → **9 compliance_check_started (26%)** → 8 → 3 first chat. `checkCompliance()` only runs AFTER the user taps "I am 18 or older", so the funnel began at the survivors of an UNMEASURED gate. ~74% never clear the welcome screen. Cause UNKNOWN — do not guess. `welcome_screen_viewed` + `welcome_age_confirmed` now instrument it; they read 0 until the next build ships. |
| Landing analytics | **PROVEN END-TO-END IN THE WILD 2026-09-03.** GA4 realtime on the NEW property 551876340 recorded real traffic from gentlequest.app: `page_view 5, cta_impression 2, first_visit 1, session_start 1`. So the repoint is not just deployed, it is RECEIVING. Backend side: a real page load moved `landing_sessions` +1 with 0 unclassified (the server classified a real Chrome UA as human), 3 reloads in one tab stayed ONE session, and two tabs held distinct ids (read directly from sessionStorage). **Test-environment gotcha:** a fully BACKGROUND tab has `document.visibilityState === 'hidden'` and Chrome does not run IntersectionObserver callbacks there, so `cta_impression` never fires. I briefly read that as a product bug. It is not — verify with a focused window, or use GA4 realtime which sees `page_view` regardless. |
| Landing page | **DEPLOYED + VERIFIED LIVE 2026-09-03.** gentlequest.app now serves `G-MBBHN4PT39` (old `G-Z4Z92EJ3DV` gone), and the bundle carries session id, keepalive, cta events, UTMs and store links. blog/rss/about/app/privacy/terms all resolve 200. **Deploy the LANDING dist, never the blog dist:** `landing-page/dist` composes landing + blog; `gentlequest-blog/dist` is blog-ONLY and deploying it to Pages would delete the landing page. And do NOT `cp static-root/*` into the landing dist — static-root has its OWN index.html that clobbers the landing one (I did this; it replaced the live homepage for ~2 minutes). |
| ~~Landing page — NOT DEPLOYED~~ | **Discovered 2026-09-03.** gentlequest.app is served by **Cloudflare Pages** (project `gentlequest-www`, via `wrangler pages deploy`), NOT by Render. The Render `gentlequest-landing` service is vestigial: it points at github.com/eidetic-works (auth-dead) and last deployed **2026-08-04**. The live bundle still carries the OLD GA4 id `G-Z4Z92EJ3DV`, has no store links, no `cta_impression`, no `analytics/log`, no `X-Session-ID`. So EVERY landing change from 2026-09-02/03 is dead code in production: GA4 repoint (5b47762f), UTM tagging (1a91b985, f88c36a9), keepalive (8c848369), session id. Needs a manual wrangler deploy — operator decision, not taken. |
| Deploy smoke | **FIXED 2026-09-03.** The smoke printed "the forged bot was not counted" while asserting only `landing_sessions >= 1` — if the bot HAD been counted the number would just be bigger and it still printed success. Now asserts the DELTA is exactly +1, which tests grouping and bot-rejection in one number. |
| Bot laundering | **FIXED 2026-09-03 (second pass).** A bot could count as human by sending a bot-UA event then a browser-UA event on the SAME session id: `session_meta.update()` was last-write-wins and the events query has no `order_by`. Now fail-closed — one bot event condemns the session. Also removed a no-op guard whose comment falsely claimed session-shape rules applied, and `insufficient_data` now covers an empty window. Found by a lane auditing the FIRST pass. |
| Landing funnel | **FIXED, NEEDS DEPLOY.** `landing_sessions` counted events (no `X-Session-ID` → new uuid4 per request). Landing page now sends a per-tab UUID. Bot filter was dead by construction: the reader took the UA from metadata, which the log endpoint's allowlist always stripped, so it substituted a hardcoded Chrome UA. Now classified server-side at write time; pre-fix events report as `unclassified_sessions` + `insufficient_data` rather than a quiet zero. |
| Deep-link stickiness | **FIXED 2026-09-03.** `homeTabDeepLink._requested` was never cleared in production, so the last tab ever requested kept overriding `HomeShell.initialTab` on every later mount. Added `consume()`. 7 nav tests + positive control. |
| Notification permission drift | **FIXED 2026-09-03.** Permission was only checked when a toggle was flipped ON; revoking it in OS settings left the toggles showing "on" while the OS dropped every notification. Added non-prompting `hasPermission()` + one-directional reconcile on Settings entry. 4 tests + positive control. |
| Crisis fallback (assessment path) | **FIXED 2026-09-03.** The Q9 bridge now writes `kLastCrisisTimestampKey`, so the in-app re-entry surface actually arms. Before, only the CHAT crisis path wrote it — a user who disclosed via Q9 and denied notification permission got neither push nor surface, while two comments claimed the surface covered them. 3 tests + positive control. |
| **Android build BLOCKED** | **`flutter build appbundle` FAILS on Flutter 3.47.2.** Chain of required bumps, all applied: Gradle 8.12->8.14.3, AGP 8.7.3->8.11.1, Kotlin 2.1.0->2.2.20. The remaining blocker is a DEPENDENCY, not config: `sentry_flutter ^8.9.0` fails `compileReleaseKotlin` under Kotlin 2.2.20 — "Language version 1.6 is no longer supported; use 1.8 or greater". Fix = upgrade sentry_flutter (9.x/10.x) and adjust `Sentry.init` in main.dart if its API moved. Scoped task, not a tweak. **The AAB already on Play internal (26090302) is unaffected and still installable** — this blocks the NEXT Android build only. Do not attempt under 6 GB free disk. |
| Toolchain | **Flutter is now 3.47.2** (was 3.32.8), on the SHARED checkout at `/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter` — a detached checkout at the tag. This affects EVERY project using that Flutter, not just GentleQuest. Required for iOS: only an engine built against the iOS 26 SDK renders on a phone once Xcode 26 links the app against SDK 26. Android AAB 26090302 currently on Play internal was built on 3.32.8; rebuild on 3.47.2 before the next Android ship so the two platforms are not on different engines. |
| targetSdk 36 risk | **LOWER than first reported.** Edge-to-edge keys off targetSdk >=35 and the app was already at 35 (incl. production 26083001), so 35->36 introduces essentially no new exposure. Notifications unaffected (inexact alarms, no FGS). Composer and bottom nav are inset-aware (SafeArea + viewInsets). Ordinary release QA still applies. |
| ADR-008 (D14 window restart) | **PROPOSED, unratified** — operator decision, kill-clause relevant |
| ASO listing | live copy is 573/4000 chars, no "ADHD"; verified replacement ready, NOT applied |

## THE MEASURED NUMBERS (do not re-derive; re-measure only if stale)

```
GA4 property 551876340, native only (iOS+Android), 7d:
  first_open 22 -> compliance_check_started 16 -> compliance_result 12
  -> first_chat_message_sent 3
Channel attribution, 30d: 100% of installs are "(direct) / (none)"
```

### ⚠️ THE 12 -> 3 CLIFF IS NOT A CLEAN NUMBER (verified 2026-09-03)

**The funnel divides an EVENT count by a USER count.** Do not act on 25% as if it
were a user conversion rate.

- `compliance_result` has **no dedupe guard** — 9 emitters in
  `compliance_service.dart`, none gated. `HomeShell.didChangeAppLifecycleState`
  calls `checkCompliance()` on **every app resume** (`home_shell.dart:86-96`), and
  the cached-allow path every returning user hits fires it unconditionally
  (`compliance_service.dart:488-492`). One user who opens the app 4 times
  contributes 4.
- `first_chat_message_sent` is once-per-install, guarded by
  `first_chat_message_logged_v1` (`chat_provider.dart:116`).

So "12" is resumes-and-checks, "3" is distinct humans. If 3 users each resumed 4
times, that is 12 -> 3 and a **100%** conversion, not 25%. The true cliff is
somewhere between 0% and 75% loss and **cannot be read off this funnel at all**.

`compliance_check_started` (16) is unguarded too — same problem.

**Before any activation work:** re-measure with a user-scoped metric (GA4
`totalUsers`/`activeUsers` per event rather than `eventCount`), or add a
once-per-install guard to the compliance events. Until then the cliff's SIZE is
unknown, not just its cause.

## OPEN QUEUE (ordered by leverage)

Rewritten 2026-09-03. The previous version described an audit that has since
finished and decisions that have since been made; it was stale enough to
mislead a cold session.

### Blocked on the operator (I cannot do these)

0. ~~Deploy the landing page~~ **DONE 2026-09-03, verified live.** The command
   that is correct (NOT `scripts/deploy_blog.sh`, which deploys the blog-only
   dist and would delete the landing page):

       cd landing-page && npm run build          # composes landing + blog
       cp ../gentlequest-blog/public/_redirects dist/_redirects
       unset CLOUDFLARE_API_TOKEN
       wrangler pages deploy dist --project-name gentlequest-www \
         --commit-dirty --branch main

   Then verify the LIVE apex, not the pages.dev preview URL, and confirm the
   bundle the HTML references returns 200.

1. **ASC `pt` token — iOS installs are unattributed.** The store link carries
   `ct` but Apple requires BOTH `pt` (provider token) and `ct`. `pt` comes from
   generating a campaign link in App Store Connect and cannot be fabricated.
   Until then iOS attribution is dead on both surfaces (`landing-page/src/App.jsx`).

2. ~~GitLab -> Render webhook~~ **FIXED 2026-09-03.** The project had ZERO
   webhooks; Render's `autoDeploy: yes` looked healthy because the setting was
   real and only the delivery mechanism was missing. GitLab hook `88208404` now
   posts to the Render deploy hook on push, filtered to `main`, SSL verify on.
   PROVEN, not assumed: a test push event produced a Render deploy with
   `trigger: deploy_hook` (not `api`), which reached `live`. Pushes to main
   deploy themselves again.

### Waiting on data (do not act before it reads)

3. **The welcome-screen cliff.** 1.7.3+26090301 (internal) is the first build
   carrying `welcome_screen_viewed` + `welcome_age_confirmed`. Until it has
   real traffic those stages read 0, which means "not deployed", not "nobody".
   When it has a day of use:
   `python3 -m metrics.onboarding_funnel_ga4 --days 7`
   That number decides whether ~74% never clearing the first screen is real or
   an artifact of the gate we just instrumented. **Do not propose a fix before
   it reads.** This plan has been wrong twice from exactly that impatience.

   **VERIFIED ON DEVICE 2026-09-03.** Fresh install on the Pixel_7 emulator,
   driven by adb, `debug.firebase.analytics.app` set: GA4 realtime showed
   `welcome_screen_viewed 2, welcome_age_confirmed 2, compliance_check_started
   2, chat_tab_viewed 1`. The whole first-run chain reports.

   Gotcha that cost 20 minutes: Android BATCHES custom events (auto events like
   first_open upload immediately, custom ones queue up to ~1h). Without
   `adb shell setprop debug.firebase.analytics.app app.gentlequest.www` the
   custom events look absent and it reads exactly like a dead instrument.

   **NEW: the vow screen is the TRUE first screen** ("This is your companion /
   Begin"), and it had zero instrumentation. Its Begin button is hidden until
   ~16.6s (halved under reduced motion) with only a small Skip link before
   that. Now instrumented: `vow_screen_viewed`, `vow_begin_tapped`,
   `vow_skipped`, the latter two carrying `elapsed_ms` + `reduced_motion`.
   NOT claimed as the cause of the ~74% — measured next build.

   Previous status of the welcome events: **INSTRUMENTED, not VERIFIED.** Both call sites and
   both funnel stages are guarded by tests with positive controls
   (`test/screens/welcome_instrumentation_test.dart`), and the names are legal
   GA4 identifiers. But no test can prove DELIVERY: `logEvent` returns early
   when Firebase is uninitialised, which is always true under `flutter test`.
   Only the live funnel reading non-zero proves the pipe works end to end.

   Do NOT read a 0 as "nobody did it" until it has read non-zero at least once.

   **Read 2026-09-04, and the answer is "not yet, and not because of lag".**
   Every install running an instrumented build is MINE (emulator) or the
   operator's phone. n=10, all internal. The 74% question needs REAL installs;
   no amount of waiting on GA4 changes that.

   Use `--min-version 1.7.3`. Without it the funnel mixes builds that cannot
   emit the new stages into the denominator and conversions exceed 100%
   (welcome_viewed read 500%). A ratio over 100% is the instrument saying the
   stages were measured over different populations — not a finding.

   Granularity limit: GA4's appVersion is the versionNAME, so 1.7.3 covers
   26090301 (no vow events) through 26090305 alike, and welcome_viewed still
   reads 500% inside it. **Bump the version NAME, not just the build number,
   when shipping a new funnel stage.**

   Emulator note: verifying on-device was attempted and abandoned. A cold boot
   grew `~/.android/avd/Pixel_7.avd/userdata-qemu.img.qcow2` to 10.3 GB and
   filled the disk mid-build — the shell stopped working entirely until the
   emulator was killed. That file is reclaimable. The device path costs more
   than it proves here; live data settles it within a day.

### Known-open, deliberately not fixed (owner: next session)

4. **Analytics are now testable for real — SEAM LANDED 2026-09-03.**
   `FirebaseService` implements a narrow `AnalyticsSink`, with a
   `@visibleForTesting static sinkOverride`. Zero call-site changes across 64
   sites. Install `RecordingAnalyticsSink` (test/helpers/) in setUp, null it in
   tearDown.

   Anonymity is checked BEFORE the seam on purpose: a privacy promise must not
   have an observability hole, and that ordering is pinned by a test.

   `welcome_screen_analytics_test.dart` is the first test that proves an event
   FIRES at runtime rather than that a string exists in the source. Measured
   difference: move the logEvent into a never-invoked closure and the widget
   test FAILS while the source-grep test PASSES.

   DONE 2026-09-03: `composer_engagement_widget_test.dart` pumps the REAL
   `InteractiveChatScreen` (ChatProvider + CompanionProvider + SurveyProvider,
   bounded pumps — `pumpAndSettle` times out on its animations) and covers
   order, once-only, and the chip path. The mirror is deleted; only its three
   source drift guards survive.

   Measured, not assumed: with the emitted event name changed to a typo — which
   silently kills the funnel stage — the mirror passed 7/7 while the widget
   test failed. That is why the mirror went.

5. **The linux-desktop bot rule is dead in both paths.**
   `is_qualified_human`'s third rule needs a real UA, and both callers supply
   something else: the write path passes constants that exempt it, the read
   path passes `DEFAULT_UA` (a Mac string). A headless Linux agent is not
   caught by it. This PREDATES 2026-09-03 and is left alone deliberately —
   fixing a filter blind, with no measurement of what it would start excluding,
   is how the last three bugs in this area were created.

### Done, recorded so nobody redoes them

- Shipped-code audit: **18/18 resolved.** 11 real bugs fixed, 3 refuted, 4
  partially-confirmed. Every fix carries an opposed control and a positive
  control.
- All four open decisions closed: funnel metric (eventCount -> totalUsers),
  landing session id, bot filter (was dead by construction), ADR-008 ratified
  with a corrected-risk amendment.
- Composer engagement ordering + inflation fixed 2026-09-03.
- **SECOND-PASS audit of that same day's work (lanes pointed at MY fixes)** —
  five more real defects, all now fixed: bot laundering via last-write-wins
  session metadata; a no-op guard whose comment claimed protection it never
  gave; `insufficient_data` False on an empty window; a deploy smoke that
  printed "the forged bot was not counted" while never checking it; drift
  guards covering only one of the two call sites.

  **The lesson, which is the point of keeping this entry:** the first pass was
  declared complete and clean. Auditing the FIXES found as many real bugs as
  auditing the original code, and three of them were the SAME defect — a check
  aimed at the wrong object — reintroduced inside the fix for it. When this
  area is touched again, audit the repair, not just the code it repaired.

### Standing operating notes

- **Backend deploys are automatic again** (hook 88208404). To deploy a
  specific commit, or to deploy AND smoke it in one step:
  `scripts/deploy_render.sh [sha]` — waits for `live`, then exercises the real
  endpoints (session grouping, forged-bot rejection). `live` is not evidence
  the change works; the script refuses to call it done on status alone.
  It also warns when the Render CLI token is near expiry — that token is a
  SESSION token, not a long-lived key, and its first symptom on expiry is a 401
  during an urgent deploy. Expires 2026-09-05; run `render login` to refresh.
- **Ship Android** with `scripts/play_upload_internal.py` (internal-only by
  construction; promotion stays a Console action).
- **Check `df -h /` before any build.** 66 test files "failed to load" earlier
  in this session at 100% disk; it was errno 28, not the code.

## CREDENTIALS / INFRA (hard-won; do not re-discover)

- Play API: `~/Downloads/gentlequest-prod-d698b1aa74fb.json` (`play-store-upload@gentlequest-prod`).
  `gentlequestapp-sa.json` has the API DISABLED; `firebase-adminsdk` lacks Console permission.
  Two different 403s, both wrong accounts — not an access wall.
- GA4: property `551876340`, web stream `G-MBBHN4PT39`. SA at `secret/gentlequestapp-sa.json`.
  This machine needs an IPv4 `socket.getaddrinfo` monkeypatch for GA4 calls.
- Render: `srv-d2r3i1fdiees73dqtov0`, key in `~/.render/cli.yaml`. Auto-deploy OFF.
- Flutter: `/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin` (SSD must be mounted).
- Gates: `flutter analyze` = **8** baseline. `flutter test` = **5 known failures**
  (interactive_chat x1, j03_compliance x4). Anything else is yours.

## HOW TO WORK HERE (learned the hard way, 2026-09-02/03)

**Delegate by default.** Use `nucleus_delegate` with `vendor:"devin", model:"glm-5-2"` for all
investigation, mechanical edits, and copy work. It is free and does not consume Claude session
limits. Chief (Claude) does: judgment calls, verification, commits, anything touching crisis or
privacy paths.

**Six times in one session a confident, well-argued conclusion was WRONG.** Every one was caught
by a control, never by thinking harder. Therefore:

- **Never trust `nucleus_delegate`'s `effect`/`changed_paths`.** It is HEAD-based and lanes are
  told not to commit, so real work reports `no_files_touched`. Reproduced 6x. Verify with
  `git status --porcelain` — and note `metrics/**` is gitignored, so files there are invisible
  to BOTH checks (`git add -f`, and see nucleus-private#316/#319).
- **A lane's fix suggestion can be worse than the bug.** One proposed flipping a boolean seed
  that would have silently disabled every notification in the app. Read the code before applying.
- **Run the positive control.** After adding a guard, break it deliberately and confirm the test
  FAILS. A guard that passes with the guard removed is untested.
- **`df -h /` before blaming load.** 66 test files "failed" at 100% disk (errno 28) while
  analyze was clean. Uniform failure across unrelated files = environment, not code.
- **Reading agreement is not verification.** Two agents reading the same lines and agreeing is
  ONE check. Ask a lane to REFUTE, or to write an opposed-pair test.
- **Never ship text the app cannot substantiate.** The ASO draft asserted "no analytics SDKs"
  and "your data stays on your device" — both false. The weekly letter attributed invented
  words to the user. In a mental-health app these are trust defects, not copy defects.

**Operator-only actions:** production promote, store listing changes, ADR ratification,
anything outward-facing, deleting files the session did not create.

---

## RE-ENTRY PROMPT (paste this to restart cheaply)

> Read `docs/GQ_STATE_AND_REENTRY.md` in ~/gq-wo and continue the OPEN QUEUE in order.
> Delegate all investigation and mechanical work to glm-5-2 via nucleus_delegate; keep only
> judgment, verification and commits for yourself. Verify every lane's work with
> `git status --porcelain` and a real test run — never the tool's verdict, never the lane's
> report. Run a positive control on any guard you add. Do not guess the activation-cliff
> cause; it needs data. Do not apply store copy, promote to production, or ratify ADR-008
> without asking me. Update the STATUS table and OPEN QUEUE in the same commit as anything
> you ship. If you find yourself confident and unverified, stop and build the control instead.
