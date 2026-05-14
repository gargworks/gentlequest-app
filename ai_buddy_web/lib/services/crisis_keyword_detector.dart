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
    'no reason to live',
    'not worth living',
    'life isn\'t worth',
    'life is not worth',
    '988',            // user typing the crisis line number is itself a signal
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
  /// Matching is case-insensitive and substring-based.
  /// An empty or whitespace-only string always returns `false`.
  static bool match(String text) {
    if (text.trim().isEmpty) return false;
    final lower = text.toLowerCase();
    for (final kw in _tier1) {
      if (lower.contains(kw)) return true;
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
    return false;
  }
}
