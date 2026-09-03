/// Web stub for NotificationService.
/// Provides the same API as notification_service_impl.dart but performs no-ops,
/// so Flutter Web builds don't attempt to link native notification plugins.
///
/// R1D18: all new methods added as no-ops to keep the API surface in sync.
class NotificationService {
  static void Function(String? payload)? onSelectNotification;

  /// Streak nudge is OFF by default on all platforms (including web stub).
  static bool _streakNudgeEnabled = false;

  static Future<void> init() async {
    // no-op on web
  }

  static Future<void> cancelReminder() async {
    // no-op on web
  }

  static Future<void> scheduleOneShot({
    required DateTime target,
    String title = 'Daily check‑in',
    String body = 'Take 2 minutes to reflect and log your mood.',
    int? notificationId,
    String payload = 'open_quest',
    bool cancelPrevious = true,
    String debugTag = '',
  }) async {
    // no-op on web
  }

  // ── R1D18 methods — no-op on web ────────────────────────────────────────

  /// No-op on web. See notification_service_impl.dart for full implementation.
  static Future<void> scheduleGentleDailyCheckin({
    required bool enabled,
    DateTime? scheduledTime,
  }) async {
    // no-op on web
  }

  /// No-op on web. See notification_service_impl.dart for full implementation.
  static Future<void> scheduleMoodLowFollowup({
    Duration delay = const Duration(hours: 1),
  }) async {
    // no-op on web
  }

  /// No-op on web. See notification_service_impl.dart for full implementation.
  static Future<void> scheduleCrisisFollowup({
    Duration delay = const Duration(hours: 24),
  }) async {
    // no-op on web
  }

  /// No-op on web. See notification_service_impl.dart for full implementation.
  static Future<void> cancelCrisisFollowup() async {
    // no-op on web
  }

  /// No-op on web. See notification_service_impl.dart for full implementation.
  static Future<void> scheduleWeeklyReviewIfEligible({
    required int logsThisWeek,
  }) async {
    // no-op on web
  }

  /// No-op on web. Streak nudge is always off on web.
  static void setStreakNudgeEnabled(bool enabled) {
    _streakNudgeEnabled = enabled;
  }

  /// Returns false on web (no push support).
  static bool get streakNudgeEnabled => _streakNudgeEnabled;

  /// No-op on web. See notification_service_impl.dart for full implementation.
  static Future<void> scheduleStreakNudge({
    required int consecutiveDays,
    required DateTime scheduledTime,
    bool heavyDayLogged = false,
  }) async {
    // no-op on web
  }

  /// No-op on web. See notification_service_impl.dart for full implementation.
  static Future<void> cancelStreakNudge() async {
    // no-op on web
  }

  /// No-op on web. See notification_service_impl.dart for full implementation.
  static Future<void> scheduleWorriedCheckin({
    required int latestMoodLevel,
    required DateTime entryTime,
  }) async {
    // no-op on web
  }

  /// No-op on web. Returns false (no notification permission on web).
  static Future<bool> requestPermissions() async {
    return false;
  }
  /// Web has no OS notification permission in this app's model; the answer
  /// is genuinely unknown rather than denied.
  static Future<bool?> hasPermission() async => null;
}
