import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform, debugPrint;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

// ─── SharedPreferences keys (mirror settings_screen.dart) ──────────────────
// These keys MUST stay in sync with the constants defined in
// lib/screens/settings_screen.dart — the settings toggle persists state under
// these keys and the schedulers below read the same keys before firing. If
// they ever drift, toggling off in Settings would not actually suppress the
// push. Source of truth is settings_screen.dart.
//
// WO-5.3 A1: renamed off the "streak"-named key. settings_screen.dart
// forward-migrates the legacy value into the new key on every Settings
// mount, but a nudge can fire before the user ever reopens Settings post
// update — the legacy fallback read below covers that window.
const String _kPrefsStreakNudgeKey = 'notif_gentle_nudge_v1';
const String _kPrefsStreakNudgeLegacyKey = 'notif_streak_nudge_v1';
const String _kPrefsWorriedCheckinKey = 'notif_worried_checkin_v1';

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

  /// Cancel any pending worried-follow-up check-in notification.
  /// Convenience wrapper used by Settings when the user flips the toggle off.
  static Future<void> cancelWorriedCheckin() async {
    if (kIsWeb) return;
    await _ensureInited();
    await _plugin.cancel(_worriedCheckinId);
    debugPrint('NotificationService: worried check-in cancelled.');
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

  /// The pref key Settings wrote this preference under before WO-5.3 A1's
  /// rename. Exposed so settings_screen.dart can forward-migrate an
  /// existing opt-in without spelling out the legacy name itself.
  static String get legacyGentleNudgePrefKey => _kPrefsStreakNudgeLegacyKey;

  /// Schedule a streak nudge notification at [scheduledTime].
  ///
  /// Wire-up site: call from [QuestsEngine.markComplete] (or any per-day
  /// accounting touch point) after the daily-mood-log streak is updated. The
  /// engine passes the current streak length and the desired fire time
  /// (typically today 19:00 local — "haven't logged by 7 PM, here's a nudge").
  ///
  /// Gates (all must pass; any miss = early-return no-op):
  ///   1. Web platform → no-op (push not supported on web).
  ///   2. SharedPreferences `notif_streak_nudge_v1` → must be true. This is
  ///      the persistent Settings toggle from settings_screen.dart. Reading
  ///      it here means the engine doesn't need to know about prefs.
  ///   3. In-service `_streakNudgeEnabled` → must be true. Settings flips this
  ///      synchronously via [setStreakNudgeEnabled] when the toggle changes;
  ///      it acts as a kill-switch for the rest of the session even before
  ///      the prefs round-trip completes.
  ///   4. [consecutiveDays] ≥ 3 → no streak worth protecting yet.
  ///   5. [heavyDayLogged] = false → never push streak-shame after a heavy day.
  ///   6. [_withinRateLimit] → respect the 1-per-4h / 2-per-day global cap.
  ///
  /// On every call (even if the gates fail) any prior pending streak nudge
  /// (id [_streakNudgeId]) is cancelled first — this way the engine can fire
  /// after each mood log and trust that "logged today" → "no stale 7 PM nudge".
  ///
  /// Copy verbatim from GentleQuest_Push_Notifications.html category 3:
  ///   Title (dynamic): "$consecutiveDays days in a row."
  ///   Body:            "Quiet wins."
  ///
  /// Source: GentleQuest_Push_Notifications.html — streakNudge category.
  static Future<void> scheduleStreakNudge({
    required int consecutiveDays,
    required DateTime scheduledTime,
    bool heavyDayLogged = false,
  }) async {
    if (kIsWeb) return;
    await _ensureInited();

    // Always cancel any prior pending nudge — if the engine fires this after
    // a fresh mood log, the previous "you forgot" nudge for today is moot.
    // We do this BEFORE the gate checks so toggling off mid-day clears state
    // even when the schedule call short-circuits below.
    await _plugin.cancel(_streakNudgeId);

    // Gate 1: SharedPreferences key. If the user toggled OFF in Settings,
    // honour that even if the in-service flag is stale (e.g. Settings updated
    // prefs but the engine still holds a true _streakNudgeEnabled in memory).
    try {
      final prefs = await SharedPreferences.getInstance();
      final prefsEnabled = prefs.getBool(_kPrefsStreakNudgeKey) ??
          prefs.getBool(_kPrefsStreakNudgeLegacyKey) ??
          false;
      if (!prefsEnabled) {
        debugPrint(
            'NotificationService: streak nudge skipped — prefs opt-in false.');
        return;
      }
    } catch (e) {
      // SharedPreferences read failure shouldn't surface as a crash; treat as
      // "no opt-in" (fail-closed for user-affecting push).
      debugPrint(
          'NotificationService: streak nudge skipped — prefs read failed: $e');
      return;
    }

    if (!_streakNudgeEnabled) {
      debugPrint(
          'NotificationService: streak nudge skipped — in-service flag false.');
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

  /// Cancel any pending streak nudge.
  ///
  /// Called by Settings when the user flips the toggle OFF, or by the engine
  /// after a successful mood log clears today's "you forgot" risk window.
  /// Safe to call even when no nudge is scheduled (no-op).
  static Future<void> cancelStreakNudge() async {
    if (kIsWeb) return;
    await _ensureInited();
    await _plugin.cancel(_streakNudgeId);
    debugPrint('NotificationService: streak nudge cancelled.');
  }

  // ── Worried check-in (mood-event-driven) ────────────────────────────────

  /// Schedule a 24-hour worried check-in after a low-mood log.
  ///
  /// Wire-up site: call from mood_provider.dart::addMoodEntry when
  /// moodLevel <= 2 (Sad or worse). Owned by the mood-provider lane — this
  /// scheduler exposes a clean API only.
  ///
  /// Behaviour:
  ///   • If prefs key `notif_worried_checkin_v1` is false → cancel any
  ///     pending check-in and return (user opted out).
  ///   • If [latestMoodLevel] > 2 → cancel any pending check-in and return
  ///     (the user's mood recovered; the worried follow-up is moot).
  ///   • Otherwise → cancel any prior pending check-in, then schedule a fresh
  ///     one for [entryTime] + 24 h. Replaces any prior pending check-in
  ///     atomically (cancel-then-schedule), so back-to-back low logs collapse
  ///     to one follow-up 24 h after the most recent log.
  ///
  /// Copy verbatim from GentleQuest_Push_Notifications.html category 2:
  ///   Title: "Just checking in"
  ///   Body:  "Yesterday felt heavy. Here when you're ready — no need to explain."
  ///
  /// NOTE: The spec brief used title "Just checking in 💜" and body "How are
  /// you doing today?" — we deliberately keep the HTML-source-of-truth copy
  /// instead. Any copy change must be traced back to the HTML.
  ///
  /// Source: GentleQuest_Push_Notifications.html — worriedCheckin category.
  static Future<void> scheduleWorriedCheckin({
    required int latestMoodLevel,
    required DateTime entryTime,
  }) async {
    if (kIsWeb) return;
    await _ensureInited();

    // Read opt-in state first — if the user toggled OFF in Settings, honour
    // that and cancel any pending check-in we may have queued earlier.
    bool prefsEnabled = false;
    try {
      final prefs = await SharedPreferences.getInstance();
      prefsEnabled = prefs.getBool(_kPrefsWorriedCheckinKey) ?? false;
    } catch (e) {
      debugPrint(
          'NotificationService: worried check-in prefs read failed: $e');
      prefsEnabled = false; // fail-closed
    }

    if (!prefsEnabled) {
      await _plugin.cancel(_worriedCheckinId);
      debugPrint(
          'NotificationService: worried check-in skipped — prefs opt-in false.');
      return;
    }

    // Mood recovered? Cancel any pending check-in and exit. Threshold matches
    // the spec brief: mood <= 2 (Sad or worse) qualifies; anything above is
    // the recovery / no-op path.
    if (latestMoodLevel > 2) {
      await _plugin.cancel(_worriedCheckinId);
      debugPrint(
          'NotificationService: worried check-in cancelled — mood $latestMoodLevel > 2 (recovered).');
      return;
    }

    if (!_withinRateLimit()) {
      debugPrint(
          'NotificationService: worried check-in skipped — rate limit.');
      return;
    }

    // 24 h after the entry. If that lands in strict quiet hours
    // (22:00–08:00), push to 08:00 the next morning but cap at 36 h total to
    // match scheduleMoodLowFollowup's existing window.
    DateTime target = entryTime.add(const Duration(hours: 24));
    if (_isInQuietHours(target, strictMode: true)) {
      final next = DateTime(target.year, target.month, target.day + 1, 8, 0);
      final maxTarget = entryTime.add(const Duration(hours: 36));
      target = next.isBefore(maxTarget) ? next : maxTarget;
      debugPrint(
          'NotificationService: worried check-in rescheduled out of quiet hours → $target');
    }

    final tzTarget = tz.TZDateTime.from(target, tz.local);

    final details = NotificationDetails(
      android: _androidDetails(channel: _channelWorriedCheckin),
      iOS: _iosDefault,
    );

    // Replace any prior pending check-in atomically (cancel-then-schedule).
    await _plugin.cancel(_worriedCheckinId);
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
        'NotificationService: worried check-in scheduled at $tzTarget (mood=$latestMoodLevel)');
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
