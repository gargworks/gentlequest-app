import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/screens/weekly_review_screen.dart';
import 'package:ai_buddy_web/widgets/shareable_mood_card.dart';

void main() {
  group('showShareableMoodCard / ShareableMoodCard', () {
    /// Pump a host that opens the shareable card sheet on mount.
    Future<void> openSheet(WidgetTester tester, WeeklyReviewData data) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) {
                // Open the sheet on first build.
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  showShareableMoodCard(context, data);
                });
                return const SizedBox.shrink();
              },
            ),
          ),
        ),
      );
      // Let the post-frame callback fire and the sheet animate in.
      await tester.pump();
      await tester.pumpAndSettle();
    }

    testWidgets('showShareableMoodCard opens a modal bottom sheet', (tester) async {
      await openSheet(tester, WeeklyReviewData.stubFull());
      // The sheet is open if its header eyebrow is visible.
      expect(find.text('SHARE YOUR WEEK'), findsOneWidget);
      // The close button (Icons.close) is in the sheet header.
      expect(find.byIcon(Icons.close), findsOneWidget);
    });

    testWidgets('the card renders the mood emoji and week label', (tester) async {
      final data = WeeklyReviewData.stubFull();
      await openSheet(tester, data);

      // Week label is rendered on the card body.
      expect(find.text(data.weekLabel), findsOneWidget);
      // The "with GentleQuest" sub-label sits next to the week label.
      expect(find.text('with GentleQuest'), findsOneWidget);
      // The "MY WEEK" eyebrow is rendered on the card itself.
      expect(find.text('MY WEEK'), findsOneWidget);
    });

    testWidgets('the card shows the GQ branding/footer', (tester) async {
      await openSheet(tester, WeeklyReviewData.stubFull());
      // Branded footer text.
      expect(find.text('GentleQuest'), findsOneWidget);
      expect(find.text('app.gentlequest.app'), findsOneWidget);
    });

    testWidgets('the share button is present', (tester) async {
      await openSheet(tester, WeeklyReviewData.stubFull());
      // The share button label (outside the captured boundary).
      expect(find.text('Share this card'), findsOneWidget);
    });
  });
}
