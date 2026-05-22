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
import 'package:intl/intl.dart';

import '../theme/gq_tokens.dart';
import '../widgets/crisis_resources.dart';
import 'journal_screen.dart' show JournalEntry, openJournalEntry;

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
    return Scaffold(
      backgroundColor: _skyColor(data.state),
      body: SafeArea(
        child: Column(
          children: [
            _NavBar(weekLabel: data.weekLabel, onClose: onDismiss),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
                child: _buildBody(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    return switch (data.state) {
      WeekState.full  => _FullWeekBody(data: data),
      WeekState.light => _LightWeekBody(data: data),
      WeekState.heavy => _HeavyWeekBody(data: data),
    };
  }

  static Color _skyColor(WeekState state) => switch (state) {
        WeekState.full  => const Color(0xFFEEF4FF),
        WeekState.light => const Color(0xFFF4F0FF),
        WeekState.heavy => const Color(0xFFFFF0EE),
      };
}

// ─── Nav bar ─────────────────────────────────────────────────────────────────

class _NavBar extends StatelessWidget {
  const _NavBar({required this.weekLabel, this.onClose});
  final String weekLabel;
  final VoidCallback? onClose;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            weekLabel.toUpperCase(),
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: GQColors.ink3,
              letterSpacing: 1.2,
            ),
          ),
          GestureDetector(
            onTap: onClose ?? () => Navigator.of(context).maybePop(),
            child: Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                border: Border.all(color: GQColors.hair),
              ),
              child: const Icon(Icons.close, size: 14, color: GQColors.ink),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Greeting card ───────────────────────────────────────────────────────────

class _GreetingCard extends StatelessWidget {
  const _GreetingCard({
    required this.eyebrow,
    required this.headline,
    required this.sub,
    required this.gradientColor,
  });

  final String eyebrow;
  final Widget headline;
  final String sub;
  final Color gradientColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withValues(alpha: 0.85),
            Colors.white.withValues(alpha: 0.55),
          ],
        ),
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.hair),
      ),
      child: Stack(
        children: [
          Positioned(
            top: -26,
            right: -18,
            child: Container(
              width: 130,
              height: 130,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  center: const Alignment(-0.4, -0.4),
                  colors: [
                    gradientColor.withValues(alpha: 0.35),
                    gradientColor.withValues(alpha: 0.0),
                  ],
                ),
              ),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                eyebrow,
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink3,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              headline,
              const SizedBox(height: 6),
              Text(
                sub,
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: GQColors.ink2,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─── MoodShapeChart ───────────────────────────────────────────────────────────
// Renders mood as bars by height, NOT a score. Missing days → dashed.
// "Shapes and streaks; never says you were depressed."

class MoodShapeChart extends StatelessWidget {
  const MoodShapeChart({
    super.key,
    required this.days,
    required this.logCount,
  });

  final List<DayMoodEntry> days;
  final int logCount;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.hair),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "THIS WEEK'S MOOD-SHAPE",
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink3,
                  letterSpacing: 1.2,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: GQColors.primarySoft,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  '$logCount / 7 LOGGED',
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 9.5,
                    fontWeight: FontWeight.w800,
                    color: GQColors.primaryDk,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 80,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: days.map((d) => _BarSlot(entry: d)).toList(),
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: days
                .map(
                  (d) => Expanded(
                    child: Center(
                      child: Text(
                        d.label,
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 9.5,
                          fontWeight: d.isToday
                              ? FontWeight.w800
                              : FontWeight.w600,
                          color: d.isToday
                              ? GQColors.primaryDk
                              : GQColors.ink3,
                        ),
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}

class _BarSlot extends StatelessWidget {
  const _BarSlot({required this.entry});
  final DayMoodEntry entry;

  @override
  Widget build(BuildContext context) {
    const maxH = 60.0;
    final idx = entry.moodIndex;
    final barH = idx == null ? 0.0 : (0.2 + idx * 0.2) * maxH;
    final color = idx == null
        ? Colors.transparent
        : GQColors.moodPalette[idx.clamp(0, 4)];

    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 2),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            if (entry.annotation != null)
              Container(
                margin: const EdgeInsets.only(bottom: 3),
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                decoration: BoxDecoration(
                  color: GQColors.ink,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  entry.annotation!,
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 8,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
            if (idx == null)
              SizedBox(
                height: maxH * 0.28,
                child: Center(
                  child: Container(
                    width: double.infinity,
                    height: 1.5,
                    color: GQColors.hair,
                  ),
                ),
              )
            else
              AnimatedContainer(
                duration: GQDurations.fade,
                height: barH,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(5),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ─── NextWeekPromptCard ───────────────────────────────────────────────────────

class NextWeekPromptCard extends StatefulWidget {
  const NextWeekPromptCard({
    super.key,
    required this.chips,
    this.emphasizeRest = false,
  });

  final List<String> chips;
  final bool emphasizeRest;

  @override
  State<NextWeekPromptCard> createState() => _NextWeekPromptCardState();
}

class _NextWeekPromptCardState extends State<NextWeekPromptCard> {
  final Set<int> _selected = {};

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.hair),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.arrow_forward, size: 14, color: GQColors.primaryDk),
              SizedBox(width: 6),
              Text(
                'Try one tiny thing this week?',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (widget.emphasizeRest) ...[
            // .emphasizeRest: "Just rest" is primary, chips are dimmed
            GestureDetector(
              onTap: () => Navigator.of(context).pop(),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: GQColors.primarySoft,
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: GQColors.primary.withValues(alpha: 0.3)),
                ),
                child: const Center(
                  child: Text(
                    'Just rest',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                      color: GQColors.primaryDk,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: List.generate(widget.chips.length, (i) {
                return _Chip(
                  label: widget.chips[i],
                  selected: _selected.contains(i),
                  dimmed: true,
                  onTap: () => setState(() {
                    if (_selected.contains(i)) {
                      _selected.remove(i);
                    } else {
                      _selected.add(i);
                    }
                  }),
                );
              }),
            ),
          ] else ...[
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: List.generate(widget.chips.length, (i) {
                return _Chip(
                  label: widget.chips[i],
                  selected: _selected.contains(i),
                  dimmed: false,
                  onTap: () => setState(() {
                    if (_selected.contains(i)) {
                      _selected.remove(i);
                    } else {
                      _selected.add(i);
                    }
                  }),
                );
              }),
            ),
          ],
          const SizedBox(height: 10),
          Center(
            child: GestureDetector(
              onTap: () => Navigator.of(context).pop(),
              child: const Text(
                "Skip this — I'll figure it out",
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                  color: GQColors.ink3,
                  decoration: TextDecoration.underline,
                  decorationColor: GQColors.ink3,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({
    required this.label,
    required this.selected,
    required this.dimmed,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final bool dimmed;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: GQDurations.fade,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: selected
              ? GQColors.primary
              : dimmed
                  ? GQColors.hair
                  : GQColors.primarySoft,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(
            color: selected
                ? GQColors.primary
                : dimmed
                    ? GQColors.hair
                    : GQColors.primary.withValues(alpha: 0.2),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: selected
                ? Colors.white
                : dimmed
                    ? GQColors.ink3
                    : GQColors.primaryDk,
          ),
        ),
      ),
    );
  }
}

// ─── Standout moment card ─────────────────────────────────────────────────────

class _StandoutMomentCard extends StatelessWidget {
  const _StandoutMomentCard({
    required this.quote,
    required this.attribution,
    this.onTap,
  });

  final String quote;
  final String attribution;

  /// Optional tap handler — when set, the card wraps in InkWell+Material
  /// so it ripples on press. The stub call sites (stubFull/stubLight/
  /// stubHeavy in WeeklyReviewData) don't pass onTap; behavior is
  /// identical to the pre-Chunk-5 card for those paths.
  final VoidCallback? onTap;

  /// Static factory: derive a tap-to-open standout card from a
  /// JournalEntry. Quote is wrapped in matching curly-quotes; attribution
  /// reads "— YOU, MONDAY" (day-of-week uppercased).
  ///
  /// The factory does NOT call JournalStorage.standoutMoments() itself
  /// — that happens at the wire-up site (deferred Chunk 5b). The factory
  /// just constructs the card with derived strings from whichever entry
  /// the wire-up surfaces.
  // ignore: unused_element
  factory _StandoutMomentCard.fromJournal({
    required BuildContext context,
    required JournalEntry entry,
  }) {
    return _StandoutMomentCard(
      quote: '"${entry.body}"',
      attribution:
          '— YOU, ${DateFormat('EEEE').format(entry.createdAt).toUpperCase()}',
      onTap: () => openJournalEntry(context, entry),
    );
  }

  @override
  Widget build(BuildContext context) {
    final card = Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF6FBF2),
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.moodGreat.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.eco_outlined, size: 14, color: GQColors.leafInk),
              SizedBox(width: 6),
              Text(
                'ONE THING WORTH REMEMBERING',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  color: GQColors.leafInk,
                  letterSpacing: 1.1,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            quote,
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13.5,
              fontWeight: FontWeight.w600,
              color: GQColors.ink,
              fontStyle: FontStyle.italic,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            attribution,
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: GQColors.ink3,
              letterSpacing: 0.4,
            ),
          ),
        ],
      ),
    );
    if (onTap == null) return card;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(GQRadii.card),
        child: card,
      ),
    );
  }
}

// ─── Observation + pattern hint card ─────────────────────────────────────────

class _ObservationCard extends StatelessWidget {
  const _ObservationCard({required this.text, this.patternHint});
  final String text;
  final String? patternHint;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.hair),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            text,
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: GQColors.ink2,
              height: 1.5,
              fontStyle: FontStyle.italic,
            ),
          ),
          if (patternHint != null) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                const Icon(Icons.wb_sunny_outlined, size: 11, color: GQColors.primaryDk),
                const SizedBox(width: 5),
                Expanded(
                  child: Text(
                    patternHint!,
                    style: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      color: GQColors.primaryDk,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

// ─── Share with therapist button ──────────────────────────────────────────────

class _ShareWithTherapistBtn extends StatelessWidget {
  const _ShareWithTherapistBtn();

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        // TODO(backend): open mailto with chart PNG — backend_weekly_review_share_missing
      },
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 11),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: GQColors.hair),
        ),
        child: const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.mail_outline, size: 13, color: GQColors.ink2),
            SizedBox(width: 5),
            Text(
              'Share with my therapist',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 12,
                fontWeight: FontWeight.w800,
                color: GQColors.ink2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── State A: Full week ───────────────────────────────────────────────────────

class _FullWeekBody extends StatelessWidget {
  const _FullWeekBody({required this.data});
  final WeeklyReviewData data;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _GreetingCard(
          eyebrow: 'SUNDAY EVENING, FRIEND',
          headline: RichText(
            text: TextSpan(
              style: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 24,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                height: 1.2,
                letterSpacing: -0.6,
              ),
              children: [
                const TextSpan(text: 'You showed up '),
                TextSpan(
                  text: '${data.logCount} times',
                  style: const TextStyle(color: GQColors.primaryDk),
                ),
                const TextSpan(text: ' this week.'),
              ],
            ),
          ),
          sub: 'Quiet wins count.',
          gradientColor: const Color(0xFFD9A678),
        ),
        const SizedBox(height: 14),
        MoodShapeChart(days: data.days, logCount: data.logCount),
        if (data.observationText != null) ...[
          const SizedBox(height: 10),
          _ObservationCard(
            text: data.observationText!,
            patternHint: data.patternHint,
          ),
        ],
        if (data.standoutQuote != null && data.standoutAttribution != null) ...[
          const SizedBox(height: 14),
          _StandoutMomentCard(
            quote: data.standoutQuote!,
            attribution: data.standoutAttribution!,
          ),
        ],
        const SizedBox(height: 14),
        NextWeekPromptCard(chips: data.nextWeekChips),
        const SizedBox(height: 12),
        const _ShareWithTherapistBtn(),
      ],
    );
  }
}

// ─── State B: Light week ──────────────────────────────────────────────────────

class _LightWeekBody extends StatelessWidget {
  const _LightWeekBody({required this.data});
  final WeeklyReviewData data;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _GreetingCard(
          eyebrow: 'SUNDAY EVENING, FRIEND',
          headline: const Text(
            'Light weeks are part of the rhythm.',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
              height: 1.25,
              letterSpacing: -0.5,
            ),
          ),
          sub: 'Rest is a headline option.',
          gradientColor: const Color(0xFFB6A3D9),
        ),
        const SizedBox(height: 14),
        MoodShapeChart(days: data.days, logCount: data.logCount),
        if (data.observationText != null) ...[
          const SizedBox(height: 10),
          _ObservationCard(text: data.observationText!),
        ],
        const SizedBox(height: 14),
        NextWeekPromptCard(chips: data.nextWeekChips, emphasizeRest: true),
        const SizedBox(height: 12),
        const _ShareWithTherapistBtn(),
      ],
    );
  }
}

// ─── State C: Heavy week ──────────────────────────────────────────────────────
// Deliberately removed: no MoodShapeChart, no NextWeekPromptCard, no standout quote.
// Crisis affordance always visible (P6 — crisis never blocks).

class _HeavyWeekBody extends StatelessWidget {
  const _HeavyWeekBody({required this.data});
  final WeeklyReviewData data;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _GreetingCard(
          eyebrow: 'SUNDAY, FRIEND. GLAD YOU\'RE HERE.',
          headline: RichText(
            text: TextSpan(
              style: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                height: 1.25,
                letterSpacing: -0.5,
              ),
              children: [
                const TextSpan(text: 'We had a heavy moment '),
                TextSpan(
                  text: data.heavyEventDay ?? 'this week',
                  style: const TextStyle(color: Color(0xFF9C3D3D)),
                ),
                const TextSpan(text: '.'),
              ],
            ),
          ),
          sub: 'How are you now?',
          gradientColor: GQColors.coral,
        ),
        const SizedBox(height: 14),
        _CalmCheckInRow(),
        const SizedBox(height: 14),
        // P6 — crisis never blocks: always visible, no interstitial
        _CrisisLineRow(context: context),
        const SizedBox(height: 14),
        _WhatHelpedField(),
        const SizedBox(height: 16),
        _OpenChatBtn(),
        const SizedBox(height: 12),
        Center(
          child: GestureDetector(
            onTap: () {
              // TODO(backend): backend_weekly_review_share_missing
            },
            child: const Text(
              'Save this week to share with my therapist',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 12,
                fontWeight: FontWeight.w800,
                color: GQColors.primaryDk,
                decoration: TextDecoration.underline,
                decorationColor: GQColors.primaryDk,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ─── CalmCheckInRow (State C) ─────────────────────────────────────────────────

class _CalmCheckInRow extends StatefulWidget {
  @override
  State<_CalmCheckInRow> createState() => _CalmCheckInRowState();
}

class _CalmCheckInRowState extends State<_CalmCheckInRow> {
  int? _selected;

  static const _faces = [
    _FaceOption(emoji: '😔', label: 'low'),
    _FaceOption(emoji: '😐', label: 'flat'),
    _FaceOption(emoji: '🙂', label: 'okay'),
    _FaceOption(emoji: '🌱', label: 'growing'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.hair),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'A QUIET CHECK-IN',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: GQColors.ink3,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: List.generate(_faces.length, (i) {
              final selected = _selected == i;
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _selected = i),
                  child: AnimatedContainer(
                    duration: GQDurations.fade,
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(
                      color: selected ? GQColors.accentSoft : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: selected
                            ? GQColors.coral.withValues(alpha: 0.4)
                            : GQColors.hair,
                      ),
                    ),
                    child: Column(
                      children: [
                        Text(_faces[i].emoji,
                            style: const TextStyle(fontSize: 22)),
                        const SizedBox(height: 4),
                        Text(
                          _faces[i].label,
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 10.5,
                            fontWeight: FontWeight.w700,
                            color: selected
                                ? GQColors.coral
                                : GQColors.ink3,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}

class _FaceOption {
  const _FaceOption({required this.emoji, required this.label});
  final String emoji;
  final String label;
}

// ─── Crisis line row (P6 — always visible) ────────────────────────────────────

class _CrisisLineRow extends StatelessWidget {
  const _CrisisLineRow({required this.context});
  final BuildContext context;

  @override
  Widget build(BuildContext _) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.coral.withValues(alpha: 0.25)),
      ),
      child: Row(
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              border: Border.all(
                color: const Color(0xFFC44A4A).withValues(alpha: 0.18),
              ),
            ),
            child: const Icon(Icons.phone_outlined,
                size: 15, color: Color(0xFFB33636)),
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Talk to someone now',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink,
                    height: 1.3,
                  ),
                ),
                Text(
                  '988 · always free, always available',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink2,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: () => showCrisisInterventionSheet(context),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFB33636),
                borderRadius: BorderRadius.circular(999),
              ),
              child: const Text(
                'Call 988',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── What's been helping field ────────────────────────────────────────────────

class _WhatHelpedField extends StatefulWidget {
  @override
  State<_WhatHelpedField> createState() => _WhatHelpedFieldState();
}

class _WhatHelpedFieldState extends State<_WhatHelpedField> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.hair),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "WHAT'S BEEN HELPING?",
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: GQColors.ink3,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _controller,
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13,
              color: GQColors.ink,
            ),
            decoration: InputDecoration(
              hintText: 'walking, the bench by the window…',
              hintStyle: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13,
                color: GQColors.ink3,
                fontWeight: FontWeight.w500,
              ),
              suffixText: 'OPTIONAL',
              suffixStyle: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: GQColors.ink3,
                letterSpacing: 0.4,
              ),
              contentPadding: const EdgeInsets.symmetric(
                  horizontal: 13, vertical: 11),
              filled: true,
              fillColor: GQColors.softBg,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: GQColors.hair),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: GQColors.hair),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: GQColors.primary.withValues(alpha: 0.4),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Open chat CTA (State C) ──────────────────────────────────────────────────

class _OpenChatBtn extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        GestureDetector(
          onTap: () => Navigator.of(context).maybePop(),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: GQColors.primary,
              borderRadius: BorderRadius.circular(999),
              boxShadow: [
                BoxShadow(
                  color: GQColors.primary.withValues(alpha: 0.35),
                  blurRadius: 24,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.chat_bubble_outline, size: 14, color: Colors.white),
                SizedBox(width: 6),
                Text(
                  'Open chat with Alex',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 6),
        const Center(
          child: Text(
            'No agenda. Just there if you want.',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: GQColors.ink3,
            ),
          ),
        ),
      ],
    );
  }
}
