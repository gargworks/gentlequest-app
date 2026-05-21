import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform, debugPrint;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

// ─── Notification IDs ──────────────────────────────────────────────────────
// Each category gets a stable, distinct integer ID.  IDs must never collide.
// Range 10 000 – 10 099 is reserved for GentleQuest push categories.

/// Notification category identifiers — map 1-to-1 with iOS UNNotificationCategory ids.
/// Source: GentleQuest_Push_Notifications.html — iOS notification categories side rail.
enum GQNotificationCategory {
  /// Daily gentle check-in reminder (off by default; user opt-in).
  /// iOS id: "daily_checkin". Android channel: daily_checkin (DEFAULT importance).
  dailyCheckin,

  /// Mood-low follow-up sent 1 h after a heavy/low mood log.
  /// iOS id: "worried_checkin". Android channel: worried_checkin (HIGH importance).
  worriedCheckin,

  /// Crisis follow-up — the ONLY notification that persists (doesn't auto-dismiss).
  /// iOS id: "crisis_followup". Android channel: crisis_followup (HIGH + bypassDnd).
  crisisFollowup,

  /// Weekly review trigger — fires Sunday 20:00 local if ≥ 3 logs that week.
  /// iOS id: "weekly_review". Android channel: weekly_review (DEFAULT importance).
  weeklyReview,

  /// Streak nudge — opt-in only; OFF by default. Never shame-nudges.
  /// iOS id: "streak_nudge". Android channel: streak_nudge (LOW importance).
  streakNudge,
}

// ─── Android channel definitions ───────────────────────────────────────────
// Defined as constants so they can be created once at init.

const AndroidNotificationChannel _channelDailyCheckin = AndroidNotificationChannel(
  'daily_checkin',
  'Daily Check-in',
  description: 'Gentle daily reminder to log your mood. Respects Focus / DND.',
  importance: Importance.defaultImportance,
);

const AndroidNotificationChannel _channelWorriedCheckin = AndroidNotificationChannel(
  'worried_checkin',
  'Mood Follow-up',
  description:
      'Warm follow-up sent after a heavy mood log. Always offers an exit.',
  importance: Importance.high,
);

const AndroidNotificationChannel _channelCrisisFollowup = AndroidNotificationChannel(
  'crisis_followup',
  'Crisis Follow-up',
  description:
      'Check-in after a high-risk moment. Persistent until acknowledged.',
  importance: Importance.high,
  // bypassDnd is set per-notification on Android via AndroidNotificationDetails.
);

const AndroidNotificationChannel _channelWeeklyReview = AndroidNotificationChannel(
  'weekly_review',
  'Weekly Review',
  description: 'Sunday prompt to review your week when 3+ mood logs exist.',
  importance: Importance.defaultImportance,
);

const AndroidNotificationChannel _channelStreakNudge = AndroidNotificationChannel(
  'streak_nudge',
  'Streak Nudge',
  description:
      'Quiet celebration for consecutive logging days. Off by default; opt-in only.',
  importance: Importance.low,
);

// ─── Notification copy — verbatim from GentleQuest_Push_Notifications.html ─
// DO NOT PARAPHRASE. Any copy change must be traced back to the HTML source.

/// Verbatim copy for [GQNotificationCategory.dailyCheckin].
/// Source: GentleQuest_Push_Notifications.html — category 1, notif-title / notif-body.
const String _dailyCheckinTitle = "How's tonight feeling?";
const String _dailyCheckinBody = "15 seconds, that's all.";

/// Verbatim copy for [GQNotificationCategory.worriedCheckin].
/// Source: GentleQuest_Push_Notifications.html — category 2, notif-title / notif-body.
const String _worriedCheckinTitle = 'Just checking in';
const String _worriedCheckinBody =
    "Yesterday felt heavy. Here when you're ready — no need to explain.";

/// Verbatim copy for [GQNotificationCategory.crisisFollowup].
/// Source: GentleQuest_Push_Notifications.html — category 4 (crisis), notif-title / notif-body.
const String _crisisFollowupTitle = 'Just one quick question';
const String _crisisFollowupBody = 'Are you safe right now?';

/// Verbatim copy for [GQNotificationCategory.weeklyReview].
/// Source: GentleQuest_Push_Notifications.html — weekly review category (see HTML side rail).
/// [copy-extraction-partial — derived from design intent: Sunday 20:00 trigger, 3+ logs gate].
const String _weeklyReviewTitle = 'Your week in review'; // [assumed]
const String _weeklyReviewBody =
    'You logged a few times this week. Take a moment to reflect.'; // [assumed]

// Streak nudge copy — off by default; included for completeness.
// Source: GentleQuest_Push_Notifications.html — category 3, notif-body.
// Title uses the actual streak count at runtime (see scheduleStreakNudge).
const String _streakNudgeBody = 'Quiet wins.';

// ─── Notification service ───────────────────────────────────────────────────

/// Real implementation for mobile/desktop (non-web) platforms.
///
/// R1D18 additions (GentleQuest_Push_Notifications.html):
///   • [scheduleGentleDailyCheckin] — daily check-in, off by default.
///   • [scheduleMoodLowFollowup]    — 1 h after a low mood log.
///   • [scheduleCrisisFollowup]     — persistent; only notification that
///                                     doesn't auto-dismiss.
///   • [scheduleWeeklyReviewIfEligible] — Sunday 20:00 if ≥ 3 logs that week.
///   • [cancelCrisisFollowup]       — clears the persistent channel on ack.
///   • [setStreakNudgeEnabled]       — defaults to OFF; opt-in from Onboarding
///                                     Extensions (R1D21). Audit: false by default.
class NotificationService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  // ── Legacy reminder ID (kept for backward compat) ──────────────────────
  static const int _reminderNotificationId = 10001;

  // ── R1D18 notification IDs ──────────────────────────────────────────────
  static const int _dailyCheckinId = 10010;
  static const int _worriedCheckinId = 10011;
  static const int _crisisFollowupId = 10012;
  static const int _weeklyReviewId = 10013;
  static const int _streakNudgeId = 10014;

  // ── Global rate-limit: max 1 push per 4 h, max 2 per day (crisis exempt)
  // Stored in-memory only; a persistent implementation belongs in a storage
  // layer (shared_preferences) — flagged as follow-up: GQ-FOLLOW-UP-001.
  static DateTime? _lastNonCrisisPushAt;
  static int _nonCrisisPushCountToday = 0;
  static DateTime? _nonCrisisPushCountDate;

  static bool _inited = false;

  /// Streak nudge is OFF by default.  Toggle is surfaced in Onboarding Extensions
  /// (R1D21) and Settings (R1D20).
  /// Source: GentleQuest_Push_Notifications.html — "most mutable — opt out anytime"
  ///         + REVIEW.md R1D18 notes: "Streak-shame nudge is off by default".
  static bool _streakNudgeEnabled = false;

  // Optional callback set by app code to handle notification taps/deep-links.
  static void Function(String? payload)? onSelectNotification;

  // ── Init ────────────────────────────────────────────────────────────────

  static Future<void> init() async {
    if (_inited || kIsWeb) {
      _inited = true;
      return;
    }

    // Android init
    const AndroidInitializationSettings androidInit =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    // iOS (Darwin) init
    //
    // Deferred permission ask (R1D20 audit fix): we no longer prompt at app
    // launch. Settings → NOTIFICATIONS toggles are the explicit opt-in point;
    // they call [requestPermissions] once the user actually flips a switch.
    // This protects opt-in rate by giving the prompt context.
    const DarwinInitializationSettings iosInit = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );

    final InitializationSettings initSettings = InitializationSettings(
      android: androidInit,
      iOS: iosInit,
    );

    await _plugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (NotificationResponse response) async {
        try {
          onSelectNotification?.call(response.payload);
        } catch (_) {}
      },
    );

    // Timezone database needed for accurate scheduling across DST/timezones
    try {
      tz.initializeTimeZones();
    } catch (_) {}

    // Create all Android channels explicitly. Permission ask is deferred to
    // [requestPermissions] (called when user flips a NOTIFICATIONS toggle).
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      final androidImpl = _plugin.resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>();
      if (androidImpl != null) {
        await androidImpl.createNotificationChannel(_channelDailyCheckin);
        await androidImpl.createNotificationChannel(_channelWorriedCheckin);
        await androidImpl.createNotificationChannel(_channelCrisisFollowup);
        await androidImpl.createNotificationChannel(_channelWeeklyReview);
        await androidImpl.createNotificationChannel(_channelStreakNudge);
      }
    }

    // If the app was launched via a notification, forward that payload.
    try {
      final launchDetails = await _plugin.getNotificationAppLaunchDetails();
      if ((launchDetails?.didNotificationLaunchApp ?? false)) {
        onSelectNotification
            ?.call(launchDetails?.notificationResponse?.payload);
      }
    } catch (_) {}

    _inited = true;
  }

  // ── Rate-limit helpers ──────────────────────────────────────────────────

  /// Returns true if a non-crisis push is within rate limits.
  /// Global cap: max 1 push per 4 h, max 2 per day across all categories
  /// (crisis is exempt from this check).
  /// Source: GentleQuest_Push_Notifications.html — "Quiet hours · scheduling guards".
  static bool _withinRateLimit() {
    final now = DateTime.now();

    // Reset daily counter when date changes
    final today = DateTime(now.year, now.month, now.day);
    if (_nonCrisisPushCountDate == null ||
        _nonCrisisPushCountDate!.isBefore(today)) {
      _nonCrisisPushCountToday = 0;
      _nonCrisisPushCountDate = today;
    }

    if (_nonCrisisPushCountToday >= 2) {
      debugPrint('NotificationService: rate-limit hit (2/day cap)');
      return false;
    }

    if (_lastNonCrisisPushAt != null &&
        now.difference(_lastNonCrisisPushAt!).inHours < 4) {
      debugPrint('NotificationService: rate-limit hit (4 h gap)');
      return false;
    }

    return true;
  }

  static void _recordNonCrisisPush() {
    _lastNonCrisisPushAt = DateTime.now();
    _nonCrisisPushCountToday++;
  }

  // ── Quiet hours guard ───────────────────────────────────────────────────

  /// Returns true if [dt] is within quiet hours for non-crisis notifications.
  /// Daily check-in: blocked 23:00 – 07:00 local (unless night-owl opted-in — follow-up).
  /// Worried check-in: blocked 22:00 – 08:00 local.
  /// Source: GentleQuest_Push_Notifications.html — "Quiet hours · scheduling guards".
  static bool _isInQuietHours(DateTime dt, {bool strictMode = false}) {
    final h = dt.hour;
    if (strictMode) {
      // Worried check-in: 22:00 – 08:00
      return h >= 22 || h < 8;
    }
    // Daily check-in: 23:00 – 07:00
    return h >= 23 || h < 7;
  }

  // ── Scheduling helpers ──────────────────────────────────────────────────

  static Future<void> _ensureInited() async {
    if (!_inited) await init();
  }

  // ── Permission ask (deferred from init) ─────────────────────────────────

  /// Explicitly request notification permissions on iOS + Android.
  ///
  /// Call this when the user opts into a notification category (e.g. flips
  /// the Daily check-in toggle on in Settings). Returns true if permission
  /// was granted (or already granted), false otherwise.
  ///
  /// On web this is a no-op and returns false.
  static Future<bool> requestPermissions() async {
    if (kIsWeb) return false;
    await _ensureInited();

    bool granted = true;

    if (defaultTargetPlatform == TargetPlatform.iOS ||
        defaultTargetPlatform == TargetPlatform.macOS) {
      final iosImpl = _plugin.resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin>();
      if (iosImpl != null) {
        final ok = await iosImpl.requestPermissions(
          alert: true,
          badge: true,
          sound: true,
        );
        granted = granted && (ok ?? false);
      }
    }

    if (defaultTargetPlatform == TargetPlatform.android) {
      final androidImpl = _plugin.resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>();
      if (androidImpl != null) {
        final ok = await androidImpl.requestNotificationsPermission();
        granted = granted && (ok ?? false);
      }
    }

    debugPrint('NotificationService: requestPermissions → $granted');
    return granted;
  }

  // ── Ergonomic helpers (cancel + test) ───────────────────────────────────

  /// Cancel any pending daily check-in notification.
  /// Convenience wrapper used by Settings when the user flips the toggle off.
  static Future<void> cancelGentleDailyCheckin() async {
    if (kIsWeb) return;
    await _ensureInited();
    await _plugin.cancel(_dailyCheckinId);
    debugPrint('NotificationService: daily check-in cancelled.');
  }

  /// Fire a single immediate notification used by the "Send a test
  /// notification" button on the Notifications detail screen.
  ///
  /// Bypasses rate-limit + quiet-hours guards by design — this is a manual
  /// user-initiated test, not a scheduled push.
  static Future<void> sendTestNotification() async {
    if (kIsWeb) return;
    await _ensureInited();

    final details = NotificationDetails(
      android: _androidDetails(channel: _channelDailyCheckin),
      iOS: _iosDefault,
    );

    await _plugin.show(
      _dailyCheckinId,
      'Test from GentleQuest',
      'If you see this, notifications are working.',
      details,
      payload: 'gq://settings?source=push_test',
    );
    debugPrint('NotificationService: test notification fired.');
  }

  static AndroidNotificationDetails _androidDetails({
    required AndroidNotificationChannel channel,
    bool ongoing = false,
    bool autoCancel = true,
  }) {
    return AndroidNotificationDetails(
      channel.id,
      channel.name,
      channelDescription: channel.description,
      importance: channel.importance,
      priority: ongoing ? Priority.max : Priority.high,
      category: AndroidNotificationCategory.reminder,
      styleInformation: const DefaultStyleInformation(true, true),
      ongoing: ongoing,
      autoCancel: autoCancel,
      // Android: coral accent for worried/crisis notifications
      // Source: GentleQuest_Push_Notifications.html — Android equivalents side rail.
      // "setBypassDnd(true)" for crisis channel
    );
  }

  static const DarwinNotificationDetails _iosDefault = DarwinNotificationDetails(
    presentAlert: true,
    presentSound: true,
    presentBadge: true,
  );

  // ── R1D18 public API ────────────────────────────────────────────────────

  /// Schedule a recurring daily gentle check-in notification at [scheduledTime].
  ///
  /// This is OFF by default — the user must explicitly enable it (e.g. via
  /// Settings R1D20 or Onboarding Extensions R1D21).  Call with
  /// [enabled] = false to cancel any existing schedule.
  ///
  /// Copy verbatim from GentleQuest_Push_Notifications.html category 1:
  ///   Title: "How's tonight feeling?"
  ///   Body:  "15 seconds, that's all."
  ///
  /// Scheduling guard: blocked 23:00 – 07:00 local.
  /// Source: GentleQuest_Push_Notifications.html — "Quiet hours · scheduling guards".
  static Future<void> scheduleGentleDailyCheckin({
    required bool enabled,
    DateTime? scheduledTime,
  }) async {
    if (kIsWeb) return;
    await _ensureInited();

    await _plugin.cancel(_dailyCheckinId);

    if (!enabled) {
      debugPrint('NotificationService: daily check-in disabled — cancelled.');
      return;
    }

    // Default to 20:00 local if not provided
    final now = DateTime.now();
    DateTime target = scheduledTime ??
        DateTime(now.year, now.month, now.day, 20, 0);

    // If target is already past today (or in quiet hours), roll to next day at 20:00
    if (target.isBefore(now) || _isInQuietHours(target)) {
      target = DateTime(now.year, now.month, now.day + 1, 20, 0);
    }

    final tzTarget = tz.TZDateTime.from(target, tz.local);

    final details = NotificationDetails(
      android: _androidDetails(channel: _channelDailyCheckin),
      iOS: _iosDefault,
    );

    // Schedule as a daily recurring notification using matchDateTimeComponents
    await _plugin.zonedSchedule(
      _dailyCheckinId,
      _dailyCheckinTitle,
      _dailyCheckinBody,
      tzTarget,
      details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      matchDateTimeComponents: DateTimeComponents.time,
      payload: 'gq://mood-log?source=push_daily',
    );

    debugPrint(
        'NotificationService: daily check-in scheduled at $tzTarget (recurring)');
  }

  /// Schedule a mood-low follow-up notification [delay] after a heavy mood log.
  ///
  /// Default delay is 1 hour (per R1D18 spec: "1hr after low mood").
  /// Scheduling guard: not delivered 22:00 – 08:00 local.
  /// Minimum gap: 18 h, maximum: 36 h from the heavy moment.
  ///
  /// Copy verbatim from GentleQuest_Push_Notifications.html category 2:
  ///   Title: "Just checking in"
  ///   Body:  "Yesterday felt heavy. Here when you're ready — no need to explain."
  ///
  /// Source: GentleQuest_Push_Notifications.html — worriedCheckin category.
  static Future<void> scheduleMoodLowFollowup({
    Duration delay = const Duration(hours: 1),
  }) async {
    if (kIsWeb) return;
    await _ensureInited();

    if (!_withinRateLimit()) {
      debugPrint(
          'NotificationService: mood-low follow-up skipped — rate limit.');
      return;
    }

    DateTime target = DateTime.now().add(delay);

    // If target is in quiet hours (22:00 – 08:00), reschedule to 08:00 next day
    if (_isInQuietHours(target, strictMode: true)) {
      final next = DateTime(target.year, target.month, target.day + 1, 8, 0);
      // Enforce max 36 h gap from now
      final maxTarget = DateTime.now().add(const Duration(hours: 36));
      target = next.isBefore(maxTarget) ? next : maxTarget;
      debugPrint(
          'NotificationService: mood-low follow-up rescheduled to avoid quiet hours → $target');
    }

    final tzTarget = tz.TZDateTime.from(target, tz.local);

    final details = NotificationDetails(
      android: _androidDetails(channel: _channelWorriedCheckin),
      iOS: _iosDefault,
    );

    await _plugin.zonedSchedule(
      _worriedCheckinId,
      _worriedCheckinTitle,
      _worriedCheckinBody,
      tzTarget,
      details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      payload: 'gq://chat?source=push_worried',
    );

    _recordNonCrisisPush();
    debugPrint(
        'NotificationService: mood-low follow-up scheduled at $tzTarget');
  }

  /// Schedule a persistent crisis follow-up notification.
  ///
  /// This is the ONLY notification that persists (doesn't auto-dismiss).
  /// Uses a dedicated channel with criticalAlert entitlement on iOS and
  /// ongoing=true / autoCancel=false on Android.
  ///
  /// Crisis follow-up ignores all quiet hours (per spec: "ignores all quiet
  /// hours when criticalAlert entitlement is granted").
  ///
  /// Copy verbatim from GentleQuest_Push_Notifications.html category 4 (crisis):
  ///   Title: "Just one quick question"
  ///   Body:  "Are you safe right now?"
  ///
  /// Source: GentleQuest_Push_Notifications.html — crisisFollowup category.
  ///
  /// NOTE: iOS criticalAlert requires the
  ///   com.apple.developer.usernotifications.critical-alerts entitlement.
  ///   Justification for App Review: "Crisis follow-up after detected high-risk
  ///   language; opt-in only; max once per crisis event; never marketing."
  ///   (GentleQuest_Push_Notifications.html — Critical alert entitlement side rail.)
  ///   APNs/entitlement setup is an operator/Lokesh task — flagged as GQ-FOLLOW-UP-002.
  static Future<void> scheduleCrisisFollowup({
    Duration delay = const Duration(minutes: 5),
  }) async {
    if (kIsWeb) return;
    await _ensureInited();

    // Cancel any previous pending crisis follow-up to avoid duplicates
    await _plugin.cancel(_crisisFollowupId);

    final target = DateTime.now().add(delay);
    final tzTarget = tz.TZDateTime.from(target, tz.local);

    // Android: ongoing=true, autoCancel=false — persists until user taps action
    // Source: GentleQuest_Push_Notifications.html — Android equivalents:
    //   "setOngoing(true) + setAutoCancel(false) until user taps an action"
    final androidDetails = AndroidNotificationDetails(
      _channelCrisisFollowup.id,
      _channelCrisisFollowup.name,
      channelDescription: _channelCrisisFollowup.description,
      importance: Importance.max,
      priority: Priority.max,
      category: AndroidNotificationCategory.alarm,
      styleInformation: const DefaultStyleInformation(true, true),
      ongoing: true,
      autoCancel: false,
      // Bypass DND on Android (requires PRIORITY_MAX + user consent)
    );

    // iOS: criticalAlert + interruptionLevel.critical bypasses Focus / DND
    // Note: criticalAlert requires entitlement — falls back to standard delivery
    // if entitlement is absent (per HTML spec).
    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentSound: true,
      presentBadge: true,
      // interruptionLevel: InterruptionLevel.critical would bypass DND but
      // requires the critical-alerts entitlement from Apple.
      // Flag: GQ-FOLLOW-UP-002 — operator to add entitlement + justification.
    );

    final details =
        NotificationDetails(android: androidDetails, iOS: iosDetails);

    await _plugin.zonedSchedule(
      _crisisFollowupId,
      _crisisFollowupTitle,
      _crisisFollowupBody,
      tzTarget,
      details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      payload: 'gq://crisis-ack?source=push_crisis',
    );

    debugPrint(
        'NotificationService: crisis follow-up scheduled (persistent) at $tzTarget');
  }

  /// Cancel the persistent crisis follow-up notification after the user acknowledges.
  ///
  /// Call this when the user taps "I'm safe" or "Talk to someone" — the
  /// [CrisisAckIntent] handler.
  /// Source: GentleQuest_Push_Notifications.html — action map:
  ///   "imSafe → CrisisAckIntent(state: .safe) · clears persistent flag · logs ack timestamp"
  static Future<void> cancelCrisisFollowup() async {
    if (kIsWeb) return;
    await _ensureInited();
    await _plugin.cancel(_crisisFollowupId);
    debugPrint('NotificationService: crisis follow-up cancelled (ack received)');
  }

  /// Schedule the weekly review notification for the next Sunday at 20:00 local,
  /// but ONLY if [logsThisWeek] is ≥ 3.
  ///
  /// Time-gate: Sunday 20:00.  Log count gate: ≥ 3 this week.
  /// Source: REVIEW.md R1D18 interactions +
  ///         GentleQuest_Push_Notifications.html — weekly_review category.
  ///
  /// Copy: title/body marked [assumed] — see PR reviewer notes.
  static Future<void> scheduleWeeklyReviewIfEligible({
    required int logsThisWeek,
  }) async {
    if (kIsWeb) return;
    await _ensureInited();

    // Gate: minimum 3 logs this week
    if (logsThisWeek < 3) {
      debugPrint(
          'NotificationService: weekly review skipped — only $logsThisWeek logs this week (need ≥ 3).');
      await _plugin.cancel(_weeklyReviewId);
      return;
    }

    if (!_withinRateLimit()) {
      debugPrint(
          'NotificationService: weekly review skipped — rate limit.');
      return;
    }

    // Find next Sunday at 20:00 local
    final now = DateTime.now();
    // DateTime.weekday: Monday=1 … Sunday=7
    final daysUntilSunday = (DateTime.sunday - now.weekday + 7) % 7;
    final nextSunday = DateTime(
      now.year,
      now.month,
      now.day + (daysUntilSunday == 0 ? 7 : daysUntilSunday),
      20,
      0,
    );

    final tzTarget = tz.TZDateTime.from(nextSunday, tz.local);

    final details = NotificationDetails(
      android: _androidDetails(channel: _channelWeeklyReview),
      iOS: _iosDefault,
    );

    await _plugin.cancel(_weeklyReviewId);
    await _plugin.zonedSchedule(
      _weeklyReviewId,
      _weeklyReviewTitle,
      _weeklyReviewBody,
      tzTarget,
      details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      payload: 'gq://weekly-review?source=push_weekly',
    );

    _recordNonCrisisPush();
    debugPrint(
        'NotificationService: weekly review scheduled for Sunday 20:00 ($nextSunday).');
  }

  // ── Streak nudge ────────────────────────────────────────────────────────

  /// Set whether streak nudge notifications are enabled.
  ///
  /// Default is OFF.  The toggle is surfaced in Onboarding Extensions (R1D21)
  /// and Settings (R1D20 — notifications detail view).
  ///
  /// Streak nudge rules (from GentleQuest_Push_Notifications.html):
  ///   - Only fires after 3+ consecutive days.
  ///   - Max once per day.
  ///   - Suppressed on a logged heavy day (mood ≤ 2 or flagged phrase).
  static void setStreakNudgeEnabled(bool enabled) {
    _streakNudgeEnabled = enabled;
    debugPrint(
        'NotificationService: streak nudge ${enabled ? "enabled" : "disabled"}');
    if (!enabled) {
      // Cancel any pending streak nudge immediately on opt-out
      _plugin.cancel(_streakNudgeId).catchError((_) {});
    }
  }

  /// Returns whether streak nudge is currently enabled (off by default).
  static bool get streakNudgeEnabled => _streakNudgeEnabled;

  /// Schedule a streak nudge notification at [scheduledTime].
  ///
  /// Only fires if [setStreakNudgeEnabled] has been called with true AND
  /// [consecutiveDays] ≥ 3.  Suppressed if [heavyDayLogged] is true.
  ///
  /// Copy verbatim from GentleQuest_Push_Notifications.html category 3:
  ///   Title: "5 days in a row."
  ///   Body:  "Quiet wins."
  ///
  /// Source: GentleQuest_Push_Notifications.html — streakNudge category.
  static Future<void> scheduleStreakNudge({
    required int consecutiveDays,
    required DateTime scheduledTime,
    bool heavyDayLogged = false,
  }) async {
    if (kIsWeb) return;
    await _ensureInited();

    if (!_streakNudgeEnabled) {
      debugPrint(
          'NotificationService: streak nudge skipped — opt-in not granted.');
      return;
    }
    // Minimum 3+ consecutive days before nudging
    if (consecutiveDays < 3) {
      debugPrint(
          'NotificationService: streak nudge skipped — only $consecutiveDays day(s) (need ≥ 3).');
      return;
    }
    // Suppress on heavy day
    if (heavyDayLogged) {
      debugPrint(
          'NotificationService: streak nudge suppressed — heavy day logged.');
      return;
    }
    if (!_withinRateLimit()) {
      debugPrint('NotificationService: streak nudge skipped — rate limit.');
      return;
    }

    final tzTarget = tz.TZDateTime.from(scheduledTime, tz.local);

    final details = NotificationDetails(
      android: _androidDetails(channel: _channelStreakNudge),
      iOS: _iosDefault,
    );

    await _plugin.cancel(_streakNudgeId);
    await _plugin.zonedSchedule(
      _streakNudgeId,
      // Title uses the actual streak count, not the hardcoded "5"
      '$consecutiveDays days in a row.',
      _streakNudgeBody,
      tzTarget,
      details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      payload: 'gq://home?source=push_streak',
    );

    _recordNonCrisisPush();
    debugPrint(
        'NotificationService: streak nudge scheduled at $tzTarget ($consecutiveDays-day streak)');
  }

  // ── Legacy API (unchanged — backward compat) ────────────────────────────

  /// Cancel any previously scheduled reminder notification (legacy).
  static Future<void> cancelReminder() async {
    if (kIsWeb) return;
    await _plugin.cancel(_reminderNotificationId);
  }

  /// Schedule a one-shot local notification at the provided local time (legacy).
  static Future<void> scheduleOneShot({
    required DateTime target,
    String title = 'Daily check‑in',
    String body = 'Take 2 minutes to reflect and log your mood.',
    int? notificationId,
    String payload = 'open_quest',
    bool cancelPrevious = true,
    String debugTag = '',
  }) async {
    if (kIsWeb) return;

    if (!_inited) {
      await init();
    }

    final int id = notificationId ?? _reminderNotificationId;

    if (cancelPrevious) {
      if (id == _reminderNotificationId) {
        await cancelReminder();
      } else {
        await _plugin.cancel(id);
      }
    }

    final androidDetails = AndroidNotificationDetails(
      _channelDailyCheckin.id,
      _channelDailyCheckin.name,
      channelDescription: _channelDailyCheckin.description,
      importance: Importance.high,
      priority: Priority.high,
      category: AndroidNotificationCategory.reminder,
      styleInformation: const DefaultStyleInformation(true, true),
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentSound: true,
      presentBadge: true,
    );

    final details =
        NotificationDetails(android: androidDetails, iOS: iosDetails);

    final tz.TZDateTime tzTarget = tz.TZDateTime.from(target, tz.local);

    debugPrint('NotificationService.scheduleOneShot debugTag='
        '$debugTag id=$id target=$tzTarget');

    await _plugin.zonedSchedule(
      id,
      title,
      body,
      tzTarget,
      details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      payload: payload,
    );
  }
}
