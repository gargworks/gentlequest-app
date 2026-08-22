import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/models/message.dart';

// WO-6.3 Phase 2a — provenance of a risk verdict.
//
// Before this file existed, `RiskSource` appeared in ZERO tests, despite
// being the single condition that decides whether a `.crisis` message may
// seize the entire screen. The distinction it encodes:
//
//   .server  — the backend classifier said crisis. Trusted enough to
//              interrupt with a full-screen takeover.
//   .keyword — the on-device deny-list matched. NOT trusted to interrupt,
//              because deny-lists false-positive on quotes, song lyrics,
//              sarcasm and third-person discussion.
//
// If provenance is ever silently downgraded from .keyword to .server, a
// false positive gains the authority to take over the screen. These tests
// exist to make that failure loud.
void main() {
  group('RiskSource serialization', () {
    test('absent risk_source parses as .server', () {
      // The backend does not emit this field today, and the only caller of
      // fromJson is ApiService.getChatHistory() — so absence genuinely means
      // "the server's own record". This asserts the documented default, so
      // that changing it becomes a deliberate act rather than a silent one.
      final m = Message.fromJson({
        'content': 'hello',
        'is_user': false,
        'risk_level': 'crisis',
      });
      expect(m.riskSource, RiskSource.server);
      expect(m.riskLevel, RiskLevel.crisis);
    });

    test('explicit risk_source is honoured, not flattened', () {
      final m = Message.fromJson({
        'content': 'hello',
        'is_user': true,
        'risk_level': 'crisis',
        'risk_source': 'keyword',
      });
      expect(m.riskSource, RiskSource.keyword);
    });

    test('unrecognised risk_source falls back to .server, not a crash', () {
      final m = Message.fromJson({
        'content': 'hello',
        'is_user': false,
        'risk_source': 'from_the_future',
      });
      expect(m.riskSource, RiskSource.server);
    });

    test('toJson writes risk_source', () {
      final m = Message(
        content: 'x',
        isUser: true,
        riskLevel: RiskLevel.crisis,
        riskSource: RiskSource.keyword,
      );
      expect(m.toJson()['risk_source'], 'keyword');
    });

    // THE REGRESSION GUARD. This is the one that matters.
    //
    // Nothing calls toJson() today, which is exactly why this is easy to
    // break: the first caller added (offline queue, draft cache) would
    // round-trip a keyword-stamped .crisis back in as .server, and the
    // takeover gate would then fire on a deny-list false positive.
    //
    // Verified to actually detect that: with the `risk_source` line removed
    // from toJson, this test fails with .server != .keyword.
    test('round-trip preserves .keyword provenance on a .crisis message', () {
      final original = Message(
        content: 'a lyric someone typed',
        isUser: true,
        riskLevel: RiskLevel.crisis,
        riskSource: RiskSource.keyword,
      );

      final revived = Message.fromJson(original.toJson());

      expect(revived.riskLevel, RiskLevel.crisis);
      expect(
        revived.riskSource,
        RiskSource.keyword,
        reason: 'a keyword-sourced crisis must never re-enter as .server — '
            'that would grant a false positive permission to take over the '
            'whole screen',
      );
    });
  });

  group('copyWith', () {
    test('preserves riskSource when not overridden', () {
      final m = Message(
        content: 'x',
        isUser: true,
        riskLevel: RiskLevel.crisis,
        riskSource: RiskSource.keyword,
      );
      expect(m.copyWith(content: 'y').riskSource, RiskSource.keyword);
    });

    test('carries every field across an unrelated single-field change', () {
      // Guards the drop-on-rebuild class of bug directly: hand-listing fields
      // is how riskSource got lost on the streaming paths in the first place.
      final m = Message(
        id: 'abc',
        content: 'x',
        isUser: true,
        type: MessageType.text,
        riskLevel: RiskLevel.high,
        riskSource: RiskSource.keyword,
        crisisMsg: 'msg',
      );
      final c = m.copyWith(content: 'changed');

      expect(c.id, 'abc');
      expect(c.isUser, isTrue);
      expect(c.riskLevel, RiskLevel.high);
      expect(c.riskSource, RiskSource.keyword);
      expect(c.crisisMsg, 'msg');
      expect(c.timestamp, m.timestamp);
    });
  });
}
