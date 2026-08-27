import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../models/message.dart' show RiskLevel;
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/crisis_resources.dart';
import '../../widgets/exercise_card_scaffold.dart';
import '../exercise_scaffold_screen.dart';
import 'assessment_models.dart';
import 'assessment_widgets.dart';

// ─────────────────────────────────────────────────────────────────────────────
// B — Result reveal screen
// "Reflection over interrogation" — no diagnosis language, no raw score first
// ─────────────────────────────────────────────────────────────────────────────

class ResultRevealScreen extends StatelessWidget {
  final AssessmentScale scale;
  final int score;
  final AssessmentSeverity severity;
  final int q9Score;
  final VoidCallback onClose;
  final VoidCallback onChatWithAlex;

  const ResultRevealScreen({
    super.key,
    required this.scale,
    required this.score,
    required this.severity,
    required this.q9Score,
    required this.onClose,
    required this.onChatWithAlex,
  });

  // Severity headline copy — no diagnostic language (from HTML sidebar)
  String get _headline {
    switch (severity) {
      case AssessmentSeverity.minimal:
        return 'Your answers point toward things looking\nsteady this stretch.';
      case AssessmentSeverity.mild:
        return 'Your answers point toward a few signals\nworth noticing.';
      case AssessmentSeverity.moderate:
        // verbatim from HTML mockup B
        return 'Your answers point toward a moderate stretch.';
      case AssessmentSeverity.moderateSevere:
      case AssessmentSeverity.severe:
        return 'Your answers point toward a heavy stretch\n— let\'s go slow.';
    }
  }

  String get _body {
    switch (severity) {
      case AssessmentSeverity.minimal:
        return 'That\'s not a label — just a signal. Keep going.';
      case AssessmentSeverity.mild:
        return 'That\'s not a diagnosis — just signals worth noticing.';
      case AssessmentSeverity.moderate:
        // verbatim from HTML
        return 'That\'s not a diagnosis — just a signal worth taking seriously.';
      case AssessmentSeverity.moderateSevere:
      case AssessmentSeverity.severe:
        return 'That\'s a signal, not a label. You\'re not alone in this.';
    }
  }

  String get _severityLabel {
    switch (severity) {
      case AssessmentSeverity.minimal:
        return 'Minimal';
      case AssessmentSeverity.mild:
        return 'Mild';
      case AssessmentSeverity.moderate:
        return 'Moderate';
      case AssessmentSeverity.moderateSevere:
        return 'Mod-severe';
      case AssessmentSeverity.severe:
        return 'Severe';
    }
  }

  // marker position 0.0 → minimal, 1.0 → severe
  double get _markerPosition {
    final max = scale.maxScore.toDouble();
    return (score / max).clamp(0.0, 1.0);
  }

  bool get _showCrisisAlways =>
      severity == AssessmentSeverity.moderateSevere ||
      severity == AssessmentSeverity.severe ||
      // PHQ-9 Q9 (suicidal ideation) ≥ 1 is a crisis signal regardless of
      // total score — a user with mild total but Q9=2 should still get the
      // crisis resource card, not the "save for therapist" path.
      q9Score >= 1;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final scaleLabel = scale == AssessmentScale.phq9 ? 'PHQ-9' : 'GAD-7';

    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: Column(
          children: [
            // Nav — "Your check-in" (verbatim from HTML B nav)
            Container(
              height: 50,
              padding: const EdgeInsets.symmetric(horizontal: 18),
              decoration: BoxDecoration(
                color: t.bg,
                border: Border(bottom: BorderSide(color: t.hair)),
              ),
              child: Row(
                children: [
                  Text(
                    'Your check-in', // verbatim from HTML mockup B header
                    style: TextStyle(
                      fontFamily: GQTypography.displayFamily,
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: t.ink,
                      letterSpacing: -0.3,
                    ),
                  ),
                  const Spacer(),
                  NavSaveExitButton(onTap: onClose),
                ],
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ── Hero card (result reveal)
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            t.primarySoft,
                            const Color(0xFFF8F1FA),
                            const Color(0xFFFAEEEC),
                          ],
                        ),
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(color: t.hair),
                      ),
                      padding: const EdgeInsets.all(18),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // "A SIGNAL · NOT A LABEL" eyebrow — verbatim
                          Text(
                            'A SIGNAL · NOT A LABEL',
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 10.5,
                              fontWeight: FontWeight.w800,
                              color: t.ink2,
                              letterSpacing: 0.7,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            _headline,
                            style: TextStyle(
                              fontFamily: GQTypography.displayFamily,
                              fontSize: 22,
                              fontWeight: FontWeight.w800,
                              color: t.ink,
                              letterSpacing: -0.5,
                              height: 1.25,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _body,
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 13.5,
                              fontWeight: FontWeight.w600,
                              color: t.ink2,
                              height: 1.5,
                            ),
                          ),

                          const SizedBox(height: 16),

                          // ── Severity band visualization
                          _SeverityBandViz(position: _markerPosition),
                          const SizedBox(height: 8),
                          _SeverityLabels(currentLabel: _severityLabel),

                          const SizedBox(height: 12),
                          // Score — small metadata (not the hero)
                          Text(
                            'SCORE · $score of ${scale.maxScore} · $scaleLabel',
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 11.5,
                              fontWeight: FontWeight.w700,
                              color: t.ink2,
                              letterSpacing: 0.3,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),

                    // ── "Things that often help" section
                    Text(
                      // verbatim from HTML
                      "THINGS THAT OFTEN HELP, WHEN IT'S LIKE THIS",
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w800,
                        color: t.ink2,
                        letterSpacing: 0.7,
                      ),
                    ),
                    const SizedBox(height: 8),

                    // Action 1 — Talk it through with Alex (primary)
                    _ResultActionCard(
                      emoji: '💬',
                      title: 'Talk it through with Alex', // verbatim from HTML
                      subtitle: 'Opens chat with this result as gentle context.',
                      isPrimary: true,
                      onTap: onChatWithAlex,
                    ),
                    const SizedBox(height: 8),

                    // Action 2 — 1-minute breathing
                    _ResultActionCard(
                      emoji: '🌬️',
                      title:
                          'Try a 1-minute breathing exercise', // verbatim from HTML
                      subtitle: '4-7-8 breathing · short and grounding.',
                      isPrimary: false,
                      // R1D16 ExerciseScaffoldScreen is shipped — wiring the
                      // CTA so a user who just completed a PHQ-9/GAD-7 doesn't
                      // get told "coming in the next update" after disclosing
                      // depression symptoms. Stale stub from before R1D16.
                      onTap: () {
                        HapticFeedback.lightImpact();
                        ExerciseScaffoldScreen.show(
                            context, ExerciseType.breathing);
                      },
                    ),
                    const SizedBox(height: 8),

                    // Action 3 — Save for therapist (or crisis card if severe)
                    if (_showCrisisAlways) ...[
                      _ResultActionCard(
                        emoji: '🤝',
                        title: 'Crisis resources are here for you',
                        subtitle: 'Free, confidential, available 24/7.',
                        isPrimary: false,
                        isCoral: true,
                        onTap: () => showCrisisInterventionSheet(
                          context,
                          risk: RiskLevel.high,
                        ),
                      ),
                    ],
                    // FUTURE WORK — "Save this result for your therapist"
                    // action card (verbatim from HTML), with a PDF-export
                    // payload sent to the user's email.
                    //
                    // Removed from the result reveal screen because the
                    // server-side PDF rendering + email handoff isn't built
                    // yet — the previous in-UI "PDF export is coming soon"
                    // SnackBar was a placeholder that promised a feature
                    // that doesn't exist. Re-add the action card once the
                    // backend exists (POST /api/assessment/{id}/export-pdf
                    // → email send). Reference design source for the
                    // copy + iconography:
                    //   docs/design/refs/htmls/GentleQuest_PHQ9_Results.html
                    //
                    //   _ResultActionCard(
                    //     emoji: '📨',
                    //     title: 'Save this result for your therapist',
                    //     subtitle: 'Exports as PDF-ready summary.',
                    //     isPrimary: false,
                    //     onTap: _exportResultPdf, // wire backend first
                    //   ),

                    const SizedBox(height: 16),

                    // Reminder toggle
                    _RemindAgainToggle(),

                    const SizedBox(height: 14),

                    // Crisis always reachable link (verbatim from HTML)
                    Center(
                      child: GestureDetector(
                        onTap: () => showCrisisInterventionSheet(
                          context,
                          risk: RiskLevel.medium,
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              // verbatim from HTML B
                              'Crisis resources are always 1 tap away',
                              style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                color: t.coral,
                                decoration: TextDecoration.underline,
                                decorationColor: t.coral,
                                height: 1.4,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Icon(
                              Icons.arrow_forward_rounded,
                              color: t.coral,
                              size: 14,
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 14),

                    // Disclaimer — uses scaleLabel so GAD-7 results don't
                    // misattribute the disclaimer to PHQ-9.
                    Center(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        child: Text(
                          '$scaleLabel is a clinical screening tool, not a diagnostic instrument.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: t.ink2,
                            height: 1.5,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Severity band visualization (Mockup B)
// ─────────────────────────────────────────────────────────────────────────────

class _SeverityBandViz extends StatelessWidget {
  final double position; // 0.0 → minimal .. 1.0 → severe

  const _SeverityBandViz({required this.position});

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return LayoutBuilder(builder: (context, constraints) {
      final markerOffset =
          (position * (constraints.maxWidth - 28)).clamp(0.0, constraints.maxWidth - 28);
      return SizedBox(
        height: 28,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            // Gradient band
            Positioned(
              left: 0,
              right: 0,
              top: 7,
              child: Container(
                height: 14,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(99),
                  gradient: const LinearGradient(
                    colors: [
                      GQColors.moodOkay,
                      GQColors.moodOkay,
                      GQColors.moodRough,
                      Color(0xFFE89A95),
                      Color(0xFFD87C7C),
                    ],
                  ),
                ),
              ),
            ),
            // Marker
            Positioned(
              left: markerOffset,
              top: 0,
              child: Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: t.surface,
                  border: Border.all(
                    color: GQColors.primaryDk,
                    width: 3,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: t.primary.withAlpha(115),
                      blurRadius: 14,
                      offset: const Offset(0, 6),
                      spreadRadius: -6,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    });
  }
}

class _SeverityLabels extends StatelessWidget {
  final String currentLabel;

  const _SeverityLabels({required this.currentLabel});

  static const _labels = ['Minimal', 'Mild', 'Moderate', 'Mod-severe', 'Severe'];

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Row(
      children: _labels.map((l) {
        final isCurrent = l == currentLabel;
        return Expanded(
          child: Text(
            l,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 9,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.4,
              color: isCurrent ? GQColors.primaryDk : t.ink2,
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Result action card (Mockup B)
// ─────────────────────────────────────────────────────────────────────────────

class _ResultActionCard extends StatelessWidget {
  final String emoji;
  final String title;
  final String subtitle;
  final bool isPrimary;
  final bool isCoral;
  final VoidCallback onTap;

  const _ResultActionCard({
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.isPrimary,
    this.isCoral = false,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    Color bgColor;
    Color borderColor;
    Color titleColor;
    Color subtitleColor;
    Color iconBg;

    if (isPrimary) {
      bgColor = t.primary;
      borderColor = t.primary;
      // White stays literal — painted directly on the primary fill above,
      // same discipline as the primaryDk CTA (contrast travels with the fill).
      titleColor = Colors.white;
      subtitleColor = Colors.white.withAlpha(204);
      iconBg = Colors.white.withAlpha(46);
    } else if (isCoral) {
      bgColor = t.accentSoft;
      borderColor = t.coral.withAlpha(77);
      titleColor = t.ink;
      subtitleColor = t.ink2;
      iconBg = t.coral.withAlpha(46);
    } else {
      bgColor = t.surface;
      borderColor = t.hair;
      titleColor = t.ink;
      subtitleColor = t.ink2;
      iconBg = t.primarySoft;
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: Border.all(color: borderColor),
        ),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: iconBg,
                borderRadius: BorderRadius.circular(11),
              ),
              child: Center(
                child: Text(emoji, style: const TextStyle(fontSize: 18)),
              ),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 13.5,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                      letterSpacing: -0.2,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                      color: subtitleColor,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_rounded,
              color: isPrimary ? Colors.white : t.ink2,
              size: 16,
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// "Take this again in 2 weeks" toggle (Mockup B)
// ─────────────────────────────────────────────────────────────────────────────

class _RemindAgainToggle extends StatefulWidget {
  const _RemindAgainToggle();

  @override
  State<_RemindAgainToggle> createState() => _RemindAgainToggleState();
}

class _RemindAgainToggleState extends State<_RemindAgainToggle> {
  bool _on = false;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: t.hair),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Take this again in 2 weeks', // verbatim from HTML
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: t.ink,
                    letterSpacing: -0.2,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Optional · gentle reminder, no streak math', // verbatim from HTML
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: t.ink2,
                  ),
                ),
              ],
            ),
          ),
          GestureDetector(
            onTap: () => setState(() => _on = !_on),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 36,
              height: 22,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(99),
                color: _on
                    ? t.primary
                    : t.ink3.withAlpha(82), // ~0.32
              ),
              child: Stack(
                children: [
                  AnimatedPositioned(
                    duration: const Duration(milliseconds: 200),
                    left: _on ? 16 : 2,
                    top: 2,
                    child: Container(
                      width: 18,
                      height: 18,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: t.surface,
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x33000000),
                            blurRadius: 3,
                            offset: Offset(0, 1),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
