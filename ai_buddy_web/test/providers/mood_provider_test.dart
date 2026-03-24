import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';

void main() {
  group('MoodProvider', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('initial state is empty and not loading', () {
      final provider = MoodProvider(eagerLoad: false);
      expect(provider.moodEntries, isEmpty);
      expect(provider.isLoading, isFalse);
      expect(provider.error, isNull);
      expect(provider.averageMood, equals(0));
    });

    test('pendingQueueLength starts at 0', () {
      final provider = MoodProvider(eagerLoad: false);
      expect(provider.pendingQueueLength, equals(0));
    });

    test('pulse data starts null', () {
      final provider = MoodProvider(eagerLoad: false);
      expect(provider.latestPulse, isNull);
      expect(provider.lastMoodLevel, isNull);
    });

    test('clearPulse resets pulse data', () {
      final provider = MoodProvider(eagerLoad: false);
      provider.clearPulse();
      expect(provider.latestPulse, isNull);
      expect(provider.lastMoodLevel, isNull);
    });

    test('getMoodEntriesForDate returns empty for no entries', () {
      final provider = MoodProvider(eagerLoad: false);
      final entries = provider.getMoodEntriesForDate(DateTime.now());
      expect(entries, isEmpty);
    });

    test('moodEntriesByDate returns empty map for no entries', () {
      final provider = MoodProvider(eagerLoad: false);
      expect(provider.moodEntriesByDate, isEmpty);
    });
  });
}
