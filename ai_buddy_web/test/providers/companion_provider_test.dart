import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/models/companion.dart';

void main() {
  group('CompanionProvider.checkIn()', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('increments totalCheckIns and adds XP', () async {
      final provider = CompanionProvider();
      // Let the async _load() from the constructor drain.
      await Future.delayed(Duration.zero);
      final checkInsBefore = provider.companion.totalCheckIns;
      final xpBefore = provider.companion.lifetimeXp;

      await provider.checkIn();

      expect(provider.companion.totalCheckIns, equals(checkInsBefore + 1));
      expect(provider.companion.lifetimeXp, greaterThan(xpBefore));
      // xpOther = 5 per check-in (mirrors QuestsEngine).
      expect(provider.companion.lifetimeXp - xpBefore, equals(5));
    });

    test('detects growth stage change (seed → sprout at 50 XP)', () async {
      // Seed a companion at 45 XP (9 check-ins worth) so one more check-in
      // crosses the 50-XP sprout threshold.
      final seed = Companion(
        level: Companion.levelForXp(45),
        growthStage: Companion.stageForXp(45),
        totalCheckIns: 9,
        totalActiveDays: 0,
        lifetimeXp: 45,
        name: 'Quest',
        mood: CompanionMood.content,
      );
      SharedPreferences.setMockInitialValues({
        'gq.companion.v1': seed.encode(),
      });

      final provider = CompanionProvider();
      await Future.delayed(Duration.zero);
      expect(provider.companion.growthStage, equals(GrowthStage.seed));

      await provider.checkIn();

      expect(provider.companion.lifetimeXp, equals(50));
      expect(provider.companion.growthStage, equals(GrowthStage.sprout));
      expect(provider.leveledUpThisCycle, isTrue);
    });

    test('XP never decrements across many check-ins', () async {
      final provider = CompanionProvider();
      await Future.delayed(Duration.zero);
      int lastXp = provider.companion.lifetimeXp;
      for (int i = 0; i < 20; i++) {
        await provider.checkIn();
        expect(provider.companion.lifetimeXp, greaterThanOrEqualTo(lastXp));
        lastXp = provider.companion.lifetimeXp;
      }
      // 20 check-ins × 5 XP = 100 XP total.
      expect(provider.companion.lifetimeXp, equals(100));
    });

    test('leveledUpThisCycle is set on stage advance and cleared by clearLevelUpFlag()', () async {
      final seed = Companion(
        level: 1,
        growthStage: GrowthStage.seed,
        totalCheckIns: 9,
        totalActiveDays: 0,
        lifetimeXp: 45,
        name: 'Quest',
        mood: CompanionMood.content,
      );
      SharedPreferences.setMockInitialValues({
        'gq.companion.v1': seed.encode(),
      });

      final provider = CompanionProvider();
      await Future.delayed(Duration.zero);
      expect(provider.leveledUpThisCycle, isFalse);

      await provider.checkIn();
      expect(provider.leveledUpThisCycle, isTrue);

      provider.clearLevelUpFlag();
      expect(provider.leveledUpThisCycle, isFalse);
    });

    test('leveledUpThisCycle stays false when no stage advance occurs', () async {
      final provider = CompanionProvider();
      await Future.delayed(Duration.zero);
      await provider.checkIn(); // 0 → 5 XP, still seed.
      expect(provider.leveledUpThisCycle, isFalse);
    });
  });

  group('CompanionProvider.syncTotalActiveDays()', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('updates the active days count when given a larger value', () async {
      final provider = CompanionProvider();
      await Future.delayed(Duration.zero);
      expect(provider.companion.totalActiveDays, equals(0));

      await provider.syncTotalActiveDays(5);
      expect(provider.companion.totalActiveDays, equals(5));

      await provider.syncTotalActiveDays(12);
      expect(provider.companion.totalActiveDays, equals(12));
    });

    test('never decrements the active days count', () async {
      final provider = CompanionProvider();
      await Future.delayed(Duration.zero);
      await provider.syncTotalActiveDays(10);
      expect(provider.companion.totalActiveDays, equals(10));

      // A smaller value is a no-op (the companion never loses progress).
      await provider.syncTotalActiveDays(3);
      expect(provider.companion.totalActiveDays, equals(10));
    });
  });
}
