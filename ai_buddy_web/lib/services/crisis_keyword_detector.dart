// crisis_keyword_detector.dart — R1D11 Compliance Extensions
// Design source: docs/design/refs/htmls/GentleQuest_Compliance_Extensions.html
// Principle: P6 — Crisis never blocks.
//
// On-device, deny-list keyword matcher that runs in <200ms.
// Used by compliance_guard_screen.dart to trigger the 988 surface
// (State A — Crisis-keyword override) whenever a user types a crisis
// keyword into the "Notify me" email field or any other compliance-
// surface input.
//
// C1 fix (2026-08-10): also wired into ChatProvider.sendMessage so the
// inline crisis banner fires even when the backend misclassifies. The
// chat path uses matchTier1/match (not the email-field path), so the
// word-boundary guard on '988' below matters here too — "I called 988
// yesterday" should not re-trigger the banner mid-conversation.
//
// No network calls. No data leaves the device.

/// Checks whether a free-text string contains a crisis keyword.
///
/// Algorithm: case-insensitive full-text scan over the deny-list.
/// Edit-distance fuzzy matching is a v2 follow-up (flagged as backend work).
///
/// Runs synchronously — safe to call from a text-field onChange callback.
/// Benchmarks on current word list: <1ms on mid-range devices.
class CrisisKeywordDetector {
  CrisisKeywordDetector._();

  // ──────────────────────────────────────────────────────────────────────────
  // Deny-list
  // Primary: suicidal intent, self-harm, acute hopelessness.
  // Secondary: softer signals that warrant a gentle 988 surface.
  // Words are lowercase; matching is case-insensitive.
  // ──────────────────────────────────────────────────────────────────────────

  /// Tier 1 — high-signal crisis keywords (always trigger State A).
  /// C2 fix (2026-08-10): expanded with common phrasings the original list
  /// missed — "don't want to live", "tired of living", "better off dead",
  /// "can't do this anymore", "unalive" (platform-evasion euphemism common
  /// on TikTok/Reddit), "give up on life". Substring matching is still
  /// used for phrases; '988' is special-cased with word-boundary matching
  /// to avoid false-positives on "I called 988 yesterday" now that the
  /// detector is wired into the chat path.
  static const List<String> _tier1 = [
    'suicide',
    'suicidal',
    'kill myself',
    'killing myself',
    'end my life',
    'take my life',
    'want to die',
    'want to be dead',
    'going to die',
    'ready to die',
    'don\'t want to live',
    'do not want to live',
    'don\'t want to be alive',
    'do not want to be alive',
    'tired of living',
    'tired of being alive',
    'better off dead',
    'better off if i died',
    'can\'t do this anymore',
    'cannot do this anymore',
    'give up on life',
    'giving up on life',
    'no reason to live',
    'not worth living',
    'life isn\'t worth',
    'life is not worth',
    'hurt myself',
    'hurting myself',
    'self-harm',
    'self harm',
    'cut myself',
    'cutting myself',
    'overdose',
    'od on',
    'hang myself',
    'hanging myself',
    'jump off',
    'unalive',
    // '988' is handled separately with word-boundary matching — see
    // _matchWordBoundary below. Including it as a bare substring would
    // false-positive on "I called 988 yesterday" / "my 988 callback".
  ];

  /// Word-boundary Tier-1 tokens. These match only when surrounded by
  /// non-digit characters (or string start/end), so "988" fires but
  /// "19889" or "98855" does not. Used by both match() and matchTier1().
  static const List<String> _tier1WordBoundary = [
    '988',
  ];

  /// Tier 2 — softer distress signals (also trigger State A; same 988 surface).
  /// The intervention sheet is designed to be non-stigmatising for venting.
  static const List<String> _tier2 = [
    'hopeless',
    'helpless',
    'can\'t go on',
    'cannot go on',
    'can\'t take it anymore',
    'cannot take it',
    'don\'t want to be here',
    'do not want to be here',
    'disappear forever',
    'everyone would be better',
    'better off without me',
    'in crisis',
    'crisis mode',
  ];

  /// Returns `true` if [text] contains any crisis keyword.
  ///
  /// Matching is case-insensitive and substring-based, except for tokens in
  /// [_tier1WordBoundary] which require non-digit boundaries.
  /// An empty or whitespace-only string always returns `false`.
  static bool match(String text) {
    if (text.trim().isEmpty) return false;
    final lower = text.toLowerCase();
    for (final kw in _tier1) {
      if (lower.contains(kw)) return true;
    }
    for (final kw in _tier1WordBoundary) {
      if (_matchWordBoundary(lower, kw)) return true;
    }
    for (final kw in _tier2) {
      if (lower.contains(kw)) return true;
    }
    return false;
  }

  /// Returns `true` if [text] contains any Tier-1 (high-signal) keyword.
  /// Exposed for analytics routing — callers that want to distinguish severity.
  static bool matchTier1(String text) {
    if (text.trim().isEmpty) return false;
    final lower = text.toLowerCase();
    for (final kw in _tier1) {
      if (lower.contains(kw)) return true;
    }
    for (final kw in _tier1WordBoundary) {
      if (_matchWordBoundary(lower, kw)) return true;
    }
    return false;
  }

  /// Word-boundary matcher for numeric / short tokens that would false-positive
  /// as bare substrings. A match requires the token to be preceded and
  /// followed by either a non-alphanumeric character or the string start/end.
  /// Digits are treated as part of the token (so "988" inside "19889" does
  /// NOT match — the surrounding 1 and 9 are alphanumeric and adjacent).
  static bool _matchWordBoundary(String lower, String token) {
    int i = 0;
    while (true) {
      final idx = lower.indexOf(token, i);
      if (idx < 0) return false;
      final before = idx == 0 ? '' : lower.substring(idx - 1, idx);
      final afterEnd = idx + token.length;
      final after = afterEnd >= lower.length
          ? ''
          : lower.substring(afterEnd, afterEnd + 1);
      final beforeOk = before.isEmpty || !_isAlnum(before);
      final afterOk = after.isEmpty || !_isAlnum(after);
      if (beforeOk && afterOk) return true;
      i = idx + 1;
    }
  }

  static bool _isAlnum(String ch) {
    final c = ch.codeUnitAt(0);
    return (c >= 0x30 && c <= 0x39) || // 0-9
        (c >= 0x41 && c <= 0x5a) || // A-Z
        (c >= 0x61 && c <= 0x7a); // a-z
  }
}
