import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/welcome_screen.dart';
import 'test_helpers.dart';

// WelcomeScreen has an infinite breathing animation — use pump(Duration)
// instead of pumpAndSettle() throughout to avoid timeout.

void main() {
  group('J02: Under-18 dignity path', () {
    setUp(setUpFreshInstall);

    testWidgets('Not yet tap shows under-18 screen', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
      await tester.pump(const Duration(milliseconds: 500));

      await tester.tap(find.text('Continue'));
      // Two pumps: first records animation startTime, second advances modal into view.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 800));

      expect(find.text('Not yet'), findsOneWidget);
      await tester.tap(find.text('Not yet'));
      // _modalCtrl.reverse() is 700ms. isDone uses strict >, so need >700ms elapsed.
      // pump() records startTime; pump(800ms) advances elapsed to 800ms > 700ms.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 800));
      await tester.pump(); // rebuild after setState(under18)

      // Under-18 state: 'Not yet' button is gone
      expect(find.text('Not yet'), findsNothing);
      expect(find.byType(WelcomeScreen), findsOneWidget);
    });

    testWidgets('has_seen_welcome_v1 is NOT written for under-18 path',
        (tester) async {
      await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.tap(find.text('Continue'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 800));
      await tester.tap(find.text('Not yet'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 800));
      await tester.pump(); // rebuild after setState(under18)

      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, isFalse);
    });
  });
}
