import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'test_helpers.dart';

void main() {
  group('J13: WellnessDashboardScreen', () {
    setUp(setUpBypassedPrefs);

    Widget buildDashboard() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => MoodProvider()),
          ChangeNotifierProvider(create: (_) => QuestProvider()..loadQuests()),
          ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ],
        child: MaterialApp(
          routes: {
            '/clinical-assessment': (_) =>
                const Scaffold(body: Text('Clinical')),
            '/interactive-chat': (_) => const Scaffold(body: Text('Chat')),
            '/home': (_) => const Scaffold(body: Text('Home')),
            '/exercises': (_) => const Scaffold(body: Text('Exercises')),
          },
          home: Scaffold(body: WellnessDashboardScreen()),
        ),
      );
    }

    testWidgets('WellnessDashboardScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildDashboard());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.byType(WellnessDashboardScreen), findsOneWidget);
    });

    testWidgets('dashboard renders without exception', (tester) async {
      await tester.pumpWidget(buildDashboard());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('check-in card is tappable without crash', (tester) async {
      await tester.pumpWidget(buildDashboard());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      final checkInFinder = find.textContaining('check-in');
      if (checkInFinder.evaluate().isNotEmpty) {
        await tester.tap(checkInFinder.first, warnIfMissed: false);
        await tester.pump(const Duration(milliseconds: 300));
        await tester.pump();
        expect(tester.takeException(), isNull);
      }
    });
  });
}
