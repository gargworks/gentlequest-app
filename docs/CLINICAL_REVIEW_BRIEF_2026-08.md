# Clinical Review Brief — GentleQuest, 2026-08

**Purpose:** one packet consolidating three outstanding clinical/legal decisions
so a single reviewer session can clear all of them, rather than three separate
threads. Nothing here is new engineering — it assembles what already shipped
or already exists in code, and names the specific decisions a clinician (and,
where marked, legal/compliance) needs to make. Engineering on any of these
three items is deliberately parked until decisions land — see Arc C in the
active plan.

**Status of the underlying app:** v1.7.2 is live in Play production (Android)
and in App Store review (iOS, auto-release on approval). All three items below
describe behavior that is either already live in production or was live in a
prior shipped version, not hypothetical future behavior.

---

## Item 1 — Loop Reset (rumination exercise): review gate was bypassed, not cleared

**Full original packet:** `docs/REVIEW_PACKET_RUMINATION_v1.7.0.md` (including
its 2026-08-27 amendment). Reproduced in full below since it is short.

### What the feature is
A finite, on-device "Loop Reset" exercise reachable from Resource Library →
Quick wins. 4 steps (Notice → Concrete facts → Choose one exit → Exit), an
optional 0–10 intensity rating that never leaves the device, and three exits
(a 5-minute values action, a trigger-bound defer, or a no-action return).

### Safety/privacy invariants already built and tested
- Every free-text field runs through the existing `CrisisKeywordDetector`
  before the user can advance.
- A Tier-1 or Tier-2 keyword match routes to the existing
  `CrisisInterventionSheet` and marks the session skipped.
- No free text, rating history, or chosen-action text ever leaves the device.
  Only `exerciseType: "rumination_reset"`, `outcome: started|completed|skipped`,
  `timeSpentSeconds` are sent.
- Every screen has a shame-free Skip/Close control. No streaks, badges,
  scores, history feed, generated interpretation, or open-ended journal CTA.
- `test/screens/rumination_reset_screen_test.dart` asserts these invariants.

### What actually happened (the amendment, verbatim from the packet)
On 2026-08-27 the operator explicitly decided to promote both platforms to
production (v1.7.1) without this packet being cleared — a deliberate,
informed call, not an oversight. The release was driven by an unrelated fix
(two accessibility defects on the live PHQ-9 suicidal-ideation screen —
988 label clipping and the 988 pill being pushable below the fold at 2x
text scale — both of which had been live in users' hands since 1.7.0). The
Loop Reset review was bypassed to ship that fix quickly. It is now a
**post-release obligation**, not a pre-release gate, and still needs to
happen.

### Decisions needed from clinical reviewer
1. Is the crisis-keyword handoff language appropriate and non-stigmatizing?
2. Do any screen instructions implicitly encourage rumination as journaling
   or analysis (the opposite of the exercise's intent)?
3. Is "no free text leaves the device" communicated clearly enough to the user?
4. Are the three exits clinically sensible for a brief on-device exercise?
5. Should any additional help-seeking prompt appear before or during it?

### Decisions needed from legal/compliance reviewer
1. Do any strings constitute an unapproved medical device or treatment claim?
2. Is the privacy disclosure sufficient for a feature that processes user
   text only locally?
3. Any COPPA/GDPR/health-data considerations from the optional intensity rating?

### Files to review
`lib/screens/rumination_reset_screen.dart` (all user-facing copy/flow),
`lib/screens/resource_library_screen.dart` (Library entry copy),
`test/screens/rumination_reset_screen_test.dart` (safety/privacy assertions).

---

## Item 2 — Crisis follow-up notification: built, wired for delivery, never called

**Full source:** GitHub issue #6, `gargworks/gentlequest-app`.

### What exists (fully implemented, currently inert)
`lib/services/notification_service_impl.dart` has a complete, ready-to-fire
mechanism: `GQNotificationCategory.crisisFollowup`, copy ("Just one quick
question" / "Are you safe right now?"), a dedicated notification id, and
`scheduleCrisisFollowup()` — which cancels duplicates, zoned-schedules,
and on Android sets `Importance.max` + `ongoing: true` +
`AndroidNotificationCategory.alarm` (i.e. it is built to be hard to miss
and to persist until tapped).

### What is missing
**Nothing calls it.** Grepping the app for `crisisFollowup` finds it only
inside its own implementation file. The intended call site —
`lib/widgets/q9_crisis_bridge_sheet.dart:18` — still carries a `TODO`
comment: `schedules a 24h check-in (TODO)`. A user who flags suicidal
ideation on PHQ-9 item 9 today receives **no automated follow-up** at all,
in the version currently live in production.

### The discrepancy that needs a decision, not just a bugfix
`scheduleCrisisFollowup()` defaults to a **5-minute** delay in code; the
sheet's own doc comment describes a **24-hour** check-in. These are two
very different clinical interventions (an immediate same-session pulse
check vs. a next-day welfare check) and the choice is not an engineering
default — it needs a clinical decision.

### Decisions needed from clinical reviewer
1. Should this follow-up exist at all, and if so, at what delay — 5 minutes,
   24 hours, both (staged), or something else?
2. Consent/opt-out posture: given `ongoing: true` + `autoCancel: false` means
   the notification persists on-device until the user taps it, what user
   control (if any) should exist over receiving it?
3. What should happen if the user does not respond — anything, or nothing?
4. Should an unanswered check-in ever escalate (and to what — nothing, an
   in-app resource surface, a real human contact)? This is a hard "does the
   app ever act on someone's behalf" question and should not be assumed.

### Known related gap (operator task, not a reviewer decision)
iOS `criticalAlert` (bypassing Focus/DND) requires the
`com.apple.developer.usernotifications.critical-alerts` entitlement, which
is not currently granted — even once wired, iOS delivery urgency is
degraded relative to Android until that entitlement request is filed and
approved by Apple. Noted here so the reviewer's decision on delay/escalation
isn't made assuming delivery reliability that doesn't yet exist on iOS.

---

## Item 3 — Crisis deep link (`gentlequest://crisis`) has no real destination

**Full source:** GitHub issue #7, `gargworks/gentlequest-app`.

### What exists
`gentlequest://crisis` maps to `AppRoutes.crisisResources` in
`lib/services/deep_link_service.dart`, but that route is not registered in
`lib/main.dart`'s routes table, and the app defines no `onUnknownRoute` —
so following the link as originally wired would crash navigation.

### Current stopgap (already shipped)
As part of the 2026-08-27 consolidation, the `/crisis` case was normalized
to route to Home instead of crashing — the same graceful-degradation
pattern already used for `/quest` and `/wellness` deep links whose target
screens no longer exist. This prevents a crash but is explicitly a stopgap,
not a real destination.

### Why this needs a clinical decision, not just a route registration
Someone following a crisis deep link — plausibly from an old push
notification, or a resource shared outside the app — landing on the
generic Home tab instead of a crisis surface is very likely the wrong
outcome. But *which* surface is correct, and under what conditions, is a
clinical/product call:
1. Which destination: the Resource Library, the crisis-resources sheet
   directly, or a 988-forward screen?
2. Should behavior differ if the user hasn't completed compliance/age
   gating yet?
3. Does an old notification payload's crisis intent still hold if it's
   being opened days or weeks later — should the app treat a stale crisis
   link differently from a fresh one?

This is deliberately adjacent to Item 2 (same reviewer, same session makes
sense) since both concern what the app does when a user is signaling
crisis-level need.

### Files involved
`lib/services/deep_link_service.dart` (`/crisis` case, currently
normalized to home), `lib/main.dart` (routes table — no `/crisis` entry,
no `onUnknownRoute`).

---

## Suggested review order
Items 2 and 3 are both "what does the app do when someone is in crisis"
decisions and are naturally reviewed together. Item 1 is a distinct
feature-clearance review and can be done independently, in either order.

## What happens after this review
Whichever items get a ruling: file the ruling as a short decision record
(a repo issue comment closing #6/#7, plus an entry in `DECISIONS.md` for
Item 1's Loop Reset clearance), then engineering picks it up on the next
train per the standing Arc C plan — opposed-pair tests (fires when it
should, never when it shouldn't, including Anonymity Mode ON and
notification-permission-off paths) before any of this ships.
