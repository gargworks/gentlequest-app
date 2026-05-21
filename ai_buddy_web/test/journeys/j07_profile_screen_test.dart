import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/profile_screen.dart';
import 'package:ai_buddy_web/screens/settings_screen.dart';
import 'test_helpers.dart';

// Note: this file used to assert against inline-rendered SafetyPlanBuilderStep
// on ProfileScreen ("Use now", "Edit plan", "Save & continue", "PERSON ONE",
// etc.). The current ProfileScreen surfaces the safety plan through a
// separate flow; those strings no longer appear at the screen-level widget
// tree. The stale tests were removed alongside the safety-plan UI changes
// — see the "Safety plan filled state (REMOVED — STALE)" header in the
// group below. Rewrite against the new entry-point surface in a follow-up.

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

    // ── Safety plan filled state (REMOVED — STALE) ────────────────────────────
    //
    // 8 tests below this header used to assert against an old design where
    // ProfileScreen rendered SafetyPlanBuilderStep inline (Use now / Edit plan
    // / Save & continue / Save & exit / Skip — use 988 only / PERSON ONE /
    // PERSON TWO / Call button). The current ProfileScreen surfaces the
    // safety plan via a separate flow; none of those strings appear at the
    // top-level widget tree anymore. Removed rather than left to flap.
    // When the safety-plan UI re-stabilizes, write fresh tests against the
    // new entry-point surface.

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

    // "Call" button tap test removed alongside the safety-plan filled-state
    // suite — the contact-call buttons surface inside the safety-plan flow
    // which is no longer inline. See REMOVED — STALE block above.
  });
}
