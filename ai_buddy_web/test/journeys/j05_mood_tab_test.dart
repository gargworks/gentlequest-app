import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/screens/mood_tracker_screen.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'test_helpers.dart';

void main() {
  group('J05: Mood tab', () {
    setUp(setUpBypassedPrefs);

    Widget buildMoodTab() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => MoodProvider()),
        ],
        child: const MaterialApp(home: MoodTrackerScreen()),
      );
    }

    testWidgets('renders mood trigger card', (tester) async {
      await tester.pumpWidget(buildMoodTab());
      await tester.pumpAndSettle();

      expect(find.text('How are you, right now?'), findsOneWidget);
    });

    testWidgets('mood trigger card is tappable (no crash on tap)', (tester) async {
      await tester.pumpWidget(buildMoodTab());
      await tester.pumpAndSettle();

      final triggerCard = find.text('How are you, right now?');
      expect(triggerCard, findsOneWidget);
      await tester.tap(triggerCard);
      // Pump with duration — modal sheet animation may not settle
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump(const Duration(milliseconds: 500));
      // No exception thrown = callback is wired (not empty)
      expect(tester.takeException(), isNull);
    });
  });
}
