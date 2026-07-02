import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/adhd_path_screen.dart';
import 'package:ai_buddy_web/services/low_stim_service.dart';

// v1.5.0 ADHD Update — ADHD-path onboarding (Workstream 2c) widget tests.
//
// Covers the three lifecycle shapes required by the scope brief: entering
// the step, completing it, and skipping it at any point. Also asserts the
// hard "no diagnostic claims" constraint holds in the rendered copy —
// no ASRS/screening/clinical/test language should ever appear on-screen.

Widget _buildTestApp(VoidCallback onFinished) {
  return MaterialApp(
    home: AdhdPathScreen(onFinished: onFinished),
  );
}

void main() {
  group('AdhdPathScreen', () {
    testWidgets('enter: shows the intro with self-discovery framing, '
        'never diagnostic language', (tester) async {
      SharedPreferences.setMockInitialValues({});
      var finished = false;

      await tester.pumpWidget(_buildTestApp(() => finished = true));
      await tester.pumpAndSettle();

      expect(find.text('One more thing,\nif you’re up for it'), findsOneWidget);
      expect(
        find.text(
          'Not a test. Not a diagnosis — just two questions, '
          'answered your way.',
        ),
        findsOneWidget,
      );
      expect(find.text("Let's do it"), findsOneWidget);
      expect(find.text('Skip for now'), findsOneWidget);

      // Never any screening/clinical vocabulary anywhere in the intro tree.
      for (final banned in ['ASRS', 'screening', 'clinical']) {
        expect(
          find.textContaining(banned, findRichText: true),
          findsNothing,
          reason: '"$banned" must never appear in ADHD-path onboarding copy',
        );
      }
      // "diagnos" is only allowed inside the required negation disclaimer
      // ("Not a ... diagnosis") — never as an affirmative claim. Exactly one
      // hit means it appears only in that one disclaimer sentence.
      expect(find.textContaining('diagnos', findRichText: true), findsOneWidget);

      expect(finished, isFalse);
    });

    testWidgets(
        'complete: answering both questions reaches suggestions (no score '
        '/ label) and finishes on Continue', (tester) async {
      SharedPreferences.setMockInitialValues({});
      var finished = false;

      await tester.pumpWidget(_buildTestApp(() => finished = true));
      await tester.pumpAndSettle();

      await tester.tap(find.text("Let's do it"));
      await tester.pumpAndSettle();

      // Q1 — tap the first option.
      expect(find.text("When it's time to start something you've been "
          'putting off, what usually happens?'), findsOneWidget);
      await tester.tap(find.text('I just start — it\'s not a big deal'));
      await tester.pumpAndSettle();

      // Q2 — tap an option; this should complete the flow.
      expect(find.text('Once you\'re actually in the middle of a task, '
          'what tends to happen?'), findsOneWidget);
      await tester.tap(find.text('I stay locked in until it\'s done'));
      await tester.pumpAndSettle();

      // Suggestions screen — feature suggestions, never a score/label.
      expect(find.text('Thanks for sharing.'), findsOneWidget);
      expect(find.text('Body doubling'), findsOneWidget);
      expect(find.text('A calmer, low-stim look'), findsOneWidget);
      expect(find.text('Gentle quests'), findsOneWidget);
      expect(
        find.text(
          'Not a diagnosis, not a label — just a few gentle defaults '
          'based on what you shared.',
        ),
        findsOneWidget,
      );
      expect(find.textContaining(RegExp(r'\bscore\b', caseSensitive: false)),
          findsNothing);

      expect(finished, isFalse);
      await tester.tap(find.text('Continue to GentleQuest'));
      await tester.pumpAndSettle();

      expect(finished, isTrue);
      final seen = await AdhdPathScreen.hasBeenSeen();
      expect(seen, isTrue);

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool(kAdhdPrefBodyDoublingKey), isTrue);
      expect(prefs.getBool(kAdhdPrefLowStimKey), isTrue);
      expect(prefs.getBool(kAdhdPrefGentleQuestsKey), isTrue);
    });

    testWidgets(
        'skip: tapping "Skip for now" on the intro finishes immediately '
        'without setting any preference defaults', (tester) async {
      SharedPreferences.setMockInitialValues({});
      var finished = false;

      await tester.pumpWidget(_buildTestApp(() => finished = true));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Skip for now'));
      await tester.pumpAndSettle();

      expect(finished, isTrue);
      final seen = await AdhdPathScreen.hasBeenSeen();
      expect(seen, isTrue);

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool(kAdhdPrefBodyDoublingKey), isNull);
      expect(prefs.getBool(kAdhdPrefLowStimKey), isNull);
      expect(prefs.getBool(kAdhdPrefGentleQuestsKey), isNull);
    });

    testWidgets('skip: is also reachable mid-flow, from Q1',
        (tester) async {
      SharedPreferences.setMockInitialValues({});
      var finished = false;

      await tester.pumpWidget(_buildTestApp(() => finished = true));
      await tester.pumpAndSettle();

      await tester.tap(find.text("Let's do it"));
      await tester.pumpAndSettle();

      expect(find.text('Skip for now'), findsOneWidget);
      await tester.tap(find.text('Skip for now'));
      await tester.pumpAndSettle();

      expect(finished, isTrue);
      final seen = await AdhdPathScreen.hasBeenSeen();
      expect(seen, isTrue);
    });

    testWidgets('hasBeenSeen returns false before the step has ever run',
        (tester) async {
      SharedPreferences.setMockInitialValues({});
      final seen = await AdhdPathScreen.hasBeenSeen();
      expect(seen, isFalse);
    });

    // ── Low-stim suggestion card — v1.5.0 quiet-mode stitch ────────────────
    //
    // PR #169 shipped this card as informational/"coming soon" because
    // PR #168 (LowStimService + Settings toggle) merged in parallel. This
    // group covers stitching the card to the *real* LowStimService: same
    // call path as the Settings toggle (settings_screen.dart
    // _onLowStimChanged), gentle confirmation feedback, and the shared
    // `low_stim_toggled` analytics event with a distinguishing source.
    group('low-stim suggestion card', () {
      const cardKey = Key('adhd_low_stim_suggestion_card');

      setUp(() {
        // LowStimService.lowStimNotifier is shared static state — reset
        // before every test so nothing leaks across the suite (same
        // pattern as low_stim_service_test.dart / j08_profile_settings_test.dart).
        LowStimService.lowStimNotifier.value = false;
      });

      Future<void> reachSuggestions(WidgetTester tester) async {
        SharedPreferences.setMockInitialValues({});
        await tester.pumpWidget(_buildTestApp(() {}));
        await tester.pumpAndSettle();
        await tester.tap(find.text("Let's do it"));
        await tester.pumpAndSettle();
        await tester.tap(find.text('I just start — it\'s not a big deal'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('I stay locked in until it\'s done'));
        await tester.pumpAndSettle();
      }

      // A single large `pump(duration)` fires the SnackBar's auto-dismiss
      // Timer but only ticks its reverse (fade-out) animation one frame, so
      // it can be left "stuck" mid-animation and still counted as showing —
      // pump in small steps so the controller actually finishes and the
      // entry is cleared from the ScaffoldMessenger queue.
      Future<void> pumpUntilSnackbarGone(WidgetTester tester) async {
        for (var i = 0;
            i < 40 && find.byType(SnackBar).evaluate().isNotEmpty;
            i++) {
          await tester.pump(const Duration(milliseconds: 100));
        }
      }

      testWidgets('renders off by default, offering to turn quiet mode on',
          (tester) async {
        await reachSuggestions(tester);

        expect(LowStimService.enabled, isFalse);
        expect(find.byKey(cardKey), findsOneWidget);
        expect(
          find.textContaining('Tap to turn it on now', findRichText: true),
          findsOneWidget,
        );
        expect(find.byIcon(Icons.circle_outlined), findsOneWidget);
      });

      testWidgets(
          'tapping the card flips the real LowStimService — same call path '
          'as the Settings toggle — and gives gentle confirmation feedback',
          (tester) async {
        await reachSuggestions(tester);

        await tester.tap(find.byKey(cardKey));
        // Explicit pumps (not pumpAndSettle) so the transient confirmation
        // snackbar is still on screen to assert against — pumpAndSettle
        // would advance past its auto-dismiss duration.
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        expect(tester.takeException(), isNull);
        expect(LowStimService.enabled, isTrue);

        final prefs = await SharedPreferences.getInstance();
        expect(prefs.getBool(LowStimService.kLowStimModeKey), isTrue);

        // Gentle confirmation feedback (matches the Settings toggle's
        // snackbar style).
        expect(find.text('Quiet mode is on.'), findsOneWidget);

        // Card copy + icon flip to reflect the now-live "on" state.
        expect(
          find.textContaining('Quiet mode is on —', findRichText: true),
          findsOneWidget,
        );
        expect(find.byIcon(Icons.check_circle_rounded), findsWidgets);
      });

      testWidgets('tapping a second time flips it back off',
          (tester) async {
        await reachSuggestions(tester);

        await tester.tap(find.byKey(cardKey));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));
        expect(LowStimService.enabled, isTrue);
        await pumpUntilSnackbarGone(tester); // let the first snackbar clear

        await tester.tap(find.byKey(cardKey));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        expect(LowStimService.enabled, isFalse);
        final prefs = await SharedPreferences.getInstance();
        expect(prefs.getBool(LowStimService.kLowStimModeKey), isFalse);
        expect(find.text('Quiet mode is off.'), findsOneWidget);
      });

      testWidgets(
          'does not disturb the unrelated adhd_pref_low_stim_v1 soft-default '
          'pref already written when the questions were completed',
          (tester) async {
        await reachSuggestions(tester);

        final prefsBefore = await SharedPreferences.getInstance();
        expect(prefsBefore.getBool(kAdhdPrefLowStimKey), isTrue);

        await tester.tap(find.byKey(cardKey));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        final prefsAfter = await SharedPreferences.getInstance();
        expect(prefsAfter.getBool(kAdhdPrefLowStimKey), isTrue);
      });
    });
  });
}
