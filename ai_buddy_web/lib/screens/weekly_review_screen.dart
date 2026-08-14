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
