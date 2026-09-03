import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Pins the two rules that make `chat_composer_focused` a usable funnel stage,
/// fixed 2026-09-03. The real screen needs a network-backed provider stack, so
/// this exercises the exact guard logic rather than the widget: a
/// once-per-screen latch, plus a chip path that engages before it sends.
///
/// If either rule breaks, the funnel lies in a specific direction, so both are
/// asserted with an opposed control.
void main() {
  late List<String> events;
  late bool engagementLogged;
  late bool composerWasFocused;

  setUp(() {
    events = [];
    engagementLogged = false;
    composerWasFocused = false;
  });

  // Mirrors _logComposerEngagedOnce().
  void logComposerEngagedOnce() {
    if (engagementLogged) return;
    engagementLogged = true;
    events.add('chat_composer_focused');
  }

  // Mirrors the FocusNode listener's rising-edge detection.
  void onFocusChanged({required bool hasFocus}) {
    if (hasFocus && !composerWasFocused) {
      composerWasFocused = true;
      logComposerEngagedOnce();
    } else if (!hasFocus) {
      composerWasFocused = false;
    }
  }

  void sendMessage() => events.add('chat_send_attempted');

  // Mirrors the starter-chip onTap.
  void tapStarterChip() {
    logComposerEngagedOnce();
    sendMessage();
  }

  test('a starter chip logs engagement BEFORE the send', () {
    tapStarterChip();
    expect(events, ['chat_composer_focused', 'chat_send_attempted'],
        reason: 'A chip calls _sendMessage() directly. Before the fix the '
            'composer was never focused, so a send appeared with no preceding '
            'engagement and any sequence reading of these stages was wrong.');
  });

  test('focus / blur / refocus logs engagement ONCE, not three times', () {
    onFocusChanged(hasFocus: true);
    onFocusChanged(hasFocus: false);
    onFocusChanged(hasFocus: true);
    onFocusChanged(hasFocus: false);
    onFocusChanged(hasFocus: true);

    expect(events.where((e) => e == 'chat_composer_focused').length, 1,
        reason: 'The stage means "this user engaged the composer", once. The '
            'old flag reset on blur, so a fidgety user counted three times '
            'against a once-per-user stage above — the step could read as '
            'growth.');
  });

  test('chip then typing does not double-count', () {
    tapStarterChip();
    onFocusChanged(hasFocus: true);
    expect(events.where((e) => e == 'chat_composer_focused').length, 1);
  });

  test('OPPOSED CONTROL: the blur reset still arms the next rising edge', () {
    // The live focus flag MUST keep resetting; only the logging latch is
    // permanent. If someone "simplifies" by never resetting composerWasFocused,
    // real focus transitions stop being detected — which would silently break
    // any future per-focus behaviour hanging off this listener.
    onFocusChanged(hasFocus: true);
    expect(composerWasFocused, isTrue);
    onFocusChanged(hasFocus: false);
    expect(composerWasFocused, isFalse,
        reason: 'Live focus state must track reality, unlike the log latch.');
    onFocusChanged(hasFocus: true);
    expect(composerWasFocused, isTrue);
  });

  // ── Drift guard ────────────────────────────────────────────────────────────
  //
  // Everything above tests a MIRROR of the screen's logic, because the real
  // widget needs a network-backed provider stack. A mirror that silently drifts
  // from the code it mirrors is worse than no test: it reports green about a
  // function it is no longer describing. These read the real source so the
  // mirror cannot rot unnoticed.

  test('DRIFT GUARD: the real screen still latches engagement once', () {
    final src = File('lib/screens/interactive_chat_screen.dart').readAsStringSync();
    expect(src.contains('void _logComposerEngagedOnce()'), isTrue,
        reason: 'The helper this file mirrors is gone or renamed. Re-read the '
            'screen and update the mirror above before trusting it.');
    expect(src.contains('if (_composerEngagementLogged) return;'), isTrue,
        reason: 'The once-per-screen latch is gone; the stage can inflate '
            'again.');
  });

  test('DRIFT GUARD: the chip logs engagement BEFORE calling _sendMessage', () {
    final src = File('lib/screens/interactive_chat_screen.dart').readAsStringSync();
    final engage = src.indexOf('_logComposerEngagedOnce();\n                          _sendMessage();');
    expect(engage, greaterThan(-1),
        reason: 'The starter chip no longer logs engagement immediately '
            'before the send. Either the order flipped back or the call was '
            'dropped — both restore the inverted-order bug this fixed.');
  });
}
