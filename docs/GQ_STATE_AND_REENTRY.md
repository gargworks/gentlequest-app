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

1. **Finish the shipped-code audit.** 18 candidates. **13 resolved** (7 real -> fixed,
   3 refuted, 3 partially-confirmed with no action), **5 UNVERIFIED**.
   Resume the workflow when Claude session limit allows:
   `Workflow({scriptPath: <workflows/scripts/audit-gq-shipped-today-*.js>, resumeFromRunId: "wf_36e2bf2b-b69"})`
   — or keep verifying via glm-5-2 lanes, which do NOT consume the Claude limit.

   RESOLVED (later round, 2026-09-03): analytics toggle copy read broader than it acts
   — it gates only the backend stream, never GA4 (real, copy fixed + pinned 896169c1);
   iOS link has ct but no pt so ASC cannot attribute, and my own commit claimed it could
   (real, RETRACTED 8c848369 — iOS installs are unattributed on BOTH surfaces);
   cta_click beacon lost on same-tab nav, web CTA only (real, keepalive added 8c848369);
   landing beacon sends no X-Session-ID so every event mints a session — this is why
   206/265 "sessions" were landing-only; `landing_sessions` is an EVENT count (real,
   NOT fixed, needs a decision); cta_impression can never be bot-filtered because the
   funnel falls back to a hardcoded human UA (real, NOT fixed); composer-focus reset is
   RELIABLE but fires once per focus/blur cycle, so the stage inflates (partially).

   RESOLVED (first round): consent opt-out could never be logged (real, fixed d402426f);
   unknown GA4 platforms inflated native total (real, fixed 27d2f4c7);
   compliance_result cardinality mismatch (real, recorded — see the warning above);
   chat_tab_viewed "is a launch counter" (REFUTED — tabs build lazily, pinned by test);
   landing-page consent header "introduced by this diff" (REFUTED — inherited from an
   ancestor commit); onboarding_funnel unknown-platform inflation (REFUTED — that module
   filters correctly, though it drops unknowns silently, which is worth a look).

   PARTIALLY-CONFIRMED, no action taken:
   - Starter chips auto-send without focusing first (`interactive_chat_screen.dart:1652`),
     so `chat_send_attempted` fires BEFORE `chat_composer_focused`. A post-frame
     `requestFocus` backfills the focus event, so counts mostly hold — but the ORDER is
     inverted, which breaks any sequence-based funnel reading.
   - New events read 0 for the current production installed base (they ship only in
     26090203, internal track), so per-stage conversions between compliance_result and
     first_chat_message show "0%" then blanks until the build reaches production.
     `overall_install_to_chat_conversion` is computed install->chat directly and is
     UNAFFECTED — read that field, not the per-stage bars, in the meantime.
   - channel_installs issues one unpaginated GA4 request (limit 100k, no row_count check).
     Moot today (1 channel row); structurally a silent-truncation risk if the dimension
     ever goes high-cardinality. onboarding_funnel copied the same pattern.

2. **Activation cliff cause.** Still unknown. Instrumentation is shipped but needs users on
   `26090203`. Hypothesis workflow: `resumeFromRunId: "wf_07ec29c2-186"`. DO NOT guess a
   cause — four guesses have already been wrong.
3. **ASO full description.** Verified 3091-char copy in `docs/ASO_STORE_OPTIMIZATION.md`
   (last section). Apply via `play-store-upload@gentlequest-prod`. Operator approval needed.
4. **Weekly-review push destination** — `notification_payload_router.dart:42` sends the
   Sunday push to the mood surface, not the letter. Product decision.
5. **Orphaned retention lever** — `scheduleWeeklyReviewIfEligible` has zero callers.
   Wire or delete; a lane investigation was dispatched and never returned.
6. **iOS release** once disk allows.

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
