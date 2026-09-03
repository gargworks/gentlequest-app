# ADR-008 — Stage-1 criterion (B): INSUFFICIENT-structural, window restarts 2026-08-27

**Status:** **RATIFIED 2026-09-03** by the operator ("do as recommended on
decisions"). It governs from today. Amend by appending — never by rewriting.
**Date:** 2026-09-02
**Decides:** the question ADR-007's second amendment deliberately left open
(`ADR-007-stage1-retention-instrument.md:182-196`).
**Supersedes nothing.** ADR-006 (criterion A, PASS) and ADR-007 (the instrument)
stand as written. This ADR only rules on how criterion (B) is scored.

---

## The question

`BILLION_DOLLAR_ROADMAP.md:90` auto-scores criterion (B) **FAILED** if the
retention pipeline was not verified live by 2026-08-15. It was not — the app had
no GA4 property at all between 2026-06-03 and 2026-08-27
(`ADR-007:128-130`, `:177-180`).

`ADR-007`'s first amendment argues the honest state is **INSUFFICIENT for
structural reasons** — an instrument that never ran is not a measurement that
came back negative.

Both documents are live and they disagree. The roadmap's middle-band clause
(`ROADMAP:96`) allows ONE automatic 4-week extension to **2026-11-05**.

## Decision

**(b): score criterion (B) INSUFFICIENT-structural, restart the acquisition
window at 2026-08-27, and invoke the single 4-week extension to 2026-11-05.**

New ratified window: **2026-08-27 → 2026-10-22**.
Earliest complete D14 read: **2026-11-05** for a cohort closing 2026-10-22;
the first fully-mature cohort reads from ~2026-09-10 onward.
Data source: GA4 property **551876340** (named here per the rule the first
amendment set — a gate ADR must name its data source in ratified text, not in a
constant).
Population: unchanged from ADR-007 — native iOS + Android only, web excluded as
`unqualified_marketing_mix`.

Criterion (B) is **not** scored today. It is scored once, on the new window.

## Why not (a) — score it FAILED

Scoring FAILED would record a **product verdict** where only an
**instrumentation gap** exists. Nothing was learned about whether users return;
the question was never asked of them. The roadmap's own governing principle is
"**Unmeasurable = FAILED** … never 'extend to find out'" (`ROADMAP:52`) — and
that principle is right, but it is aimed at a different failure: refusing to
accept a bad number that the instrument *did* produce. Here the instrument
produced nothing at all, because it did not exist.

The distinction is the one this project already ratified elsewhere: `not_mature`
implies data is accruing; when nothing is accruing, that is a different verdict.
Collapsing INSUFFICIENT into FAILED destroys exactly the information the third
state exists to preserve.

This is not "extending to find out." The extension clause is being invoked for
its stated purpose, once, with a hard stop.

## What this ADR does NOT do

- It does **not** weaken the threshold. D14 ≥15%, n≥40 is unchanged. n<40 on the
  new window is still FAILED, not another extension.
- It does **not** grant a second extension. `ROADMAP:96` allows one; this is it.
  A miss on 2026-11-05 freezes the ADR, per the kill clause.
- It does **not** re-open criterion (A). ADR-006 closed it PASS on 2026-08-18
  (209 native + 144 web = 353).

## Risk this ruling accepts, stated plainly

The new window buys 4 weeks, and the product's re-engagement mechanism is
**partly repaired but still blocked at the first-run gate**.

*(Corrected 2026-09-02, before ratification. An earlier draft of this section
claimed scheduled notifications were wholly undeliverable, citing the
2026-08-20 finding. That claim was 13 days stale and is **false as of today** —
verified by direct read. It is corrected here rather than silently dropped,
because the stale version briefly informed this ADR's reasoning.)*

- **Fixed:** `ScheduledNotificationReceiver` and `ScheduledNotificationBootReceiver`
  (with `BOOT_COMPLETED`, `MY_PACKAGE_REPLACED`, and two `QUICKBOOT_POWERON`
  variants) **are** declared —
  `ai_buddy_web/android/app/src/main/AndroidManifest.xml:104-116`. All
  `zonedSchedule` call sites use `AndroidScheduleMode.inexactAllowWhileIdle`,
  deliberately avoiding the exact-alarm Play-policy review. The AlarmManager
  path is intact.
- **Also correct by design, contrary to a second claim I made here:** the three
  toggle-driven categories (daily reminder, gentle nudge, worried check-in)
  default OFF, schedule nothing until an explicit opt-in, and each toggle
  awaits `requestPermissions()` and **reverts the pref on denial**
  (`settings_screen.dart:211-221,260-265,297-302`). The permission is requested
  exactly when it is first needed. Nothing is "silently suppressed" — most
  categories are simply never scheduled, which is the intended behaviour.
- **One real defect existed and is now fixed** (`c9f48350`):
  `scheduleCrisisFollowup` — the only category not behind a toggle — scheduled
  with no permission request at all, so a user picking "heavy" in the Q9 crisis
  bridge received a follow-up the OS silently discarded. It now asks first, at
  the service level, with an opposed-pair test and a verified positive control.

*(Second correction to this section, and worth recording as such: this ADR has
now carried two different wrong claims about notifications — first "wholly
dead", then "every scheduled notification suppressed". Both were mine, both
were refuted by dispatching a lane specifically to attack them. The section
survived only because it was checked twice before ratification. Treat any
remaining confident claim in this ADR accordingly.)*

**Revised risk.** Notifications are NOT the blocker this ADR originally named.
The honest residual risk is narrower and less tractable: almost nobody opts in,
because the toggles default off and live in Settings. Whether that suppresses
D14 enough to fail the gate is unknown, and should be settled by the funnel
instrumentation shipped in `78d0d757` rather than by another guess. The
extension is still only worth invoking if real activation/retention work ships
inside it.

That is the correct outcome if it happens — a real number, honestly obtained.
But it means the extension is only worth invoking if the retention work
*actually ships inside it*. **Ratifying this ADR without fixing notifications is
choosing a slower path to the same failure.**

A prior finding (2026-08-20) warned that no notification lever could move the
D14 gate, because 78% of the then-denominator was landing-page visitors who
never installed. **That warning applied to the old `analytics_events`-based
instrument and is now obsolete**: ADR-007's population is native-only and
excludes web by construction, so the denominator is now people who actually
installed the app and can, in principle, be re-engaged.

## Verification

The ruling is verifiable, not merely asserted:

```bash
# the instrument, against the ratified property
python3 metrics/d14_cohort_ga4.py            # expect: property 551876340
python3 metrics/onboarding_funnel_ga4.py --days 7

# honest verdict while the new window matures:
#   insufficient/not_mature   <- correct until a cohort completes D14
#   NOT a number, and NOT `fail`
```

If the instrument ever returns a *number* for a window whose start predates
2026-08-27, that is a bug — it is mixing the dark period into the denominator,
which is the precise failure this ADR exists to prevent.

## Operator ratification

RATIFIED 2026-09-03. The ruling in "Decision" now governs: criterion (B) is
scored INSUFFICIENT-structural, the acquisition window is 2026-08-27 →
2026-10-22, and the single 4-week extension to 2026-11-05 is invoked. Amend by
appending — never by rewriting.

---

## Amendment 1 (2026-09-03) — the residual risk named above is the WRONG one

Ratified with this correction attached, because the risk section it carries is
now known to be aimed at the smaller problem.

That section concluded: "almost nobody opts in, because the toggles default off
and live in Settings … the extension is only worth invoking if real
activation/retention work ships inside it." The reasoning stands. The target
does not.

Re-measuring the funnel today with `totalUsers` (it had been reporting
`eventCount`, which divided an event count by a user count) and adding the two
stages that were missing entirely gives, GA4 551876340, 30d:

```
first_open                 34
session_start              35     <- installs DO open the app
compliance_check_started    9     <- 26%
compliance_result           8
first_chat_message_sent     3
```

`compliance_check_started` fires inside `checkCompliance()`, which on the
welcome screen runs only AFTER the user taps "I am 18 or older"
(`welcome_screen.dart:_confirmAdult`). The welcome screen itself had no
instrumentation at all. So the funnel silently began at the survivors of an
unmeasured gate, and roughly **three quarters of installs never clear the first
screen**.

**Why this matters to THIS gate.** D14 is measured over installs. If ~74% never
get past the welcome screen, the retention denominator is dominated by people
who never reached the product — and no notification or activation work inside
the extension window can move them, because they never arrive. The extension
was justified on the belief that re-engagement was the lever. On today's
numbers the first-screen gate is a larger one, and it is upstream of everything
this ADR reasoned about.

**What does NOT change:** the ruling itself. An instrument that never ran is
still not a measurement that came back negative, and that argument is
independent of where the cliff sits. The window restart stands.

**What DOES change:** what has to ship inside the window for the extension to
be worth anything. Not primarily notification opt-in — the welcome-screen gate.

**What is NOT yet known, and must not be guessed:** why they leave. Nothing in
this amendment names a cause. `welcome_screen_viewed` and
`welcome_age_confirmed` (commit 515a6a9d) make the gap measurable and read 0
until that build reaches users. This ADR has already carried two confident,
wrong claims about notifications, both mine, both caught only because a lane was
sent to attack them. A third confident guess about a cliff discovered hours ago
would be the same mistake in a new place.
