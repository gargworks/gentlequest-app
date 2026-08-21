import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/screens/home/wellness_home_screen.dart';
import 'package:ai_buddy_web/widgets/gq/gq.dart';

import '../../journeys/test_helpers.dart';

void main() {
  setUp(setUpBypassedPrefs);

  Widget buildHome() {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => MoodProvider()),
        ChangeNotifierProvider(create: (_) => CompanionProvider()),
      ],
      child: const MaterialApp(home: WellnessHomeScreen()),
    );
  }

  testWidgets('renders all 5 zones without crashing on a fresh install',
      (tester) async {
    await tester.pumpWidget(buildHome());
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(tester.takeException(), isNull);
    // Zone 2 — not-logged state is the default with no mood entries yet.
    expect(find.text("Log how you're feeling — 15 seconds."), findsOneWidget);
    expect(find.text('Quick check-in'), findsOneWidget);
    // Zone 4 — quick lanes.
    expect(find.text('Talk to Alex'), findsOneWidget);
    expect(find.text('Log mood'), findsOneWidget);
    expect(find.text('Exercises'), findsOneWidget);
    // Zone 5 — gentle nudge (below the fold on the test viewport).
    await tester.dragUntilVisible(
      find.text('A gentle daily nudge?'),
      find.byType(ListView),
      const Offset(0, -100),
    );
    expect(find.text('A gentle daily nudge?'), findsOneWidget);
  });

  testWidgets('Quick check-in CTA pushes MoodTrackerScreen', (tester) async {
    await tester.pumpWidget(buildHome());
    await tester.pump();
    await tester.tap(find.widgetWithText(GQButton, 'Quick check-in'));
    await tester.pumpAndSettle();
    expect(find.text("Let's check in"), findsOneWidget);
  });

  testWidgets('reselect notifier scrolls back to top without throwing',
      (tester) async {
    final reselect = ValueNotifier<int>(0);
    await tester.pumpWidget(MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => MoodProvider()),
        ChangeNotifierProvider(create: (_) => CompanionProvider()),
      ],
      child: MaterialApp(
        home: WellnessHomeScreen(showBottomNav: false, reselect: reselect),
      ),
    ));
    await tester.pump();
    reselect.value++;
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));
    expect(tester.takeException(), isNull);
  });
}
