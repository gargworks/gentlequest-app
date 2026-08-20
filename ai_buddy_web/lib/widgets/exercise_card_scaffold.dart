import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme/gq_tokens.dart';

/// ExerciseCardScaffold — R1D16 Exercise Cards
///
/// Shared scaffold for all three GentleQuest exercise types, rendered in
/// two contexts per Mockup A/B/C in GentleQuest_Exercise_Cards.html.
///
/// Design source: docs/design/refs/htmls/GentleQuest_Exercise_Cards.html
/// Tier: R1D16  Principle alignment: P2, P3, P7, P11
///
/// Exercise types:
///   ExerciseType.breathing  — 4-7-8 Breathing (Mockup A)
///   ExerciseType.grounding  — 5-4-3-2-1 Grounding (Mockup B)
///   ExerciseType.bodyScan   — 3-minute Body Scan (Mockup C)
///
/// Copy verbatim from HTML:
///   "EXERCISE"
///   "4-7-8 Breathing"
///   "PHASE 2 OF 3"  / "Hold"  / "5 / 7"  / "ROUND 1 OF 3"
///   "Pause"  / "Skip phase"  / "I'm done"
///   "Calm voice guide"
///   "Grounding · 5-4-3-2-1"   / "STEP 1 OF 5"
///   "things you can see/hear/feel/smell/taste"
///   "Name them out loud, or just notice."
///   "TAP AS YOU FIND THEM · OPTIONAL"
///   "Got 5 · next sense"  / "Skip to chat"
///   "3-minute body scan"
///   "FOCUS · SHOULDERS"
///   "Notice your shoulders."
///   "No need to relax them — just notice."
///   "Mute audio, just visual"
///   "Open fullscreen · Skip phase · I'm done"

// ─── Enums ───────────────────────────────────────────────────────────────────

enum ExerciseType { breathing, grounding, bodyScan }

enum ExerciseContext { inline, standalone }

enum _BreathPhase { inhale, hold, exhale }

enum _GroundingSense { see, hear, feel, smell, taste }

// ─── Main entry point ────────────────────────────────────────────────────────

/// Drop this widget anywhere. When [context] is [ExerciseContext.standalone]
/// it renders fullscreen chrome. When [ExerciseContext.inline] it renders a
/// compact card (~60% height) suitable for embedding in the chat stream.
class ExerciseCardScaffold extends StatefulWidget {
  const ExerciseCardScaffold({
    super.key,
    required this.type,
    this.exerciseContext = ExerciseContext.inline,
    this.onDone,
    this.onOpenFullscreen,
    this.onSkip,
  });

  final ExerciseType type;
  final ExerciseContext exerciseContext;

  /// Called when user taps "I'm done" or exercise completes.
  final VoidCallback? onDone;

  /// Only relevant in inline context — tapping "Open fullscreen" fires this.
  final VoidCallback? onOpenFullscreen;

  /// Called when user taps skip/cancel (P2 — skip anything, no shame).
  final VoidCallback? onSkip;

  @override
  State<ExerciseCardScaffold> createState() => _ExerciseCardScaffoldState();
}

class _ExerciseCardScaffoldState extends State<ExerciseCardScaffold>
    with TickerProviderStateMixin {
  // ── 4-7-8 Breathing state ─────────────────────────────────────────────────
  // Note: we don't kick off `.repeat()` in the field initializer — it's
  // started from `initState` with `count: _breathTotalRounds` so the
  // controller fires `AnimationStatus.completed` after the final cycle
  // (which lets us trigger `_onDone()` deterministically).
  late final AnimationController _breathCtrl = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 19000),
  );

  int _breathRound = 1;
  static const _breathTotalRounds = 3;
  _BreathPhase _breathPhase = _BreathPhase.inhale;
  bool _breathPaused = false;
  bool _voiceGuideOn = false;
  // R1D16 fix: `_breathCtrl.repeat()` wraps `value` from ~1.0 back to 0.0
  // between frames, so a per-frame `value >= 1.0` check fires
  // non-deterministically (or not at all on a fast tick). Track the
  // previous tick's value and detect the wrap-around explicitly to
  // advance the round counter.
  double _prevBreathValue = 0.0;

  static const _inhaleMs = 4000;
  static const _holdMs = 7000;
  static const _exhaleMs = 8000;
  static const _cycleMs = _inhaleMs + _holdMs + _exhaleMs; // 19000

  // ── 5-4-3-2-1 Grounding state ─────────────────────────────────────────────
  int _groundStep = 0; // 0-indexed → steps 1-5
  final List<int> _groundChecked = []; // tapped bullets (0-indexed per sense)
  static const _groundSenseCount = [5, 4, 3, 2, 1];
  static const _groundSenseLabels = ['see', 'hear', 'feel', 'smell', 'taste'];
  static const _groundSenseSequence = 'SEE · HEAR · FEEL · SMELL · TASTE';

  // ── Body scan state ────────────────────────────────────────────────────────
  late final AnimationController _scanCtrl = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 180000), // 3 min
  )..forward();

  bool _scanPaused = false;
  bool _scanMuted = false;
  // 6 focus zones matching silhouette: head, shoulders, chest, abdomen, legs, feet
  static const _scanFocusLabels = [
    'HEAD',
    'SHOULDERS',
    'CHEST',
    'ABDOMEN',
    'LEGS',
    'FEET',
  ];
  static const _scanFocusCaptions = [
    'Notice your head and face.',
    'Notice your shoulders.',
    'Notice your chest as it rises and falls.',
    'Notice your abdomen.',
    'Notice your legs.',
    'Notice your feet.',
  ];
  static const _scanFocusSubtext = [
    'No need to change anything — just notice.',
    'No need to relax them — just notice.',
    'No need to deepen your breath — just notice.',
    'No need to tighten or release — just notice.',
    'No need to move — just notice.',
    'Feel the ground beneath you — just notice.',
  ];

  @override
  void initState() {
    super.initState();
    _breathCtrl.addListener(_onBreathTick);
    // Listen for `AnimationStatus.completed` — when `repeat(count: N)` is
    // used, the controller emits `completed` only once, after the Nth
    // cycle finishes. This is our deterministic "all rounds done" signal.
    _breathCtrl.addStatusListener(_onBreathStatus);
    // Start with an explicit cycle count so the controller knows when to
    // stop and emit `completed`. Without `count`, a plain `.repeat()`
    // never fires `completed` and the orb would pulse forever — exactly
    // the bug we're fixing here.
    _breathCtrl.repeat(count: _breathTotalRounds);
  }

  void _onBreathTick() {
    if (_breathPaused) return;
    final v = _breathCtrl.value;
    // Detect wrap-around: when `repeat()` finishes a cycle, `value` jumps
    // from ~1.0 back to ~0.0 between two consecutive ticks. That wrap is
    // our cue to bump the round counter. We compare against the previous
    // tick's value rather than against a fixed threshold, because the
    // tick that lands exactly at 1.0 is not guaranteed.
    final ms = v * _cycleMs;
    final _BreathPhase np;
    if (ms < _inhaleMs) {
      np = _BreathPhase.inhale;
    } else if (ms < _inhaleMs + _holdMs) {
      np = _BreathPhase.hold;
    } else {
      np = _BreathPhase.exhale;
    }

    final wrapped = v < _prevBreathValue;
    _prevBreathValue = v;

    if (wrapped && _breathRound < _breathTotalRounds) {
      // A cycle just ended (value wrapped back to ~0). The controller is
      // still running (`completed` only fires after the final cycle when
      // `count: N` is set), so this is a mid-exercise round boundary.
      setState(() {
        _breathRound++;
        _breathPhase = _BreathPhase.inhale;
      });
      return;
    }
    if (np != _breathPhase) setState(() => _breathPhase = np);
  }

  void _onBreathStatus(AnimationStatus status) {
    // With `repeat(count: _breathTotalRounds)`, the controller emits
    // `AnimationStatus.completed` exactly once — after the final cycle.
    // That's the natural-completion path that ends the exercise.
    if (status != AnimationStatus.completed) return;
    _breathCtrl.stop();
    _onDone();
  }

  /// Number of cycles still to play given the current `_breathRound`.
  /// `_breathRound` is 1-based and represents the round currently in
  /// progress, so remaining = total - round + 1.
  int get _breathRoundsRemaining =>
      (_breathTotalRounds - _breathRound + 1).clamp(1, _breathTotalRounds);

  void _toggleBreathPause() {
    setState(() => _breathPaused = !_breathPaused);
    if (_breathPaused) {
      _breathCtrl.stop();
    } else {
      // Resume with a finite count so `AnimationStatus.completed` still
      // fires once the remaining rounds finish.
      _breathCtrl.repeat(count: _breathRoundsRemaining);
    }
  }

  /// P7 — explicit phase skip; never auto-advances.
  void _skipBreathPhase() {
    _breathCtrl.stop();
    setState(() {
      switch (_breathPhase) {
        case _BreathPhase.inhale:
          _breathPhase = _BreathPhase.hold;
          _breathCtrl.value = _inhaleMs / _cycleMs;
        case _BreathPhase.hold:
          _breathPhase = _BreathPhase.exhale;
          _breathCtrl.value = (_inhaleMs + _holdMs) / _cycleMs;
        case _BreathPhase.exhale:
          // end of cycle: advance round or done
          if (_breathRound < _breathTotalRounds) {
            _breathRound++;
            _breathPhase = _BreathPhase.inhale;
            _breathCtrl.value = 0;
          } else {
            _onDone();
            return;
          }
      }
    });
    // Reset the wrap-detection baseline so the manual `value` jump above
    // isn't misread as a natural cycle wrap by `_onBreathTick`.
    _prevBreathValue = _breathCtrl.value;
    if (!_breathPaused) _breathCtrl.repeat(count: _breathRoundsRemaining);
  }



  void _advanceGroundStep() {
    if (_groundStep < 4) {
      setState(() {
        _groundStep++;
        _groundChecked.clear();
      });
    } else {
      _onDone();
    }
  }

  void _toggleScanMute() => setState(() => _scanMuted = !_scanMuted);

  void _toggleScanPause() {
    setState(() => _scanPaused = !_scanPaused);
    _scanPaused ? _scanCtrl.stop() : _scanCtrl.forward();
  }

  void _scanSkip30() {
    final newValue =
        (_scanCtrl.value + (30000 / 180000)).clamp(0.0, 1.0);
    _scanCtrl.value = newValue;
    if (newValue >= 1.0) _onDone();
  }

  void _onDone() {
    _breathCtrl.stop();
    _scanCtrl.stop();
    widget.onDone?.call();
  }

  @override
  void dispose() {
    _breathCtrl.removeListener(_onBreathTick);
    _breathCtrl.removeStatusListener(_onBreathStatus);
    _breathCtrl.dispose();
    _scanCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return switch (widget.type) {
      ExerciseType.breathing => _buildBreathingCard(),
      ExerciseType.grounding => _buildGroundingCard(),
      ExerciseType.bodyScan => _buildBodyScanCard(),
    };
  }

  // ══════════════════════════════════════════════════════════════════════════
  // A · 4-7-8 BREATHING
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildBreathingCard() {
    final isInline = widget.exerciseContext == ExerciseContext.inline;
    return Container(
      decoration: BoxDecoration(
        color: GQColors.softBg,
        borderRadius: BorderRadius.circular(
            isInline ? GQRadii.card : 0),
        border: isInline
            ? Border.all(color: GQColors.hair)
            : null,
        boxShadow: isInline
            ? const [
                BoxShadow(
                  color: Color(0x1A1F1B3A),
                  blurRadius: 20,
                  offset: Offset(0, 8),
                  spreadRadius: -8,
                ),
              ]
            : null,
      ),
      padding: EdgeInsets.all(isInline ? 14 : 18),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildExerciseHeader(
            // Verbatim from HTML
            title: '4-7-8 Breathing',
            subtitle: isInline
                ? '4-7-8 · Round $_breathRound of $_breathTotalRounds'
                : null,
          ),
          SizedBox(height: isInline ? 8 : 12),
          _buildBreathOrb(isInline),
          const SizedBox(height: 8),
          if (!isInline) _buildRoundCounter(),
          if (!isInline) const SizedBox(height: 16),
          _buildBreathingControls(isInline),
          if (!isInline) ...[
            const SizedBox(height: 12),
            _buildVoiceGuideToggle(),
          ],
        ],
      ),
    );
  }

  Widget _buildBreathOrb(bool isInline) {
    final orbSize = isInline ? 120.0 : 200.0;
    final ringSize = isInline ? 170.0 : 280.0;
    // Phase display verbatim from HTML
    final phaseLabel = switch (_breathPhase) {
      _BreathPhase.inhale => 'PHASE 1 OF 3',
      _BreathPhase.hold => 'PHASE 2 OF 3',
      _BreathPhase.exhale => 'PHASE 3 OF 3',
    };
    final phaseVerb = switch (_breathPhase) {
      _BreathPhase.inhale => 'Inhale',
      _BreathPhase.hold => 'Hold',
      _BreathPhase.exhale => 'Exhale',
    };
    final phaseDurationMs = switch (_breathPhase) {
      _BreathPhase.inhale => _inhaleMs,
      _BreathPhase.hold => _holdMs,
      _BreathPhase.exhale => _exhaleMs,
    };

    return SizedBox(
      height: isInline ? 180 : 300,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Progress ring
          AnimatedBuilder(
            animation: _breathCtrl,
            builder: (ctx, _) {
              final circumference = 2 * math.pi * (ringSize / 2 * 0.857);
              final progress = _breathCtrl.value;
              final dashOffset = circumference * (1 - progress);
              return CustomPaint(
                size: Size(ringSize, ringSize),
                painter: _RingPainter(
                  radius: ringSize / 2 * 0.857,
                  progress: 1 - dashOffset / circumference,
                ),
              );
            },
          ),
          // Breathing orb
          AnimatedBuilder(
            animation: _breathCtrl,
            builder: (ctx, _) {
              final reduceMotion =
                  MediaQuery.of(ctx).accessibleNavigation;
              double scale;
              if (reduceMotion || _breathPaused) {
                scale = 0.85;
              } else {
                final t = _breathCtrl.value;
                if (t < 0.2105) {
                  // inhale 4s → scale 0.85→1.15
                  scale = 0.85 + (0.30 * (t / 0.2105));
                } else if (t < 0.5789) {
                  // hold 7s
                  scale = 1.15;
                } else {
                  // exhale 8s → scale 1.15→0.85
                  scale = 1.15 - (0.30 * ((t - 0.5789) / 0.4211));
                }
              }
              return Transform.scale(
                scale: scale,
                child: Container(
                  width: orbSize,
                  height: orbSize,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const RadialGradient(
                      center: Alignment(-0.3, -0.35),
                      colors: [
                        Color(0xF2FFFFFF), // white core
                        GQColors.primarySoft, // EEF0FE
                        Color(0xB3B6A8FA), // soft violet
                      ],
                      stops: [0.0, 0.5, 1.0],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: GQColors.primary.withValues(alpha: 0.45),
                        blurRadius: isInline ? 30 : 60,
                        offset: const Offset(0, 14),
                        spreadRadius: isInline ? -12 : -20,
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
          // Phase text overlay inside orb
          if (!isInline)
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Verbatim: "PHASE 2 OF 3"
                Text(
                  phaseLabel,
                  style: const TextStyle(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.7,
                    color: GQColors.primaryDk,
                  ),
                ),
                const SizedBox(height: 4),
                // Verbatim: "Hold"
                Text(
                  phaseVerb,
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink,
                    letterSpacing: -0.4,
                  ),
                ),
                const SizedBox(height: 6),
                // Verbatim: "5 / 7"
                AnimatedBuilder(
                  animation: _breathCtrl,
                  builder: (ctx, _) {
                    final ms = _breathCtrl.value * _cycleMs;
                    final double elapsedInPhase;
                    if (_breathPhase == _BreathPhase.inhale) {
                      elapsedInPhase = ms.clamp(0, _inhaleMs.toDouble());
                    } else if (_breathPhase == _BreathPhase.hold) {
                      elapsedInPhase =
                          (ms - _inhaleMs).clamp(0, _holdMs.toDouble());
                    } else {
                      elapsedInPhase = (ms - _inhaleMs - _holdMs)
                          .clamp(0, _exhaleMs.toDouble());
                    }
                    final elapsed =
                        (elapsedInPhase / 1000).ceil();
                    final total = phaseDurationMs ~/ 1000;
                    return Text(
                      '$elapsed / $total',
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink2,
                      ),
                    );
                  },
                ),
              ],
            )
          else
            // Inline: just verb + timer
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  phaseVerb,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink,
                    letterSpacing: -0.2,
                  ),
                ),
                const SizedBox(height: 2),
                AnimatedBuilder(
                  animation: _breathCtrl,
                  builder: (ctx, _) {
                    final ms = _breathCtrl.value * _cycleMs;
                    final double elapsedInPhase;
                    if (_breathPhase == _BreathPhase.inhale) {
                      elapsedInPhase = ms.clamp(0, _inhaleMs.toDouble());
                    } else if (_breathPhase == _BreathPhase.hold) {
                      elapsedInPhase =
                          (ms - _inhaleMs).clamp(0, _holdMs.toDouble());
                    } else {
                      elapsedInPhase = (ms - _inhaleMs - _holdMs)
                          .clamp(0, _exhaleMs.toDouble());
                    }
                    final elapsed =
                        (elapsedInPhase / 1000).ceil();
                    final total = phaseDurationMs ~/ 1000;
                    return Text(
                      '$elapsed / $total',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink2,
                      ),
                    );
                  },
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildRoundCounter() {
    return Column(
      children: [
        // Verbatim: "ROUND 1 OF 3"
        Text(
          'ROUND $_breathRound OF $_breathTotalRounds',
          style: const TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.7,
            color: GQColors.ink2,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(_breathTotalRounds, (i) {
            final active = i < _breathRound;
            return AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              margin: const EdgeInsets.symmetric(horizontal: 3),
              width: active ? 22 : 6,
              height: 6,
              decoration: BoxDecoration(
                color: active
                    ? GQColors.primary
                    : const Color(0x40667EEA),
                borderRadius: BorderRadius.circular(GQRadii.button),
              ),
            );
          }),
        ),
      ],
    );
  }

  Widget _buildBreathingControls(bool isInline) {
    if (isInline) {
      return Column(
        children: [
          // Primary CTA — Pause / Resume
          Semantics(
            button: true,
            label: _breathPaused ? 'Resume exercise' : 'Pause exercise',
            child: GestureDetector(
              onTap: _toggleBreathPause,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 11),
                decoration: BoxDecoration(
                  color: GQColors.primary,
                  borderRadius: BorderRadius.circular(GQRadii.button),
                  boxShadow: [
                    BoxShadow(
                      color: GQColors.primary.withValues(alpha: 0.55),
                      blurRadius: 22,
                      offset: const Offset(0, 10),
                      spreadRadius: -10,
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _breathPaused
                          ? Icons.play_arrow_rounded
                          : Icons.pause_rounded,
                      size: 14,
                      color: Colors.white,
                    ),
                    const SizedBox(width: 6),
                    // Verbatim: "Pause"
                    Text(
                      _breathPaused ? 'Resume' : 'Pause',
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 4),
          // Ghost row — open fullscreen / skip phase / done (P7)
          Semantics(
            button: true,
            child: GestureDetector(
              onTap: widget.onOpenFullscreen,
              child: const Padding(
                padding: EdgeInsets.symmetric(vertical: 6),
                child: Text(
                  // Verbatim from HTML inline ghost row
                  "Open fullscreen · Skip phase · I'm done",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink2,
                  ),
                ),
              ),
            ),
          ),
        ],
      );
    }

    // Standalone controls row
    return Row(
      children: [
        // Pause (primary)
        Expanded(
          child: Semantics(
            button: true,
            label: _breathPaused ? 'Resume exercise' : 'Pause exercise',
            child: GestureDetector(
              onTap: _toggleBreathPause,
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 11),
                decoration: BoxDecoration(
                  color: GQColors.primary,
                  borderRadius: BorderRadius.circular(GQRadii.button),
                  boxShadow: [
                    BoxShadow(
                      color: GQColors.primary.withValues(alpha: 0.55),
                      blurRadius: 22,
                      offset: const Offset(0, 10),
                      spreadRadius: -10,
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _breathPaused
                          ? Icons.play_arrow_rounded
                          : Icons.pause_rounded,
                      size: 12,
                      color: Colors.white,
                    ),
                    const SizedBox(width: 5),
                    // Verbatim: "Pause"
                    Text(
                      _breathPaused ? 'Resume' : 'Pause',
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        // Skip phase (ghost) — P7 explicit skip, never auto-advances
        Expanded(
          child: Semantics(
            button: true,
            label: 'Skip current phase',
            child: GestureDetector(
              onTap: _skipBreathPhase,
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 11),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(GQRadii.button),
                  border: Border.all(color: GQColors.hair),
                ),
                child: const Center(
                  // Verbatim: "Skip phase"
                  child: Text(
                    'Skip phase',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink2,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 4),
        // I'm done (link/text) — P2 exit any time
        Semantics(
          button: true,
          label: "Exit exercise",
          child: GestureDetector(
            onTap: _onDone,
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 8, vertical: 11),
              // Verbatim: "I'm done"
              child: Text(
                "I'm done",
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink2,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildVoiceGuideToggle() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        GestureDetector(
          onTap: () => setState(() => _voiceGuideOn = !_voiceGuideOn),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: 34,
            height: 20,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(GQRadii.button),
              color: _voiceGuideOn
                  ? GQColors.primary
                  : const Color(0x33667EEA),
            ),
            padding: const EdgeInsets.all(2),
            child: Align(
              alignment: _voiceGuideOn
                  ? Alignment.centerRight
                  : Alignment.centerLeft,
              child: Container(
                width: 16,
                height: 16,
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
          ),
        ),
        const SizedBox(width: 10),
        // Verbatim: "Calm voice guide"
        const Text(
          'Calm voice guide',
          style: TextStyle(
            fontSize: 11.5,
            fontWeight: FontWeight.w700,
            color: GQColors.ink2,
          ),
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // B · 5-4-3-2-1 GROUNDING
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildGroundingCard() {
    final isInline = widget.exerciseContext == ExerciseContext.inline;
    final sense = _GroundingSense.values[_groundStep];
    final count = _groundSenseCount[_groundStep];
    final senseLabel = _groundSenseLabels[_groundStep];

    return Container(
      decoration: BoxDecoration(
        color: GQColors.softBg,
        borderRadius: BorderRadius.circular(
            isInline ? GQRadii.card : 0),
        border: isInline ? Border.all(color: GQColors.hair) : null,
        boxShadow: isInline
            ? const [
                BoxShadow(
                  color: Color(0x1A1F1B3A),
                  blurRadius: 20,
                  offset: Offset(0, 8),
                  spreadRadius: -8,
                ),
              ]
            : null,
      ),
      padding: EdgeInsets.all(isInline ? 14 : 18),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildExerciseHeader(
            // Verbatim: "Grounding · 5-4-3-2-1"
            title: 'Grounding · 5-4-3-2-1',
            subtitle: isInline
                ? 'Grounding · ${_groundStep + 1} of 5'
                : null,
          ),
          const SizedBox(height: 8),
          // Step progress bar (5 segments)
          _buildStepProgressBar(current: _groundStep + 1, total: 5),
          const SizedBox(height: 4),
          if (!isInline)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Verbatim: "STEP 1 OF 5"
                Text(
                  'STEP ${_groundStep + 1} OF 5',
                  style: const TextStyle(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    color: GQColors.ink2,
                  ),
                ),
                // Verbatim: "SEE · HEAR · FEEL · SMELL · TASTE"
                const Text(
                  _groundSenseSequence,
                  style: TextStyle(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    color: GQColors.ink2,
                  ),
                ),
              ],
            ),
          SizedBox(height: isInline ? 8 : 16),
          _buildGroundingPrompt(
              isInline, sense, count, senseLabel),
          const SizedBox(height: 12),
          _buildGroundingControls(isInline, count, senseLabel),
        ],
      ),
    );
  }

  Widget _buildGroundingPrompt(
      bool isInline, _GroundingSense sense, int count, String senseLabel) {
    if (isInline) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon badge
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [GQColors.primarySoft, GQColors.accentSoft],
              ),
            ),
            child: Center(
              child: Icon(
                _senseIcon(sense),
                size: 22,
                color: GQColors.primaryDk,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$count',
                  style: const TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.w800,
                    color: GQColors.primary,
                    letterSpacing: -1,
                    height: 1,
                  ),
                ),
                Text(
                  // Verbatim pattern: "things you can [sense]"
                  'things you can $senseLabel',
                  style: const TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink,
                  ),
                ),
                const SizedBox(height: 2),
                const Text(
                  'just notice',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink2,
                  ),
                ),
              ],
            ),
          ),
        ],
      );
    }

    // Standalone prompt card
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        border: Border.all(color: GQColors.hair),
        boxShadow: const [
          BoxShadow(
            color: Color(0x2E1F1B3A),
            blurRadius: 50,
            offset: Offset(0, 20),
            spreadRadius: -20,
          ),
        ],
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          // Icon
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [GQColors.primarySoft, GQColors.accentSoft],
              ),
            ),
            child: Center(
              child: Icon(
                _senseIcon(sense),
                size: 30,
                color: GQColors.primaryDk,
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            '$count',
            style: const TextStyle(
              fontSize: 64,
              fontWeight: FontWeight.w800,
              color: GQColors.primary,
              height: 1,
              letterSpacing: -2,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            // Verbatim: "things you can see"
            'things you can $senseLabel',
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
              letterSpacing: -0.3,
            ),
          ),
          const SizedBox(height: 8),
          // Verbatim: "Name them out loud, or just notice."
          const Text(
            'Name them out loud, or just notice.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: GQColors.ink2,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 20),
          // Optional sense bullets (P2 — optional, no shame)
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(count, (i) {
              final checked = _groundChecked.contains(i);
              return Semantics(
                button: true,
                label: checked
                    ? 'Unmark item ${i + 1}'
                    : 'Mark item ${i + 1} found',
                child: GestureDetector(
                  onTap: () => setState(() {
                    if (checked) {
                      _groundChecked.remove(i);
                    } else {
                      _groundChecked.add(i);
                    }
                  }),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: checked ? GQColors.primarySoft : Colors.white,
                      border: Border.all(
                        color: checked
                            ? GQColors.primary
                            : GQColors.hair,
                        width: 1.5,
                      ),
                    ),
                    child: Center(
                      child: checked
                          ? const Icon(Icons.check_rounded,
                              size: 16, color: GQColors.primaryDk)
                          : Text(
                              '${i + 1}',
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w800,
                                color: GQColors.ink2,
                              ),
                            ),
                    ),
                  ),
                ),
              );
            }),
          ),
          const SizedBox(height: 8),
          // Verbatim: "TAP AS YOU FIND THEM · OPTIONAL"
          const Text(
            'TAP AS YOU FIND THEM · OPTIONAL',
            style: TextStyle(
              fontSize: 10.5,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.5,
              color: GQColors.ink2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGroundingControls(
      bool isInline, int count, String senseLabel) {
    final isLastStep = _groundStep == 4;
    final ctaLabel = isLastStep
        ? "I'm done"
        : 'Got $count · next sense';

    return Column(
      children: [
        Semantics(
          button: true,
          label: ctaLabel,
          child: GestureDetector(
            onTap: _advanceGroundStep,
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(
                  vertical: isInline ? 11 : 14),
              decoration: BoxDecoration(
                color: GQColors.primary,
                borderRadius: BorderRadius.circular(GQRadii.button),
                boxShadow: [
                  BoxShadow(
                    color: GQColors.primary.withValues(alpha: 0.55),
                    blurRadius: 22,
                    offset: const Offset(0, 10),
                    spreadRadius: -10,
                  ),
                ],
              ),
              child: Center(
                // Verbatim: "Got 5 · next sense"
                child: Text(
                  ctaLabel,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 4),
        // P2 — skip any time
        Semantics(
          button: true,
          label: 'Skip to chat',
          child: GestureDetector(
            onTap: widget.onSkip ?? _onDone,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              // Verbatim: "Skip to chat"
              child: Text(
                isInline
                    ? "Open fullscreen · Skip to chat"
                    : "Skip to chat",
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink2,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  IconData _senseIcon(_GroundingSense sense) {
    return switch (sense) {
      _GroundingSense.see => Icons.visibility_outlined,
      _GroundingSense.hear => Icons.hearing_outlined,
      _GroundingSense.feel => Icons.touch_app_outlined,
      _GroundingSense.smell => Icons.air_outlined,
      _GroundingSense.taste => Icons.restaurant_outlined,
    };
  }

  // ══════════════════════════════════════════════════════════════════════════
  // C · BODY SCAN
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildBodyScanCard() {
    final isInline = widget.exerciseContext == ExerciseContext.inline;

    return Container(
      decoration: BoxDecoration(
        color: GQColors.softBg,
        borderRadius: BorderRadius.circular(
            isInline ? GQRadii.card : 0),
        border: isInline ? Border.all(color: GQColors.hair) : null,
        boxShadow: isInline
            ? const [
                BoxShadow(
                  color: Color(0x1A1F1B3A),
                  blurRadius: 20,
                  offset: Offset(0, 8),
                  spreadRadius: -8,
                ),
              ]
            : null,
      ),
      padding: EdgeInsets.all(isInline ? 12 : 18),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildExerciseHeader(
            // Verbatim: "3-minute body scan"
            title: '3-minute body scan',
            subtitle: isInline ? null : null,
          ),
          SizedBox(height: isInline ? 8 : 16),
          isInline
              ? _buildBodyScanInlineContent()
              : _buildBodyScanStandaloneContent(),
          const SizedBox(height: 12),
          _buildBodyScanControls(isInline),
          if (!isInline) ...[
            const SizedBox(height: 8),
            _buildBodyScanWaveform(),
          ],
        ],
      ),
    );
  }

  Widget _buildBodyScanInlineContent() {
    // Inline: compact silhouette + progress row
    return AnimatedBuilder(
      animation: _scanCtrl,
      builder: (ctx, _) {
        final focusIndex =
            (_scanCtrl.value * _scanFocusLabels.length).floor().clamp(
                  0,
                  _scanFocusLabels.length - 1,
                );
        final caption = _scanFocusCaptions[focusIndex];
        final subtext = _scanFocusSubtext[focusIndex];
        final focusLabel = _scanFocusLabels[focusIndex];
        final elapsed = Duration(
            milliseconds: (_scanCtrl.value * 180000).round());
        final elapsedStr =
            '${elapsed.inMinutes}:${(elapsed.inSeconds % 60).toString().padLeft(2, '0')}';

        return Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Compact silhouette
            SizedBox(
              width: 44,
              height: 80,
              child: CustomPaint(
                painter: _SilhouettePainter(
                  glowProgress: _scanCtrl.value,
                  focusIndex: focusIndex,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          caption,
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                            color: GQColors.ink,
                            height: 1.4,
                          ),
                        ),
                      ),
                      Text(
                        // Verbatim pattern: "SHOULDERS · 1:12"
                        '$focusLabel · $elapsedStr',
                        style: const TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                          color: GQColors.ink2,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtext,
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: GQColors.ink2,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 8),
                  // Mini progress bar
                  ClipRRect(
                    borderRadius:
                        BorderRadius.circular(GQRadii.button),
                    child: LinearProgressIndicator(
                      value: _scanCtrl.value,
                      minHeight: 4,
                      backgroundColor: const Color(0x261F1B3A),
                      valueColor: AlwaysStoppedAnimation<Color>(
                        GQColors.primary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildBodyScanStandaloneContent() {
    return AnimatedBuilder(
      animation: _scanCtrl,
      builder: (ctx, _) {
        final focusIndex =
            (_scanCtrl.value * _scanFocusLabels.length).floor().clamp(
                  0,
                  _scanFocusLabels.length - 1,
                );
        final focusLabel = _scanFocusLabels[focusIndex];
        final caption = _scanFocusCaptions[focusIndex];
        final subtext = _scanFocusSubtext[focusIndex];
        final elapsed = Duration(
            milliseconds: (_scanCtrl.value * 180000).round());
        final remaining = Duration(
            milliseconds: 180000 -
                (_scanCtrl.value * 180000).round());
        final elapsedStr =
            '${elapsed.inMinutes}:${(elapsed.inSeconds % 60).toString().padLeft(2, '0')}';
        final remainStr =
            '${remaining.inMinutes}:${(remaining.inSeconds % 60).toString().padLeft(2, '0')}';

        return Column(
          children: [
            // Silhouette
            SizedBox(
              height: 280,
              child: CustomPaint(
                size: const Size(200, 280),
                painter: _SilhouettePainter(
                  glowProgress: _scanCtrl.value,
                  focusIndex: focusIndex,
                  large: true,
                ),
              ),
            ),
            const SizedBox(height: 12),
            // Verbatim: "FOCUS · SHOULDERS"
            Text(
              'FOCUS · $focusLabel',
              style: const TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.7,
                color: GQColors.primaryDk,
              ),
            ),
            const SizedBox(height: 8),
            // Verbatim: "Notice your shoulders."
            Text(
              caption,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: GQColors.ink,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 4),
            // Verbatim: "No need to relax them — just notice."
            Text(
              subtext,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: GQColors.ink2,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 16),
            // Progress bar with timestamps
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 6),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(elapsedStr,
                          style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              color: GQColors.ink2)),
                      Text(remainStr,
                          style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              color: GQColors.ink2)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(GQRadii.button),
                    child: LinearProgressIndicator(
                      value: _scanCtrl.value,
                      minHeight: 5,
                      backgroundColor: const Color(0x261F1B3A),
                      valueColor: const AlwaysStoppedAnimation<Color>(
                        GQColors.primary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildBodyScanControls(bool isInline) {
    if (isInline) {
      return Column(
        children: [
          // Pause primary CTA
          Semantics(
            button: true,
            label: _scanPaused ? 'Resume body scan' : 'Pause body scan',
            child: GestureDetector(
              onTap: _toggleScanPause,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 11),
                decoration: BoxDecoration(
                  color: GQColors.primary,
                  borderRadius: BorderRadius.circular(GQRadii.button),
                  boxShadow: [
                    BoxShadow(
                      color: GQColors.primary.withValues(alpha: 0.55),
                      blurRadius: 22,
                      offset: const Offset(0, 10),
                      spreadRadius: -10,
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _scanPaused
                          ? Icons.play_arrow_rounded
                          : Icons.pause_rounded,
                      size: 14,
                      color: Colors.white,
                    ),
                    const SizedBox(width: 6),
                    // Verbatim: "Pause"
                    Text(
                      _scanPaused ? 'Resume' : 'Pause',
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 4),
          Semantics(
            button: true,
            child: GestureDetector(
              onTap: widget.onOpenFullscreen,
              child: const Padding(
                padding: EdgeInsets.symmetric(vertical: 6),
                child: Text(
                  // Verbatim from inline ghost row
                  "Open fullscreen · +30s · I'm done",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink2,
                  ),
                ),
              ),
            ),
          ),
        ],
      );
    }

    // Standalone row: I'm done | pause FAB | +30s
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        // I'm done (P2 exit)
        Semantics(
          button: true,
          child: GestureDetector(
            onTap: _onDone,
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 4, vertical: 8),
              // Verbatim: "I'm done"
              child: Text(
                "I'm done",
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink2,
                ),
              ),
            ),
          ),
        ),
        // Centre pause FAB
        Semantics(
          button: true,
          label: _scanPaused ? 'Resume scan' : 'Pause scan',
          child: GestureDetector(
            onTap: _toggleScanPause,
            child: Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: GQColors.primary,
                boxShadow: [
                  BoxShadow(
                    color: GQColors.primary.withValues(alpha: 0.55),
                    blurRadius: 28,
                    offset: const Offset(0, 14),
                    spreadRadius: -10,
                  ),
                ],
              ),
              child: Icon(
                _scanPaused
                    ? Icons.play_arrow_rounded
                    : Icons.pause_rounded,
                color: Colors.white,
                size: 28,
              ),
            ),
          ),
        ),
        // +30s ghost button (P7 — explicit control, never auto-advances)
        Semantics(
          button: true,
          label: 'Add 30 seconds',
          child: GestureDetector(
            onTap: _scanSkip30,
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(GQRadii.button),
                border: Border.all(color: GQColors.hair),
              ),
              child: const Row(
                children: [
                  Icon(Icons.fast_forward_rounded,
                      size: 14, color: GQColors.ink2),
                  SizedBox(width: 4),
                  Text(
                    '+30s',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink2,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBodyScanWaveform() {
    // Mute audio toggle row
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // 5 animated wave bars (visual only — audio not implemented per scope)
        ...List.generate(5, (i) {
          return AnimatedContainer(
            duration: Duration(milliseconds: 800 + i * 80),
            margin: const EdgeInsets.symmetric(horizontal: 1),
            width: 2,
            height: _scanMuted ? 4 : (6 + i * 2).toDouble(),
            decoration: BoxDecoration(
              color: GQColors.primary,
              borderRadius: BorderRadius.circular(1),
            ),
          );
        }),
        const SizedBox(width: 8),
        // Verbatim: "Mute audio, just visual"
        const Text(
          'Mute audio, just visual',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            color: GQColors.ink2,
          ),
        ),
        const SizedBox(width: 8),
        GestureDetector(
          onTap: _toggleScanMute,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: 30,
            height: 18,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(GQRadii.button),
              color: _scanMuted
                  ? GQColors.primary
                  : const Color(0x33667EEA),
            ),
            padding: const EdgeInsets.all(2),
            child: Align(
              alignment: _scanMuted
                  ? Alignment.centerRight
                  : Alignment.centerLeft,
              child: Container(
                width: 14,
                height: 14,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // Shared helpers
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildExerciseHeader({
    required String title,
    String? subtitle,
  }) {
    final isInline = widget.exerciseContext == ExerciseContext.inline;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Icon badge
        Container(
          width: isInline ? 28 : 32,
          height: isInline ? 28 : 32,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: GQColors.primarySoft,
          ),
          child: Center(
            child: Icon(
              _typeIcon(widget.type),
              size: isInline ? 14 : 16,
              color: GQColors.primary,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Verbatim: "EXERCISE"
              const Text(
                'EXERCISE',
                style: TextStyle(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.7,
                  color: GQColors.ink2,
                ),
              ),
              const SizedBox(height: 1),
              Text(
                title,
                style: TextStyle(
                  fontSize: isInline ? 13.5 : 17,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink,
                  letterSpacing: -0.3,
                ),
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 1),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink2,
                  ),
                ),
              ],
            ],
          ),
        ),
        // Close / cancel button (P2 — always present)
        Semantics(
          button: true,
          label: 'Close exercise',
          child: GestureDetector(
            onTap: widget.onSkip ?? _onDone,
            child: Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.transparent,
              ),
              child: const Icon(
                Icons.close_rounded,
                size: 16,
                color: GQColors.ink3,
              ),
            ),
          ),
        ),
      ],
    );
  }

  IconData _typeIcon(ExerciseType type) {
    return switch (type) {
      ExerciseType.breathing => Icons.air_outlined,
      ExerciseType.grounding => Icons.public_outlined,
      ExerciseType.bodyScan => Icons.self_improvement_outlined,
    };
  }

  Widget _buildStepProgressBar({required int current, required int total}) {
    return Row(
      children: List.generate(total, (i) {
        final filled = i < current;
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(right: i < total - 1 ? 4 : 0),
            height: widget.exerciseContext == ExerciseContext.inline ? 4 : 6,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(GQRadii.button),
              color: filled ? GQColors.primary : const Color(0x33667EEA),
            ),
          ),
        );
      }),
    );
  }
}

// ─── Custom painters ─────────────────────────────────────────────────────────

class _RingPainter extends CustomPainter {
  const _RingPainter({required this.radius, required this.progress});

  final double radius;
  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final centre = Offset(size.width / 2, size.height / 2);
    final trackPaint = Paint()
      ..color = const Color(0x1F667EEA)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6
      ..strokeCap = StrokeCap.round;
    canvas.drawCircle(centre, radius, trackPaint);

    final progressPaint = Paint()
      ..shader = const LinearGradient(
        colors: [GQColors.primary, Color(0xFFB6A8FA), GQColors.coral],
      ).createShader(Rect.fromCircle(center: centre, radius: radius))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: centre, radius: radius),
      -math.pi / 2,
      2 * math.pi * progress,
      false,
      progressPaint,
    );
  }

  @override
  bool shouldRepaint(_RingPainter old) => old.progress != progress;
}

class _SilhouettePainter extends CustomPainter {
  const _SilhouettePainter({
    required this.glowProgress,
    required this.focusIndex,
    this.large = false,
  });

  final double glowProgress;
  final int focusIndex;
  final bool large;

  @override
  void paint(Canvas canvas, Size size) {
    final sh = size.height;
    // Silhouette fill
    final fill = Paint()
      ..color = GQColors.primary.withValues(alpha: 0.18)
      ..style = PaintingStyle.fill;
    final stroke = Paint()
      ..color = GQColors.primary.withValues(alpha: 0.40)
      ..style = PaintingStyle.stroke
      ..strokeWidth = large ? 1.2 : 0.8;

    final scaleX = size.width / 200.0;
    final scaleY = sh / 380.0;

    canvas.save();
    canvas.scale(scaleX, scaleY);

    // Head
    canvas.drawCircle(const Offset(100, 42), 28, fill);
    canvas.drawCircle(const Offset(100, 42), 28, stroke);

    // Torso path
    final torso = Path()
      ..moveTo(88, 70)
      ..lineTo(88, 80)
      ..quadraticBezierTo(60, 85, 50, 110)
      ..quadraticBezierTo(42, 145, 50, 200)
      ..quadraticBezierTo(55, 240, 60, 270)
      ..quadraticBezierTo(66, 310, 70, 340)
      ..quadraticBezierTo(72, 360, 80, 370)
      ..lineTo(120, 370)
      ..quadraticBezierTo(128, 360, 130, 340)
      ..quadraticBezierTo(134, 310, 140, 270)
      ..quadraticBezierTo(145, 240, 150, 200)
      ..quadraticBezierTo(158, 145, 150, 110)
      ..quadraticBezierTo(140, 85, 112, 80)
      ..lineTo(112, 70)
      ..close();
    canvas.drawPath(torso, fill);
    canvas.drawPath(torso, stroke);

    canvas.restore();

    // Traveling glow — position maps to focusIndex
    final glowYFractions = [0.13, 0.22, 0.33, 0.46, 0.62, 0.80];
    final glowY = glowYFractions[focusIndex.clamp(0, 5)] * sh;
    final glowPaint = Paint()
      ..shader = RadialGradient(
        colors: [
          GQColors.coral.withValues(alpha: 0.55),
          GQColors.coral.withValues(alpha: 0.18),
          Colors.transparent,
        ],
        stops: const [0.0, 0.5, 1.0],
      ).createShader(Rect.fromCenter(
        center: Offset(size.width / 2, glowY),
        width: size.width * 1.2,
        height: large ? 80 : 22,
      ));
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(size.width / 2, glowY),
        width: size.width * (large ? 0.85 : 1.0),
        height: large ? 80 : 22,
      ),
      glowPaint,
    );
  }

  @override
  bool shouldRepaint(_SilhouettePainter old) =>
      old.glowProgress != glowProgress || old.focusIndex != focusIndex;
}
