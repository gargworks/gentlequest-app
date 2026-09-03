import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/screens/onboarding_vow_screen.dart';
import 'package:ai_buddy_web/services/firebase_service.dart';

import '../helpers/recording_analytics_sink.dart';

/// The vow screen is the TRUE first screen of a fresh install (found on an
/// emulator 2026-09-03), and it had no instrumentation. These pump the real
/// widget and observe through the AnalyticsSink seam.
void main() {
  late RecordingAnalyticsSink sink;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    sink = RecordingAnalyticsSink();
    FirebaseService.sinkOverride = sink;
  });
  tearDown(() => FirebaseService.sinkOverride = null);

  Future<void> pumpVow(WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: OnboardingVowScreen()));
    await tester.pump(const Duration(milliseconds: 300));
  }

  testWidgets('mount fires vow_screen_viewed once, and nothing else yet',
      (tester) async {
    await pumpVow(tester);
    expect(sink.count('vow_screen_viewed'), 1);
    expect(sink.count('vow_begin_tapped'), 0,
        reason: 'Begin must require a tap. If it fired on mount the wait '
            'would read as zero and this screen would look frictionless.');
    expect(sink.count('vow_skipped'), 0);
  });

  testWidgets('Skip fires vow_skipped with an elapsed_ms figure',
      (tester) async {
    await pumpVow(tester);
    await tester.pump(const Duration(milliseconds: 700));
    await tester.tap(find.text('Skip'));
    await tester.pump(const Duration(milliseconds: 100));

    expect(sink.count('vow_skipped'), 1);
    final p = sink.params[sink.names.indexOf('vow_skipped')]!;
    expect(p['elapsed_ms'], isA<int>());
    // Wall-clock, not the pumped test clock: tester.pump() advances fake
    // time, DateTime.now() does not. So assert presence and sanity, not a
    // pumped duration — the first version of this test got that wrong.
    expect(p['elapsed_ms'] as int, greaterThanOrEqualTo(0),
        reason: 'elapsed_ms is the load-bearing field — it is what lets the '
            'data say whether people waited for Begin or bailed.');
    expect(p['reduced_motion'], isA<bool>());
  });
}
