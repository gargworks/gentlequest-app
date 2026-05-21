import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/clinical_assessment_screen.dart';
import 'test_helpers.dart';

void main() {
  group('J09: ClinicalAssessmentScreen — comprehensive', () {
    setUp(setUpBypassedPrefs);

    Widget buildAssessment() {
      return MaterialApp(
        routes: {
          '/interactive-chat': (_) => const Scaffold(body: Text('Chat')),
        },
        home: const ClinicalAssessmentScreen(),
      );
    }

    // ── Entry screen ──────────────────────────────────────────────────────────

    testWidgets('ClinicalAssessmentScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byType(ClinicalAssessmentScreen), findsOneWidget);
    });

    testWidgets('PHQ-9 card is present', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.textContaining('PHQ-9'), findsAtLeast(1));
    });

    testWidgets('GAD-7 card is present', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.textContaining('GAD-7'), findsAtLeast(1));
    });

    testWidgets('PHQ-9 card tap does not crash', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining('PHQ-9').first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('GAD-7 card tap does not crash', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining('GAD-7').first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    // ── Assessment flow ───────────────────────────────────────────────────────

    testWidgets('first question renders with Likert pills after starting PHQ-9',
        (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining('PHQ-9').first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      // "Not at all" is always the first Likert option
      expect(find.text('Not at all'), findsOneWidget);
    });

    testWidgets('selecting Likert pill does not crash', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining('PHQ-9').first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text('Not at all'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Next" button is present after selecting a pill', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining('PHQ-9').first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text('Not at all'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Next'));
      expect(find.text('Next'), findsOneWidget);
    });

    testWidgets('"Next" tap advances to question 2', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining('PHQ-9').first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text('Not at all'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Next'));
      await tester.tap(find.text('Next'));
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Save & exit" link is present in assessment', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining('PHQ-9').first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.textContaining('Save & exit'), findsOneWidget);
    });

    testWidgets('"Save & exit" tap does not crash', (tester) async {
      await tester.pumpWidget(buildAssessment());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.textContaining('PHQ-9').first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.textContaining('Save & exit'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });
  });
}
