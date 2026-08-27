import 'package:flutter/material.dart';
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import 'assessment_models.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Question card (Mockup A)
// ─────────────────────────────────────────────────────────────────────────────

class AssessmentQuestionCard extends StatelessWidget {
  final int qIdx;
  final int total;
  final String questionText;
  final bool whyWeAskExpanded;
  final VoidCallback onToggleWhyWeAsk;

  const AssessmentQuestionCard({
    super.key,
    required this.qIdx,
    required this.total,
    required this.questionText,
    required this.whyWeAskExpanded,
    required this.onToggleWhyWeAsk,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      decoration: BoxDecoration(
        // IMG-TINT — soft card wash, raw hex, not a GQColors reference.
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFF4F5FE), Color(0xFFFAF1F1)],
        ),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: t.hair),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // "QUESTION 4 OF 9" — verbatim eyebrow
          Text(
            'QUESTION ${qIdx + 1} OF $total',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10.5,
              fontWeight: FontWeight.w800,
              color: t.ink2,
              letterSpacing: 0.7,
            ),
          ),
          const SizedBox(height: 8),

          // Question text
          Text(
            questionText,
            style: TextStyle(
              fontFamily: GQTypography.displayFamily,
              fontSize: 21,
              fontWeight: FontWeight.w800,
              color: t.ink,
              letterSpacing: -0.5,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 12),

          // "Why we ask" expandable — verbatim label
          GestureDetector(
            onTap: onToggleWhyWeAsk,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: t.primary.withAlpha(26), // 0.10
                borderRadius: BorderRadius.circular(99),
              ),
              // primaryDk stays static — no GQTheme slot (CTA-fill discipline).
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Why we ask', // verbatim from HTML
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w800,
                      color: GQColors.primaryDk,
                    ),
                  ),
                  const SizedBox(width: 4),
                  AnimatedRotation(
                    turns: whyWeAskExpanded ? 0.5 : 0,
                    duration: const Duration(milliseconds: 260),
                    child: const Icon(
                      Icons.keyboard_arrow_down_rounded,
                      color: GQColors.primaryDk,
                      size: 16,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Expandable body — 260ms per spec
          AnimatedCrossFade(
            duration: const Duration(milliseconds: 260),
            crossFadeState: whyWeAskExpanded
                ? CrossFadeState.showFirst
                : CrossFadeState.showSecond,
            firstChild: Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Text(
                'PHQ-9 and GAD-7 are validated screening tools used by clinicians worldwide. '
                'We use them to help you notice patterns — not to label you. '
                'Your answers are private and never shared.',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 12.5,
                  fontWeight: FontWeight.w500,
                  color: t.ink2,
                  height: 1.5,
                ),
              ),
            ),
            secondChild: const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Likert vertical pills (Mockup A)
// ─────────────────────────────────────────────────────────────────────────────

class LikertSelector extends StatelessWidget {
  final int? selected;
  final void Function(int) onSelect;

  const LikertSelector({super.key, required this.selected, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(kLikertLabels.length, (i) {
        final isSelected = selected == i;
        return Padding(
          padding: const EdgeInsets.only(bottom: 9),
          child: _LikertPill(
            index: i,
            label: kLikertLabels[i], // verbatim
            isSelected: isSelected,
            onTap: () => onSelect(i),
          ),
        );
      }),
    );
  }
}

class _LikertPill extends StatelessWidget {
  final int index;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _LikertPill({
    required this.index,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: const Cubic(0.22, 0.94, 0.32, 1),
        constraints: const BoxConstraints(minHeight: 56),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: isSelected ? t.primary : t.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? t.primary : t.hair,
            width: 1.5,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: t.primary.withAlpha(140),
                    blurRadius: 28,
                    offset: const Offset(0, 14),
                    spreadRadius: -12,
                  )
                ]
              : null,
        ),
        child: Row(
          children: [
            // Score number. Colors.white (selected) is the foreground on the
            // t.primary FILL — stays literal, contrast travels with the fill.
            SizedBox(
              width: 14,
              child: Text(
                '$index',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: isSelected
                      ? Colors.white.withAlpha(179)
                      : t.ink2,
                  letterSpacing: 0.4,
                ),
              ),
            ),
            const SizedBox(width: 12),
            // Label — verbatim. Colors.white (selected) stays literal for the
            // same reason as the score number above.
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: isSelected ? Colors.white : t.ink,
                  letterSpacing: -0.2,
                ),
              ),
            ),
            // Check ring. Judgment call: fill+border stay static Colors.white
            // (not t.surface) in the selected branch — this badge exists
            // solely to back the static GQColors.primaryDk checkmark below
            // with a guaranteed-contrast surface, the same CTA-fill
            // discipline applied to a badge instead of a button. Converting
            // the badge to t.surface while the icon stays fixed-value would
            // risk exactly the contrast drift GQTheme's primaryDk exclusion
            // is designed to prevent.
            Container(
              width: 22,
              height: 22,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? Colors.white : Colors.transparent,
                border: Border.all(
                  color: isSelected ? Colors.white : t.ink.withAlpha(41),
                  width: 1.5,
                ),
              ),
              child: isSelected
                  ? const Icon(
                      Icons.check_rounded,
                      color: GQColors.primaryDk,
                      size: 14,
                    )
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}
