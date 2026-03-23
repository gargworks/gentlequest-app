import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/welcome_screen.dart';

void main() {
  group('WelcomeScreen', () {
    testWidgets('renders Meet Alex heading', (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({});

      await tester.pumpWidget(
        const MaterialApp(home: WelcomeScreen()),
      );

      expect(find.text('Meet Alex'), findsOneWidget);
      expect(find.text('Your wellness companion'), findsOneWidget);
    });

    testWidgets('shows three value propositions', (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({});

      await tester.pumpWidget(
        const MaterialApp(home: WelcomeScreen()),
      );

      expect(find.text('Someone to talk to, anytime'), findsOneWidget);
      expect(find.text('Your conversations stay private'), findsOneWidget);
      expect(find.text('No judgment, just support'), findsOneWidget);
    });

    testWidgets('shows Get Started button', (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({});

      await tester.pumpWidget(
        const MaterialApp(home: WelcomeScreen()),
      );

      expect(find.text('Get Started'), findsOneWidget);
    });

    testWidgets('hasBeenSeen returns false initially',
        (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({});

      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, false);
    });

    testWidgets('hasBeenSeen returns true after marking seen',
        (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({'has_seen_welcome_v1': true});

      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, true);
    });
  });
}
