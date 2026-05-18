import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/weekly_review_screen.dart';
import 'test_helpers.dart';

void main() {
  group('J11: WeeklyReviewScreen', () {
    setUp(setUpBypassedPrefs);

    Widget build(WeeklyReviewData data) {
      return MaterialApp(
        home: Scaffold(
          body: WeeklyReviewScreen(data: data),
        ),
      );
    }

    // ── Rendering ─────────────────────────────────────────────────────────────

    testWidgets('WeekState.full renders without crash', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubFull()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byType(WeeklyReviewScreen), findsOneWidget);
    });

    testWidgets('WeekState.light renders without crash', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byType(WeeklyReviewScreen), findsOneWidget);
    });

    testWidgets('WeekState.heavy renders without crash', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubHeavy()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byType(WeeklyReviewScreen), findsOneWidget);
    });

    // ── "Just rest" button (light state with emphasizeRest) ───────────────────

    testWidgets('"Just rest" button is present in light state', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('Just rest'), findsOneWidget);
    });

    testWidgets('"Just rest" tap does not crash', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Just rest'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    // ── "Skip this" link ──────────────────────────────────────────────────────

    testWidgets('"Skip this" link is present', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.textContaining("Skip this"), findsOneWidget);
    });

    testWidgets('"Skip this" tap does not crash', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining("Skip this"));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });
  });
}
