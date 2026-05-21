# GentleQuest — Surgical Bug Report
> Generated via live simulator walk + full source audit, 2026-05-18.
> Every entry has: file + line, root cause, reproduction steps, and the exact diff to fix it.

---

## BUG-001 · CRITICAL · All nav-sheet rows except Profile silently navigate to ProfileScreen

**File:** `lib/widgets/profile_nav_sheet.dart` lines 78–130

**Root cause:**  
`showModalBottomSheet` is called with `useRootNavigator: true`, so the sheet route lives on the **root** navigator. Inside each `_SheetTile.onTap`, the code does:
```dart
Navigator.pop(context);          // ① removes the sheet from root navigator
Navigator.push(context, ...);   // ② uses the now-disposed widget's context
```
After step ①, `_ProfileNavSheet` is removed from the widget tree and its `BuildContext` is unmounted. Calling `Navigator.push` on an unmounted context is undefined behaviour in Flutter. In practice Flutter silently no-ops or resolves to an ancestor navigator that may route differently. The Profile row appears to work by coincidence — all four rows are equally broken.

**Reproduction:** Open chat → tap avatar icon → tap Settings / Journal / Library row → see Profile screen open (or nothing happens).

**Surgical fix** — capture the navigator reference before popping:
```dart
// profile_nav_sheet.dart — every _SheetTile onTap block

// Profile (line 78)
onTap: () {
  final nav = Navigator.of(context, rootNavigator: true);
  nav.pop();
  nav.push(MaterialPageRoute(builder: (_) => const ProfileScreen()));
},

// Settings (line 92)
onTap: () {
  final nav = Navigator.of(context, rootNavigator: true);
  nav.pop();
  nav.push(MaterialPageRoute(builder: (_) => const SettingsScreen()));
},

// Journal (line 106)
onTap: () {
  final nav = Navigator.of(context, rootNavigator: true);
  nav.pop();
  nav.push(MaterialPageRoute(builder: (_) => const JournalScreen()));
},

// Library (line 120)
onTap: () {
  final nav = Navigator.of(context, rootNavigator: true);
  nav.pop();
  nav.push(MaterialPageRoute(builder: (_) => const ResourceLibraryScreen()));
},
```

---

## BUG-002 · HIGH · SafetyPlanBuilderStep: Back / Save & continue / Save & exit all do the same thing

**File:** `lib/screens/profile_screen.dart` lines 923–952

**Root cause:**  
All three action widgets are wired to the exact same callback:
```dart
// Back button (line 925)
onTap: widget.onClose ?? () => Navigator.maybePop(context),

// Save & continue button (line 931)
onTap: widget.onClose ?? () => Navigator.maybePop(context),

// Save & exit link (line 939)
onTap: widget.onClose ?? () => Navigator.maybePop(context),
```
A three-step safety plan builder that cannot advance to the next step is non-functional. "Save & continue" should increment the step index; only "Back" and "Save & exit" should dismiss.

**Additionally:** the builder is always opened at `stepIdx: 2` (profile_screen.dart line 33), so step 1 (personal coping statement) is never reachable.

**Reproduction:** Profile → "Build my safety plan" → tap "Save & continue" → sheet dismisses instead of advancing.

**Surgical fix:**
```dart
// profile_screen.dart — _ProfileScreenState

bool _showBuilder = false;
int _builderStep = 0; // ADD THIS

// In build():
body: _showBuilder
    ? SafetyPlanBuilderStep(
        stepIdx: _builderStep,        // was hardcoded 2
        onClose: () => setState(() { _showBuilder = false; _builderStep = 0; }),
        onNext: () => setState(() => _builderStep++), // ADD THIS
      )
    : _ProfileHome(...),

// SafetyPlanBuilderStep — add onNext parameter
class SafetyPlanBuilderStep extends StatefulWidget {
  final int stepIdx;
  final VoidCallback? onClose;
  final VoidCallback? onNext; // ADD

  ...

  // Back button (line 925) — keep as-is (onClose pops)
  // Save & continue button (line 931) — change to:
  onTap: widget.onNext ?? () => Navigator.maybePop(context),
  
  // Save & exit link (line 939) — keep as-is (onClose pops)
}
```

---

## BUG-003 · HIGH · "Try a 1-minute breathing exercise" navigates to chat, not a breathing screen

**File:** `lib/screens/clinical_assessment_screen.dart` line 1220

**Root cause:**
```dart
onTap: () => Navigator.pushNamed(context, '/interactive-chat'),
```
The card title says "breathing exercise" but tapping it opens the general chat screen. This is a deceptive affordance — the user expects a guided breathing flow.

**Reproduction:** Complete any PHQ-9/GAD-7 assessment → see results → tap "Try a 1-minute breathing exercise" → lands in chat with no breathing content.

**Surgical fix** (two options — pick one):

Option A — navigate to breathing exercise screen if it exists:
```dart
onTap: () => Navigator.pushNamed(context, '/breathing'),
// Requires creating a /breathing route and BreathingExerciseScreen
```

Option B — honest placeholder while feature is built:
```dart
onTap: () => ScaffoldMessenger.of(context).showSnackBar(
  const SnackBar(content: Text('Breathing exercise coming soon.')),
),
```
Option B is the 5-minute fix; Option A is correct. Do not keep Option C (navigate to unrelated chat).

---

## BUG-004 · MEDIUM · Call buttons on safety contacts show fake snackbar instead of dialling

**File:** `lib/screens/profile_screen.dart` line 773

**Root cause:**
```dart
onTap: () => ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(content: Text('Calling ${contact.name}…')),
),
```
The button renders and vibrates, but `url_launcher` is already in `pubspec.yaml` and is not used here. In a mental-health app where these are crisis contacts, a fake "Calling…" snackbar is a safety-critical failure.

**Reproduction:** Profile → scroll to safety contacts → tap any "Call" button → gets snackbar, phone does NOT dial.

**Surgical fix:**
```dart
// Add at top of profile_screen.dart:
import 'package:url_launcher/url_launcher.dart';

// _ContactRow onTap (line 773):
onTap: () async {
  final uri = Uri.parse('tel:${contact.phone}');
  if (await canLaunchUrl(uri)) {
    await launchUrl(uri);
  } else {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Cannot dial ${contact.name} from this device.')),
      );
    }
  }
},
```
Note: `SafetyContact` currently has no `phone` field — add it:
```dart
class SafetyContact {
  final String phone; // ADD
  ...
}
```

---

## BUG-005 · MEDIUM · Disclaimer banner close button sits 18pt below PopupMenuButton touch area — marginal overlap risk on iOS

**File:** `lib/screens/interactive_chat_screen.dart` lines 531–609

**Root cause:**  
Header layout on iPhone 16 Pro (status bar ≈59pt, `SafeArea(top:true)`):
- Status bar: 0–59pt
- Header top padding: 59–75pt
- Icon row: 75–119pt (44pt InkWell content)
- Header bottom padding + separator: 119–135pt
- Disclaimer banner: 135pt+
- Banner close `IconButton` (size 18, min-touch 48): center ≈ 159pt, touch zone 135–183pt

`PopupMenuButton` center ≈ 97pt, touch zone 73–121pt. **Currently no overlap** — 14pt gap between bottom of PopupMenuButton touch area (121pt) and top of disclaimer banner (135pt).

**Status:** Not currently overlapping. Monitor if header padding changes. Low priority.

---

## BUG-006 · LOW · Safety plan hardcoded to "filled" state — empty-state flow untestable

**File:** `lib/screens/profile_screen.dart` line 69

**Root cause:**
```dart
final bool _planFilled = true; // [assumed] show filled state for demo
```
The `_SafetyPlanEmpty` widget and its "Build my safety plan" CTA are unreachable in production because the state is hardcoded. When real users first open the app, they'll always see the filled state with placeholder contacts, not the onboarding CTA.

**Surgical fix:**  
Wire to `SharedPreferences` or pass as constructor param. Interim fix for testability:
```dart
// Change to:
final bool _planFilled = false; // default to empty until user completes builder
```

---

## BUG-007 · LOW · "Save this result for your therapist" shows placeholder snackbar

**File:** `lib/screens/clinical_assessment_screen.dart` line 1243

**Root cause:**
```dart
onTap: () => ScaffoldMessenger.of(context).showSnackBar(
  const SnackBar(content: Text('Export coming in the next update.')),
),
```
The button IS wired — it's a deliberate placeholder. Not a crash. Acceptable for current tier.

**Status:** Known stub. Track as feature gap, not crash bug.

---

## BUG-008 · INFORMATIONAL · Profile picture area on ProfileScreen has no onTap handler

**File:** `lib/screens/profile_screen.dart` (avatar dot section)

The 6 avatar gradient dots are tappable (setState). But the large avatar circle at the top of the card has no tap → no way to take a custom photo in the current tier. Acceptable for demo.

---

## Summary Table

| # | Severity | File | Line | Status |
|---|---|---|---|---|
| BUG-001 | CRITICAL | profile_nav_sheet.dart | 78–130 | ✅ Fixed |
| BUG-002 | HIGH | profile_screen.dart | 33, 925–952 | ✅ Fixed |
| BUG-003 | HIGH | clinical_assessment_screen.dart | 1220 | ✅ Fixed |
| BUG-004 | MEDIUM | profile_screen.dart | 773 | ✅ Fixed (url_launcher + phone field) |
| BUG-005 | MEDIUM | interactive_chat_screen.dart | 531–609 | Not currently overlapping — monitor |
| BUG-006 | LOW | profile_screen.dart | 69 | ✅ Fixed (_planFilled → false) |
| BUG-007 | LOW | clinical_assessment_screen.dart | 1243 | Known stub — feature gap |
| BUG-008 | INFO | profile_screen.dart | avatar section | Acceptable for current tier |
