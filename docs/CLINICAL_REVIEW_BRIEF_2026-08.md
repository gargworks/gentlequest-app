# Clinical Review Brief — GentleQuest, 2026-08

**Purpose:** one packet consolidating three outstanding clinical/legal decisions.
Originally scoped to wait for a licensed clinical/legal reviewer. On
2026-08-28/29 the operator explicitly instructed engineering to make these
calls directly ("make clinical and legal calls as well ... I am not going to
get human") rather than continue waiting. What follows is the record of what
was and was not decided under that instruction — see the **Operator-directed
decisions** section below, added 2026-08-29, for exactly what changed, on
what evidence, and what is explicitly still open. Nothing in that section is
a licensed clinical or legal opinion; it is engineering judgment informed by
published, cited sources, executed on direct operator instruction. The
original three items are preserved below unchanged as the historical record
of what this packet originally asked a reviewer to decide.

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

---

## Operator-directed decisions — 2026-08-29

Executed on explicit operator instruction to decide directly rather than
wait for a licensed reviewer. Sourced where a source was found; flagged as
ungrounded where none was. Not a substitute for licensed clinical or legal
review — the operator has been told this and chose to proceed anyway,
consistent with the same authority already exercised for the 1.7.1 bypass
recorded in `REVIEW_PACKET_RUMINATION_v1.7.0.md`.

### Item 1 — Loop Reset: informationally cleared

Checked against the FDA's public general-wellness boundary (FDA guidance on
general wellness / low-risk devices, and third-party summaries of the
2026-01 update): the disqualifying line is a product that claims to
"diagnose, treat, cure, or prevent a disease." Loop Reset's existing copy
already avoids this — "not a treatment or diagnosis," "user expected to
discuss the protocol with a licensed clinician," no efficacy claims
displayed in-app. This is an **informational read of public criteria, not
formal legal counsel** — the operator should still get real legal review
before any claims expand beyond the current copy. No code change; closing
this item's engineering side as reviewed-against-public-criteria.

### Item 2 — Crisis follow-up notification: real bug found and fixed; copy/styling left open

**Correction to the original issue #6 finding:** the TODO it cited
(`lib/widgets/q9_crisis_bridge_sheet.dart`) is in a class that turned out to
be **dead code** — nothing in the app instantiates it. A second, live class
with the same name in a different file
(`lib/screens/clinical_assessment/q9_crisis_bridge.dart`, imported by
`assessment_flow_screen.dart`) is what users actually see. Its "heavy
moment" outcome was queuing a local timestamp
(`follow_up_24h_pending`) that nothing ever read — a second, independent
dead end, not the one issue #6 named. Both were real: the notification
mechanism existed and was never called; the call site that should have
called it was queuing intent to a list nobody consumed.

**Fixed (2026-08-29):** `assessment_flow_screen.dart`'s `heavy` case now
calls `NotificationService.scheduleCrisisFollowup()` for real, alongside
the existing (harmless, kept) local timestamp stamp. The 5-min-vs-24h
conflict is resolved to **24 hours** — not a new number invented for this
decision, but the number the live code's own `follow_up_24h_pending`
naming had already independently committed to elsewhere in the same file.
The evidence surveyed (SAMHSA/Zero Suicide "Caring Contacts" model,
Motto & Bostrom) supports *some* follow-up existing after a risk
disclosure, but its cadence in the published evidence base is much longer
and gentler than either 5 minutes or a single day (an initial published
schedule: 3 contacts in week 1, tapering over 12 months) — 24h is a
reasonable single first touch, not a claim that it matches the full
evidence-based cadence.

**Left deliberately untouched — copy and delivery styling.** The current
copy ("Are you safe right now?") and delivery (`Importance.max`,
`AndroidNotificationCategory.alarm`, `ongoing: true`/`autoCancel: false` —
persists until tapped) predate this session and are governed by an
explicit in-file rule: `notification_service_impl.dart` states *"DO NOT
PARAPHRASE. Any copy change must be traced back to the [HTML] source"* —
a real design-governance artifact (`GentleQuest_Push_Notifications.html`)
that was not available in this checkout to trace against. Two things are
flagged as evidence the current copy may be wrong, without being resolved
here:
1. The live crisis-bridge sheet's own file states a design principle,
   "P10 reflection-over-interrogation" (found in the sibling/dead file's
   header, describing the same UX). "Are you safe right now?" is a direct
   question demanding an answer — an interrogation. The app's own
   `worriedCheckin` category (a comparable low-mood follow-up, already
   shipped) uses a **non-demand** tone instead: *"Just checking in" /
   "Yesterday felt heavy. Here when you're ready — no need to explain."*
2. The evidence-based Caring Contacts model is explicitly built around
   **non-demand** messages — brief, supportive, and not requiring a
   response. A persistent, alarm-category, un-dismissible notification
   asking a direct safety question is a materially different design than
   what the cited evidence supports.
No escalation exists today if the notification goes unanswered (there
never was any — this was not removed, it was simply never built), and none
was added. The app does not act on anyone's behalf without their own
input anywhere else in this codebase; extending that pattern here rather
than inventing an escalation path is the conservative default, not a
gap.

**Genuinely unresolved, flagged rather than guessed at:** every published
follow-up protocol found (988 Lifeline crisis-center follow-up, Caring
Contacts) assumes a **human** sender on the other end. No published
guidance was found for what a fully automated, unattended app should do —
this app has no human reading responses to `scheduleCrisisFollowup()`. The
honest answer is that gap wasn't closed by research; it was closed by
scope (don't build automated escalation) rather than by finding an answer
that doesn't exist in the literature surveyed.

**Still open, needs a real decision (design or clinical, not just legal):**
whether to change `_crisisFollowupTitle`/`_crisisFollowupBody` and the
Android/iOS delivery styling to match the non-demand pattern above. This
is the single highest-stakes remaining item in this entire brief and the
one place this session deliberately declined to act unilaterally against
an explicit in-repo "trace to source" governance rule.

### Item 3 — Crisis deep link: routed to real crisis resources

**Decided and shipped (2026-08-29):** both crisis deep-link paths
(`gentlequest://crisis` and the `type: 'crisis'` share-content path) now
route to `ResourceLibraryScreen` (newly registered as the named route
`/crisis` in `main.dart`) instead of Home. Reasoning: asymmetric risk —
the cost of showing crisis resources to someone whose old link is stale is
near zero; the cost of landing someone mid-crisis on a generic home screen
is not. No compliance/age-gate check added in front of it: crisis
resources should not be the one surface gated behind onboarding. This
resolves issue #7's core question (which surface) with the least-invasive
option already built into the app, not a new screen. The two secondary
questions in the original item 3 (behavior for an incomplete-compliance
user; whether staleness should matter) were answered implicitly by "always
show it, never gate it" rather than decided as separate branches — flagged
here in case that blanket answer is wrong for a case not considered.

### What is NOT resolved by this section
The Item 2 copy/styling question above. The App Review justification
comment in `notification_service_impl.dart` promises "opt-in only" for the
crisis-follow-up category specifically, distinct from ordinary OS
notification permission — no dedicated in-app consent flow for this
category exists (it relies on the same general OS notification permission
every other category uses); this session did not build one, and whether
that's sufficient is unaddressed. Item 1's claims-boundary read is
informational, not legal sign-off. None of this replaces getting a
licensed reviewer when the operator is in a position to.
