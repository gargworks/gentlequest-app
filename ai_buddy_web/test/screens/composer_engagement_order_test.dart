import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Source-level drift guards for composer engagement.
///
/// TRIMMED 2026-09-03. This file used to also contain four tests that
/// reimplemented the screen's latch logic locally and asserted on the copy.
/// Those are deleted: the behaviour is now tested against the real widget in
/// `composer_engagement_widget_test.dart`, through the AnalyticsSink seam.
///
/// The mirror was not merely redundant, it was misleading, and that was
/// measured rather than assumed. With the emitted event name changed from
/// `chat_composer_focused` to a typo — which silently kills the funnel stage —
/// the mirror passed 7/7 while the widget test failed. A test that reports
/// green about a copy of the code is worse than no test.
///
/// What survives here are the two things a runtime test does NOT cover: that
/// the call sites still exist in the source in the right ORDER. Cheap, and
/// they catch a deletion before anyone has to notice a funnel going flat.
void main() {
  test('DRIFT GUARD: the real screen still latches engagement once', () {
    final src = File('lib/screens/interactive_chat_screen.dart').readAsStringSync();
    expect(src.contains('void _logComposerEngagedOnce()'), isTrue,
        reason: 'The helper is gone or renamed.');
    expect(src.contains('if (_composerEngagementLogged) return;'), isTrue,
        reason: 'The once-per-screen latch is gone; the stage can inflate.');
  });

  test('DRIFT GUARD: the chip logs engagement BEFORE calling _sendMessage', () {
    final src = File('lib/screens/interactive_chat_screen.dart').readAsStringSync();
    // Whitespace-insensitive: an earlier version hardcoded 26 spaces of
    // indentation and would have failed on a dartfmt reflow — a guard that
    // cries wolf on formatting gets deleted, and then nothing is guarded.
    final chipOrder = RegExp(r'_logComposerEngagedOnce\(\);\s*_sendMessage\(\);');
    expect(chipOrder.hasMatch(src), isTrue,
        reason: 'The chip no longer logs engagement immediately before the '
            'send.');
  });

  test('DRIFT GUARD: the focus listener still logs engagement', () {
    // Two paths reach this stage. An audit caught that only the chip path was
    // guarded, so deleting the listener call left every test green while
    // everyone who TYPES stopped counting.
    final src = File('lib/screens/interactive_chat_screen.dart').readAsStringSync();
    final listenerCall =
        RegExp(r'_composerWasFocused\s*=\s*true;\s*_logComposerEngagedOnce\(\);');
    expect(listenerCall.hasMatch(src), isTrue,
        reason: 'The focus listener no longer logs engagement.');
  });
}
