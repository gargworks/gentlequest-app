import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Low-stim "quiet mode" preference — v1.5.0 ADHD update (ADR-006),
/// docs/V1_5_0_ADHD_UPDATE_SCOPE.md workstream 2b.
///
/// One settings toggle swaps the active color theme for a
/// low-saturation/low-motion variant app-wide (the render-side filter lives
/// in theme/low_stim_mode.dart — LowStimOverlay). This service owns
/// persistence + the reactive notifier the overlay (and any future screen)
/// listens to, mirroring the SharedPreferences-toggle pattern already used
/// for notification prefs and anonymity mode in settings_screen.dart.
class LowStimService {
  LowStimService._();

  /// SharedPreferences key — follows the existing `feature_name_v1`
  /// convention (see `_kNotifDailyReminderKey` etc. in settings_screen.dart).
  static const String kLowStimModeKey = 'low_stim_mode_v1';

  /// Reactive flag. LowStimOverlay listens to this to re-filter the whole
  /// routed subtree the instant the toggle flips — no restart needed.
  /// In-memory default is false so a fresh install/cold boot before
  /// [hydrate] completes never shows the wrong (loud) state as "quiet".
  static final ValueNotifier<bool> lowStimNotifier = ValueNotifier<bool>(false);

  static bool get enabled => lowStimNotifier.value;

  /// Hydrate from SharedPreferences at app start, mirroring
  /// `ProfileConfig.hydrateFromPrefs()` / `AuthService.instance.hydrate()`
  /// in main(). Swallows errors — leaves the safe default (off) on failure.
  static Future<void> hydrate() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      lowStimNotifier.value = prefs.getBool(kLowStimModeKey) ?? false;
    } catch (_) {
      // No-op: leave default (false). Persisted state syncs on next toggle.
    }
  }

  /// Persist + apply immediately. Returns false on a persistence failure so
  /// callers (the Settings toggle) can revert the visible switch, matching
  /// the revert-on-failure pattern used by the notification toggles.
  static Future<bool> setEnabled(bool value) async {
    lowStimNotifier.value = value; // apply instantly — no navigation needed
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(kLowStimModeKey, value);
      return true;
    } catch (_) {
      return false;
    }
  }
}
