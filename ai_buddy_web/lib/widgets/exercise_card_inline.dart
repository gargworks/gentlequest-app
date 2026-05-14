import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme/gq_tokens.dart';

/// ExerciseCardInline — State C (R1D7 Chat Active States)
///
/// Inline compact exercise card rendered in the chat stream. Per P11, the same
/// ExerciseCardScaffold logic applies at 60% height, embedded in chat.
/// This widget implements the 4-7-8 Breathing variant shown in Mockup C.
///
/// Breathing cycle: 19s total (in 4s → hold 7s → out 8s).
/// Card collapse: 320ms ease-in. Follow-up bubble enters 500ms after collapse.
///
/// Design source: GentleQuest_Chat_Active_States.html — Mockup C.
/// Copy verbatim:
///   "4-7-8 Breathing"
///   "~ 1 minute · Round 1 of 3"
///   "BREATHE IN" / "HOLD" / "BREATHE OUT"
///   "through your nose" / "hold steady" / "out through your mouth"
///   "Pause" / "I'm done"
///   "LIVE"
///   "in · hold · out"

enum BreathPhase { inhale, hold, exhale }

class ExerciseCardInline extends StatefulWidget {
  const ExerciseCardInline({
    super.key,
    this.totalRounds = 3,
    required this.onDone,
    this.onCollapsed,
  });

  final int totalRounds;
  final VoidCallback onDone;
  /// Called 320ms after user taps "I'm done" (after collapse animation).
  final VoidCallback? onCollapsed;

  @override
  State<ExerciseCardInline> createState() => _ExerciseCardInlineState();
}

class _ExerciseCardInlineState extends State<ExerciseCardInline>
    with SingleTickerProviderStateMixin {
  // Breathing orb: 19s cycle (4+7+8)
  late final AnimationController _breatheCtrl = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 19000),
  )..repeat();

  int _currentRound = 1;
  BreathPhase _phase = BreathPhase.inhale;
  bool _paused = false;
  bool _collapsed = false;

  // Phase durations in ms
  static const _inhaleDuration = 4000;
  static const _holdDuration = 7000;
  static const _exhaleDuration = 8000;
  static const _totalDuration = _inhaleDuration + _holdDuration + _exhaleDuration; // 19000

  @override
  void initState() {
    super.initState();
    _breatheCtrl.addListener(_onTick);
  }

  void _onTick() {
    if (_paused) return;
    final ms = _breatheCtrl.value * _totalDuration;
    BreathPhase newPhase;
    if (ms < _inhaleDuration) {
      newPhase = BreathPhase.inhale;
    } else if (ms < _inhaleDuration + _holdDuration) {
      newPhase = BreathPhase.hold;
    } else {
      newPhase = BreathPhase.exhale;
    }
    if (newPhase != _phase) {
      setState(() => _phase = newPhase);
    }
    // Track round completion
    if (_breatheCtrl.value >= 1.0) {
      if (_currentRound < widget.totalRounds) {
        setState(() {
          _currentRound++;
          _phase = BreathPhase.inhale;
        });
      }
    }
  }

  void _togglePause() {
    setState(() => _paused = !_paused);
    if (_paused) {
      _breatheCtrl.stop();
    } else {
      _breatheCtrl.repeat();
    }
  }

  void _onDone() async {
    _breatheCtrl.stop();
    setState(() => _collapsed = true);
    // 320ms collapse animation before calling back
    await Future.delayed(const Duration(milliseconds: 320));
    widget.onDone();
    // 500ms before follow-up bubble per spec
    await Future.delayed(const Duration(milliseconds: 500));
    widget.onCollapsed?.call();
  }

  @override
  void dispose() {
    _breatheCtrl.removeListener(_onTick);
    _breatheCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.of(context).accessibleNavigation;

    return AnimatedSize(
      duration: const Duration(milliseconds: 320),
      curve: Curves.easeIn,
      child: _collapsed
          ? const SizedBox.shrink()
          : _buildCard(reduceMotion),
    );
  }

  Widget _buildCard(bool reduceMotion) {
    return AnimatedOpacity(
      opacity: 1.0,
      duration: const Duration(milliseconds: 700),
      child: Container(
        margin: const EdgeInsets.fromLTRB(4, 4, 4, 10),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment(-0.5, -1),
            end: Alignment(0.5, 1),
            colors: [
              GQColors.primarySoft,       // EEF0FE
              Color(0xFFFBF1F4),           // warm mid
              GQColors.accentSoft,         // FFE8E8
            ],
            stops: [0.0, 0.6, 1.0],
          ),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Color(0x2E667EEA)),
          boxShadow: const [
            BoxShadow(
              color: Color(0x40667EEA),
              blurRadius: 24,
              offset: Offset(0, 8),
              spreadRadius: -12,
            ),
          ],
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 6),
            _buildBreathOrb(reduceMotion),
            const SizedBox(height: 4),
            _buildPhaseDots(),
            const SizedBox(height: 16),
            _buildControls(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'EXERCISE',
                style: TextStyle(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.6,
                  color: GQColors.primaryDk,
                ),
              ),
              const SizedBox(height: 2),
              const Text(
                // Verbatim from HTML
                '4-7-8 Breathing',
                style: TextStyle(
                  fontSize: 15.5,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink,
                  letterSpacing: -0.2,
                ),
              ),
              const SizedBox(height: 1),
              Text(
                // Verbatim from HTML (dynamic round)
                '~ 1 minute · Round $_currentRound of ${widget.totalRounds}',
                style: const TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                  color: GQColors.ink3,
                ),
              ),
            ],
          ),
        ),
        // "LIVE" badge
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(GQRadii.button),
            border: Border.all(color: Color(0x33667EEA)),
          ),
          child: const Text(
            // Verbatim from HTML
            'LIVE',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: GQColors.primaryDk,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBreathOrb(bool reduceMotion) {
    final phaseLabel = switch (_phase) {
      BreathPhase.inhale => 'BREATHE IN',
      BreathPhase.hold => 'HOLD',
      BreathPhase.exhale => 'BREATHE OUT',
    };
    final phaseSubLabel = switch (_phase) {
      BreathPhase.inhale => 'through your nose',
      BreathPhase.hold => 'hold steady',
      BreathPhase.exhale => 'out through your mouth',
    };

    return SizedBox(
      height: 148,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Breathing orb animation
          AnimatedBuilder(
            animation: _breatheCtrl,
            builder: (ctx, _) {
              double scale;
              if (reduceMotion || _paused) {
                scale = 0.75;
              } else {
                final t = _breatheCtrl.value;
                // 0-21.05%: scale 0.55→1.0 (inhale 4s)
                // 21.05-57.89%: scale 1.0 (hold 7s)
                // 57.89-100%: scale 1.0→0.55 (exhale 8s)
                if (t < 0.2105) {
                  scale = 0.55 + (0.45 * (t / 0.2105));
                } else if (t < 0.5789) {
                  scale = 1.0;
                } else {
                  scale = 1.0 - (0.45 * ((t - 0.5789) / 0.4211));
                }
              }
              return Transform.scale(
                scale: scale,
                child: Container(
                  width: 130,
                  height: 130,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      center: Alignment(-0.3, -0.4),
                      colors: [
                        Color(0x8C667EEA), // primary ~55% opacity
                        Color(0x73FF6B6B), // coral ~45% opacity
                      ],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Color(0x80667EEA),
                        blurRadius: 40,
                        offset: Offset(0, 12),
                        spreadRadius: -10,
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
          // Phase label overlay
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                phaseLabel,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.8,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 4),
              AnimatedBuilder(
                animation: _breatheCtrl,
                builder: (ctx, _) {
                  // Show elapsed seconds within current phase
                  final ms = _breatheCtrl.value * _totalDuration;
                  final double elapsed;
                  if (_phase == BreathPhase.inhale) {
                    elapsed = math.min(ms, _inhaleDuration.toDouble()) / 1000;
                  } else if (_phase == BreathPhase.hold) {
                    elapsed = math.min(ms - _inhaleDuration, _holdDuration.toDouble()) / 1000;
                  } else {
                    elapsed = math.min(ms - _inhaleDuration - _holdDuration, _exhaleDuration.toDouble()) / 1000;
                  }
                  return Text(
                    '${elapsed.toStringAsFixed(1)}s',
                    style: const TextStyle(
                      fontSize: 34,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.5,
                      height: 1,
                      color: Colors.white,
                    ),
                  );
                },
              ),
              const SizedBox(height: 3),
              Text(
                phaseSubLabel,
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPhaseDots() {
    // 3 dots: in · hold · out; active dot = full primary
    final phases = [BreathPhase.inhale, BreathPhase.hold, BreathPhase.exhale];
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        ...phases.map((p) {
          final active = p == _phase;
          return Container(
            margin: const EdgeInsets.symmetric(horizontal: 2),
            width: 18,
            height: 5,
            decoration: BoxDecoration(
              color: active
                  ? GQColors.primary
                  : const Color(0x40667EEA),
              borderRadius: BorderRadius.circular(GQRadii.button),
            ),
          );
        }),
        const SizedBox(width: 6),
        const Text(
          // Verbatim from HTML
          'in · hold · out',
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w700,
            color: GQColors.ink3,
          ),
        ),
      ],
    );
  }

  Widget _buildControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        // Pause button
        Semantics(
          button: true,
          label: _paused ? 'Resume exercise' : 'Pause exercise',
          child: GestureDetector(
            onTap: _togglePause,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(GQRadii.button),
                border: Border.all(color: GQColors.hair),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _paused ? Icons.play_arrow_rounded : Icons.pause_rounded,
                    size: 14,
                    color: GQColors.ink,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    _paused ? 'Resume' : 'Pause',
                    style: const TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        // "I'm done" link
        Semantics(
          button: true,
          label: "I'm done with the exercise",
          child: GestureDetector(
            onTap: _onDone,
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 4, vertical: 8),
              child: Text(
                // Verbatim from HTML
                "I'm done",
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink3,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// ExerciseCollapsedRow — the collapsed summary shown after completion.
/// Design source: GentleQuest_Chat_Active_States.html — Mockup C collapsed row.
/// Copy verbatim: "Done — you completed 3 rounds of grounding earlier today"
class ExerciseCollapsedRow extends StatelessWidget {
  const ExerciseCollapsedRow({
    super.key,
    this.label = 'Done — exercise complete',
  });

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      margin: const EdgeInsets.fromLTRB(4, 0, 4, 10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.65),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: GQColors.hair),
      ),
      child: Row(
        children: [
          const Text('🌱', style: TextStyle(fontSize: 14)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: GQColors.ink2,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
