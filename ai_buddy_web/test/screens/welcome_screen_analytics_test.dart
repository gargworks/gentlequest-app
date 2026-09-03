import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/screens/welcome_screen.dart';
import 'package:ai_buddy_web/services/firebase_service.dart';

import '../helpers/recording_analytics_sink.dart';

/// A REAL widget test of the welcome-screen instrumentation, 2026-09-03.
///
/// This replaces guessing. `welcome_instrumentation_test.dart` can only assert
/// that certain strings exist in the source at certain byte offsets — it cannot
/// tell whether the call actually executes, which is the only thing that
/// matters for a funnel stage. Now that FirebaseService has an AnalyticsSink
/// seam, this pumps the real screen and watches what really fires.
///
/// Load-bearing: `welcome_screen_viewed` is the denominator for the largest
/// unexplained drop in the product (~74% of installs never clear this screen).
/// If it silently stops firing, that drop reads as zero and the wound looks
/// healed.
void main() {
  late RecordingAnalyticsSink sink;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    sink = RecordingAnalyticsSink();
    FirebaseService.sinkOverride = sink;
  });

  tearDown(() => FirebaseService.sinkOverride = null);

  Future<void> pumpWelcome(WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
    await tester.pump(const Duration(milliseconds: 300));
  }

  testWidgets('mounting the screen fires welcome_screen_viewed exactly once',
      (tester) async {
    await pumpWelcome(tester);

    expect(sink.count('welcome_screen_viewed'), 1,
        reason: 'The impression must fire on mount. Zero means the funnel '
            'silently starts one stage later; more than one inflates the '
            'denominator of the biggest drop in the product.');
  });

  testWidgets(
      'welcome_age_confirmed does NOT fire merely from viewing the screen',
      (tester) async {
    // The opposed control, and the one that matters. If the confirmation event
    // fired on mount, impressions would equal confirmations, the ~74% drop
    // would read as 0%, and we would conclude the wound had healed.
    await pumpWelcome(tester);

    expect(sink.count('welcome_age_confirmed'), 0,
        reason: 'Confirmation must require the actual tap. If this fires on '
            'mount the drop-off measurement is worthless.');
  });

  testWidgets('the two events are distinct — viewing is not confirming',
      (tester) async {
    await pumpWelcome(tester);

    expect(sink.only({'welcome_screen_viewed', 'welcome_age_confirmed'}),
        ['welcome_screen_viewed'],
        reason: 'Exactly one of the pair, in the right order, on a pure view.');
  });
}
