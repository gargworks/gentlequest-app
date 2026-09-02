# ADR-008 — Stage-1 criterion (B): INSUFFICIENT-structural, window restarts 2026-08-27

**Status:** PROPOSED — requires operator ratification before it governs.
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
- **Still broken, and this is the live blocker:** `POST_NOTIFICATIONS` is
  declared and *is* requested at runtime — but **only from Settings**
  (`settings_screen.dart:211,260,297`), the notification detail screen
  (`notification_detail_screen.dart:49`), and the mood tracker
  (`mood_tracker.dart:810`). **None of these is on the first-run path.** With
  `targetSdkVersion 35`, a fresh-install user who never opens Settings is never
  asked for the permission, so every scheduled notification is silently
  suppressed by the OS. Working receivers behind an ungranted permission
  deliver exactly as many notifications as no receivers at all.

If the first-run permission prompt is not added, the extension is likely to
produce a genuine, measured FAIL rather than a pass.

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

This ADR is PROPOSED. It has kill-clause implications and changes a ratified
gate date, so it does not take effect until the operator ratifies it. Amend by
appending — never by rewriting.
