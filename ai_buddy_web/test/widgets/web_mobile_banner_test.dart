import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/widgets/web_mobile_banner.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    // Start each test with a clean SharedPreferences mock.
    SharedPreferences.setMockInitialValues({});
  });

  Future<void> pumpBanner(
    WidgetTester tester, {
    bool isWebOverride = true,
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Column(
            children: [
              WebMobileBanner(isWebOverride: isWebOverride),
              const Expanded(child: Text('chat content')),
            ],
          ),
        ),
      ),
    );
    // Allow the async _loadDismissState() future to resolve.
    await tester.pumpAndSettle();
  }

  testWidgets('banner shows on web (isWebOverride = true)',
      (WidgetTester tester) async {
    await pumpBanner(tester, isWebOverride: true);

    expect(find.byType(WebMobileBanner), findsOneWidget);
    expect(find.textContaining('GentleQuest is also available'), findsOneWidget);
    expect(find.byKey(const Key('web_mobile_banner_get_app')), findsOneWidget);
    expect(find.byKey(const Key('web_mobile_banner_dismiss')), findsOneWidget);
  });

  testWidgets('banner does not show on non-web (isWebOverride = false)',
      (WidgetTester tester) async {
    await pumpBanner(tester, isWebOverride: false);

    // The widget renders a SizedBox.shrink — no banner content visible.
    expect(find.textContaining('GentleQuest is also available'), findsNothing);
    expect(find.byKey(const Key('web_mobile_banner_get_app')), findsNothing);
  });

  testWidgets('dismiss button hides the banner', (WidgetTester tester) async {
    await pumpBanner(tester, isWebOverride: true);

    // Banner is visible before dismiss.
    expect(find.textContaining('GentleQuest is also available'), findsOneWidget);

    // Tap the dismiss X button.
    await tester.tap(find.byKey(const Key('web_mobile_banner_dismiss')));
    await tester.pumpAndSettle();

    // Banner content is gone after dismiss.
    expect(find.textContaining('GentleQuest is also available'), findsNothing);
    expect(find.byKey(const Key('web_mobile_banner_get_app')), findsNothing);
  });

  testWidgets('banner does not show after prior dismissal (prefs persisted)',
      (WidgetTester tester) async {
    // Simulate a prior dismissal by pre-seeding SharedPreferences.
    SharedPreferences.setMockInitialValues({
      WebMobileBanner.prefsKey: true,
    });

    await pumpBanner(tester, isWebOverride: true);

    // Banner should not appear because the dismissed flag is already set.
    expect(find.textContaining('GentleQuest is also available'), findsNothing);
    expect(find.byKey(const Key('web_mobile_banner_get_app')), findsNothing);
  });

  testWidgets("'Get the app' link is present and tappable",
      (WidgetTester tester) async {
    await pumpBanner(tester, isWebOverride: true);

    final getAppLink = find.byKey(const Key('web_mobile_banner_get_app'));
    expect(getAppLink, findsOneWidget);
    expect(find.text('Get the app'), findsOneWidget);

    // Tapping should not throw (url_launcher may fail in test env, but
    // the gesture itself must be handled without crashing).
    await tester.tap(getAppLink);
    await tester.pumpAndSettle();
  });
}
