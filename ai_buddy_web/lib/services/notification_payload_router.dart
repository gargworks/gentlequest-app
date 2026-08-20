/// Maps notification payloads onto the app's bare routing tokens.
///
/// Lives in its own file (rather than as a private helper in main.dart) so it
/// can be unit-tested. It exists because of a real, shipped bug:
///
/// Every scheduled notification in `notification_service_impl.dart` carries a
/// `gq://<host>?source=...` payload, but `main.dart`'s handler only ever
/// matched the bare strings 'open_quest' / 'open_today' / 'open_mood' /
/// 'open_talk'. The two sets did not overlap at all, so tapping ANY scheduled
/// notification did nothing. Five shipped categories deep-linked to a no-op and
/// nobody noticed, because nothing fails loudly when a payload simply matches
/// no branch.
///
/// The drift guard for that is in
/// `test/services/notification_payload_router_test.dart`: it reads the payload
/// strings out of `notification_service_impl.dart` and asserts every one maps
/// to a known token. If someone adds a sixth category with a new host, that
/// test fails rather than the feature silently doing nothing.
///
/// See docs/NOTIFICATION_AND_RETENTION_FINDINGS_2026-08-20.md §2.
library;

/// Routing tokens understood by `_handleNotificationPayload` in main.dart.
const String kOpenQuest = 'open_quest';
const String kOpenMood = 'open_mood';
const String kOpenTalk = 'open_talk';

/// All tokens a payload is allowed to normalise to.
const Set<String> kKnownRoutingTokens = {
  kOpenQuest,
  kOpenMood,
  kOpenTalk,
  'open_today', // legacy alias for kOpenQuest, still handled in main.dart
};

/// `gq://` hosts this app schedules, mapped to routing tokens.
///
/// Keep in sync with the `payload:` values in notification_service_impl.dart.
/// The drift test enforces that; do not hand-wave a new host past it.
const Map<String, String> kGqHostToToken = {
  'mood-log': kOpenMood,
  'weekly-review': kOpenMood, // the weekly letter lives in the mood surface
  'chat': kOpenTalk,
  'crisis-ack': kOpenTalk, // crisis follow-up must land where support is
  'home': kOpenQuest,
  'settings': kOpenQuest, // no dedicated settings route registered today
};

/// Normalise a raw notification payload to a routing token.
///
/// Non-`gq://` payloads pass through untouched, preserving the existing
/// bare-token behaviour. Unrecognised `gq://` hosts fall back to [kOpenQuest]
/// rather than returning something unroutable — a tap should always do
/// something, since doing nothing is the bug this file exists to fix.
String normalizeNotificationPayload(String payload) {
  if (!payload.startsWith('gq://')) return payload;
  final host = Uri.tryParse(payload)?.host ?? '';
  return kGqHostToToken[host] ?? kOpenQuest;
}
