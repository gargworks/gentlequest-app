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
import '../widgets/gq/gq.dart';
import 'clinical_assessment/assessment_flow_screen.dart';
import 'clinical_assessment/assessment_models.dart';

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
      appBar: const GQHeader(title: 'Check in'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // WO-5.1 Part C: spec's "current" headline/sub assumed
            // "How are you feeling?" / "Take a validated screening to
            // better understand your mental health." — this screen's
            // actual copy had already moved past that (warmer sub, already
            // non-clinical-cold). Style token swapped to GQType.title per
            // spec; copy left as-is since it already meets the sweep's
            // intent and the spec gave no replacement for this exact text.
            Text('How are you, really?', style: GQTypography.title.copyWith(color: GQColors.ink)),
            const SizedBox(height: 6),
            Text(
              'These short check-ins use clinical screening tools to give you a signal — not a verdict.',
              style: GQTypography.body.copyWith(color: GQColors.ink2),
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

            // Disclaimer — legally load-bearing, copy unchanged (WO-5.1 Part C).
            const GQBanner(
              category: GQBannerCategory.info,
              message: 'PHQ-9 is a clinical screening tool, not a diagnostic instrument.',
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

  // WO-5.1 Part C: spec's replacement copy ("How the last two weeks have
  // felt" / "How worry has been sitting") assumed the current subtitle was
  // "Depression Screening" / "Anxiety Screening" — it's actually already
  // "Depression screener · clinical-grade · ~2 min" (not clinical-cold, but
  // not the warm register either). Applying the spec's intended warm
  // subtitle, and keeping the scale name + time estimate as the small
  // caption underneath per the spec's own "stays clinically identifiable"
  // instruction, rather than dropping that info to force a literal match.
  String get _warmSubtitle => scale == AssessmentScale.phq9
      ? 'How the last two weeks have felt'
      : 'How worry has been sitting';

  String get _clinicalCaption =>
      scale == AssessmentScale.phq9 ? 'PHQ-9 · ~2 min' : 'GAD-7 · ~2 min';

  @override
  Widget build(BuildContext context) {
    final isPhq9 = scale == AssessmentScale.phq9;
    final iconTile = isPhq9 ? GQColors.primarySoft : GQColors.moodOkay.withValues(alpha: 0.18);
    final accentColor = isPhq9 ? GQColors.primaryDk : GQColors.coralDk;
    final icon = isPhq9
        ? Icons.sentiment_neutral_rounded
        : Icons.psychology_rounded;

    return GQCard(
      large: true,
      onTap: onTap,
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(color: iconTile, shape: BoxShape.circle),
            child: Icon(icon, color: accentColor, size: 24),
          ),
          const SizedBox(width: GQSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_warmSubtitle, style: GQTypography.titleSm.copyWith(fontSize: 16, color: GQColors.ink)),
                const SizedBox(height: GQSpacing.xs),
                Text(_clinicalCaption, style: GQTypography.micro.copyWith(color: GQColors.ink2)),
              ],
            ),
          ),
          Icon(Icons.arrow_forward_ios_rounded, color: accentColor, size: 16),
        ],
      ),
    );
  }
}
