import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/welcome_screen.dart';
import 'test_helpers.dart';

// WelcomeScreen has an infinite breathing animation — use pump(Duration)
// instead of pumpAndSettle() to avoid timeout.

void main() {
  group('J01: Cold launch — new user onboarding', () {
    setUp(setUpFreshInstall);

    testWidgets('WelcomeScreen renders headline and Continue button',
        (tester) async {
      await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
      await tester.pump(const Duration(milliseconds: 500));

      expect(find.text('A quiet place,\nwhenever you need it.'), findsOneWidget);
      expect(find.text('Continue'), findsOneWidget);
    });

    testWidgets('Continue tap opens age modal', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
      await tester.pump(const Duration(milliseconds: 500));

      await tester.tap(find.text('Continue'));
      await tester.pump(const Duration(milliseconds: 800));

      expect(find.text('Are you 13 or older?'), findsOneWidget);
      expect(find.text('Not yet'), findsOneWidget);
      expect(find.text('Yes, I am'), findsOneWidget);
    });

    testWidgets('hasBeenSeen returns false on fresh install', (tester) async {
      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, isFalse);
    });

    testWidgets('Yes I am writes has_seen_welcome_v1 to prefs', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        routes: {'/main': _HomeStub.route},
        home: WelcomeScreen(),
      ));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.tap(find.text('Continue'));
      // Two pumps: first records animation startTime (elapsed=0), second advances it.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 800));
      await tester.tap(find.text('Yes, I am'));
      await tester.pump(); // start async chain in _confirmAdult
      await tester.pump(); // SharedPreferences futures resolve
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
