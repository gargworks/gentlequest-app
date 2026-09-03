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

  testWidgets(
      'a consumed deep link does not override initialTab on a LATER mount',
      (tester) async {
    // Regression for the 2026-09-03 audit finding — the second half of the
    // 78d0d757 bug. `_requested` used to be write-once-and-sticky: nothing
    // cleared it in production, so the last tab ever requested kept winning
    // over the route argument on every subsequent mount.
    //
    // Real sequence this reproduces: the user taps a quest notification
    // (main.dart:87 -> request(AppTab.home)), the shell mounts on Home, and
    // then later the compliance gate clears and routes /main with AppTab.talk.
    // Before the fix, the stale Home request overrode it and the user landed
    // on Home.
    final navKey = GlobalKey<NavigatorState>();

    // Mount 1: a genuine deep-link request to Home is made and honoured.
    homeTabDeepLink.request(AppTab.home);
    await navigateToMain(tester, navKey, arguments: AppTab.talk);
    expect(find.byType(WellnessHomeScreen), findsOneWidget,
        reason: 'The live deep-link request must win on the mount that '
            'receives it — that is the whole point of the bus.');

    // Mount 2: no new request. The route argument must now be obeyed.
    final navKey2 = GlobalKey<NavigatorState>();
    await navigateToMain(tester, navKey2, arguments: AppTab.talk);

    expect(find.byType(InteractiveChatScreen), findsOneWidget,
        reason: 'The Home request was already consumed by the first mount. '
            'If this fails, a stale request is still overriding initialTab '
            'and the route argument is being silently discarded.');
    final stack = tester.widget<IndexedStack>(find.byType(IndexedStack));
    expect(stack.index, 1); // AppTab.talk
  });

  testWidgets(
      'OPPOSED CONTROL: a fresh request still overrides initialTab',
      (tester) async {
    // Without this, consume() could be "fixed" by ignoring deep links
    // entirely and the test above would still pass.
    final navKey = GlobalKey<NavigatorState>();
    homeTabDeepLink.request(AppTab.talk);
    await navigateToMain(tester, navKey); // no argument -> would be Home

    expect(find.byType(InteractiveChatScreen), findsOneWidget,
        reason: 'A live request must still beat the default. If this fails, '
            'deep links are dead and the bus does nothing at all.');
  });
}
