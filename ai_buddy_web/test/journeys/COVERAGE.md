# GentleQuest Widget Coverage

## How to run

```bash
cd ai_buddy_web
flutter test test/journeys/
# Expected: all 100 tests pass, zero failures
```

## Screen coverage status

| Test file | Screen(s) covered | Key widgets tested | Source fixes applied |
|-----------|-------------------|-------------------|----------------------|
| j01 | WelcomeScreen | Continue, age modal, "Yes I am", "Not yet" | — |
| j02 | Under-18 path | Age gate → block flow | — |
| j03 | ComplianceGuardScreen | Age gate yes/no, "I am 18 or older", "I am under 18" | — |
| j04 | InteractiveChatScreen | TextField, send button, profile avatar icon, voice semantics | — |
| j05 | MoodTrackerScreen (tab) | Mood trigger card, check-in card, weekly review row | — |
| j06 | QuestScreen (tab) | Quest cards, "3 Good Things", "Complete today" | — |
| j07 | ProfileScreen | ABOUT YOU, HOW ALEX TALKS TO YOU, tone buttons, Use now, Edit plan, SafetyPlanBuilder (Save & continue / Save & exit / Skip), Settings → link, Settings → opens SettingsScreen, Call button | Settings link wired; Maybe later/Skip wired; Call → snackbar; Save & continue/exit use onClose |
| j08 | InteractiveChatScreen header + SettingsScreen | YOUR DATA (Export / Delete / Anonymity), NOTIFICATIONS (Daily check-in / Streak nudge), Privacy policy, Crisis resources, notification detail ON DAYS chips, Send test notification | — |
| j09 | ClinicalAssessmentScreen | PHQ-9 / GAD-7 entry cards, Likert pills, Next button, Save & exit | Breathing exercise → pushNamed; Save-for-therapist → snackbar |
| j10 | MoodTrackerScreen | "How are you right now?", trigger card, bottom sheet | — |
| j11 | WeeklyReviewScreen | WeekState.full/light/heavy renders, "Just rest" button, "Skip this" link | "Just rest" → pop; "Skip this" → pop; maxH reduced to 60 to fix chart overflow |
| j12 | ResourceLibraryScreen | Renders without crash, Breathing/Grounding/Sleep filter chips + taps | Spacer() → SizedBox(height:12) in _ExerciseGridItem |
| j13 | WellnessDashboardScreen | Renders without crash, no exception, check-in card tap | MultiProvider (MoodProvider + QuestProvider + ProgressProvider) required in test |
| j14 | QuestScreen + QuestPreviewScreen | Quest list, "3 Good Things", Start button ValueKey, Start/Continue label, quest cards | quest_preview_start_button ValueKey confirmed |

## Broken callbacks fixed (source)

| Screen | Callback | Fix applied |
|--------|----------|-------------|
| profile_screen.dart | Settings → link | Navigator.push to SettingsScreen |
| profile_screen.dart | Use now | showCrisisInterventionSheet (transitionAnimationController leak fixed in crisis_resources.dart) |
| profile_screen.dart | Maybe later | Navigator.of(context).maybePop() |
| profile_screen.dart | Call buttons (3×) | ScaffoldMessenger snackbar (SafetyContact has no phone field) |
| profile_screen.dart | Save & continue | widget.onClose ?? maybePop |
| profile_screen.dart | Save & exit | widget.onClose ?? maybePop |
| profile_screen.dart | Skip — use 988 only | Navigator.of(context).maybePop() |
| clinical_assessment_screen.dart | Try breathing exercise | Navigator.pushNamed('/interactive-chat') |
| clinical_assessment_screen.dart | Save for therapist | ScaffoldMessenger snackbar (share_plus not in pubspec) |
| weekly_review_screen.dart | Just rest | Navigator.of(context).pop() |
| weekly_review_screen.dart | Skip this — I'll figure it out | Navigator.of(context).pop() |

## Known deferred (backend-gated or out of scope)

- `settings_screen.dart` — anonymity backend suppression (UI tap works; backend not wired)
- `settings_screen.dart` — account delete API call (sheet opens; actual deletion not wired)
- `weekly_review_screen.dart` — share-with-therapist mailto (no email client in test env)
- `profile_screen.dart` — Call buttons use snackbar placeholder (SafetyContact.phone field not present in model)
- `clinical_assessment_screen.dart` — Save for therapist uses snackbar placeholder (share_plus not in pubspec)
- Crisis resources — AnimationController for custom transition removed; uses Flutter default animation

## Test infrastructure

All tests use `setUp(setUpBypassedPrefs)` from `test_helpers.dart` to bypass SharedPreferences onboarding checks.

Screens with infinite animations (BreathingOrb in ResourceLibraryScreen) use `pump(Duration)` rather than `pumpAndSettle()`.

WellnessDashboardScreen requires `MultiProvider` with `MoodProvider`, `QuestProvider`, `ProgressProvider`.
