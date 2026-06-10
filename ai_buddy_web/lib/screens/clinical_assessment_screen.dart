// clinical_assessment_screen.dart — R1D8 Clinical Assessment
// Design source: docs/design/refs/htmls/GentleQuest_Clinical_Assessment.html
// REVIEW.md tier: R1D8
// Principles: P2 (skip/save), P6 (crisis never blocks), P10, P1
//
// Three surfaces (Mockups A · B · C):
//   A — Mid-flow question (PHQ-9 / GAD-7) with vertical Likert pills + WhyWeAsk
//        (clinical_assessment/assessment_flow_screen.dart)
//   B — Result reveal — reflection over interrogation, no diagnosis language
//        (clinical_assessment/result_reveal_screen.dart)
//   C — Q9 crisis bridge — soft sheet; hands off to CrisisInterventionSheet
//        (clinical_assessment/q9_crisis_bridge.dart)
//
// Q9 bridge approach: Q9CrisisBridge bottom sheet.
//   .imSafe / .heavy → continues assessment
//   .talkNow → hands off to existing CrisisInterventionSheet (source: phq9Q9)
//
// Backend flag: assessment_drafts storage + FirebaseAnalytics integration are
// NOT yet implemented. Partial-draft auto-save is local in-memory only for now.
// Flag: backend_assessment_storage_missing — needs server-side persistence.

import 'package:flutter/material.dart';
import '../theme/gq_tokens.dart';
import 'clinical_assessment/assessment_flow_screen.dart';
import 'clinical_assessment/assessment_models.dart';
import 'clinical_assessment/assessment_widgets.dart';

// Re-export the section libraries so existing `import 'clinical_assessment_screen.dart'`
// consumers (tests, routes) keep seeing the same public symbols as before
// the lib/screens/clinical_assessment/ split.
export 'clinical_assessment/assessment_flow_screen.dart';
export 'clinical_assessment/assessment_models.dart';
export 'clinical_assessment/assessment_question_card.dart';
export 'clinical_assessment/assessment_widgets.dart';
export 'clinical_assessment/q9_crisis_bridge.dart';
export 'clinical_assessment/result_reveal_screen.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Public entry point
// ─────────────────────────────────────────────────────────────────────────────

/// Top-level screen — picks which scale to run (PHQ-9 or GAD-7).
/// Preserves backward-compat for existing routes that push this screen.
class ClinicalAssessmentScreen extends StatelessWidget {
  const ClinicalAssessmentScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: AppBar(
        backgroundColor: GQColors.softBg,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        title: const Text(
          'Check-ins',
          style: TextStyle(
            fontFamily: GQTypography.displayFamily,
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: GQColors.ink,
            letterSpacing: -0.3,
          ),
        ),
        leading: NavBackButton(onTap: () => Navigator.of(context).maybePop()),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header copy — verbatim from HTML design intent
            const Text(
              'How are you, really?',
              style: TextStyle(
                fontFamily: GQTypography.displayFamily,
                fontSize: 24,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'These short check-ins use clinical screening tools to give you a signal — not a verdict.',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13.5,
                fontWeight: FontWeight.w500,
                color: GQColors.ink2,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 24),

            // PHQ-9 card
            _AssessmentEntryCard(
              scale: AssessmentScale.phq9,
              onTap: () => _startAssessment(context, AssessmentScale.phq9),
            ),
            const SizedBox(height: 14),

            // GAD-7 card
            _AssessmentEntryCard(
              scale: AssessmentScale.gad7,
              onTap: () => _startAssessment(context, AssessmentScale.gad7),
            ),

            const SizedBox(height: 28),

            // Disclaimer — verbatim aligned
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: GQColors.primarySoft,
                borderRadius: BorderRadius.circular(GQRadii.card),
                border: Border.all(color: GQColors.primary.withAlpha(38)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    color: GQColors.primaryDk,
                    size: 18,
                  ),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      'PHQ-9 is a clinical screening tool, not a diagnostic instrument.',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                        color: GQColors.ink2,
                        height: 1.5,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _startAssessment(
      BuildContext context, AssessmentScale scale) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AssessmentFlowScreen(scale: scale),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Assessment entry card (home screen)
// ─────────────────────────────────────────────────────────────────────────────

class _AssessmentEntryCard extends StatelessWidget {
  final AssessmentScale scale;
  final VoidCallback onTap;

  const _AssessmentEntryCard({required this.scale, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isPhq9 = scale == AssessmentScale.phq9;
    final bgColor = isPhq9 ? GQColors.primarySoft : GQColors.accentSoft;
    final borderColor = isPhq9
        ? GQColors.primary.withAlpha(51)
        : GQColors.coral.withAlpha(51);
    final accentColor = isPhq9 ? GQColors.primary : GQColors.coral;
    final icon = isPhq9
        ? Icons.sentiment_neutral_rounded
        : Icons.psychology_rounded;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(GQRadii.cardLg),
          border: Border.all(color: borderColor),
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: accentColor.withAlpha(38),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: accentColor, size: 24),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    scale.title,
                    style: TextStyle(
                      fontFamily: GQTypography.displayFamily,
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink,
                      letterSpacing: -0.3,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    scale.subtitle,
                    style: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: GQColors.ink2,
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.arrow_forward_ios_rounded, color: accentColor, size: 16),
          ],
        ),
      ),
    );
  }
}
