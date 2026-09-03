import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Guards the welcome-screen instrumentation added 2026-09-03.
///
/// WHAT THIS PROVES: the two call sites exist, in the right places, and the
/// event names are legal GA4 identifiers.
///
/// WHAT IT DOES NOT PROVE, stated plainly so nobody reads more into a green
/// run than it earns: that GA4 actually RECEIVES them. FirebaseService.logEvent
/// returns early when `!_initialized` (firebase_service.dart:177), and Firebase
/// is never initialized under `flutter test` — so no widget test can observe an
/// emission. Delivery is only proven by the live funnel reading non-zero:
///     python3 -m metrics.onboarding_funnel_ga4 --days 7
/// Until that reads, treat these events as INSTRUMENTED, not VERIFIED.
///
/// These guards exist because the events are load-bearing for the biggest open
/// question in the product — whether ~74% of installs really never clear the
/// first screen — and a silently-deleted logEvent call would look exactly like
/// the answer being "no".
void main() {
  final src = File('lib/screens/welcome_screen.dart').readAsStringSync();

  test('welcome_screen_viewed fires from initState, not from a tap handler',
      () {
    expect(src.contains("logEvent('welcome_screen_viewed')"), isTrue,
        reason: 'The impression event is gone. Without it the denominator of '
            'the welcome-screen step vanishes and the funnel silently starts '
            'one stage later — the exact bug this instrumentation fixed.');

    final initStateAt = src.indexOf('void initState()');
    final eventAt = src.indexOf("logEvent('welcome_screen_viewed')");
    final confirmAt = src.indexOf('Future<void> _confirmAdult()');
    expect(initStateAt, greaterThan(-1));
    expect(eventAt, greaterThan(initStateAt),
        reason: 'Must fire on mount.');
    expect(eventAt, lessThan(confirmAt),
        reason: 'If this moved below _confirmAdult it is firing on the tap, '
            'not the view — impressions would equal confirmations and the '
            'drop-off would read as zero.');
  });

  test('welcome_age_confirmed fires inside _confirmAdult', () {
    final confirmAt = src.indexOf('Future<void> _confirmAdult()');
    final eventAt = src.indexOf("logEvent('welcome_age_confirmed')");
    expect(eventAt, greaterThan(confirmAt),
        reason: 'The confirmation event must sit inside _confirmAdult — that '
            'is the exact tap the missing ~74% never make.');
  });

  test('both names are legal GA4 event names', () {
    // GA4: <=40 chars, alphanumeric + underscore, must start with a letter.
    // An illegal name is dropped SILENTLY at the SDK, which would look
    // identical to nobody triggering it.
    final legal = RegExp(r'^[a-zA-Z][a-zA-Z0-9_]{0,39}$');
    for (final name in ['welcome_screen_viewed', 'welcome_age_confirmed']) {
      expect(legal.hasMatch(name), isTrue, reason: '$name is not a legal GA4 event name.');
      expect(name.length, lessThanOrEqualTo(40));
    }
  });

  test('the funnel script still lists both stages', () {
    final funnel =
        File('../metrics/onboarding_funnel_ga4.py').readAsStringSync();
    expect(funnel.contains('welcome_screen_viewed'), isTrue);
    expect(funnel.contains('welcome_age_confirmed'), isTrue,
        reason: 'The app can emit an event the funnel never asks for. Both '
            'ends have to agree or the stage reads 0 forever — a working '
            'emitter and a reader that never looks at it is this codebase\'s '
            'most repeated failure.');
  });
}
