/// GentleQuest companion state manager.
///
/// Owns the [Companion] value object, persists it to SharedPreferences as
/// JSON, and notifies listeners on any state change. The companion grows
/// with gentle check-ins and NEVER punishes absence — no streaks that
/// break, no decay, no shame.
///
/// XP awards mirror the QuestsEngine scheme (xpTask=10, xpOther=5). The
/// companion's [Companion.lifetimeXp] is independent of the quests engine's
/// lifetime XP so the creature can grow even before the user touches a quest
/// — a mood check-in alone is enough to feed it.
library;

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/companion.dart';

/// SharedPreferences key for the serialized companion blob.
const String _kCompanionPrefsKey = 'gq.companion.v1';

/// XP awarded per mood check-in. Matches QuestsEngine.xpOther (a check-in
/// is a non-task action). Kept as a local constant so the companion module
/// stays self-contained and doesn't import the quests engine.
const int _kCheckInXp = 5;

class CompanionProvider extends ChangeNotifier {
  Companion _companion = Companion.fresh();
  bool _isLoading = false;
  bool _leveledUpThisCycle = false;

  CompanionProvider() {
    // Load asynchronously; notify once loaded so any UI built before the
    // await completes re-renders with real state.
    _load();
  }

  /// Current companion state (immutable snapshot).
  Companion get companion => _companion;

  bool get isLoading => _isLoading;

  /// True iff the most recent [checkIn] crossed a growth-stage boundary.
  /// UI reads and then clears this via [clearLevelUpFlag] to fire a
  /// one-shot celebration animation.
  bool get leveledUpThisCycle => _leveledUpThisCycle;

  /// Load the companion from SharedPreferences. Safe to call multiple
  /// times; a corrupt or missing blob resets to [Companion.fresh] (the
  /// creature just starts over — no shame).
  Future<void> _load() async {
    _isLoading = true;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      _companion = Companion.decode(prefs.getString(_kCompanionPrefsKey));
    } catch (e) {
      if (kDebugMode) {
        debugPrint('[CompanionProvider] load failed, resetting: $e');
      }
      _companion = Companion.fresh();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Force a reload from disk (e.g. after an external state change).
  Future<void> reload() => _load();

  /// Record a gentle check-in.
  ///
  /// - Increments [Companion.totalCheckIns].
  /// - Awards [_kCheckInXp] to lifetime XP (never decrements).
  /// - Recomputes level + growth stage from the new XP.
  /// - Sets [leveledUpThisCycle] iff the growth stage advanced.
  /// - Persists the new state and notifies listeners.
  ///
  /// [recentCheckInDays] and [checkInsToday] feed the mood derivation; the
  /// caller (typically the mood tracker) knows the live cadence. When
  /// omitted, mood is left unchanged — absence is never punished.
  Future<void> checkIn({
    int? recentCheckInDays,
    int? checkInsToday,
  }) async {
    final newTotalCheckIns = _companion.totalCheckIns + 1;
    final newXp = _companion.lifetimeXp + _kCheckInXp;
    final newLevel = Companion.levelForXp(newXp);
    final newStage = Companion.stageForXp(newXp);

    final bool stageAdvanced = newStage.index > _companion.growthStage.index;

    CompanionMood newMood = _companion.mood;
    if (recentCheckInDays != null && checkInsToday != null) {
      newMood = Companion.moodFromRecent(
        recentCheckInDays: recentCheckInDays,
        checkInsToday: checkInsToday,
      );
    }

    _companion = _companion.copyWith(
      totalCheckIns: newTotalCheckIns,
      lifetimeXp: newXp,
      level: newLevel,
      growthStage: newStage,
      mood: newMood,
    );
    _leveledUpThisCycle = stageAdvanced;

    await _persist();
    notifyListeners();
  }

  /// Update the companion's mood without awarding XP. Used when the mood
  /// cadence changes but no new check-in occurred (e.g. app foregrounded
  /// after a quiet day — the companion rests, never punishes).
  Future<void> updateMood({
    required int recentCheckInDays,
    required int checkInsToday,
  }) async {
    final newMood = Companion.moodFromRecent(
      recentCheckInDays: recentCheckInDays,
      checkInsToday: checkInsToday,
    );
    if (newMood == _companion.mood) return; // no-op, no notify
    _companion = _companion.copyWith(mood: newMood);
    await _persist();
    notifyListeners();
  }

  /// Sync the companion's [Companion.totalActiveDays] from the quests
  /// engine's authoritative count. The companion never decrements this;
  /// it only ever grows. Safe to call with the same value repeatedly.
  Future<void> syncTotalActiveDays(int totalActiveDays) async {
    if (totalActiveDays <= _companion.totalActiveDays) return;
    _companion = _companion.copyWith(totalActiveDays: totalActiveDays);
    await _persist();
    notifyListeners();
  }

  /// Rename the companion. Empty strings are ignored.
  Future<void> rename(String name) async {
    final trimmed = name.trim();
    if (trimmed.isEmpty || trimmed == _companion.name) return;
    _companion = _companion.copyWith(name: trimmed);
    await _persist();
    notifyListeners();
  }

  /// Current growth stage (convenience accessor).
  GrowthStage getGrowthStage() => _companion.growthStage;

  /// Clear the one-shot level-up flag after the UI has consumed it.
  void clearLevelUpFlag() {
    if (!_leveledUpThisCycle) return;
    _leveledUpThisCycle = false;
    notifyListeners();
  }

  Future<void> _persist() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_kCompanionPrefsKey, _companion.encode());
    } catch (e) {
      if (kDebugMode) {
        debugPrint('[CompanionProvider] persist failed: $e');
      }
    }
  }
}
