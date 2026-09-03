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
| iOS | NOT built this cycle. Needs disk headroom (an archive wants several GB) |
| Android build | **1.7.3+26090301 LIVE on internal** 2026-09-03, verified via Play API (`internal: completed [26090301]`). Production untouched at `26083001`. Carries the welcome-screen instrumentation. Release script now exists: `scripts/play_upload_internal.py` (internal-only by construction). |
| Backend | **DEPLOYED 2026-09-03**, `de786fac`, dep-dacjalbm8hqs73b4s0eg, live. Smoke-verified in the wild: 3 events one session id -> `landing_sessions: 1`; a bot-UA event declaring `_ua_class:human` was REJECTED; `unclassified_sessions: 8` + `insufficient_data: true`. NOTE: Render says `autoDeploy: yes` but had not deployed since 2026-09-02 — the GitLab webhook is not firing. Deploy manually until that is fixed. |
| **Activation cliff — RELOCATED 2026-09-03** | The cliff is NOT at chat. Re-measured with `totalUsers` (was `eventCount`): 34 installs → 35 session_start → **9 compliance_check_started (26%)** → 8 → 3 first chat. `checkCompliance()` only runs AFTER the user taps "I am 18 or older", so the funnel began at the survivors of an UNMEASURED gate. ~74% never clear the welcome screen. Cause UNKNOWN — do not guess. `welcome_screen_viewed` + `welcome_age_confirmed` now instrument it; they read 0 until the next build ships. |
| Landing funnel | **FIXED, NEEDS DEPLOY.** `landing_sessions` counted events (no `X-Session-ID` → new uuid4 per request). Landing page now sends a per-tab UUID. Bot filter was dead by construction: the reader took the UA from metadata, which the log endpoint's allowlist always stripped, so it substituted a hardcoded Chrome UA. Now classified server-side at write time; pre-fix events report as `unclassified_sessions` + `insufficient_data` rather than a quiet zero. |
| Deep-link stickiness | **FIXED 2026-09-03.** `homeTabDeepLink._requested` was never cleared in production, so the last tab ever requested kept overriding `HomeShell.initialTab` on every later mount. Added `consume()`. 7 nav tests + positive control. |
| Notification permission drift | **FIXED 2026-09-03.** Permission was only checked when a toggle was flipped ON; revoking it in OS settings left the toggles showing "on" while the OS dropped every notification. Added non-prompting `hasPermission()` + one-directional reconcile on Settings entry. 4 tests + positive control. |
| Crisis fallback (assessment path) | **FIXED 2026-09-03.** The Q9 bridge now writes `kLastCrisisTimestampKey`, so the in-app re-entry surface actually arms. Before, only the CHAT crisis path wrote it — a user who disclosed via Q9 and denied notification permission got neither push nor surface, while two comments claimed the surface covered them. 3 tests + positive control. |
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

1. **ASC `pt` token — iOS installs are unattributed.** The store link carries
   `ct` but Apple requires BOTH `pt` (provider token) and `ct`. `pt` comes from
   generating a campaign link in App Store Connect and cannot be fabricated.
   Until then iOS attribution is dead on both surfaces (`landing-page/src/App.jsx`).

2. **GitLab -> Render webhook does not exist.** Confirmed 2026-09-03 via the
   GitLab API: the project has ZERO webhooks. Render reports `autoDeploy: yes`,
   which is why the setting looks healthy — nothing is listening to tell it a
   push happened. Every deploy must be triggered by hand (see below) until a
   hook is added. Creating a webhook is a persistent config change on the repo,
   so it needs an explicit go-ahead.

### Waiting on data (do not act before it reads)

3. **The welcome-screen cliff.** 1.7.3+26090301 (internal) is the first build
   carrying `welcome_screen_viewed` + `welcome_age_confirmed`. Until it has
   real traffic those stages read 0, which means "not deployed", not "nobody".
   When it has a day of use:
   `python3 -m metrics.onboarding_funnel_ga4 --days 7`
   That number decides whether ~74% never clearing the first screen is real or
   an artifact of the gate we just instrumented. **Do not propose a fix before
   it reads.** This plan has been wrong twice from exactly that impatience.

   Status of those events: **INSTRUMENTED, not VERIFIED.** Both call sites and
   both funnel stages are guarded by tests with positive controls
   (`test/screens/welcome_instrumentation_test.dart`), and the names are legal
   GA4 identifiers. But no test can prove DELIVERY: `logEvent` returns early
   when Firebase is uninitialised, which is always true under `flutter test`.
   Only the live funnel reading non-zero proves the pipe works end to end.

   Do NOT read a 0 as "nobody did it" until it has read non-zero at least once.

   Emulator note: verifying on-device was attempted and abandoned. A cold boot
   grew `~/.android/avd/Pixel_7.avd/userdata-qemu.img.qcow2` to 10.3 GB and
   filled the disk mid-build — the shell stopped working entirely until the
   emulator was killed. That file is reclaimable. The device path costs more
   than it proves here; live data settles it within a day.

### Done, recorded so nobody redoes them

- Shipped-code audit: **18/18 resolved.** 11 real bugs fixed, 3 refuted, 4
  partially-confirmed. Every fix carries an opposed control and a positive
  control.
- All four open decisions closed: funnel metric (eventCount -> totalUsers),
  landing session id, bot filter (was dead by construction), ADR-008 ratified
  with a corrected-risk amendment.
- Composer engagement ordering + inflation fixed 2026-09-03 (the last
  outstanding audit finding).

### Standing operating notes

- **Deploy the backend by hand** until the webhook exists:
  `POST https://api.render.com/v1/services/srv-d2r3i1fdiees73dqtov0/deploys`
  with `{"commitId": "<sha>"}` and the key from `~/.render/cli.yaml`.
  Then SMOKE IT — `live` status is not evidence the change works.
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
