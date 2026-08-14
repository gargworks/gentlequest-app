// weekly_letter_test.dart — Tests for the Anti-Dashboard WeeklyLetter widget.
//
// Verifies:
//   • Letter renders 'Dear you' header
//   • Empty week shows 'you were living'
//   • User quote is bold (w600)
//   • Companion present (CompanionWidget renders)

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/screens/weekly_review_screen.dart';
import 'package:ai_buddy_web/widgets/companion_widget.dart';
import 'package:ai_buddy_web/widgets/weekly_letter.dart';

void main() {
  group('WeeklyLetter', () {
    Future<void> buildWith(
      WidgetTester tester,
      WeeklyReviewData data,
    ) async {
      SharedPreferences.setMockInitialValues({});
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChangeNotifierProvider(
              create: (_) => CompanionProvider(),
              child: SingleChildScrollView(
                child: WeeklyLetter(data: data),
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
    }

    /// Extracts all text from a RichText widget's span tree.
    String _richTextText(RichText richText) {
      String extract(InlineSpan span) {
        if (span is TextSpan) {
          return span.text ?? '';
        }
        return '';
      }
      final span = richText.text;
      if (span is TextSpan) {
        final buf = StringBuffer();
        buf.write(span.text ?? '');
        for (final child in span.children ?? <InlineSpan>[]) {
          buf.write(extract(child));
        }
        return buf.toString();
      }
      return '';
    }

    /// Finds all RichText widgets and returns their concatenated text.
    String _allRichTextText(WidgetTester tester) {
      final richTexts = tester.widgetList<RichText>(find.byType(RichText));
      return richTexts.map(_richTextText).join('\n');
    }

    testWidgets('renders "Dear you" header', (tester) async {
      await buildWith(tester, WeeklyReviewData.stubFull());
      expect(find.text('Dear you,'), findsOneWidget);
    });

    testWidgets('empty week shows "you were living"', (tester) async {
      final emptyData = const WeeklyReviewData(
        state: WeekState.light,
        weekLabel: 'Week of May 6 – 12',
        logCount: 0,
        days: [],
      );
      await buildWith(tester, emptyData);
      final allText = _allRichTextText(tester);
      expect(allText.contains('you were living'), isTrue,
          reason: 'Empty week letter should contain "you were living"');
    });

    testWidgets('user quote is rendered bold (w600)', (tester) async {
      await buildWith(tester, WeeklyReviewData.stubFull());
      // The standout quote from stubFull is:
      // '"walked for 20 mins, said no to a meeting, slept by 10."'
      // It's rendered inside a RichText as a TextSpan with w600.
      final richTexts = tester.widgetList<RichText>(find.byType(RichText));
      bool foundBold = false;
      for (final rt in richTexts) {
        final text = _richTextText(rt);
        if (text.contains('walked for 20 mins')) {
          // Check the span tree for a w600 span.
          void checkSpan(InlineSpan span) {
            if (span is TextSpan) {
              if (span.style?.fontWeight == FontWeight.w600 &&
                  (span.text ?? '').contains('walked for 20 mins')) {
                foundBold = true;
              }
              for (final child in span.children ?? <InlineSpan>[]) {
                checkSpan(child);
              }
            }
          }
          checkSpan(rt.text);
        }
      }
      expect(foundBold, isTrue,
          reason: 'User quote should be rendered with FontWeight.w600');
    });

    testWidgets('companion is present', (tester) async {
      await buildWith(tester, WeeklyReviewData.stubFull());
      expect(find.byType(CompanionWidget), findsOneWidget);
    });

    testWidgets('renders "Next week asks for nothing" in last paragraph',
        (tester) async {
      await buildWith(tester, WeeklyReviewData.stubFull());
      final allText = _allRichTextText(tester);
      expect(allText.contains('Next week asks for nothing'), isTrue);
    });

    testWidgets('empty week shows only Close button (no Keep a line)',
        (tester) async {
      final emptyData = const WeeklyReviewData(
        state: WeekState.light,
        weekLabel: 'Week of May 6 – 12',
        logCount: 0,
        days: [],
      );
      await buildWith(tester, emptyData);
      expect(find.text('Close'), findsOneWidget);
      expect(find.text('Keep a line from this'), findsNothing);
    });

    testWidgets('non-empty week shows Keep a line and Not now buttons',
        (tester) async {
      await buildWith(tester, WeeklyReviewData.stubFull());
      expect(find.text('Keep a line from this'), findsOneWidget);
      expect(find.text('Not now'), findsOneWidget);
    });

    testWidgets('letter never asks a question (no ? in body)', (tester) async {
      await buildWith(tester, WeeklyReviewData.stubFull());
      final allText = _allRichTextText(tester);
      // Exclude the week label and header from the check.
      final bodyText = allText
          .split('\n')
          .where((line) =>
              !line.startsWith('YOUR WEEK') &&
              !line.startsWith('Dear you,') &&
              !line.startsWith('— with you'))
          .join(' ');
      expect(bodyText.contains('?'), isFalse,
          reason: 'Letter must never ask a question');
    });
  });
}
