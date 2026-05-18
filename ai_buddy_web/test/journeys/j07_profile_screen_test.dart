import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/profile_screen.dart';
import 'package:ai_buddy_web/screens/settings_screen.dart';
import 'test_helpers.dart';

void main() {
  group('J07: ProfileScreen — comprehensive widget coverage', () {
    setUp(setUpBypassedPrefs);

    Widget buildProfile() {
      return const MaterialApp(home: ProfileScreen());
    }

    // ── Rendering ────────────────────────────────────────────────────────────

    testWidgets('ProfileScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byType(ProfileScreen), findsOneWidget);
    });

    // ── Section labels visible above fold ──────────────────────────────────

    testWidgets('ABOUT YOU section is present', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('ABOUT YOU'), findsOneWidget);
    });

    testWidgets('HOW ALEX TALKS TO YOU section is present', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('HOW ALEX TALKS TO YOU'), findsOneWidget);
    });

    // ── Tone selectors ────────────────────────────────────────────────────────

    testWidgets('tone "Warm" button is tappable', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Warm'));
      await tester.pump(const Duration(milliseconds: 200));

      expect(tester.takeException(), isNull);
    });

    testWidgets('tone "Direct" button is tappable', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Direct'));
      await tester.pump(const Duration(milliseconds: 200));

      expect(tester.takeException(), isNull);
    });

    testWidgets('tone "Quiet" button is tappable', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Quiet'));
      await tester.pump(const Duration(milliseconds: 200));

      expect(tester.takeException(), isNull);
    });

    // ── Safety plan filled state ──────────────────────────────────────────────

    testWidgets('"Use now" button is present', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Use now'));
      expect(find.text('Use now'), findsOneWidget);
    });

    testWidgets('"Use now" tap does not crash', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Use now'));
      await tester.tap(find.text('Use now'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Edit plan" button is present', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Edit plan'));
      expect(find.text('Edit plan'), findsOneWidget);
    });

    testWidgets('"Edit plan" opens SafetyPlanBuilderStep', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Edit plan'));
      await tester.tap(find.text('Edit plan'));
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pump();

      expect(tester.takeException(), isNull);
      expect(find.byType(SafetyPlanBuilderStep), findsOneWidget);
    });

    // ── SafetyPlanBuilderStep ─────────────────────────────────────────────────

    testWidgets('"Save & continue" tappable in builder', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Edit plan'));
      await tester.tap(find.text('Edit plan'));
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pump();

      expect(find.text('Save & continue'), findsOneWidget);
      await tester.tap(find.text('Save & continue'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Save & exit" link tappable in builder', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Edit plan'));
      await tester.tap(find.text('Edit plan'));
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pump();

      await tester.ensureVisible(find.textContaining('Save & exit'));
      expect(find.textContaining('Save & exit'), findsOneWidget);
      await tester.tap(find.textContaining('Save & exit'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Skip — use 988 only" tappable in builder', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Edit plan'));
      await tester.tap(find.text('Edit plan'));
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pump();

      await tester.ensureVisible(find.text('Skip — use 988 only'));
      expect(find.text('Skip — use 988 only'), findsOneWidget);
      await tester.tap(find.text('Skip — use 988 only'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('PERSON ONE + PERSON TWO present in builder', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Edit plan'));
      await tester.tap(find.text('Edit plan'));
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pump();

      expect(find.text('PERSON ONE'), findsOneWidget);
      expect(find.text('PERSON TWO'), findsOneWidget);
    });

    // ── Settings link ─────────────────────────────────────────────────────────

    testWidgets('Settings → link present', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Settings →'));
      expect(find.text('Settings →'), findsOneWidget);
    });

    testWidgets('Settings → tap does not crash', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Settings →'));
      await tester.tap(find.text('Settings →'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('Settings → tap opens SettingsScreen', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Settings →'));
      await tester.tap(find.text('Settings →'));
      await tester.pump(const Duration(milliseconds: 800));
      await tester.pump();

      expect(find.byType(SettingsScreen), findsOneWidget);
    });

    // ── Call buttons ──────────────────────────────────────────────────────────

    testWidgets('"Call" button tap does not crash', (tester) async {
      await tester.pumpWidget(buildProfile());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      final callButtons = find.text('Call');
      await tester.ensureVisible(callButtons.first);
      expect(callButtons, findsWidgets);

      await tester.tap(callButtons.first);
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });
  });
}
