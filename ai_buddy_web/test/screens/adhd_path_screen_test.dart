import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/adhd_path_screen.dart';

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
  });
}
