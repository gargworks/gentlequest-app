import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/services/notification_payload_router.dart';

/// Guards the bug that shipped: every scheduled notification carried a
/// `gq://<host>` payload while main.dart's handler matched only bare tokens
/// like 'open_mood'. The sets did not overlap, so every notification tap was a
/// no-op — and nothing failed loudly, because an unmatched payload just falls
/// through every branch.
///
/// The drift test below is the important one: it reads the ACTUAL payload
/// strings out of notification_service_impl.dart rather than a hand-copied
/// list, so adding a sixth category with a new host fails here instead of
/// silently doing nothing in production.
void main() {
  group('normalizeNotificationPayload', () {
    test('bare tokens pass through untouched', () {
      for (final token in ['open_quest', 'open_today', 'open_mood', 'open_talk']) {
        expect(normalizeNotificationPayload(token), token);
      }
    });

    test('mood-log and weekly-review route to the mood surface', () {
      expect(normalizeNotificationPayload('gq://mood-log?source=push_daily'), 'open_mood');
      expect(normalizeNotificationPayload('gq://weekly-review?source=push_weekly'), 'open_mood');
    });

    test('chat and crisis-ack route to talk, where support lives', () {
      expect(normalizeNotificationPayload('gq://chat?source=push_worried'), 'open_talk');
      expect(normalizeNotificationPayload('gq://crisis-ack?source=push_crisis'), 'open_talk');
    });

    test('home and settings route to quest/home', () {
      expect(normalizeNotificationPayload('gq://home?source=push_streak'), 'open_quest');
      expect(normalizeNotificationPayload('gq://settings?source=push_test'), 'open_quest');
    });

    test('an unknown gq host falls back to a real destination, never a no-op', () {
      final result = normalizeNotificationPayload('gq://some-future-screen?source=x');
      expect(kKnownRoutingTokens.contains(result), isTrue,
          reason: 'unknown hosts must still route somewhere; doing nothing is the bug');
    });

    test('a malformed payload does not throw', () {
      expect(() => normalizeNotificationPayload('gq://'), returnsNormally);
      expect(() => normalizeNotificationPayload('gq://%%%'), returnsNormally);
    });
  });

  test('DRIFT GUARD: every payload the app actually schedules maps to a known token', () {
    final impl = File('lib/services/notification_service_impl.dart');
    expect(impl.existsSync(), isTrue,
        reason: 'expected to run from the ai_buddy_web package root');

    final source = impl.readAsStringSync();
    final payloads = RegExp(r"payload:\s*'(gq://[^']*)'")
        .allMatches(source)
        .map((m) => m.group(1)!)
        .toSet();

    expect(payloads, isNotEmpty,
        reason: 'found no gq:// payloads — the regex or the impl file changed shape, '
            'which would make this guard silently vacuous');

    for (final payload in payloads) {
      final host = Uri.parse(payload).host;
      expect(kGqHostToToken.containsKey(host), isTrue,
          reason: 'Scheduled payload "$payload" has host "$host", which is NOT in '
              'kGqHostToToken. Tapping that notification would fall back to home '
              'instead of its intended screen. Add the host to the map in '
              'notification_payload_router.dart.');
      expect(kKnownRoutingTokens.contains(normalizeNotificationPayload(payload)), isTrue);
    }
  });
}
