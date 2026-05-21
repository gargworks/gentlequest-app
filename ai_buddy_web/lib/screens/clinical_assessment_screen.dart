// clinical_assessment_screen.dart — R1D8 Clinical Assessment
// Design source: docs/design/refs/htmls/GentleQuest_Clinical_Assessment.html
// REVIEW.md tier: R1D8
// Principles: P2 (skip/save), P6 (crisis never blocks), P10, P1
//
// Three surfaces (Mockups A · B · C):
//   A — Mid-flow question (PHQ-9 / GAD-7) with vertical Likert pills + WhyWeAsk
//   B — Result reveal — reflection over interrogation, no diagnosis language
//   C — Q9 crisis bridge — soft sheet; hands off to CrisisInterventionSheet
//
// Q9 bridge approach: Q9CrisisBridge bottom sheet.
//   .imSafe / .heavy → continues assessment
//   .talkNow → hands off to existing CrisisInterventionSheet (source: phq9Q9)
//
// Backend flag: assessment_drafts storage + FirebaseAnalytics integration are
// NOT yet implemented. Partial-draft auto-save is local in-memory only for now.
// Flag: backend_assessment_storage_missing — needs server-side persistence.

import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/message.dart' show RiskLevel;
import '../navigation/home_tab_deeplink.dart';
import '../providers/assessment_provider.dart';
import '../theme/gq_tokens.dart';
import '../widgets/app_bottom_nav.dart' show AppTab;
import '../widgets/crisis_resources.dart';
import '../widgets/exercise_card_scaffold.dart';
import 'exercise_scaffold_screen.dart';

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
        leading: _NavBackButton(onTap: () => Navigator.of(context).maybePop()),
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
        builder: (_) => _AssessmentFlowScreen(scale: scale),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Assessment scale + question bank
// ─────────────────────────────────────────────────────────────────────────────

enum AssessmentScale { phq9, gad7 }

enum AssessmentSeverity { minimal, mild, moderate, moderateSevere, severe }

extension AssessmentScaleX on AssessmentScale {
  String get title => this == AssessmentScale.phq9 ? 'PHQ-9 Check-in' : 'GAD-7 Check-in';
  String get subtitle => this == AssessmentScale.phq9
      ? 'Depression screener · clinical-grade · ~2 min'
      : 'Anxiety screener · clinical-grade · ~2 min';
  int get totalQuestions => this == AssessmentScale.phq9 ? 9 : 7;
  int get maxScore => totalQuestions * 3;
}

/// Standard 4-option Likert response labels (verbatim from HTML).
const _kLikertLabels = [
  'Not at all',
  'Several days',
  'More than half the days',
  'Nearly every day',
];

/// PHQ-9 question bank — verbatim from html + clinical spec.
const _kPhq9Questions = [
  'Little interest or pleasure in doing things.',
  'Feeling down, depressed, or hopeless.',
  'Trouble falling or staying asleep, or sleeping too much.',
  // Q4 verbatim from HTML mockup A:
  'Over the last 2 weeks, how often have you felt tired or had little energy?',
  'Poor appetite or overeating.',
  'Feeling bad about yourself — or that you are a failure or have let yourself or your family down.',
  'Trouble concentrating on things, such as reading the newspaper or watching television.',
  'Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual.',
  // Q9 — suicidality question, verbatim from HTML mockup C:
  'Thoughts that you would be better off dead, or of hurting yourself.',
];

/// GAD-7 question bank.
const _kGad7Questions = [
  'Feeling nervous, anxious, or on edge.',
  'Not being able to stop or control worrying.',
  'Worrying too much about different things.',
  'Trouble relaxing.',
  'Being so restless that it is hard to sit still.',
  'Becoming easily annoyed or irritable.',
  'Feeling afraid, as if something awful might happen.',
];

/// Compute severity band from PHQ-9 score (0–27).
AssessmentSeverity _phq9Severity(int score) {
  if (score <= 4) return AssessmentSeverity.minimal;
  if (score <= 9) return AssessmentSeverity.mild;
  if (score <= 14) return AssessmentSeverity.moderate;
  if (score <= 19) return AssessmentSeverity.moderateSevere;
  return AssessmentSeverity.severe;
}

/// Compute severity band from GAD-7 score (0–21).
AssessmentSeverity _gad7Severity(int score) {
  if (score <= 4) return AssessmentSeverity.minimal;
  if (score <= 9) return AssessmentSeverity.mild;
  if (score <= 14) return AssessmentSeverity.moderate;
  return AssessmentSeverity.severe;
}

// ─────────────────────────────────────────────────────────────────────────────
// A — Assessment flow screen
// ─────────────────────────────────────────────────────────────────────────────

class _AssessmentFlowScreen extends StatefulWidget {
  final AssessmentScale scale;
  const _AssessmentFlowScreen({required this.scale});

  @override
  State<_AssessmentFlowScreen> createState() => _AssessmentFlowScreenState();
}

class _AssessmentFlowScreenState extends State<_AssessmentFlowScreen>
    with SingleTickerProviderStateMixin {
  int _qIdx = 0;
  // responses: null = unanswered/skipped, int = selected value (0–3)
  late final List<int?> _responses;
  bool _whyWeAskExpanded = false;
  bool _showResult = false;
  bool _q9BridgePending = false;

  // Animation for question card transition
  late final AnimationController _slideCtrl;
  late final Animation<Offset> _slideAnim;
  late final Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    final total = widget.scale.totalQuestions;
    _responses = List.filled(total, null);

    _slideCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 320),
    );
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.06),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _slideCtrl, curve: Curves.easeOut));
    _fadeAnim = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _slideCtrl, curve: Curves.easeOut),
    );
    _slideCtrl.forward();
  }

  @override
  void dispose() {
    _slideCtrl.dispose();
    super.dispose();
  }

  List<String> get _questions => widget.scale == AssessmentScale.phq9
      ? _kPhq9Questions
      : _kGad7Questions;

  int get _totalQ => _questions.length;

  int get _totalScore =>
      _responses.whereType<int>().fold(0, (sum, v) => sum + v);

  AssessmentSeverity get _severity => widget.scale == AssessmentScale.phq9
      ? _phq9Severity(_totalScore)
      : _gad7Severity(_totalScore);

  // Returns true if Q9 (PHQ-9 only, index 8) score ≥ 1
  bool get _q9Triggered =>
      widget.scale == AssessmentScale.phq9 &&
      _qIdx == 8 &&
      (_responses[8] ?? 0) >= 1;

  void _selectOption(int value) {
    HapticFeedback.lightImpact();
    setState(() {
      _responses[_qIdx] = value;
    });
    // Auto-advance after 300ms (per spec)
    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) _advance();
    });
  }

  void _advance() {
    // Check Q9 bridge condition before advancing
    if (_q9Triggered && !_q9BridgePending) {
      _openQ9Bridge();
      return;
    }
    if (_qIdx < _totalQ - 1) {
      _animateToQuestion(_qIdx + 1);
    } else {
      _submitToBackend();
      setState(() => _showResult = true);
    }
  }

  /// Send the completed assessment to /api/assessment via the provider.
  /// Fire-and-forget; surface failure via provider.error → SnackBar on the
  /// result reveal screen. Without this, the user's PHQ-9/GAD-7 responses
  /// were computed locally + dropped — no row, no follow-up, no audit
  /// trail.
  void _submitToBackend() {
    final responses = _responses
        .whereType<int>()
        .toList(growable: false);
    if (responses.length != _totalQ) return;
    // ignore: unawaited_futures
    context.read<AssessmentProvider>().submitAssessment(
          assessmentType: widget.scale == AssessmentScale.phq9 ? 'phq9' : 'gad7',
          responses: responses,
        );
  }

  void _animateToQuestion(int newIdx) {
    _slideCtrl.reset();
    setState(() {
      _qIdx = newIdx;
      _whyWeAskExpanded = false;
      _q9BridgePending = false;
    });
    _slideCtrl.forward();
  }

  void _openQ9Bridge() {
    setState(() => _q9BridgePending = true);
    showModalBottomSheet<_BridgeAction>(
      context: context,
      isDismissible: false,
      enableDrag: false,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: GQColors.ink.withAlpha(82), // ~0.32 per spec
      builder: (_) => const _Q9CrisisBridgeSheet(),
    ).then((action) {
      if (!mounted) return;
      switch (action) {
        case _BridgeAction.imSafe:
        case _BridgeAction.heavy:
          // Continue past Q9 → result (it's the last question)
          if (_qIdx < _totalQ - 1) {
            _animateToQuestion(_qIdx + 1);
          } else {
            _submitToBackend();
            setState(() => _showResult = true);
          }
          if (action == _BridgeAction.heavy) {
            // The user just signaled "this is heavy — check on me later".
            // Backend persistence (POST /api/follow-up) isn't built yet,
            // but silently dropping a self-harm-adjacent commitment is
            // the wrong fail mode (per feedback_silent_skip_paths). Stamp
            // a local timestamp so QA + the next session can at least
            // see the request landed; queue can be drained later.
            SharedPreferences.getInstance().then((prefs) async {
              final ts = DateTime.now().toIso8601String();
              final list = prefs.getStringList('follow_up_24h_pending') ?? [];
              list.add(ts);
              await prefs.setStringList('follow_up_24h_pending', list);
              if (kDebugMode) {
                debugPrint('[follow-up] 24h flag queued @ $ts');
              }
            });
          }
        case _BridgeAction.talkNow:
          // Hand off to existing CrisisInterventionSheet (R1D9)
          showCrisisInterventionSheet(context, risk: RiskLevel.high);
        case null:
          // Sheet closed without explicit choice (system back gesture on
          // Android, etc.). The user just signaled Q9 ≥ 1 — silently
          // advancing past a self-harm signal is the worst possible
          // failure mode. Re-open the bridge so the user must pick.
          _openQ9Bridge();
      }
    });
  }

  void _saveAndExit() {
    // [backend_assessment_storage_missing] — partial draft saved only in memory.
    // Synthetic UX QA UC-CA3: confirm to the user the action registered before
    // popping, so the exit doesn't feel like a silent drop. Show snackbar
    // BEFORE pop so it surfaces on the parent route's messenger (otherwise
    // the popped Scaffold's messenger has already been deactivated).
    HapticFeedback.lightImpact();
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    messenger.showSnackBar(
      SnackBar(
        content: const Text(
          'Progress saved · resume anytime from the Mood tab',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
        ),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 3),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GQRadii.card),
        ),
        backgroundColor: GQColors.ink2,
      ),
    );
    nav.maybePop();
  }

  @override
  Widget build(BuildContext context) {
    if (_showResult) {
      return _ResultRevealScreen(
        scale: widget.scale,
        score: _totalScore,
        severity: _severity,
        q9Score: widget.scale == AssessmentScale.phq9
            ? (_responses[8] ?? 0)
            : 0,
        onClose: () => Navigator.of(context).pop(),
        onChatWithAlex: () {
          // Pop the assessment screen, then switch to the Talk tab so
          // the user lands in chat with Alex. Subtitle promises this
          // ("Opens chat with this result as gentle context"); previously
          // just popped to nowhere, leaving the user stranded at the
          // most fragile post-disclosure moment.
          Navigator.of(context).pop();
          homeTabDeepLink.value = AppTab.talk;
        },
      );
    }

    final question = _questions[_qIdx];
    final selected = _responses[_qIdx];
    final progressFilled = _qIdx + 1; // current segment index (1-based filled)

    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: Column(
          children: [
            // ── Nav bar (Mockup A)
            _AssessmentNavBar(
              title: widget.scale.title, // verbatim: "PHQ-9 Check-in"
              filled: progressFilled,
              total: _totalQ,
              onBack: _qIdx > 0 ? () => _animateToQuestion(_qIdx - 1) : null,
              onClose: _saveAndExit,
            ),

            // ── Scrollable content
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Subtitle — verbatim: "Depression screener · clinical-grade · ~2 min"
                    Center(
                      child: Text(
                        widget.scale.subtitle,
                        style: const TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: GQColors.ink2,
                          letterSpacing: 0.4,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // ── Question card (Mockup A)
                    SlideTransition(
                      position: _slideAnim,
                      child: FadeTransition(
                        opacity: _fadeAnim,
                        child: _AssessmentQuestionCard(
                          qIdx: _qIdx,
                          total: _totalQ,
                          questionText: question,
                          whyWeAskExpanded: _whyWeAskExpanded,
                          onToggleWhyWeAsk: () => setState(
                              () => _whyWeAskExpanded = !_whyWeAskExpanded),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // ── Likert pills
                    _LikertSelector(
                      selected: selected,
                      onSelect: _selectOption,
                    ),

                    const SizedBox(height: 20),

                    // ── Back / Next row
                    Row(
                      children: [
                        if (_qIdx > 0) ...[
                          _PillButton(
                            label: 'Back',
                            onTap: () => _animateToQuestion(_qIdx - 1),
                            style: _PillButtonStyle.ghost,
                          ),
                          const SizedBox(width: 10),
                        ],
                        Expanded(
                          child: _PillButton(
                            label: 'Next',
                            onTap: selected != null ? _advance : null,
                            style: _PillButtonStyle.primary,
                          ),
                        ),
                      ],
                    ),

                    // ── "Save & exit · we'll keep your spot" — verbatim
                    const SizedBox(height: 10),
                    Center(
                      child: _SaveAndExitLink(onTap: _saveAndExit),
                    ),

                    const SizedBox(height: 14),
                    // Privacy note
                    const Center(
                      child: Text(
                        'Your answers stay private. We don\'t share results.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 10.5,
                          fontWeight: FontWeight.w600,
                          color: GQColors.ink3,
                          height: 1.5,
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
// Nav bar — title + segmented progress + back/close
// ─────────────────────────────────────────────────────────────────────────────

class _AssessmentNavBar extends StatelessWidget {
  final String title;
  final int filled;
  final int total;
  final VoidCallback? onBack;
  final VoidCallback onClose;

  const _AssessmentNavBar({
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
          _NavBackButton(
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
          const SizedBox(width: 8),
          _NavCloseButton(onTap: onClose),
        ],
      ),
    );
  }
}

class _NavBackButton extends StatelessWidget {
  final VoidCallback? onTap;
  const _NavBackButton({this.onTap});

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

class _NavCloseButton extends StatelessWidget {
  final VoidCallback onTap;
  const _NavCloseButton({required this.onTap});

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
          Icons.close_rounded,
          color: GQColors.ink,
          size: 16,
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
// Question card (Mockup A)
// ─────────────────────────────────────────────────────────────────────────────

class _AssessmentQuestionCard extends StatelessWidget {
  final int qIdx;
  final int total;
  final String questionText;
  final bool whyWeAskExpanded;
  final VoidCallback onToggleWhyWeAsk;

  const _AssessmentQuestionCard({
    required this.qIdx,
    required this.total,
    required this.questionText,
    required this.whyWeAskExpanded,
    required this.onToggleWhyWeAsk,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFF4F5FE), Color(0xFFFAF1F1)],
        ),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: GQColors.hair),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // "QUESTION 4 OF 9" — verbatim eyebrow
          Text(
            'QUESTION ${qIdx + 1} OF $total',
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10.5,
              fontWeight: FontWeight.w800,
              color: GQColors.ink3,
              letterSpacing: 0.7,
            ),
          ),
          const SizedBox(height: 8),

          // Question text
          Text(
            questionText,
            style: const TextStyle(
              fontFamily: GQTypography.displayFamily,
              fontSize: 21,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
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
                color: GQColors.primary.withAlpha(26), // 0.10
                borderRadius: BorderRadius.circular(99),
              ),
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
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 12.5,
                  fontWeight: FontWeight.w500,
                  color: GQColors.ink2,
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

class _LikertSelector extends StatelessWidget {
  final int? selected;
  final void Function(int) onSelect;

  const _LikertSelector({required this.selected, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(_kLikertLabels.length, (i) {
        final isSelected = selected == i;
        return Padding(
          padding: const EdgeInsets.only(bottom: 9),
          child: _LikertPill(
            index: i,
            label: _kLikertLabels[i], // verbatim
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
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: const Cubic(0.22, 0.94, 0.32, 1),
        constraints: const BoxConstraints(minHeight: 56),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: isSelected ? GQColors.primary : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? GQColors.primary : GQColors.hair,
            width: 1.5,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: GQColors.primary.withAlpha(140),
                    blurRadius: 28,
                    offset: const Offset(0, 14),
                    spreadRadius: -12,
                  )
                ]
              : null,
        ),
        child: Row(
          children: [
            // Score number
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
                      : GQColors.ink3,
                  letterSpacing: 0.4,
                ),
              ),
            ),
            const SizedBox(width: 12),
            // Label — verbatim
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: isSelected ? Colors.white : GQColors.ink,
                  letterSpacing: -0.2,
                ),
              ),
            ),
            // Check ring
            Container(
              width: 22,
              height: 22,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? Colors.white : Colors.transparent,
                border: Border.all(
                  color: isSelected ? Colors.white : GQColors.ink.withAlpha(41),
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

// ─────────────────────────────────────────────────────────────────────────────
// Pill buttons (Back / Next)
// ─────────────────────────────────────────────────────────────────────────────

enum _PillButtonStyle { primary, ghost }

class _PillButton extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;
  final _PillButtonStyle style;

  const _PillButton({
    required this.label,
    required this.onTap,
    required this.style,
  });

  @override
  Widget build(BuildContext context) {
    final isPrimary = style == _PillButtonStyle.primary;
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

class _SaveAndExitLink extends StatelessWidget {
  final VoidCallback onTap;
  const _SaveAndExitLink({required this.onTap});

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
          color: GQColors.ink3,
          decoration: TextDecoration.underline,
          decorationColor: GQColors.ink3,
          decorationStyle: TextDecorationStyle.solid,
          height: 1.4,
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// B — Result reveal screen
// "Reflection over interrogation" — no diagnosis language, no raw score first
// ─────────────────────────────────────────────────────────────────────────────

class _ResultRevealScreen extends StatelessWidget {
  final AssessmentScale scale;
  final int score;
  final AssessmentSeverity severity;
  final int q9Score;
  final VoidCallback onClose;
  final VoidCallback onChatWithAlex;

  const _ResultRevealScreen({
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
    final scaleLabel = scale == AssessmentScale.phq9 ? 'PHQ-9' : 'GAD-7';

    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: Column(
          children: [
            // Nav — "Your check-in" (verbatim from HTML B nav)
            Container(
              height: 50,
              padding: const EdgeInsets.symmetric(horizontal: 18),
              decoration: const BoxDecoration(
                color: GQColors.softBg,
                border: Border(bottom: BorderSide(color: GQColors.hair)),
              ),
              child: Row(
                children: [
                  const Text(
                    'Your check-in', // verbatim from HTML mockup B header
                    style: TextStyle(
                      fontFamily: GQTypography.displayFamily,
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink,
                      letterSpacing: -0.3,
                    ),
                  ),
                  const Spacer(),
                  _NavCloseButton(onTap: onClose),
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
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            Color(0xFFEEF0FE),
                            Color(0xFFF8F1FA),
                            Color(0xFFFAEEEC),
                          ],
                        ),
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(color: GQColors.hair),
                      ),
                      padding: const EdgeInsets.all(18),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // "A SIGNAL · NOT A LABEL" eyebrow — verbatim
                          const Text(
                            'A SIGNAL · NOT A LABEL',
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 10.5,
                              fontWeight: FontWeight.w800,
                              color: GQColors.ink3,
                              letterSpacing: 0.7,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            _headline,
                            style: const TextStyle(
                              fontFamily: GQTypography.displayFamily,
                              fontSize: 22,
                              fontWeight: FontWeight.w800,
                              color: GQColors.ink,
                              letterSpacing: -0.5,
                              height: 1.25,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _body,
                            style: const TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 13.5,
                              fontWeight: FontWeight.w600,
                              color: GQColors.ink2,
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
                            style: const TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 11.5,
                              fontWeight: FontWeight.w700,
                              color: GQColors.ink3,
                              letterSpacing: 0.3,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),

                    // ── "Things that often help" section
                    const Text(
                      // verbatim from HTML
                      "THINGS THAT OFTEN HELP, WHEN IT'S LIKE THIS",
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink3,
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
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              // verbatim from HTML B
                              'Crisis resources are always 1 tap away',
                              style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                color: Color(0xFFB33636),
                                decoration: TextDecoration.underline,
                                decorationColor: Color(0xFFB33636),
                                height: 1.4,
                              ),
                            ),
                            SizedBox(width: 4),
                            Icon(
                              Icons.arrow_forward_rounded,
                              color: Color(0xFFB33636),
                              size: 14,
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 14),

                    // Disclaimer — verbatim from HTML
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.symmetric(horizontal: 8),
                        child: Text(
                          'PHQ-9 is a clinical screening tool, not a diagnostic instrument.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: GQColors.ink3,
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
                      Color(0xFFBFD3FF),
                      Color(0xFFC9B7F0),
                      Color(0xFFC49AD9),
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
                  color: Colors.white,
                  border: Border.all(
                    color: GQColors.primaryDk,
                    width: 3,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: GQColors.primary.withAlpha(115),
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
              color: isCurrent ? GQColors.primaryDk : GQColors.ink3,
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
    Color bgColor;
    Color borderColor;
    Color titleColor;
    Color subtitleColor;
    Color iconBg;

    if (isPrimary) {
      bgColor = GQColors.primary;
      borderColor = GQColors.primary;
      titleColor = Colors.white;
      subtitleColor = Colors.white.withAlpha(204);
      iconBg = Colors.white.withAlpha(46);
    } else if (isCoral) {
      bgColor = GQColors.accentSoft;
      borderColor = GQColors.coral.withAlpha(77);
      titleColor = GQColors.ink;
      subtitleColor = GQColors.ink2;
      iconBg = GQColors.coral.withAlpha(46);
    } else {
      bgColor = Colors.white;
      borderColor = GQColors.hair;
      titleColor = GQColors.ink;
      subtitleColor = GQColors.ink2;
      iconBg = GQColors.primarySoft;
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
              color: isPrimary ? Colors.white : GQColors.ink2,
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
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: GQColors.hair),
      ),
      child: Row(
        children: [
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Take this again in 2 weeks', // verbatim from HTML
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink,
                    letterSpacing: -0.2,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Optional · gentle reminder, no streak math', // verbatim from HTML
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink3,
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
                    ? GQColors.primary
                    : GQColors.ink3.withAlpha(82), // ~0.32
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
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white,
                        boxShadow: [
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

// ─────────────────────────────────────────────────────────────────────────────
// C — Q9 crisis bridge sheet
// Soft pre-step; does NOT duplicate CrisisInterventionSheet.
// .talkNow branches to existing CrisisInterventionSheet from crisis_resources.dart
// ─────────────────────────────────────────────────────────────────────────────

enum _BridgeAction { imSafe, talkNow, heavy }

class _Q9CrisisBridgeSheet extends StatefulWidget {
  const _Q9CrisisBridgeSheet();

  @override
  State<_Q9CrisisBridgeSheet> createState() => _Q9CrisisBridgeSheetState();
}

class _Q9CrisisBridgeSheetState extends State<_Q9CrisisBridgeSheet>
    with SingleTickerProviderStateMixin {
  // Cupped-hands animation: 3.4s ease-in-out ±2px Y (per HTML spec)
  late final AnimationController _handsCtrl;
  late final Animation<double> _handsY;

  @override
  void initState() {
    super.initState();
    _handsCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3400),
    )..repeat(reverse: true);
    _handsY = Tween<double>(begin: 0, end: -2).animate(
      CurvedAnimation(parent: _handsCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _handsCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(28),
        ),
        boxShadow: [
          BoxShadow(
            color: Color(0x59000000),
            blurRadius: 50,
            offset: Offset(0, -22),
            spreadRadius: -12,
          )
        ],
      ),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 22),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Drag handle
          Container(
            width: 42,
            height: 4,
            decoration: BoxDecoration(
              color: GQColors.ink.withAlpha(46),
              borderRadius: BorderRadius.circular(99),
            ),
          ),
          const SizedBox(height: 12),

          // Animated cupped-hands icon
          AnimatedBuilder(
            animation: _handsY,
            builder: (context, child) {
              return Transform.translate(
                offset: Offset(0, _handsY.value),
                child: child,
              );
            },
            child: Container(
              width: 54,
              height: 54,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFFFFF1E5), GQColors.accentSoft],
                ),
              ),
              child: const Icon(
                Icons.pan_tool_alt_rounded,
                color: GQColors.coral,
                size: 26,
              ),
            ),
          ),
          const SizedBox(height: 10),

          // "A QUIET PAUSE" eyebrow — verbatim
          const Text(
            'A QUIET PAUSE',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10.5,
              fontWeight: FontWeight.w800,
              color: GQColors.ink3,
              letterSpacing: 0.7,
            ),
          ),
          const SizedBox(height: 4),

          // Headline — verbatim from HTML
          const Text(
            'Thank you for being honest with that one.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: GQTypography.displayFamily,
              fontSize: 21,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
              letterSpacing: -0.5,
              height: 1.25,
            ),
          ),
          const SizedBox(height: 8),

          // Body — verbatim from HTML
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 6),
            child: Text(
              'What you said matters. Before we keep going — are you safe right now?',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: GQColors.ink2,
                height: 1.5,
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Option 1 — I'm safe (green)
          _BridgeOptionCard(
            iconEmoji: '✓',
            iconBg: GQColors.moodGreat.withAlpha(46),
            iconColor: const Color(0xFF5C7A48),
            title: "I'm safe — let's continue the check-in", // verbatim from HTML
            subtitle: 'Returns to the assessment, no judgement',
            style: _BridgeCardStyle.green,
            onTap: () {
              HapticFeedback.lightImpact();
              Navigator.of(context).pop(_BridgeAction.imSafe);
            },
          ),
          const SizedBox(height: 8),

          // Option 2 — Talk now (primary)
          _BridgeOptionCard(
            iconEmoji: '💬',
            iconBg: Colors.white.withAlpha(51),
            iconColor: Colors.white,
            title: 'I want to talk to someone now', // verbatim from HTML
            subtitle: 'Pauses this. Opens crisis support sheet.',
            style: _BridgeCardStyle.primary,
            onTap: () {
              HapticFeedback.lightImpact();
              Navigator.of(context).pop(_BridgeAction.talkNow);
            },
          ),
          const SizedBox(height: 8),

          // Option 3 — Just having a heavy moment (coral)
          _BridgeOptionCard(
            iconEmoji: '🤍',
            iconBg: GQColors.coral.withAlpha(46),
            iconColor: const Color(0xFFB33636),
            title: 'Just having a heavy moment', // verbatim from HTML
            subtitle: 'Continue. We\'ll check in tomorrow.',
            style: _BridgeCardStyle.coral,
            onTap: () {
              HapticFeedback.lightImpact();
              Navigator.of(context).pop(_BridgeAction.heavy);
            },
          ),

          const SizedBox(height: 14),

          // 988 always-present deeplink
          GestureDetector(
            onTap: () => _launchUri988(context),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 11),
              decoration: BoxDecoration(
                color: const Color(0xFFFFEBEB), // rgba(196,74,74,0.08) approx
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0x33C44A4A)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.phone_rounded,
                    color: Color(0xFFB33636),
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  const Text(
                    'Call 988 now · always tap-ready', // verbatim from HTML
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 12.5,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFFB33636),
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

Future<void> _launchUri988(BuildContext context) async {
  final messenger = ScaffoldMessenger.maybeOf(context);
  final uri = Uri.parse('tel:988');
  try {
    final launched = await canLaunchUrl(uri) &&
        await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (launched) return;
  } catch (_) {
    // fall through
  }
  await Clipboard.setData(const ClipboardData(text: '988'));
  messenger?.showSnackBar(
    const SnackBar(content: Text('988 copied to clipboard')),
  );
}

enum _BridgeCardStyle { green, primary, coral }

class _BridgeOptionCard extends StatelessWidget {
  final String iconEmoji;
  final Color iconBg;
  final Color iconColor;
  final String title;
  final String subtitle;
  final _BridgeCardStyle style;
  final VoidCallback onTap;

  const _BridgeOptionCard({
    required this.iconEmoji,
    required this.iconBg,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.style,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    Color borderColor;
    Color titleColor;
    Color subtitleColor;

    switch (style) {
      case _BridgeCardStyle.green:
        bgColor = GQColors.moodGreat.withAlpha(26); // rgba(156,196,135,0.10)
        borderColor = GQColors.moodGreat.withAlpha(77); // rgba(156,196,135,0.30)
        titleColor = GQColors.ink;
        subtitleColor = GQColors.ink2;
      case _BridgeCardStyle.primary:
        bgColor = GQColors.primary;
        borderColor = GQColors.primary;
        titleColor = Colors.white;
        subtitleColor = Colors.white.withAlpha(217);
      case _BridgeCardStyle.coral:
        bgColor = GQColors.coral.withAlpha(31); // gradient approx
        borderColor = GQColors.coral.withAlpha(77);
        titleColor = GQColors.ink;
        subtitleColor = GQColors.ink2;
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: borderColor),
        ),
        child: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: iconBg,
                borderRadius: BorderRadius.circular(11),
              ),
              child: Center(
                child: Text(
                  iconEmoji,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: iconColor,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
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
                      height: 1.25,
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
                      height: 1.4,
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
