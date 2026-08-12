import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/models/companion.dart';

void main() {
  group('Companion.fresh()', () {
    test('creates a seed-stage companion with 0 XP', () {
      final c = Companion.fresh();
      expect(c.growthStage, equals(GrowthStage.seed));
      expect(c.lifetimeXp, equals(0));
      expect(c.level, equals(1));
      expect(c.totalCheckIns, equals(0));
      expect(c.totalActiveDays, equals(0));
      expect(c.mood, equals(CompanionMood.content));
    });
  });

  group('Companion.stageForXp() — thresholds', () {
    test('returns correct stage at each threshold', () {
      expect(Companion.stageForXp(0), equals(GrowthStage.seed));
      expect(Companion.stageForXp(50), equals(GrowthStage.sprout));
      expect(Companion.stageForXp(150), equals(GrowthStage.sapling));
      expect(Companion.stageForXp(400), equals(GrowthStage.young));
      expect(Companion.stageForXp(1000), equals(GrowthStage.mature));
    });

    test('returns correct stage above the top threshold', () {
      expect(Companion.stageForXp(5000), equals(GrowthStage.mature));
    });
  });

  group('Companion.stageForXp() — boundaries', () {
    test('49 → seed (not sprout)', () {
      expect(Companion.stageForXp(49), equals(GrowthStage.seed));
    });
    test('50 → sprout', () {
      expect(Companion.stageForXp(50), equals(GrowthStage.sprout));
    });
    test('149 → sprout (not sapling)', () {
      expect(Companion.stageForXp(149), equals(GrowthStage.sprout));
    });
    test('150 → sapling', () {
      expect(Companion.stageForXp(150), equals(GrowthStage.sapling));
    });
    test('399 → sapling (not young)', () {
      expect(Companion.stageForXp(399), equals(GrowthStage.sapling));
    });
    test('400 → young', () {
      expect(Companion.stageForXp(400), equals(GrowthStage.young));
    });
    test('999 → young (not mature)', () {
      expect(Companion.stageForXp(999), equals(GrowthStage.young));
    });
    test('1000 → mature', () {
      expect(Companion.stageForXp(1000), equals(GrowthStage.mature));
    });
  });

  group('Companion.levelForXp()', () {
    test('starts at 1 for 0 XP', () {
      expect(Companion.levelForXp(0), equals(1));
    });
    test('increases with XP (every 25 XP = 1 level)', () {
      expect(Companion.levelForXp(24), equals(1));
      expect(Companion.levelForXp(25), equals(2));
      expect(Companion.levelForXp(50), equals(3));
      expect(Companion.levelForXp(100), equals(5));
      expect(Companion.levelForXp(1000), equals(41));
    });
  });

  group('Companion.moodFromRecent() — absence floor', () {
    test('total absence returns content (never negative/punishing)', () {
      final mood = Companion.moodFromRecent(
        recentCheckInDays: 0,
        checkInsToday: 0,
      );
      expect(mood, equals(CompanionMood.content));
    });
    test('the floor is content regardless of how long the absence', () {
      final mood = Companion.moodFromRecent(
        recentCheckInDays: 0,
        checkInsToday: 0,
      );
      // No "sad"/"lonely"/negative mood exists in the enum; floor = content.
      expect(mood, isNot(equals(CompanionMood.excited)));
      expect(mood, equals(CompanionMood.content));
    });
    test('multiple check-ins today → excited', () {
      expect(
        Companion.moodFromRecent(recentCheckInDays: 1, checkInsToday: 2),
        equals(CompanionMood.excited),
      );
    });
    test('one check-in today + steady week → happy', () {
      expect(
        Companion.moodFromRecent(recentCheckInDays: 3, checkInsToday: 1),
        equals(CompanionMood.happy),
      );
    });
    test('one check-in today, quiet week → peaceful', () {
      expect(
        Companion.moodFromRecent(recentCheckInDays: 1, checkInsToday: 1),
        equals(CompanionMood.peaceful),
      );
    });
    test('no check-in today but steady week → sleepy', () {
      expect(
        Companion.moodFromRecent(recentCheckInDays: 3, checkInsToday: 0),
        equals(CompanionMood.sleepy),
      );
    });
  });

  group('Companion encode()/decode() roundtrip', () {
    test('preserves all fields', () {
      final original = Companion(
        level: 7,
        growthStage: GrowthStage.sapling,
        totalCheckIns: 42,
        totalActiveDays: 12,
        lifetimeXp: 180,
        name: 'Sproutly',
        mood: CompanionMood.excited,
      );
      final restored = Companion.decode(original.encode());
      expect(restored.level, equals(7));
      expect(restored.growthStage, equals(GrowthStage.sapling));
      expect(restored.totalCheckIns, equals(42));
      expect(restored.totalActiveDays, equals(12));
      expect(restored.lifetimeXp, equals(180));
      expect(restored.name, equals('Sproutly'));
      expect(restored.mood, equals(CompanionMood.excited));
    });

    test('roundtrips the fresh companion', () {
      final fresh = Companion.fresh();
      final restored = Companion.decode(fresh.encode());
      expect(restored.level, equals(fresh.level));
      expect(restored.growthStage, equals(fresh.growthStage));
      expect(restored.totalCheckIns, equals(fresh.totalCheckIns));
      expect(restored.totalActiveDays, equals(fresh.totalActiveDays));
      expect(restored.lifetimeXp, equals(fresh.lifetimeXp));
      expect(restored.name, equals(fresh.name));
      expect(restored.mood, equals(fresh.mood));
    });
  });

  group('Companion.decode() — corrupt JSON', () {
    test('null returns fresh (no crash, no shame)', () {
      final c = Companion.decode(null);
      expect(c.growthStage, equals(GrowthStage.seed));
      expect(c.lifetimeXp, equals(0));
    });
    test('empty string returns fresh', () {
      final c = Companion.decode('');
      expect(c.growthStage, equals(GrowthStage.seed));
      expect(c.lifetimeXp, equals(0));
    });
    test('malformed JSON returns fresh', () {
      final c = Companion.decode('{not valid json');
      expect(c.growthStage, equals(GrowthStage.seed));
      expect(c.lifetimeXp, equals(0));
    });
    test('valid JSON with missing fields falls back to fresh defaults', () {
      final c = Companion.decode('{}');
      expect(c.level, equals(1));
      expect(c.growthStage, equals(GrowthStage.seed));
      expect(c.totalCheckIns, equals(0));
      expect(c.lifetimeXp, equals(0));
      expect(c.name, equals('Quest'));
      expect(c.mood, equals(CompanionMood.content));
    });
    test('unknown stage string falls back to seed', () {
      final c = Companion.decode('{"growth_stage":"galaxy","level":3}');
      expect(c.growthStage, equals(GrowthStage.seed));
    });
  });
}
