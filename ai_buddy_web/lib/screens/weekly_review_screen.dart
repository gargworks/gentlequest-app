// weekly_review_screen.dart — R1D15 Weekly Review
// Design source: docs/design/refs/htmls/GentleQuest_Weekly_Review.html
// REVIEW.md tier: R1D15
// Principles: P-reflection (mood shapes; never diagnoses), P6 (crisis never blocks),
//             coral-not-red, numbers-as-recognition, .withValues not .withOpacity
//
// Three WeekState variants (A · B · C):
//   A — full  : 4–7 logs  → MoodShapeChart + StandoutMomentCard + NextWeekPromptCard
//   B — light : 1–3 logs  → MoodShapeChart (dashed gaps) + NextWeekPromptCard(.emphasizeRest)
//   C — heavy : post-crisis → CalmCheckInRow + CrisisLineRow + WhatHelpedField; NO chart/chips
//
// Data stub: WeeklyReviewData is constructed with static sample values.
//   Backend flag: backend_weekly_review_aggregation_missing — real aggregation (mood logs,
//   journal standout, pattern detector) must be wired via server-side weekly digest payload.
//   The WeekState.heavy flag is also server-decided (crisisFlag from this week).

import 'package:flutter/material.dart';

import '../models/mood_entry.dart';
import 'weekly_letter_screen.dart';

// ─── Data models ─────────────────────────────────────────────────────────────

enum WeekState { full, light, heavy }

/// One day slot for MoodShapeChart.
/// [moodIndex] 0–4 (null = not logged). [annotation] optional inline label.
class DayMoodEntry {
  const DayMoodEntry({
    required this.label,
    this.moodIndex,
    this.annotation,
    this.isToday = false,
  });
  final String label;
  final int? moodIndex; // null → dashed / missing
  final String? annotation; // e.g. "LIFTED"
  final bool isToday;
}

/// Stub weekly data supplied to WeeklyReviewScreen.
/// BACKEND FLAG: backend_weekly_review_aggregation_missing
class WeeklyReviewData {
  const WeeklyReviewData({
    required this.state,
    required this.weekLabel,
    required this.logCount,
    required this.days,
    this.observationText,
    this.patternHint,
    this.standoutQuote,
    this.standoutAttribution,
    this.nextWeekChips = const [],
    this.heavyEventDay,
  });

  final WeekState state;
  final String weekLabel;
  final int logCount;
  final List<DayMoodEntry> days; // must be length 7 (Mon–Sun)
  final String? observationText;
  final String? patternHint;
  final String? standoutQuote;
  final String? standoutAttribution;
  final List<String> nextWeekChips;
  final String? heavyEventDay; // e.g. "Wednesday" — used in heavy greeting

  /// Builds weekly review data from the user's ACTUAL mood entries for the
  /// current week (Monday–Sunday). No fabricated text: days with no entry
  /// stay unlogged (moodIndex null), standoutQuote is sourced from a real
  /// user note (or null), and no invented assertions are emitted.
  factory WeeklyReviewData.fromMoodEntries(List<MoodEntry> entries) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final monday = today.subtract(Duration(days: today.weekday - 1));
    final sunday = monday.add(const Duration(days: 6));

    // Filter to this week's entries (local time).
    final weekEntries = entries.where((e) {
      final d = e.timestamp.toLocal();
      final day = DateTime(d.year, d.month, d.day);
      return !day.isBefore(monday) && !day.isAfter(sunday);
    }).toList();

    final logCount = weekEntries.length;

    // Empty week → degrade to the kind empty-week path (days: []).
    if (logCount == 0) {
      return WeeklyReviewData(
        state: WeekState.light,
        weekLabel: _weekLabel(monday, sunday),
        logCount: 0,
        days: const [],
      );
    }

    // Build 7 day slots (Mon–Sun) from real entries.
    const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    final days = <DayMoodEntry>[];
    for (var i = 0; i < 7; i++) {
      final date = monday.add(Duration(days: i));
      final dayEntries = entries.where((e) {
        final d = e.timestamp.toLocal();
        return d.year == date.year &&
            d.month == date.month &&
            d.day == date.day;
      }).toList()
        ..sort((a, b) => a.timestamp.compareTo(b.timestamp));
      final isToday = date.year == today.year &&
          date.month == today.month &&
          date.day == today.day;
      if (dayEntries.isEmpty) {
        days.add(DayMoodEntry(label: dayLabels[i], isToday: isToday));
      } else {
        final last = dayEntries.last;
        days.add(DayMoodEntry(
          label: dayLabels[i],
          moodIndex: last.moodLevel - 1, // 1-5 → 0-4
          isToday: isToday,
        ));
      }
    }

    // Standout quote: the most recent entry with a non-empty note.
    // Real user text only; degrades to null when absent.
    String? standoutQuote;
    String? standoutAttribution;
    final withNotes = weekEntries
        .where((e) => e.note != null && e.note!.trim().isNotEmpty)
        .toList()
      ..sort((a, b) => a.timestamp.compareTo(b.timestamp));
    if (withNotes.isNotEmpty) {
      final e = withNotes.last;
      standoutQuote = '"${e.note!.trim()}"';
      const wdNames = [
        '', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY',
        'FRIDAY', 'SATURDAY', 'SUNDAY'
      ];
      standoutAttribution = '— YOU, ${wdNames[e.timestamp.toLocal().weekday]}';
    }

    final state = logCount >= 4 ? WeekState.full : WeekState.light;

    return WeeklyReviewData(
      state: state,
      weekLabel: _weekLabel(monday, sunday),
      logCount: logCount,
      days: days,
      standoutQuote: standoutQuote,
      standoutAttribution: standoutAttribution,
    );
  }

  static String _weekLabel(DateTime monday, DateTime sunday) {
    const months = [
      '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    if (monday.month == sunday.month) {
      return 'Week of ${months[monday.month]} ${monday.day} – ${sunday.day}';
    }
    return 'Week of ${months[monday.month]} ${monday.day} – '
        '${months[sunday.month]} ${sunday.day}';
  }

  @visibleForTesting
  static WeeklyReviewData stubFull() => const WeeklyReviewData(
        state: WeekState.full,
        weekLabel: 'Week of Mar 18 – 24',
        logCount: 5,
        days: [
          DayMoodEntry(label: 'Mon', moodIndex: 1),
          DayMoodEntry(label: 'Tue', moodIndex: 2),
          DayMoodEntry(label: 'Wed', moodIndex: 4, annotation: 'LIFTED'),
          DayMoodEntry(label: 'Thu', moodIndex: 2),
          DayMoodEntry(label: 'Fri', moodIndex: 0),
          DayMoodEntry(label: 'Sat'), // not logged
          DayMoodEntry(label: 'Sun', moodIndex: 3, isToday: true),
        ],
        observationText:
            'Wednesday lifted you up. Friday felt heavy. The arc was real, and you stayed with it.',
        patternHint: 'A pattern · you felt better after journaling on 3 days',
        standoutQuote:
            '"walked for 20 mins, said no to a meeting, slept by 10."',
        standoutAttribution: '— YOU, TUESDAY',
        nextWeekChips: [
          'Log mood at lunch',
          'Try 1 minute of breathing',
          'Write 3 words on Sunday',
        ],
      );

  static WeeklyReviewData stubLight() => const WeeklyReviewData(
        state: WeekState.light,
        weekLabel: 'Week of Mar 11 – 17',
        logCount: 2,
        days: [
          DayMoodEntry(label: 'Mon'),
          DayMoodEntry(label: 'Tue', moodIndex: 2),
          DayMoodEntry(label: 'Wed'),
          DayMoodEntry(label: 'Thu'),
          DayMoodEntry(label: 'Fri', moodIndex: 1),
          DayMoodEntry(label: 'Sat'),
          DayMoodEntry(label: 'Sun', isToday: true),
        ],
        observationText:
            'Two data points isn\'t much. Want to use this week to log a few more, or just rest?',
        nextWeekChips: ['Log mood at lunch'],
      );

  static WeeklyReviewData stubHeavy() => const WeeklyReviewData(
        state: WeekState.heavy,
        weekLabel: 'Week of Mar 4 – 10',
        logCount: 4,
        days: [],
        heavyEventDay: 'Wednesday',
      );
}

// ─── Screen entry point ──────────────────────────────────────────────────────

class WeeklyReviewScreen extends StatelessWidget {
  const WeeklyReviewScreen({
    super.key,
    required this.data,
    this.onDismiss,
  });

  final WeeklyReviewData data;
  final VoidCallback? onDismiss;

  @override
  Widget build(BuildContext context) {
    // Anti-Dashboard: the weekly review is now a prose letter, not a
    // chart/blob/count dashboard. Route to WeeklyLetterScreen which hosts
    // the WeeklyLetter widget. The data models (WeekState, DayMoodEntry,
    // WeeklyReviewData) remain in this file as the shared shape.
    return WeeklyLetterScreen(data: data, onDismiss: onDismiss);
  }
}
