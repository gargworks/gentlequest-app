import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:ai_buddy_web/navigation/home_shell.dart';
import 'package:ai_buddy_web/navigation/home_tab_deeplink.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/widgets/app_bottom_nav.dart';

import '../journeys/test_helpers.dart';

/// Design Authority D5 — 4-tab IA: Home / Chat / Journal / You.
///
/// Supersedes the deleted test/legacy/legacy_home_test.dart, which asserted
/// the retired 5-tab (Talk/Mood/Quest/Yours/Community) shape.
void main() {
  setUp(() {
    setUpBypassedPrefs();
    // homeTabDeepLink is a process-wide singleton; a prior test file (e.g.
    // j04_talk_tab_test.dart) can leave it pointed at AppTab.talk, which
    // HomeShell.initState() would immediately pick up and switch away from
    // Home on mount. Reset it so each test here starts from a known state.
    homeTabDeepLink.request(AppTab.home);
  });

  Widget buildShell({AppTab initialTab = AppTab.home}) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ChatProvider()),
        ChangeNotifierProvider(create: (_) => MoodProvider()),
        ChangeNotifierProvider(create: (_) => AssessmentProvider()),
        ChangeNotifierProvider(create: (_) => TaskProvider()),
        ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ChangeNotifierProvider(create: (_) => QuestProvider()),
        ChangeNotifierProvider(create: (_) => CompanionProvider()),
      ],
      child: MaterialApp(home: HomeShell(initialTab: initialTab)),
    );
  }

  testWidgets('renders exactly 4 tabs: Home, Chat, Journal, You',
      (tester) async {
    await tester.pumpWidget(buildShell());
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.byType(AppBottomNav), findsOneWidget);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Chat'), findsOneWidget);
    expect(find.text('Journal'), findsOneWidget);
    expect(find.text('You'), findsOneWidget);
    // The retired labels must not reappear.
    expect(find.text('Talk'), findsNothing);
    expect(find.text('Mood'), findsNothing);
    expect(find.text('Quest'), findsNothing);
    expect(find.text('Community'), findsNothing);
  });

  testWidgets('defaults to the Home tab', (tester) async {
    await tester.pumpWidget(buildShell());
    await tester.pump(const Duration(milliseconds: 300));
    final stack = tester.widget<IndexedStack>(find.byType(IndexedStack));
    expect(stack.index, 0); // Home is index 0 in HomeShell._index
  });

  testWidgets('tapping Journal switches the visible IndexedStack page',
      (tester) async {
    await tester.pumpWidget(buildShell());
    await tester.pump(const Duration(milliseconds: 300));

    await tester.tap(find.text('Journal'));
    await tester.pump(const Duration(milliseconds: 300));

    final stack = tester.widget<IndexedStack>(find.byType(IndexedStack));
    expect(stack.index, 2); // Journal is index 2 in HomeShell._index
  });

  for (final retired in [AppTab.mood, AppTab.quest, AppTab.community]) {
    testWidgets(
        'a retired AppTab.$retired passed as initialTab does not crash — '
        'normalizes to Home', (tester) async {
      await tester.pumpWidget(buildShell(initialTab: retired));
      await tester.pump(const Duration(milliseconds: 300));
      expect(tester.takeException(), isNull);
      expect(find.byType(AppBottomNav), findsOneWidget);
    });
  }
}
