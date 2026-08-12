/// GentleQuest companion creature — the emotional-attachment core loop.
///
/// Design principles (from the billion-dollar roadmap):
///   • The companion GROWS with gentle check-ins.
///   • It NEVER punishes absence — no streaks that break, no decay, no shame.
///   • Anti-streak: uses total active days, not consecutive days.
///
/// Growth stages unlock at lifetime-XP thresholds. XP is awarded by
/// [CompanionProvider.checkIn] and mirrors the QuestsEngine award scheme
/// (xpTask=10, xpOther=5). The companion never loses progress.
library;

import 'dart:convert';

/// Five growth stages, ordered low → high. Each maps to an emoji in
/// [CompanionWidget] and unlocks at a fixed lifetime-XP threshold.
enum GrowthStage {
  seed,
  sprout,
  sapling,
  young,
  mature,
}

/// Companion mood — derived from recent check-in cadence, never from absence.
/// Absence never produces a negative mood; the floor is [CompanionMood.content].
enum CompanionMood {
  content,
  happy,
  sleepy,
  excited,
  peaceful,
}

/// XP thresholds at which each growth stage unlocks.
/// Keys are [GrowthStage] values; values are the minimum lifetime XP required.
const Map<GrowthStage, int> growthStageThresholds = {
  GrowthStage.seed: 0,
  GrowthStage.sprout: 50,
  GrowthStage.sapling: 150,
  GrowthStage.young: 400,
  GrowthStage.mature: 1000,
};

/// Ordered stages low → high, used to find the current stage and the next one.
const List<GrowthStage> _orderedStages = [
  GrowthStage.seed,
  GrowthStage.sprout,
  GrowthStage.sapling,
  GrowthStage.young,
  GrowthStage.mature,
];

/// A GentleQuest companion creature.
///
/// Immutable value object; mutations go through [CompanionProvider], which
/// builds a new [Companion] via [copyWith] and persists it to
/// SharedPreferences as JSON.
class Companion {
  final int level;
  final GrowthStage growthStage;
  final int totalCheckIns;
  final int totalActiveDays;
  final int lifetimeXp;
  final String name;
  final CompanionMood mood;

  const Companion({
    required this.level,
    required this.growthStage,
    required this.totalCheckIns,
    required this.totalActiveDays,
    required this.lifetimeXp,
    required this.name,
    required this.mood,
  });

  /// A fresh companion: level 1, seed stage, zero check-ins, default name.
  factory Companion.fresh({String name = 'Quest'}) => const Companion(
        level: 1,
        growthStage: GrowthStage.seed,
        totalCheckIns: 0,
        totalActiveDays: 0,
        lifetimeXp: 0,
        name: 'Quest',
        mood: CompanionMood.content,
      );

  /// Derive the [GrowthStage] for a given lifetime XP total.
  /// Returns the highest stage whose threshold the XP meets or exceeds.
  static GrowthStage stageForXp(int lifetimeXp) {
    GrowthStage result = GrowthStage.seed;
    for (final stage in _orderedStages) {
      if (lifetimeXp >= growthStageThresholds[stage]!) {
        result = stage;
      }
    }
    return result;
  }

  /// Derive the companion's level from lifetime XP.
  ///
  /// Level is a gentle, ever-increasing counter (every 25 XP = 1 level) so
  /// the user always sees forward progress even within a growth stage.
  /// Level never decreases.
  static int levelForXp(int lifetimeXp) => 1 + (lifetimeXp ~/ 25);

  /// Derive a companion mood from recent check-in cadence.
  ///
  /// [recentCheckInDays] = number of distinct days with a check-in in the
  /// last 7 days. [checkInsToday] = check-ins logged today. Absence (low
  /// recentCheckInDays) never produces a negative mood — the floor is
  /// [CompanionMood.content] ("your companion is always glad to see you").
  static CompanionMood moodFromRecent({
    required int recentCheckInDays,
    required int checkInsToday,
  }) {
    // Multiple check-ins today → excited (the companion is engaged right now).
    if (checkInsToday >= 2) return CompanionMood.excited;
    // One check-in today and a steady week → happy.
    if (checkInsToday >= 1 && recentCheckInDays >= 3) {
      return CompanionMood.happy;
    }
    // One check-in today, quieter week → peaceful (calm presence).
    if (checkInsToday >= 1) return CompanionMood.peaceful;
    // No check-in today but a steady week → sleepy (resting, not sad).
    if (recentCheckInDays >= 3) return CompanionMood.sleepy;
    // Default floor — absence is never punished.
    return CompanionMood.content;
  }

  Companion copyWith({
    int? level,
    GrowthStage? growthStage,
    int? totalCheckIns,
    int? totalActiveDays,
    int? lifetimeXp,
    String? name,
    CompanionMood? mood,
  }) =>
      Companion(
        level: level ?? this.level,
        growthStage: growthStage ?? this.growthStage,
        totalCheckIns: totalCheckIns ?? this.totalCheckIns,
        totalActiveDays: totalActiveDays ?? this.totalActiveDays,
        lifetimeXp: lifetimeXp ?? this.lifetimeXp,
        name: name ?? this.name,
        mood: mood ?? this.mood,
      );

  Map<String, dynamic> toJson() => {
        'level': level,
        'growth_stage': _stageToString(growthStage),
        'total_check_ins': totalCheckIns,
        'total_active_days': totalActiveDays,
        'lifetime_xp': lifetimeXp,
        'name': name,
        'mood': _moodToString(mood),
      };

  factory Companion.fromJson(Map<String, dynamic> j) {
    GrowthStage parseStage(Object? v) {
      if (v is String) {
        for (final s in GrowthStage.values) {
          if (_stageToString(s) == v) return s;
        }
      }
      return GrowthStage.seed;
    }

    CompanionMood parseMood(Object? v) {
      if (v is String) {
        for (final m in CompanionMood.values) {
          if (_moodToString(m) == v) return m;
        }
      }
      return CompanionMood.content;
    }

    return Companion(
      level: (j['level'] as num?)?.toInt() ?? 1,
      growthStage: parseStage(j['growth_stage']),
      totalCheckIns: (j['total_check_ins'] as num?)?.toInt() ?? 0,
      totalActiveDays: (j['total_active_days'] as num?)?.toInt() ?? 0,
      lifetimeXp: (j['lifetime_xp'] as num?)?.toInt() ?? 0,
      name: (j['name'] as String?) ?? 'Quest',
      mood: parseMood(j['mood']),
    );
  }

  /// Serialize to a JSON string for SharedPreferences persistence.
  String encode() => jsonEncode(toJson());

  /// Parse a JSON string (from SharedPreferences) into a [Companion].
  /// Returns [Companion.fresh] on any decode failure so a corrupt prefs
  /// blob never bricks the companion — the creature just starts over,
  /// which is consistent with the no-shame design.
  static Companion decode(String? stored) {
    if (stored == null || stored.isEmpty) return Companion.fresh();
    try {
      final decoded = jsonDecode(stored);
      if (decoded is Map<String, dynamic>) return Companion.fromJson(decoded);
    } catch (_) {}
    return Companion.fresh();
  }
}

String _stageToString(GrowthStage s) {
  switch (s) {
    case GrowthStage.seed:
      return 'seed';
    case GrowthStage.sprout:
      return 'sprout';
    case GrowthStage.sapling:
      return 'sapling';
    case GrowthStage.young:
      return 'young';
    case GrowthStage.mature:
      return 'mature';
  }
}

String _moodToString(CompanionMood m) {
  switch (m) {
    case CompanionMood.content:
      return 'content';
    case CompanionMood.happy:
      return 'happy';
    case CompanionMood.sleepy:
      return 'sleepy';
    case CompanionMood.excited:
      return 'excited';
    case CompanionMood.peaceful:
      return 'peaceful';
  }
}
