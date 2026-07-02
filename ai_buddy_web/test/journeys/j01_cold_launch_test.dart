import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/welcome_screen.dart';
import 'test_helpers.dart';

// WelcomeScreen has an infinite breathing animation — use pump(Duration)
// instead of pumpAndSettle() to avoid timeout.
//
// 2026-07-02: rewritten for the one-tap onboarding redesign (32f2aa57) —
// the old modal flow ("Continue" → age modal → "Yes, I am") was collapsed
// into a single attestation button, so these tests were failing at the
// very first tap (`find.text('Continue')` no longer exists). Also fixes
// the button copy itself, which had drifted to "I'm 13 or older" — see
// welcome_screen.dart for the compliance rationale.

void main() {
  group('J01: Cold launch — new user onboarding', () {
    setUp(setUpFreshInstall);

    testWidgets(
        'WelcomeScreen renders headline, 18+ attestation button, and under-18 link',
        (tester) async {
      await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
      await tester.pump(const Duration(milliseconds: 500));

      expect(find.text('A quiet place,\nwhenever you need it.'), findsOneWidget);
      expect(find.text("I'm 18 or older"), findsOneWidget);
      expect(find.text('Under 18? Find support made for you →'), findsOneWidget);
    });

    testWidgets('hasBeenSeen returns false on fresh install', (tester) async {
      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, isFalse);
    });

    testWidgets("I'm 18 or older tap writes has_seen_welcome_v1 to prefs",
        (tester) async {
      await tester.pumpWidget(const MaterialApp(
        routes: {'/main': _HomeStub.route},
        home: WelcomeScreen(),
      ));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.tap(find.text("I'm 18 or older"));
      // _confirmAdult() writes has_seen_welcome_v1 synchronously, before
      // the async compliance/network chain — a few pumps let those
      // trailing futures resolve without needing to await them directly.
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, isTrue);
    });
  });
}

class _HomeStub extends StatelessWidget {
  const _HomeStub();
  static Widget route(BuildContext context) => const _HomeStub();

  @override
  Widget build(BuildContext context) => const Scaffold(body: Text('Home'));
}
