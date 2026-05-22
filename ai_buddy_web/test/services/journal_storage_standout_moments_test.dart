// Unit tests for JournalStorageReader.standoutMoments — exercises the
// filter logic via an in-memory _StubStorage that implements the abstract
// interface. The real JournalStorage is all-static and doesn't formally
// implement the interface (see journal_storage_reader.dart contract doc);
// these tests cover the contract surface that production callers depend on.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/screens/journal_screen.dart'
    show JournalEntry, JournalMood;
import 'package:ai_buddy_web/services/journal_storage_reader.dart';

void main() {
  group('JournalStorageReader.standoutMoments (via _StubStorage)', () {
    late DateTime monday;
    late DateTimeRange thisWeek;

    setUp(() {
      // Anchor against a real Monday so DateTimeRange semantics match
      // the way Weekly Review constructs its window.
      monday = DateTime(2026, 5, 18); // a Monday
      thisWeek = DateTimeRange(
        start: monday,
        end: monday.add(const Duration(days: 7)),
      );
    });

    test('empty journal returns empty list', () async {
      final s = _StubStorage([]);
      expect(await s.standoutMoments(window: thisWeek), isEmpty);
    });

    test('filters mood below good (rough/meh/okay excluded)', () async {
      final s = _StubStorage([
        _entry(monday.add(const Duration(days: 1)), JournalMood.rough,
            "Walked at lunch even though I didn't want to. Heavy day."),
        _entry(monday.add(const Duration(days: 2)), JournalMood.meh,
            "Got through the meeting. Not much else. Tired by 9."),
        _entry(monday.add(const Duration(days: 3)), JournalMood.okay,
            "Quiet day. The kind that doesn't leave a mark."),
      ]);
      expect(await s.standoutMoments(window: thisWeek), isEmpty);
    });

    test('filters body shorter than 40 chars', () async {
      final s = _StubStorage([
        _entry(monday.add(const Duration(days: 1)), JournalMood.great,
            'Good day.'),
        _entry(monday.add(const Duration(days: 2)), JournalMood.good, 'walked'),
      ]);
      expect(await s.standoutMoments(window: thisWeek), isEmpty);
    });

    test('returns qualifying entries ranked recent-first', () async {
      final tue = _entry(monday.add(const Duration(days: 1)), JournalMood.good,
          "Walked at lunch even though I didn't want to. Said no to a meeting.");
      final wed = _entry(monday.add(const Duration(days: 2)), JournalMood.great,
          "Long call with mom that wasn't tense for the first time in months.");
      final thu = _entry(monday.add(const Duration(days: 3)), JournalMood.good,
          'Slept badly but the morning was quiet. Made tea instead of doom-scrolling.');
      final s = _StubStorage([tue, wed, thu]);

      final picks = await s.standoutMoments(window: thisWeek);
      expect(picks.length, 3);
      expect(picks[0].id, thu.id);
      expect(picks[1].id, wed.id);
      expect(picks[2].id, tue.id);
    });

    test('respects limit parameter', () async {
      final entries = List.generate(5, (i) {
        return _entry(
          monday.add(Duration(days: i + 1)),
          JournalMood.good,
          'Entry ${i + 1} body. Long enough to pass the 40-char floor.',
        );
      });
      final s = _StubStorage(entries);
      final picks = await s.standoutMoments(window: thisWeek, limit: 2);
      expect(picks.length, 2);
    });

    test('excludes entries outside the window', () async {
      final lastWeek = _entry(
          monday.subtract(const Duration(days: 2)),
          JournalMood.great,
          'A week ago — should not surface this week even though it qualifies.');
      final thisOne = _entry(monday.add(const Duration(days: 1)),
          JournalMood.good, 'A few days back, well inside the current week.');
      final s = _StubStorage([lastWeek, thisOne]);

      final picks = await s.standoutMoments(window: thisWeek);
      expect(picks.length, 1);
      expect(picks.first.id, thisOne.id);
    });

    test('window.start is inclusive (boundary)', () async {
      final atStart = _entry(monday, JournalMood.good,
          'Right at the start of the window — should be included per spec.');
      final s = _StubStorage([atStart]);
      expect(
        (await s.standoutMoments(window: thisWeek)).length,
        1,
        reason: 'window.start is inclusive — entries at start should match',
      );
    });
  });
}

JournalEntry _entry(DateTime at, JournalMood mood, String body) {
  return JournalEntry(
    id: 'test-${at.millisecondsSinceEpoch}',
    body: body,
    createdAt: at,
    mood: mood,
    tags: const [],
  );
}

/// Minimal in-memory implementation of JournalStorageReader for unit
/// tests. Exercises standoutMoments() directly against load() without
/// touching SharedPreferences or the network. Test stub duplicates the
/// filter logic — intentional, testing the contract not the
/// implementation. An integration test against the real static
/// JournalStorage.standoutMoments ships in a follow-up after Render
/// env-vars stabilize.
class _StubStorage implements JournalStorageReader {
  _StubStorage(this._entries);

  final List<JournalEntry> _entries;

  @override
  Future<List<JournalEntry>> load() async => List.of(_entries);

  @override
  Future<List<JournalEntry>> standoutMoments({
    required DateTimeRange window,
    int limit = 3,
  }) async {
    final entries = await load();
    final qualifying = entries.where((e) {
      if (e.createdAt.isBefore(window.start)) return false;
      if (e.createdAt.isAfter(window.end)) return false;
      if (e.mood != JournalMood.great && e.mood != JournalMood.good) {
        return false;
      }
      if (e.body.trim().length < 40) return false;
      return true;
    }).toList()
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return qualifying.take(limit).toList();
  }
}
