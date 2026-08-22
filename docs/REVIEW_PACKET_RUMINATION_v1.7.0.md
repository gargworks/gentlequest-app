# Clinical / Legal Review Packet — GentleQuest v1.7.0

## Feature under review
**Loop Reset** (rumination_reset_screen.dart)
- A finite, on-device exercise accessible from Resource Library → Quick wins.
- 4 steps: Notice → Concrete facts → Choose one exit → Exit.
- Optional 0–10 intensity rating (local only, never uploaded).
- Exits: a 5-minute values action, a trigger-bound defer, or a no-action return.

## Safety and privacy invariants
- All free-text fields run through the existing `CrisisKeywordDetector` before advancing.
- Tier-1 or Tier-2 keyword match routes to the existing `CrisisInterventionSheet` and marks the session skipped.
- No free text, rating history, or chosen-action text leaves the device.
- Only structured outcome is sent: `exerciseType: "rumination_reset"`, `outcome: started|completed|skipped`, `timeSpentSeconds`.
- Every screen has a shame-free Skip/Close control.
- No streaks, badges, scores, history feed, generated interpretation, or open-ended journal CTA.

## Clinical positioning (to be confirmed by reviewer)
- Positioned as a **wellness adjunct** and between-session self-help tool, not a treatment or diagnosis.
- No claims of cure, prevention, relapse reduction, or clinical efficacy.
- Efficacy evidence is not collected or displayed in the app.
- User is expected to discuss the protocol with a licensed clinician.

## Files to review
- `lib/screens/rumination_reset_screen.dart` — all user-facing copy and flow.
- `lib/screens/resource_library_screen.dart` — Library entry copy.
- `test/screens/rumination_reset_screen_test.dart` — safety and privacy test assertions.

## Questions for clinical reviewer
1. Is the crisis-keyword handoff language appropriate and non-stigmatizing?
2. Do any screen instructions implicitly encourage rumination as journaling or analysis?
3. Is the "no free text leaves the device" framing clear enough to the user?
4. Are the three exits clinically sensible for a brief on-device exercise?
5. Should any additional help-seeking prompt appear before or during the exercise?

## Questions for legal / compliance reviewer
1. Do any strings constitute an unapproved medical device or treatment claim?
2. Is the privacy disclosure sufficient for a feature that processes user text only locally?
3. Are there any COPPA / GDPR / health-data considerations introduced by the optional intensity rating?

## Release gating
- Code review complete by `main` (Claude Code).
- This human packet must be reviewed and cleared before the build is promoted from internal track to production.
- iOS / Android builds will be uploaded to internal / TestFlight only until this review is cleared.
