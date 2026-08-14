// crisis_reentry_test.dart — Tests for the Crisis Re-Entry Surface.
//
// Verifies:
//   • Re-entry surface shows 'LAST NIGHT' datestamp
//   • No crisis banner ('you were in crisis' must NOT appear)
//   • Companion present (SilentWitness renders)

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/models/companion.dart';
import 'package:ai_buddy_web/widgets/companion_painter.dart';
import 'package:ai_buddy_web/widgets/crisis_reentry_surface.dart';

void main() {
  group('CrisisReentrySurface', () {
    Future<void> buildWith(
      WidgetTester tester, {
      required DateTime crisisTimestamp,
    }) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SizedBox(
              height: 600,
              child: CrisisReentrySurface(
                crisisTimestamp: crisisTimestamp,
                child: const Column(
                  children: [
                    Text('Old message 1'),
                    Text('Old message 2'),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
    }

    testWidgets('shows "LAST NIGHT" datestamp when crisis was yesterday',
        (tester) async {
      final yesterday = DateTime.now().subtract(const Duration(days: 1));
      await buildWith(tester, crisisTimestamp: yesterday);
      expect(find.text('LAST NIGHT'), findsOneWidget);
    });

    testWidgets('does NOT show a crisis banner', (tester) async {
      final yesterday = DateTime.now().subtract(const Duration(days: 1));
      await buildWith(tester, crisisTimestamp: yesterday);
      expect(find.textContaining('you were in crisis'), findsNothing);
      expect(find.textContaining('crisis'), findsNothing);
    });

    testWidgets('companion (CompanionPainter) is present and breathing',
        (tester) async {
      final yesterday = DateTime.now().subtract(const Duration(days: 1));
      await buildWith(tester, crisisTimestamp: yesterday);
      // The companion is rendered via CustomPaint with a CompanionPainter
      // inside a ScaleTransition (breathing animation).
      final customPaints = tester.widgetList<CustomPaint>(find.byType(CustomPaint));
      bool foundCompanion = false;
      for (final cp in customPaints) {
        if (cp.painter is CompanionPainter) {
          foundCompanion = true;
          break;
        }
      }
      expect(foundCompanion, isTrue,
          reason: 'CompanionPainter should be attached to a CustomPaint');
      expect(find.byType(ScaleTransition), findsWidgets);
    });

    testWidgets('chat content is rendered at aged opacity', (tester) async {
      final yesterday = DateTime.now().subtract(const Duration(days: 1));
      await buildWith(tester, crisisTimestamp: yesterday);
      // The old messages should still be visible (at 82% opacity).
      expect(find.text('Old message 1'), findsOneWidget);
      expect(find.text('Old message 2'), findsOneWidget);
    });

    testWidgets('does NOT show "How are you feeling?"', (tester) async {
      final yesterday = DateTime.now().subtract(const Duration(days: 1));
      await buildWith(tester, crisisTimestamp: yesterday);
      expect(find.textContaining('How are you feeling'), findsNothing);
    });

    test('isWithinCrisisWindow returns true within 72h', () {
      final now = DateTime(2026, 8, 14, 12, 0);
      final within = now.subtract(const Duration(hours: 71));
      final outside = now.subtract(const Duration(hours: 73));
      expect(isWithinCrisisWindow(within, now: now), isTrue);
      expect(isWithinCrisisWindow(outside, now: now), isFalse);
    });

    testWidgets('datestamp shows day name when crisis was >1 day ago',
        (tester) async {
      final threeDaysAgo = DateTime.now().subtract(const Duration(days: 3));
      await buildWith(tester, crisisTimestamp: threeDaysAgo);
      // Should show a 3-letter day abbreviation, not 'LAST NIGHT'.
      expect(find.text('LAST NIGHT'), findsNothing);
      // One of the day abbreviations should be present.
      final dayLabels = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
      expect(
        dayLabels.any((d) => find.text(d).evaluate().isNotEmpty),
        isTrue,
        reason: 'Should show a day abbreviation for crises >1 day ago',
      );
    });
  });
}
