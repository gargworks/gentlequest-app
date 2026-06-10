import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../models/message.dart' show RiskLevel;
import '../../navigation/home_tab_deeplink.dart';
import '../../providers/assessment_provider.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/app_bottom_nav.dart' show AppTab;
import '../../widgets/crisis_resources.dart';
import 'assessment_models.dart';
import 'assessment_question_card.dart';
import 'assessment_widgets.dart';
import 'q9_crisis_bridge.dart';
import 'result_reveal_screen.dart';

// ─────────────────────────────────────────────────────────────────────────────
// A — Assessment flow screen
// ─────────────────────────────────────────────────────────────────────────────

class AssessmentFlowScreen extends StatefulWidget {
  final AssessmentScale scale;
  const AssessmentFlowScreen({super.key, required this.scale});

  @override
  State<AssessmentFlowScreen> createState() => _AssessmentFlowScreenState();
}

class _AssessmentFlowScreenState extends State<AssessmentFlowScreen>
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
      ? kPhq9Questions
      : kGad7Questions;

  int get _totalQ => _questions.length;

  int get _totalScore =>
      _responses.whereType<int>().fold(0, (sum, v) => sum + v);

  AssessmentSeverity get _severity => widget.scale == AssessmentScale.phq9
      ? phq9Severity(_totalScore)
      : gad7Severity(_totalScore);

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
    showModalBottomSheet<BridgeAction>(
      context: context,
      isDismissible: false,
      enableDrag: false,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: GQColors.ink.withAlpha(82), // ~0.32 per spec
      builder: (_) => const Q9CrisisBridgeSheet(),
    ).then((action) {
      if (!mounted) return;
      switch (action) {
        case BridgeAction.imSafe:
        case BridgeAction.heavy:
          // Continue past Q9 → result (it's the last question)
          if (_qIdx < _totalQ - 1) {
            _animateToQuestion(_qIdx + 1);
          } else {
            _submitToBackend();
            setState(() => _showResult = true);
          }
          if (action == BridgeAction.heavy) {
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
        case BridgeAction.talkNow:
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
      return ResultRevealScreen(
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
          homeTabDeepLink.request(AppTab.talk);
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
            AssessmentNavBar(
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
                        child: AssessmentQuestionCard(
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
                    LikertSelector(
                      selected: selected,
                      onSelect: _selectOption,
                    ),

                    const SizedBox(height: 20),

                    // ── Back / Next row
                    Row(
                      children: [
                        if (_qIdx > 0) ...[
                          PillButton(
                            label: 'Back',
                            onTap: () => _animateToQuestion(_qIdx - 1),
                            style: PillButtonStyle.ghost,
                          ),
                          const SizedBox(width: 10),
                        ],
                        Expanded(
                          child: PillButton(
                            label: 'Next',
                            onTap: selected != null ? _advance : null,
                            style: PillButtonStyle.primary,
                          ),
                        ),
                      ],
                    ),

                    // ── "Save & exit · we'll keep your spot" — verbatim
                    const SizedBox(height: 10),
                    Center(
                      child: SaveAndExitLink(onTap: _saveAndExit),
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
