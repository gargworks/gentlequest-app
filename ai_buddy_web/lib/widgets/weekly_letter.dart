// weekly_letter.dart — Anti-Dashboard: Weekly Review as Letter
//
// Replaces the chart/blob/count dashboard with a prose letter compiled from
// WeeklyReviewData. The letter is second person, past tense, opens with
// "Dear you," in Fraunces serif, and signs "— with you, Quest & Alex".
//
// Voice rules (enforced in _LetterComposer):
//   • Second person, past tense
//   • At most one quoted count per letter
//   • No adjectives about the user (hard days are hard; user is never "resilient")
//   • Every negative sentence followed by its "anyway" if one exists in data
//   • The letter never asks a question
//   • XP never prints — growth narrated, not measured
//
// Design source: Fable-level spec — Anti-Dashboard.

import 'package:flutter/material.dart';

import '../screens/weekly_review_screen.dart' show WeeklyReviewData, DayMoodEntry;
import '../theme/gq_tokens.dart';
import 'companion_painter.dart';
import 'companion_widget.dart' show CompanionWidget;
import 'letter_fragment_picker.dart';
import '../models/companion.dart' show GrowthStage;

/// Renders the weekly review as a prose letter.
///
/// Pass [data] (a [WeeklyReviewData]). The letter is compiled by
/// [_LetterComposer] from the data fields; the widget only handles layout,
/// typography, the highlight underline, and the action buttons.
class WeeklyLetter extends StatelessWidget {
  const WeeklyLetter({
    super.key,
    required this.data,
    this.onClose,
  });

  final WeeklyReviewData data;
  final VoidCallback? onClose;

  @override
  Widget build(BuildContext context) {
    final composer = _LetterComposer(data);
    final isEmpty = data.days.isEmpty && data.logCount == 0;

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _WeekLabel(label: data.weekLabel),
          const SizedBox(height: 18),
          _DearYouHeader(),
          const SizedBox(height: 14),
          _LetterBody(composer: composer),
          const SizedBox(height: 18),
          if (isEmpty)
            Center(
              child: Column(
                children: [
                  const _BreathingCompanion(),
                  const SizedBox(height: 10),
                  const Text(
                    'Sapling · 34 active days · unchanged',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: GQColors.ink2,
                    ),
                  ),
                ],
              ),
            )
          else
            _Signature(companion: CompanionWidget()),
          const SizedBox(height: 22),
          _LetterButtons(isEmpty: isEmpty, onKeep: () => _openPicker(context), onNotNow: onClose ?? () => Navigator.of(context).maybePop()),
        ],
      ),
    );
  }

  void _openPicker(BuildContext context) {
    final composer = _LetterComposer(data);
    final sentences = composer.shareableSentences();
    if (sentences.isEmpty) return;
    showLetterFragmentPicker(context, sentences: sentences, weekLabel: data.weekLabel);
  }
}

// ─── Week label ──────────────────────────────────────────────────────────────

class _WeekLabel extends StatelessWidget {
  const _WeekLabel({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    // Spec: 'YOUR WEEK · MAY 6 – 12' — 10px, w700, ink3, uppercase, 1.4px tracking
    final display = label.toUpperCase();
    return Text(
      'YOUR WEEK · $display',
      style: const TextStyle(
        fontFamily: GQTypography.bodyFamily,
        fontSize: 10,
        fontWeight: FontWeight.w700,
        color: GQColors.ink2,
        letterSpacing: 1.4,
      ),
    );
  }
}

// ─── "Dear you," header ──────────────────────────────────────────────────────

class _DearYouHeader extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // Fraunces, 27px, w500, -0.3px tracking
    return const Text(
      'Dear you,',
      style: TextStyle(
        fontFamily: GQTypography.journalSerif,
        fontSize: 27,
        fontWeight: FontWeight.w500,
        color: GQColors.ink,
        letterSpacing: -0.3,
        height: 1.2,
      ),
    );
  }
}

// ─── Letter body ─────────────────────────────────────────────────────────────

class _LetterBody extends StatelessWidget {
  const _LetterBody({required this.composer});
  final _LetterComposer composer;

  @override
  Widget build(BuildContext context) {
    final paragraphs = composer.paragraphs();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < paragraphs.length; i++) ...[
          _Paragraph(
            spans: paragraphs[i].spans,
          ),
          if (i < paragraphs.length - 1) const SizedBox(height: 12),
        ],
      ],
    );
  }
}

/// One paragraph of the letter. [spans] is the rich-text content.
class _Paragraph extends StatelessWidget {
  const _Paragraph({required this.spans});
  final List<InlineSpan> spans;

  @override
  Widget build(BuildContext context) {
    // Letter body: Fraunces serif, 16.5px, line-height 1.75, GQColors.ink
    const baseStyle = TextStyle(
      fontFamily: GQTypography.journalSerif,
      fontSize: 16.5,
      height: 1.75,
      color: GQColors.ink,
    );
    const boldStyle = TextStyle(
      fontFamily: GQTypography.journalSerif,
      fontSize: 16.5,
      height: 1.75,
      color: GQColors.ink,
      fontWeight: FontWeight.w600,
    );

    return RichText(
      text: TextSpan(
        style: baseStyle,
        children: spans.map((s) {
          if (s is TextSpan && s.style?.fontWeight == FontWeight.w600) {
            return TextSpan(text: s.text, style: boldStyle);
          }
          return s;
        }).toList(),
      ),
    );
  }
}

// ─── Breathing companion (empty-week state) ──────────────────────────────────

/// 84px companion with a breathing ScaleTransition, shown in the empty-week
/// state. Renders a CustomPaint with CompanionPainter (simplified: false)
/// at 84px, centered, breathing.
class _BreathingCompanion extends StatefulWidget {
  const _BreathingCompanion();

  @override
  State<_BreathingCompanion> createState() => _BreathingCompanionState();
}

class _BreathingCompanionState extends State<_BreathingCompanion>
    with SingleTickerProviderStateMixin {
  late final AnimationController _breatheController;
  late final Animation<double> _breatheAnimation;
  bool _reduceMotion = false;
  // The first didChangeDependencies pass must ALWAYS apply, even when rm
  // equals the initial `false`. Without this the equality guard below
  // early-returns on first mount and the animation is never started at
  // all — the failure is invisible to tests because nothing asserts that
  // a perpetual animation is actually running.
  bool _motionGateInitialised = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // ADR-006: respect quiet-mode reduced motion.
    final rm = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (_motionGateInitialised && rm == _reduceMotion) return;
    _motionGateInitialised = true;
    _reduceMotion = rm;
    if (rm) {
      _breatheController.stop();
    } else {
      _breatheController.repeat(reverse: true);
    }
  }

  @override
  void initState() {
    super.initState();
    _breatheController = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    );
    _breatheAnimation = Tween<double>(begin: 1.0, end: 1.035).animate(
      CurvedAnimation(parent: _breatheController, curve: Curves.easeInOut),
    );
    _breatheController.value = 0.5;
  }

  @override
  void dispose() {
    _breatheController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _breatheAnimation,
      child: CustomPaint(
        size: const Size.square(84),
        painter: const CompanionPainter(
          stage: GrowthStage.sapling,
          simplified: false,
        ),
      ),
    );
  }
}

// ─── Signature ───────────────────────────────────────────────────────────────

class _Signature extends StatelessWidget {
  const _Signature({required this.companion});
  final Widget companion;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Text(
            '— with you, Quest & Alex',
            style: TextStyle(
              fontFamily: GQTypography.journalSerif,
              fontSize: 15,
              height: 1.5,
              color: GQColors.ink2,
              fontStyle: FontStyle.italic,
            ),
          ),
        ),
        const SizedBox(width: 12),
        SizedBox(width: 48, height: 48, child: companion),
      ],
    );
  }
}

// ─── Buttons ─────────────────────────────────────────────────────────────────

class _LetterButtons extends StatelessWidget {
  const _LetterButtons({
    required this.isEmpty,
    required this.onKeep,
    required this.onNotNow,
  });

  final bool isEmpty;
  final VoidCallback onKeep;
  final VoidCallback onNotNow;

  @override
  Widget build(BuildContext context) {
    if (isEmpty) {
      // Empty week: only 'Close' button
      return _LetterButton(
        label: 'Close',
        primary: true,
        onTap: onNotNow,
      );
    }
    return Column(
      children: [
        _LetterButton(
          label: 'Keep a line from this',
          primary: true,
          onTap: onKeep,
        ),
        const SizedBox(height: 10),
        _LetterButton(
          label: 'Not now',
          primary: false,
          onTap: onNotNow,
        ),
      ],
    );
  }
}

class _LetterButton extends StatelessWidget {
  const _LetterButton({
    required this.label,
    required this.primary,
    required this.onTap,
  });

  final String label;
  final bool primary;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    // 13.5px w700, stadium, 44px min height
    return GestureDetector(
      onTap: onTap,
      child: Container(
        constraints: const BoxConstraints(minHeight: 44),
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 12),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: primary ? GQColors.primary : Colors.white,
          borderRadius: BorderRadius.circular(GQRadii.button),
          border: primary ? null : Border.all(color: GQColors.hair),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 13.5,
            fontWeight: FontWeight.w700,
            color: primary ? Colors.white : GQColors.ink2,
          ),
        ),
      ),
    );
  }
}

// ─── Letter composer — data → prose ──────────────────────────────────────────

/// A single paragraph of the letter, with rich-text spans and an optional
/// highlight sentence (the "anyway" that gets the underline background).
class _LetterParagraph {
  const _LetterParagraph(this.spans);
  final List<InlineSpan> spans;
}

/// Compiles [WeeklyReviewData] into letter paragraphs following the voice rules.
///
/// The composer is pure: same data in → same letter out. This makes it
/// testable without a widget tree.
class _LetterComposer {
  _LetterComposer(this.data);

  final WeeklyReviewData data;

  // Small word-number map for the "at most one quoted count" rule.
  static const _numberWords = [
    'zero', 'one', 'two', 'three', 'four', 'five',
    'six', 'seven', 'eight', 'nine', 'ten',
  ];

  String _spell(int n) =>
      (n >= 0 && n < _numberWords.length) ? _numberWords[n] : '$n';

  List<_LetterParagraph> paragraphs() {
    // Empty week — Frame B path.
    if (data.days.isEmpty && data.logCount == 0) {
      return _emptyWeekParagraphs();
    }

    final paras = <_LetterParagraph>[];
    final usedCount = <bool>[false]; // at most one quoted count

    // ── Paragraph 1: the heavy day (if any) ──
    final heavy = _heavyDaySentence(usedCount);
    if (heavy != null) {
      paras.add(heavy);
    }

    // ── Paragraph 2: adversity + small act + consequence ──
    final adversity = _adversityParagraph(usedCount);
    if (adversity != null) {
      paras.add(adversity);
    }

    // ── Paragraph 3: trigger chip frequency ──
    final trigger = _triggerParagraph(usedCount);
    if (trigger != null) {
      paras.add(trigger);
    }

    // ── Paragraph 4: standout quote (bold, mid-letter) ──
    if (data.standoutQuote != null && data.standoutQuote!.isNotEmpty) {
      paras.add(_standoutParagraph());
    }

    // ── Paragraph 5: check-in count + XP (narrated, not measured) ──
    final checkin = _checkinParagraph(usedCount);
    if (checkin != null) {
      paras.add(checkin);
    }

    // ── Final paragraph: next week asks for nothing ──
    paras.add(_nextWeekParagraph());

    return paras;
  }

  // ── Empty week (Frame B) ──
  List<_LetterParagraph> _emptyWeekParagraphs() {
    return [
      _LetterParagraph([
        const TextSpan(
          text:
              "No entries this week. That's not a gap — you were living, and that counts.",
        ),
      ]),
    ];
  }

  // ── Heavy day sentence ──
  _LetterParagraph? _heavyDaySentence(List<bool> usedCount) {
    if (data.heavyEventDay == null || data.heavyEventDay!.isEmpty) return null;
    final day = data.heavyEventDay!;
    // Find that day's moodIndex if present.
    final dayEntry = data.days.firstWhere(
      (d) => d.label.toLowerCase() == day.toLowerCase().substring(0, 3),
      orElse: () => const DayMoodEntry(label: ''),
    );
    final isLow = dayEntry.moodIndex != null && dayEntry.moodIndex! <= 1;

    String text;
    if (isLow) {
      text = '$day was hard.';
    } else {
      text = '$day was hard.';
    }

    // Midnight honesty clause: if the entry's timestamp is after 11 PM.
    // We don't have a timestamp field on DayMoodEntry; the spec says "if
    // timestamp after 11 PM". Since the model lacks a timestamp, we skip
    // this clause rather than fabricate one. (Honest accounting: the data
    // shape doesn't carry it.)
    return _LetterParagraph([TextSpan(text: text)]);
  }

  // ── Adversity + small act + consequence ──
  // OMITTED: the previous implementation invented "You walked at lunch
  // anyway. That mattered." regardless of the user's actual data. The
  // data model carries no real "anyway" act, so this paragraph is never
  // emitted. Do not reinvent a replacement sentence — putting words in
  // the user's mouth is the worst defect in a mental-health app.
  _LetterParagraph? _adversityParagraph(List<bool> usedCount) {
    return null;
  }

  // ── Trigger chip frequency ──
  // OMITTED: the previous implementation hardcoded "Work pressed on you
  // …" — a trigger the user may never have tagged. The data model carries
  // no real recurring-trigger label, so this paragraph is never emitted.
  // Do not reinvent a replacement sentence.
  _LetterParagraph? _triggerParagraph(List<bool> usedCount) {
    return null;
  }

  // ── Standout quote (bold, mid-letter) ──
  _LetterParagraph _standoutParagraph() {
    final quote = data.standoutQuote!;
    return _LetterParagraph([
      TextSpan(
        text: quote,
        style: const TextStyle(fontWeight: FontWeight.w600),
      ),
    ]);
  }

  // ── Check-in count + XP (narrated) ──
  _LetterParagraph? _checkinParagraph(List<bool> usedCount) {
    if (data.logCount <= 0) return null;
    final countWord = _spell(data.logCount);
    // XP never prints — growth narrated.
    final text =
        'You checked in $countWord ${data.logCount == 1 ? 'time' : 'times'}. Quest grew a little on each of those days. Nothing shrank on the others.';
    if (!usedCount[0]) usedCount[0] = true;
    return _LetterParagraph([TextSpan(text: text)]);
  }

  // ── Next week: one concrete callback, zero goals ──
  _LetterParagraph _nextWeekParagraph() {
    // If nextWeekChips is non-empty, use the first as a concrete callback.
    // Otherwise: "Next week asks for nothing."
    if (data.nextWeekChips.isNotEmpty) {
      final chip = data.nextWeekChips.first;
      return _LetterParagraph([
        TextSpan(text: 'Next week asks for nothing. $chip, if it comes up.'),
      ]);
    }
    return const _LetterParagraph([
      TextSpan(text: 'Next week asks for nothing.'),
    ]);
  }

  /// Returns 2-3 sentences from the letter suitable for the fragment picker.
  /// Picks the most "shareable" sentences: the standout quote (if present),
  /// the check-in narration, and the next-week callback.
  List<String> shareableSentences() {
    final out = <String>[];
    if (data.standoutQuote != null && data.standoutQuote!.isNotEmpty) {
      out.add(data.standoutQuote!);
    }
    final checkin = _checkinParagraph([false]);
    if (checkin != null) {
      final text = checkin.spans
          .whereType<TextSpan>()
          .map((s) => s.text ?? '')
          .join();
      if (text.isNotEmpty) out.add(text);
    }
    final next = _nextWeekParagraph();
    final nextText =
        next.spans.whereType<TextSpan>().map((s) => s.text ?? '').join();
    if (nextText.isNotEmpty) out.add(nextText);
    // De-dup and cap at 3.
    return out.toSet().toList().take(3).toList();
  }
}
