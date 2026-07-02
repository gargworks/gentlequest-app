import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/welcome_screen.dart';
import 'test_helpers.dart';

// WelcomeScreen has an infinite breathing animation — use pump(Duration)
// instead of pumpAndSettle() throughout to avoid timeout.
//
// 2026-07-02: rewritten for the one-tap onboarding redesign (32f2aa57),
// which collapsed the age modal ("Continue" → "Not yet") into a single
// attestation screen and — as a side effect — stopped surfacing the
// under-18 decline path (crisis-never-blocks). The compliance fix restores
// it as a small "Under 18?" link on the welcome screen that jumps straight
// to the existing under-18 dignity screen, so these tests now exercise
// that link instead of the old modal's "Not yet" button.

void main() {
  group('J02: Under-18 dignity path', () {
    setUp(setUpFreshInstall);

    testWidgets('Under-18 link tap shows under-18 screen', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
      await tester.pump(const Duration(milliseconds: 500));

      expect(find.text('Under 18? Find support made for you →'), findsOneWidget);
      await tester.tap(find.text('Under 18? Find support made for you →'));
      // _showUnder18() reverses the (never-forwarded) modal controller
      // then fades the under-18 screen in over GQDurations.fade — a couple
      // of pumps covers both.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 800));
      await tester.pump(); // rebuild after setState(under18)

      // Under-18 state: welcome CTA is gone, dignity-path copy is shown.
      expect(find.text("I'm 18 or older"), findsNothing);
      expect(find.text('Thank you\nfor being honest.'), findsOneWidget);
      expect(find.byType(WelcomeScreen), findsOneWidget);
    });

    testWidgets('has_seen_welcome_v1 is NOT written for under-18 path',
        (tester) async {
      await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.tap(find.text('Under 18? Find support made for you →'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 800));
      await tester.pump(); // rebuild after setState(under18)

      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, isFalse);
    });
  });
}
