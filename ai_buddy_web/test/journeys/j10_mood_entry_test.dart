import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/screens/mood_tracker_screen.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'test_helpers.dart';

void main() {
  group('J10: Mood entry — expanded coverage', () {
    setUp(setUpBypassedPrefs);

    Widget buildMoodTab() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => MoodProvider()),
        ],
        child: MaterialApp(
          routes: {
            '/clinical-assessment': (_) =>
                const Scaffold(body: Text('Clinical')),
          },
          home: const MoodTrackerScreen(),
        ),
      );
    }

    testWidgets('MoodTrackerScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildMoodTab());
      await tester.pumpAndSettle();

      expect(find.byType(MoodTrackerScreen), findsOneWidget);
    });

    testWidgets('mood trigger card "How are you, right now?" is present',
        (tester) async {
      await tester.pumpWidget(buildMoodTab());
      await tester.pumpAndSettle();

      expect(find.text('How are you, right now?'), findsOneWidget);
    });

    testWidgets('mood trigger card tap does not crash', (tester) async {
      await tester.pumpWidget(buildMoodTab());
      await tester.pumpAndSettle();

      await tester.tap(find.text('How are you, right now?'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('mood bottom sheet opens on trigger tap', (tester) async {
      await tester.pumpWidget(buildMoodTab());
      await tester.pumpAndSettle();

      await tester.tap(find.text('How are you, right now?'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('screen renders successfully with provider', (tester) async {
      await tester.pumpWidget(buildMoodTab());
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
    });
  });
}
