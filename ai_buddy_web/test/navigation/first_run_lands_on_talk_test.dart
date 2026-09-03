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
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/screens/home/wellness_home_screen.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/widgets/app_bottom_nav.dart';

import '../journeys/test_helpers.dart';

/// Regression for the 2026-09-02 activation finding: first-time users who
/// finished onboarding must land on Talk, while returning users with no
/// argument must still land on Home. Junk arguments fall back to Home via
/// the `args is AppTab` guard.
void main() {
  setUp(() {
    setUpBypassedPrefs();
    // homeTabDeepLink is a process-wide singleton, so a request made by any
    // earlier test would leak in here and override initialTab. Reset it to
    // the pristine "nothing requested" state, which is what a real first
    // launch looks like.
    homeTabDeepLink.resetForTest();
  });

  Widget buildTestApp(GlobalKey<NavigatorState> navKey) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ChatProvider()),
        ChangeNotifierProvider(create: (_) => MoodProvider()),
        ChangeNotifierProvider(create: (_) => AssessmentProvider()),
        ChangeNotifierProvider(create: (_) => TaskProvider()),
        ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ChangeNotifierProvider(create: (_) => CompanionProvider()),
      ],
      child: MaterialApp(
        navigatorKey: navKey,
        home: const SizedBox.shrink(),
        routes: {
          '/main': (context) {
            final args = ModalRoute.of(context)?.settings.arguments;
            return HomeShell(
              initialTab: args is AppTab ? args : AppTab.home,
            );
          },
        },
      ),
    );
  }

  Future<void> navigateToMain(
    WidgetTester tester,
    GlobalKey<NavigatorState> navKey, {
    Object? arguments,
  }) async {
    await tester.pumpWidget(buildTestApp(navKey));
    await tester.pump();
    navKey.currentState!.pushNamed('/main', arguments: arguments);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
  }

  testWidgets(
      '/main with arguments: AppTab.talk lands on Talk (not Home)',
      (tester) async {
    final navKey = GlobalKey<NavigatorState>();
    await navigateToMain(tester, navKey, arguments: AppTab.talk);

    expect(find.byType(InteractiveChatScreen), findsOneWidget);
    expect(find.byType(WellnessHomeScreen), findsNothing);

    final stack = tester.widget<IndexedStack>(find.byType(IndexedStack));
    expect(stack.index, 1); // AppTab.talk
  });

  testWidgets(
      '/main with no arguments still lands on Home for returning users',
      (tester) async {
    final navKey = GlobalKey<NavigatorState>();
    await navigateToMain(tester, navKey);

    expect(find.byType(WellnessHomeScreen), findsOneWidget);
    expect(find.byType(InteractiveChatScreen), findsNothing);

    final stack = tester.widget<IndexedStack>(find.byType(IndexedStack));
    expect(stack.index, 0); // AppTab.home
  });

  testWidgets(
      '/main with junk String argument falls back to Home',
      (tester) async {
    final navKey = GlobalKey<NavigatorState>();
    await navigateToMain(tester, navKey, arguments: 'talk');

    expect(find.byType(WellnessHomeScreen), findsOneWidget);
    expect(find.byType(InteractiveChatScreen), findsNothing);

    final stack = tester.widget<IndexedStack>(find.byType(IndexedStack));
    expect(stack.index, 0); // AppTab.home
  });

  testWidgets(
      '/main with junk int argument falls back to Home',
      (tester) async {
    final navKey = GlobalKey<NavigatorState>();
    await navigateToMain(tester, navKey, arguments: 42);

    expect(find.byType(WellnessHomeScreen), findsOneWidget);
    expect(find.byType(InteractiveChatScreen), findsNothing);

    final stack = tester.widget<IndexedStack>(find.byType(IndexedStack));
    expect(stack.index, 0); // AppTab.home
  });

  testWidgets(
      'tab screens are built LAZILY — chat_tab_viewed is not a launch counter',
      (tester) async {
    // Load-bearing for the activation funnel. HomeShell renders its four tabs
    // inside an IndexedStack (home_shell.dart:318), and IndexedStack builds ALL
    // children eagerly — which would make chat_tab_viewed (fired in
    // InteractiveChatScreen.initState) count app launches rather than visits to
    // the Talk tab, quietly destroying the funnel step it exists to measure.
    //
    // It does NOT, because each tab is wrapped in its own Navigator whose route
    // is inserted lazily through an Overlay, so the screen widget is not built
    // until its tab is selected. That is a subtle, easily-broken guarantee
    // sitting between two widgets that say nothing about each other — so it is
    // pinned here. An audit lane flagged this exact behaviour as a defect on
    // 2026-09-03; it was refuted by this probe, not by argument.
    final navKey = GlobalKey<NavigatorState>();
    await navigateToMain(tester, navKey); // no argument -> Home tab

    expect(find.byType(WellnessHomeScreen), findsOneWidget,
        reason: 'Home tab is the default landing tab.');
    expect(find.byType(InteractiveChatScreen), findsNothing,
        reason: 'The chat screen must NOT be built while the user is on Home. '
            'If this fails, InteractiveChatScreen.initState is running at app '
            'launch and chat_tab_viewed has silently become a launch counter — '
            'the funnel step is then meaningless.');
  });
}
