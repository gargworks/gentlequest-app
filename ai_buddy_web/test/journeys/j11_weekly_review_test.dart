import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/screens/weekly_review_screen.dart';
import 'test_helpers.dart';

void main() {
  group('J11: WeeklyReviewScreen', () {
    setUp(setUpBypassedPrefs);

    Widget build(WeeklyReviewData data) {
      return MaterialApp(
        home: Scaffold(
          body: ChangeNotifierProvider(
            create: (_) => CompanionProvider(),
            child: WeeklyReviewScreen(data: data),
          ),
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

    // ── Letter format (replaced old NextWeekPromptCard dashboard) ─────────────

    testWidgets('renders "Dear you" letter header', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('Dear you,'), findsOneWidget);
    });

    testWidgets('letter body is present (non-empty prose)', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      // The letter body is rendered as RichText. At least one RichText
      // widget should contain meaningful prose (not just the header).
      final richTexts = tester.widgetList<RichText>(find.byType(RichText));
      final hasBody = richTexts.any((rt) {
        String extract(InlineSpan span) {
          if (span is TextSpan) {
            final buf = StringBuffer(span.text ?? '');
            for (final child in span.children ?? <InlineSpan>[]) {
              buf.write(extract(child));
            }
            return buf.toString();
          }
          return '';
        }
        final text = extract(rt.text);
        return text.isNotEmpty &&
            !text.startsWith('Dear you,') &&
            !text.startsWith('YOUR WEEK');
      });
      expect(hasBody, isTrue, reason: 'Letter body prose should be present');
    });

    testWidgets('"Keep a line from this" or "Close" button is present',
        (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      // Non-empty weeks show 'Keep a line from this'; empty weeks show 'Close'.
      final keepLine = find.text('Keep a line from this');
      final close = find.text('Close');
      expect(
        keepLine.evaluate().isNotEmpty || close.evaluate().isNotEmpty,
        isTrue,
        reason: 'Either "Keep a line from this" or "Close" should be present',
      );
    });

    testWidgets('letter button tap does not crash', (tester) async {
      await tester.pumpWidget(build(WeeklyReviewData.stubLight()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      // Tap whichever button is present.
      final keepLine = find.text('Keep a line from this');
      final close = find.text('Close');
      if (keepLine.evaluate().isNotEmpty) {
        await tester.tap(keepLine);
      } else if (close.evaluate().isNotEmpty) {
        await tester.tap(close);
      }
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });
  });
}
