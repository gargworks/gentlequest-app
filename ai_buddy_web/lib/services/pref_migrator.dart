// pref_migrator.dart — one-shot key-drift cleanup + app-start scheduler re-arm.
//
// Two responsibilities:
//
//   1) Migrate any legacy onboarding pref keys (daily_checkin_enabled,
//      streak_nudge_enabled) onto the canonical scheduler keys
//      (notif_daily_reminder_v1, notif_streak_nudge_v1).  If the legacy
//      key is set and the canonical key is unset, copy through.  This
//      handles users who completed onboarding under the pre-2026-05-24
//      drift bug — their opt-in was silently ignored until they manually
//      re-toggled in Settings.
//
//   2) Re-arm notification schedulers on app start.  flutter_local_notifications
//      should persist schedules across reboots, but reinstall (or a stale
//      cancel) can leave the user's saved opt-in pointing at a non-existent
//      schedule.  Reading the canonical keys + calling the schedulers
//      makes the persisted toggle state authoritative.
//
// Audit reference: .brain/audits/2026-05-24_gq_v1.3.0_honesty_audit.md §1+§2.

import 'package:flutter/foundation.dart' show debugPrint;
import 'package:shared_preferences/shared_preferences.dart';

import 'notification_service.dart';

abstract final class PrefMigrator {
  // Canonical (scheduler-readable) keys. Source of truth lives in
  // settings_screen.dart + notification_service_impl.dart.
  static const _kDailyReminder = 'notif_daily_reminder_v1';
  static const _kStreakNudge = 'notif_streak_nudge_v1';

  // Legacy keys written by older builds' onboarding sheet.
  static const _kLegacyDaily = 'daily_checkin_enabled';
  static const _kLegacyStreak = 'streak_nudge_enabled';

  /// Run all one-shot migrations + scheduler re-arming. Safe to call on every
  /// app start — the migration steps no-op when canonical keys already exist.
  static Future<void> run() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await _migrateLegacyNotificationKeys(prefs);
      await _rearmSchedulers(prefs);
    } catch (e) {
      debugPrint('PrefMigrator: run() failed: $e');
    }
  }

  static Future<void> _migrateLegacyNotificationKeys(
      SharedPreferences prefs) async {
    final legacyDaily = prefs.getBool(_kLegacyDaily);
    if (legacyDaily != null && prefs.getBool(_kDailyReminder) == null) {
      await prefs.setBool(_kDailyReminder, legacyDaily);
      debugPrint(
          'PrefMigrator: migrated $_kLegacyDaily → $_kDailyReminder = $legacyDaily');
    }
    final legacyStreak = prefs.getBool(_kLegacyStreak);
    if (legacyStreak != null && prefs.getBool(_kStreakNudge) == null) {
      await prefs.setBool(_kStreakNudge, legacyStreak);
      debugPrint(
          'PrefMigrator: migrated $_kLegacyStreak → $_kStreakNudge = $legacyStreak');
    }
  }

  static Future<void> _rearmSchedulers(SharedPreferences prefs) async {
    final dailyOn = prefs.getBool(_kDailyReminder) ?? false;
    if (dailyOn) {
      try {
        // 20:00 local default; matches Settings + Onboarding wiring.
        final now = DateTime.now();
        final at = DateTime(now.year, now.month, now.day, 20, 0);
        await NotificationService.scheduleGentleDailyCheckin(
          enabled: true,
          scheduledTime: at,
        );
      } catch (e) {
        debugPrint('PrefMigrator: daily re-arm failed: $e');
      }
    }
    final streakOn = prefs.getBool(_kStreakNudge) ?? false;
    if (streakOn) {
      try {
        NotificationService.setStreakNudgeEnabled(true);
      } catch (e) {
        debugPrint('PrefMigrator: streak re-arm failed: $e');
      }
    }
  }
}
