// adhd_path_screen.dart — v1.5.0 "ADHD Update", Workstream 2c
// Scope:  docs/V1_5_0_ADHD_UPDATE_SCOPE.md § Workstream 2 (c)
// Intent: .brain/artifacts/research/ADHD_product_strategy.md § 3 ("Micro-ASRS")
//
// Framing (hard constraint, do not relax): this step is presented to the
// user as "getting to know your brain a bit" — never as a screening, test,
// or diagnostic tool, and never as ASRS/clinical language. It is loosely
// *inspired* by ASRS-v1.1 Part A's themes (task initiation, sustained
// attention) but deliberately does not use the clinical wording, the 0–4
// Likert scale, or any scoring/severity output. There is no score and no
// label anywhere in this flow — the only output is a fixed list of feature
// suggestions (body doubling, low-stim mode, gentle quests), framed as
// defaults we set for the user, not a diagnosis.
//
// Wiring: shown at most once, immediately after the existing age +
// compliance gates pass in the first-run onboarding flow (see
// WelcomeScreen._confirmAdult). Every screen in this flow is skippable —
// this step must never block access to the rest of the app.
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/firebase_service.dart';
import '../theme/gq_tokens.dart';

/// Persisted, non-diagnostic "what tends to help" preference flags written
/// on completion. Nothing here is a score — they're just soft defaults for
/// whichever surface (body-doubling entry, low-stim theme, quest tab) wants
/// to read them later.
const String kAdhdPrefBodyDoublingKey = 'adhd_pref_body_doubling_v1';
const String kAdhdPrefLowStimKey = 'adhd_pref_low_stim_v1';
const String kAdhdPrefGentleQuestsKey = 'adhd_pref_gentle_quests_v1';

class AdhdPathScreen extends StatefulWidget {
  const AdhdPathScreen({super.key, required this.onFinished});

  /// Called exactly once, when the user either completes or skips this
  /// step. The caller owns what "finished" means (normally a
  /// pushReplacementNamed('/main')) — this widget never navigates on its
  /// own so it stays agnostic of the surrounding route table.
  final VoidCallback onFinished;

  static const String _kSeenKey = 'has_seen_adhd_path_v1';

  /// Whether the user has already completed or skipped this step.
  static Future<bool> hasBeenSeen() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kSeenKey) ?? false;
  }

  @override
  State<AdhdPathScreen> createState() => _AdhdPathScreenState();
}

enum _Step { intro, q1, q2, suggestions }

class _AdhdPathScreenState extends State<AdhdPathScreen> {
  _Step _step = _Step.intro;
  int? _q1Answer;
  int? _q2Answer;
  bool _completedLogged = false;

  @override
  void initState() {
    super.initState();
    // Fire-and-forget — analytics must never gate/slow the UI.
    FirebaseService().logEvent('onboarding_adhd_path_entered');
  }

  Future<void> _markSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(AdhdPathScreen._kSeenKey, true);
  }

  Future<void> _skip(String fromStep) async {
    await FirebaseService().logEvent('onboarding_adhd_path_skipped', {
      'step': fromStep,
    });
    await _markSeen();
    if (!mounted) return;
    widget.onFinished();
  }

  void _answerQ1(int index) {
    HapticFeedback.selectionClick();
    setState(() {
      _q1Answer = index;
      _step = _Step.q2;
    });
  }

  Future<void> _answerQ2(int index) async {
    HapticFeedback.selectionClick();
    setState(() => _q2Answer = index);
    await _completeQuestions();
  }

  Future<void> _completeQuestions() async {
    if (!_completedLogged) {
      _completedLogged = true;
      // q1/q2 are raw option indices, never a derived score or severity —
      // useful for product analysis of which framing resonates, not a
      // clinical signal.
      await FirebaseService().logEvent('onboarding_adhd_path_completed', {
        'q1': _q1Answer,
        'q2': _q2Answer,
      });
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(kAdhdPrefBodyDoublingKey, true);
    await prefs.setBool(kAdhdPrefLowStimKey, true);
    await prefs.setBool(kAdhdPrefGentleQuestsKey, true);
    await _markSeen();
    if (!mounted) return;
    setState(() => _step = _Step.suggestions);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: GQDurations.fade,
          child: _buildStep(),
        ),
      ),
    );
  }

  Widget _buildStep() {
    switch (_step) {
      case _Step.intro:
        return _IntroContent(
          key: const ValueKey('adhd_path_intro'),
          onContinue: () => setState(() => _step = _Step.q1),
          onSkip: () => _skip('intro'),
        );
      case _Step.q1:
        return _QuestionContent(
          key: const ValueKey('adhd_path_q1'),
          stepIndex: 1,
          totalSteps: 2,
          question:
              "When it's time to start something you've been putting off, "
              'what usually happens?',
          options: _q1Options,
          onAnswer: _answerQ1,
          onSkip: () => _skip('q1'),
        );
      case _Step.q2:
        return _QuestionContent(
          key: const ValueKey('adhd_path_q2'),
          stepIndex: 2,
          totalSteps: 2,
          question: "Once you're actually in the middle of a task, "
              'what tends to happen?',
          options: _q2Options,
          onAnswer: (i) => _answerQ2(i),
          onSkip: () => _skip('q2'),
        );
      case _Step.suggestions:
        return _SuggestionsContent(
          key: const ValueKey('adhd_path_suggestions'),
          onContinue: () async {
            await _markSeen();
            if (!mounted) return;
            widget.onFinished();
          },
        );
    }
  }
}

// Self-discovery-toned options — deliberately conversational, never the
// literal ASRS Likert wording ("Never" .. "Very Often") or clinical framing.
const List<String> _q1Options = [
  'I just start — it\'s not a big deal',
  'I need a little nudge, but I get there',
  'Starting is the hardest part — I stall a lot',
  'I do best when someone\'s doing it alongside me',
];

const List<String> _q2Options = [
  'I stay locked in until it\'s done',
  'I drift off, then come back to it',
  'Something shinier usually pulls me away',
  'I forget I was even doing it',
];

// ─────────────────────────────────────────────────────────────────────────────
// Shared chrome — skip affordance
// ─────────────────────────────────────────────────────────────────────────────

class _SkipButton extends StatelessWidget {
  const _SkipButton({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topRight,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 20, 12),
          child: Text(
            'Skip for now',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: GQColors.ink3,
            ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Screen 1 — Intro
// ─────────────────────────────────────────────────────────────────────────────

class _IntroContent extends StatelessWidget {
  const _IntroContent({super.key, required this.onContinue, required this.onSkip});

  final VoidCallback onContinue;
  final VoidCallback onSkip;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _SkipButton(onTap: onSkip),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 28),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(height: 12),
                Container(
                  width: 72,
                  height: 72,
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [GQColors.primarySoft, GQColors.accentSoft],
                    ),
                    shape: BoxShape.circle,
                  ),
                  child: const Center(
                    child: Text('🧠', style: TextStyle(fontSize: 32)),
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  'One more thing,\nif you’re up for it',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: GQTypography.displayFamily,
                    fontSize: 26,
                    fontWeight: FontWeight.w800,
                    height: 1.2,
                    letterSpacing: -0.4,
                    color: GQColors.ink,
                  ),
                ),
                const SizedBox(height: 14),
                Text(
                  'A couple of quick questions to get to know your brain a '
                  'little better — so we can suggest what might actually help.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                    height: 1.5,
                    color: GQColors.ink2,
                  ),
                ),
                const SizedBox(height: 20),
                // "Not a diagnosis" microcopy — app's existing disclaimer
                // pattern (small print, ink3, centered).
                Text(
                  'Not a test. Not a diagnosis — just two questions, '
                  'answered your way.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    height: 1.5,
                    color: GQColors.ink3,
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 0, 24, 28),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: onContinue,
              style: ElevatedButton.styleFrom(
                backgroundColor: GQColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: const StadiumBorder(),
                elevation: 0,
              ),
              child: const Text(
                "Let's do it",
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Screens 2–3 — Questions
// ─────────────────────────────────────────────────────────────────────────────

class _QuestionContent extends StatelessWidget {
  const _QuestionContent({
    super.key,
    required this.stepIndex,
    required this.totalSteps,
    required this.question,
    required this.options,
    required this.onAnswer,
    required this.onSkip,
  });

  final int stepIndex;
  final int totalSteps;
  final String question;
  final List<String> options;
  final ValueChanged<int> onAnswer;
  final VoidCallback onSkip;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _SkipButton(onTap: onSkip),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(totalSteps, (i) {
              final filled = i < stepIndex;
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: Container(
                  width: 28,
                  height: 5,
                  decoration: BoxDecoration(
                    color: filled ? GQColors.primary : GQColors.hair,
                    borderRadius: BorderRadius.circular(99),
                  ),
                ),
              );
            }),
          ),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(28, 24, 28, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  question,
                  style: TextStyle(
                    fontFamily: GQTypography.displayFamily,
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    height: 1.3,
                    letterSpacing: -0.3,
                    color: GQColors.ink,
                  ),
                ),
                const SizedBox(height: 24),
                ...List.generate(options.length, (i) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: _OptionCard(
                      label: options[i],
                      onTap: () => onAnswer(i),
                    ),
                  );
                }),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _OptionCard extends StatelessWidget {
  const _OptionCard({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: Border.all(color: GQColors.hair),
          boxShadow: [
            BoxShadow(
              color: GQColors.ink.withAlpha(8),
              blurRadius: 2,
              offset: const Offset(0, 1),
            ),
          ],
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 15,
            fontWeight: FontWeight.w600,
            height: 1.4,
            color: GQColors.ink,
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Screen 4 — Suggestions (no score, no label — ever)
// ─────────────────────────────────────────────────────────────────────────────

class _SuggestionsContent extends StatelessWidget {
  const _SuggestionsContent({super.key, required this.onContinue});

  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(28, 20, 28, 28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 12),
          Text(
            'Thanks for sharing.',
            style: TextStyle(
              fontFamily: GQTypography.displayFamily,
              fontSize: 26,
              fontWeight: FontWeight.w800,
              height: 1.2,
              letterSpacing: -0.4,
              color: GQColors.ink,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'Here’s what tends to help — we’ve turned these on for you '
            'by default. You can change any of it later in Settings.',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 15,
              fontWeight: FontWeight.w500,
              height: 1.5,
              color: GQColors.ink2,
            ),
          ),
          const SizedBox(height: 22),
          const _SuggestionCard(
            emoji: '🤝',
            title: 'Body doubling',
            subtitle:
                'Alex can sit with you while you work — a timer plus gentle '
                'check-ins, right inside chat. No camera, no small talk.',
          ),
          const SizedBox(height: 10),
          const _SuggestionCard(
            emoji: '🌙',
            title: 'A calmer, low-stim look',
            subtitle:
                'A quieter color and motion theme, on the way — we’ll '
                'switch you to it automatically once it ships.',
          ),
          const SizedBox(height: 10),
          const _SuggestionCard(
            emoji: '🌱',
            title: 'Gentle quests',
            subtitle:
                'Small, no-pressure steps instead of big to-do lists. '
                'Miss a day? Nothing resets, nothing is lost.',
          ),
          const SizedBox(height: 22),
          // "Not a diagnosis" microcopy — required at the result surface.
          Center(
            child: Text(
              'Not a diagnosis, not a label — just a few gentle defaults '
              'based on what you shared.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 11,
                fontWeight: FontWeight.w600,
                height: 1.5,
                color: GQColors.ink3,
              ),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: onContinue,
              style: ElevatedButton.styleFrom(
                backgroundColor: GQColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: const StadiumBorder(),
                elevation: 0,
              ),
              child: const Text(
                'Continue to GentleQuest',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SuggestionCard extends StatelessWidget {
  const _SuggestionCard({
    required this.emoji,
    required this.title,
    required this.subtitle,
  });

  final String emoji;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        border: Border.all(color: GQColors.hair),
        boxShadow: [
          BoxShadow(
            color: GQColors.ink.withAlpha(8),
            blurRadius: 2,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: const BoxDecoration(
              color: GQColors.primarySoft,
              shape: BoxShape.circle,
            ),
            child: Center(child: Text(emoji, style: const TextStyle(fontSize: 20))),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: GQColors.ink,
                        ),
                      ),
                    ),
                    Icon(Icons.check_circle_rounded,
                        size: 18, color: GQColors.successInk),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 12.5,
                    fontWeight: FontWeight.w500,
                    height: 1.45,
                    color: GQColors.ink2,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
