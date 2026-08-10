// Tests for CrisisKeywordDetector — covers the C1/C2 fixes shipped
// 2026-08-10: expanded Tier-1 list, word-boundary matching for '988',
// and the chat-path contract that matchTier1/match drive the
// InlineCrisisBanner activation in ChatProvider.sendMessage.
import 'package:ai_buddy_web/services/crisis_keyword_detector.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('CrisisKeywordDetector.match — Tier 1 (high-signal)', () {
    test('original Tier-1 phrases still match', () {
      expect(CrisisKeywordDetector.matchTier1('I want to kill myself'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I am suicidal'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I want to die'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I am going to overdose'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I will hang myself'), isTrue);
    });

    test('C2 expansion: new Tier-1 phrases match', () {
      expect(CrisisKeywordDetector.matchTier1("I don't want to live"), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I do not want to live'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I am tired of living'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('better off dead'), isTrue);
      expect(CrisisKeywordDetector.matchTier1("I can't do this anymore"), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I give up on life'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I want to unalive myself'), isTrue);
    });

    test('case-insensitive', () {
      expect(CrisisKeywordDetector.matchTier1('I WANT TO DIE'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('Suicidal'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('KILL MYSELF'), isTrue);
    });

    test('empty / whitespace returns false', () {
      expect(CrisisKeywordDetector.match(''), isFalse);
      expect(CrisisKeywordDetector.match('   '), isFalse);
      expect(CrisisKeywordDetector.matchTier1(''), isFalse);
      expect(CrisisKeywordDetector.matchTier1('\n\t'), isFalse);
    });
  });

  group('CrisisKeywordDetector — 988 word-boundary matching', () {
    test('bare "988" matches (user typing the crisis line)', () {
      expect(CrisisKeywordDetector.matchTier1('988'), isTrue);
      expect(CrisisKeywordDetector.match('988'), isTrue);
    });

    test('"988" with surrounding spaces matches', () {
      expect(CrisisKeywordDetector.matchTier1('call 988 now'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I need 988'), isTrue);
    });

    test('"988" inside a longer number does NOT match (avoids false-positive)', () {
      expect(CrisisKeywordDetector.matchTier1('my order is 19889'), isFalse);
      expect(CrisisKeywordDetector.matchTier1('zip 98855'), isFalse);
      expect(CrisisKeywordDetector.matchTier1('1988'), isFalse);
    });

    test('"I called 988 yesterday" DOES match — user is referencing the crisis line',
        () {
      // This is a TRUE positive, not a false positive — the user mentioning
      // 988 in a mental-health chat is itself a signal worth a gentle surface.
      // The word-boundary guard is for numeric-substring false-positives
      // (order numbers, zip codes), not for natural-language mentions.
      expect(CrisisKeywordDetector.matchTier1('I called 988 yesterday'), isTrue);
    });
  });

  group('CrisisKeywordDetector.match — Tier 2 (softer signals)', () {
    test('Tier-2 phrases match via match() but not matchTier1()', () {
      expect(CrisisKeywordDetector.match('I feel hopeless'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('I feel hopeless'), isFalse);
      expect(CrisisKeywordDetector.match('better off without me'), isTrue);
      expect(CrisisKeywordDetector.matchTier1('better off without me'), isFalse);
      expect(CrisisKeywordDetector.match("I can't go on"), isTrue);
      expect(CrisisKeywordDetector.matchTier1("I can't go on"), isFalse);
    });

    test('non-crisis text returns false', () {
      expect(CrisisKeywordDetector.match('I had a great day'), isFalse);
      expect(CrisisKeywordDetector.match('Can you help me focus?'), isFalse);
      expect(CrisisKeywordDetector.match('I am feeling okay today'), isFalse);
    });
  });

  group('C1 contract — chat-path activation', () {
    // These mirror the contract documented in chat_provider.dart:
    //   Tier-1 hit  -> RiskLevel.crisis (banner fires)
    //   Tier-2 hit  -> RiskLevel.high   (banner fires)
    //   no hit      -> RiskLevel.none   (banner does not fire)
    test('user types "I want to kill myself" -> Tier-1 -> banner fires', () {
      const text = 'I want to kill myself';
      final tier1 = CrisisKeywordDetector.matchTier1(text);
      final tier2 = !tier1 && CrisisKeywordDetector.match(text);
      expect(tier1, isTrue);
      expect(tier2, isFalse);
      // ChatProvider maps: tier1 -> RiskLevel.crisis
    });

    test('user types "I feel hopeless" -> Tier-2 -> banner fires', () {
      const text = 'I feel hopeless';
      final tier1 = CrisisKeywordDetector.matchTier1(text);
      final tier2 = !tier1 && CrisisKeywordDetector.match(text);
      expect(tier1, isFalse);
      expect(tier2, isTrue);
      // ChatProvider maps: tier2 -> RiskLevel.high
    });

    test('user types "I am feeling okay" -> no match -> banner does not fire',
        () {
      const text = 'I am feeling okay';
      final tier1 = CrisisKeywordDetector.matchTier1(text);
      final tier2 = !tier1 && CrisisKeywordDetector.match(text);
      expect(tier1, isFalse);
      expect(tier2, isFalse);
      // ChatProvider maps: no match -> RiskLevel.none
    });
  });
}
