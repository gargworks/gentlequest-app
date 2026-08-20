import 'package:flutter/material.dart';
import '../../theme/gq_tokens.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Nav bar — title + segmented progress + back/close
// ─────────────────────────────────────────────────────────────────────────────

class AssessmentNavBar extends StatelessWidget {
  final String title;
  final int filled;
  final int total;
  final VoidCallback? onBack;
  final VoidCallback onClose;

  const AssessmentNavBar({
    super.key,
    required this.title,
    required this.filled,
    required this.total,
    this.onBack,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 50,
      padding: const EdgeInsets.symmetric(horizontal: 18),
      decoration: BoxDecoration(
        color: GQColors.softBg.withAlpha(217),
        border: const Border(
          bottom: BorderSide(color: GQColors.hair),
        ),
      ),
      child: Row(
        children: [
          NavBackButton(
            onTap: onBack ?? () => Navigator.of(context).maybePop(),
          ),
          const SizedBox(width: 10),
          Text(
            title,
            style: const TextStyle(
              fontFamily: GQTypography.displayFamily,
              fontSize: 14.5,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
              letterSpacing: -0.3,
            ),
          ),
          const SizedBox(width: 8),
          // Segmented progress bar
          Expanded(
            child: _AssessmentProgressBar(filled: filled, total: total),
          ),
          const SizedBox(width: 4),
          NavSaveExitButton(onTap: onClose),
        ],
      ),
    );
  }
}

class NavBackButton extends StatelessWidget {
  final VoidCallback? onTap;
  const NavBackButton({super.key, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 30,
        height: 30,
        decoration: BoxDecoration(
          color: Colors.white,
          shape: BoxShape.circle,
          border: Border.all(color: GQColors.hair),
        ),
        child: const Icon(
          Icons.chevron_left_rounded,
          color: GQColors.ink,
          size: 20,
        ),
      ),
    );
  }
}

/// Top-right "Save & exit" text button in the assessment nav bar.
/// Replaces the ambiguous × icon so the affordance is visible above-the-fold
/// (UC-CA3 fix — synthetic QA 2026-06-12: users couldn't see the exit path).
/// NOTE: progress is held in memory only for this session; cross-restart
/// persistence is a follow-up (backend_assessment_storage_missing).
class NavSaveExitButton extends StatelessWidget {
  final VoidCallback onTap;
  const NavSaveExitButton({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
        child: Text(
          'Save & exit',
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: GQColors.primary,
            decoration: TextDecoration.underline,
            decorationColor: GQColors.primary,
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Segmented progress bar
// ─────────────────────────────────────────────────────────────────────────────

class _AssessmentProgressBar extends StatelessWidget {
  final int filled;
  final int total;

  const _AssessmentProgressBar({required this.filled, required this.total});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(total, (i) {
        // i < filled-1 → fully filled; i == filled-1 → current; i >= filled → empty
        final isCurrent = i == filled - 1;
        final isFilled = i < filled;
        return Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 2),
            height: 5,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(99),
              color: isFilled
                  ? GQColors.primary
                  : GQColors.ink.withAlpha(26), // ~0.10
              boxShadow: isCurrent
                  ? [
                      BoxShadow(
                        color: GQColors.primary.withAlpha(90),
                        blurRadius: 4,
                        spreadRadius: 1,
                      )
                    ]
                  : null,
            ),
          ),
        );
      }),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Pill buttons (Back / Next)
// ─────────────────────────────────────────────────────────────────────────────

enum PillButtonStyle { primary, ghost }

class PillButton extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;
  final PillButtonStyle style;

  const PillButton({
    super.key,
    required this.label,
    required this.onTap,
    required this.style,
  });

  @override
  Widget build(BuildContext context) {
    final isPrimary = style == PillButtonStyle.primary;
    return GestureDetector(
      onTap: onTap,
      child: Opacity(
        opacity: onTap == null ? 0.4 : 1.0,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
          decoration: BoxDecoration(
            color: isPrimary ? GQColors.primary : Colors.white,
            borderRadius: BorderRadius.circular(GQRadii.button),
            border: isPrimary ? null : Border.all(color: GQColors.hair),
            boxShadow: isPrimary
                ? [
                    BoxShadow(
                      color: GQColors.primary.withAlpha(140),
                      blurRadius: 26,
                      offset: const Offset(0, 12),
                      spreadRadius: -10,
                    )
                  ]
                : null,
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13.5,
                fontWeight: FontWeight.w800,
                color: isPrimary ? Colors.white : GQColors.ink2,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// "Save & exit · we'll keep your spot" — verbatim copy
// ─────────────────────────────────────────────────────────────────────────────

class SaveAndExitLink extends StatelessWidget {
  final VoidCallback onTap;
  const SaveAndExitLink({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: const Text(
        "Save & exit · we'll keep your spot", // verbatim from HTML
        style: TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 11.5,
          fontWeight: FontWeight.w800,
          color: GQColors.ink2,
          decoration: TextDecoration.underline,
          decorationColor: GQColors.ink2,
          decorationStyle: TextDecorationStyle.solid,
          height: 1.4,
        ),
      ),
    );
  }
}
