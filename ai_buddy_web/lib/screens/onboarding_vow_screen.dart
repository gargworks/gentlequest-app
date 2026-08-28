/// Onboarding Vow — the first thing a new user sees.
///
/// Five vow lines appear one at a time with designed silences between them,
/// a seed companion arrives mid-breath at 3.4s, and a 'Begin' button fades
/// in at 16.6s. Tap anywhere advances to the next line immediately; Skip
/// jumps to the complete vow with Begin ready. Shown once
/// (SharedPreferences key: 'onboarding_vow_seen_v1').
///
/// Design principles:
///   • '988' is the only color in the sequence (coral, w800).
///   • No wordmark on this screen (P9).
///   • Reduced motion: rises become plain fades, timings halve, seed still
///     arrives mid-breath.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/companion.dart';
import '../theme/gq_theme.dart';
import '../theme/gq_tokens.dart';
import '../widgets/companion_painter.dart';
import 'welcome_screen.dart';

/// SharedPreferences key recording that the vow has been seen.
const String kOnboardingVowSeenKey = 'onboarding_vow_seen_v1';

/// The five vow lines, in order.
const List<String> _kVowLines = [
  'This is your companion.',
  'It will wait for you.',
  'It never punishes.',
  'What you say here stays here.',
  'If it gets bad, 988 is always one tap away — even offline.',
];

/// Cue times (seconds) for each line + the Begin button, at full speed.
const List<double> _kCueTimes = [1.2, 5.6, 8.5, 11.4, 14.6, 16.6];

/// The seed companion arrives at 3.4s.
const double _kSeedArriveTime = 3.4;

class OnboardingVowScreen extends StatefulWidget {
  const OnboardingVowScreen({super.key});

  /// Returns true if the vow has already been seen (SharedPreferences).
  static Future<bool> hasBeenSeen() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(kOnboardingVowSeenKey) ?? false;
  }

  @override
  State<OnboardingVowScreen> createState() => _OnboardingVowScreenState();
}

class _OnboardingVowScreenState extends State<OnboardingVowScreen>
    with TickerProviderStateMixin {
  late final AnimationController _master;
  late final AnimationController _breathe;
  late final Animation<double> _breatheAnim;

  /// Index of the last line that has been revealed (0-based). -1 = none yet.
  int _revealedCount = -1;
  bool _beginVisible = false;
  bool _seedVisible = false;
  bool _reducedMotion = false;
  bool _reduceMotion = false;
  // The first didChangeDependencies pass must ALWAYS apply, even when rm
  // equals the initial `false`. Without this the equality guard below
  // early-returns on first mount and the animation is never started at
  // all — the failure is invisible to tests because nothing asserts that
  // a perpetual animation is actually running.
  bool _motionGateInitialised = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // ADR-006: respect quiet-mode reduced motion.
    final rm = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (_motionGateInitialised && rm == _reduceMotion) return;
    _motionGateInitialised = true;
    _reduceMotion = rm;
    if (rm) {
      _breathe.stop();
    } else if (_seedVisible) {
      _breathe.repeat(reverse: true);
    }
  }

  @override
  void initState() {
    super.initState();
    _reducedMotion =
        WidgetsBinding.instance.platformDispatcher.accessibilityFeatures
                .reduceMotion ||
            false;
    final totalMs = (_kCueTimes.last * 1000).round();
    _master = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: totalMs),
    );
    _master.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _revealAll();
      }
    });
    _master.addListener(_onMasterTick);

    _breathe = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    );
    _breatheAnim = Tween<double>(begin: 1.0, end: 1.035).animate(
      CurvedAnimation(parent: _breathe, curve: Curves.easeInOut),
    );

    // Start the staggered sequence. Reduced motion halves the speed.
    if (_reducedMotion) {
      _master.duration = Duration(milliseconds: totalMs ~/ 2);
    }
    _master.forward();
  }

  void _onMasterTick() {
    final t = _master.value * _kCueTimes.last; // current seconds
    final reduced = _reducedMotion ? 2.0 : 1.0; // halved timings
    // Seed arrives at 3.4s (full speed) / 1.7s (reduced).
    final seedTime = _kSeedArriveTime / reduced;
    if (!_seedVisible && t >= seedTime) {
      setState(() {
        _seedVisible = true;
        _breathe.value = 0.5; // mid-breath
      });
      if (!_reduceMotion) _breathe.repeat(reverse: true);
    }
    // Reveal lines at their cue times.
    for (int i = 0; i < _kVowLines.length; i++) {
      final cue = _kCueTimes[i] / reduced;
      if (t >= cue && _revealedCount < i) {
        setState(() => _revealedCount = i);
      }
    }
    // Begin button at last cue.
    final beginCue = _kCueTimes.last / reduced;
    if (!_beginVisible && t >= beginCue) {
      setState(() => _beginVisible = true);
    }
  }

  void _revealAll() {
    setState(() {
      _revealedCount = _kVowLines.length - 1;
      _beginVisible = true;
      _seedVisible = true;
    });
    if (!_breathe.isAnimating && !_reduceMotion) {
      _breathe.value = 0.5;
      _breathe.repeat(reverse: true);
    }
  }

  /// Tap anywhere advances to the next cue immediately.
  void _advance() {
    final nextIndex = _revealedCount + 1;
    if (nextIndex >= _kVowLines.length) {
      // Past last line → show Begin.
      if (!_beginVisible) {
        _master.animateTo(1.0, duration: const Duration(milliseconds: 200));
        setState(() => _beginVisible = true);
      }
      return;
    }
    final targetFraction = _kCueTimes[nextIndex] / _kCueTimes.last;
    _master.animateTo(targetFraction,
        duration: const Duration(milliseconds: 250));
  }

  void _skip() {
    _master.stop();
    _revealAll();
  }

  Future<void> _onBegin() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(kOnboardingVowSeenKey, true);
    if (!mounted) return;
    // The CompanionProvider already initializes with Companion.fresh() in
    // its constructor, so a new user gets a fresh companion automatically.
    // Proceed to the existing welcome/compliance flow.
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const WelcomeScreen()),
    );
  }

  @override
  void dispose() {
    _master.removeListener(_onMasterTick);
    _master.dispose();
    _breathe.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Scaffold(
      body: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: _advance,
        child: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFFF8F7FF),
                Color(0xFFF2F1FE),
                Color(0xFFFBF6F6),
              ],
            ),
          ),
          child: SafeArea(
            child: Stack(
              children: [
                // Skip button — top-right, present from first frame.
                Positioned(
                  top: 10,
                  right: 16,
                  child: Opacity(
                    opacity: 0.55,
                    child: TextButton(
                      onPressed: _skip,
                      style: TextButton.styleFrom(
                        minimumSize: Size.zero,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 4),
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      child: Text(
                        'Skip',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: t.ink2,
                        ),
                      ),
                    ),
                  ),
                ),
                // Vow lines — centered vertically, accumulating.
                Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        for (int i = 0; i < _kVowLines.length; i++)
                          _VowLine(
                            index: i,
                            revealedCount: _revealedCount,
                            reducedMotion: _reducedMotion,
                            seedVisible: _seedVisible,
                            breatheAnim: _breatheAnim,
                          ),
                      ],
                    ),
                  ),
                ),
                // Begin button — bottom, stadium shape, fades in at 16.6s.
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: 48,
                  child: Center(
                    child: AnimatedOpacity(
                      opacity: _beginVisible ? 1.0 : 0.0,
                      duration: const Duration(milliseconds: 500),
                      child: _beginVisible
                          ? ElevatedButton(
                              onPressed: _onBegin,
                              style: ElevatedButton.styleFrom(
                                // primaryDk stays static — CTA fill w/ white text (theme exception).
                                backgroundColor: GQColors.primaryDk,
                                foregroundColor: Colors.white,
                                shape: const StadiumBorder(),
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 48, vertical: 16),
                                elevation: 0,
                              ),
                              child: const Text(
                                'Begin',
                                style: TextStyle(
                                  fontFamily: GQTypography.displayFamily,
                                  fontSize: 17,
                                  fontWeight: FontWeight.w700,
                                  color: Colors.white,
                                ),
                              ),
                            )
                          : const SizedBox.shrink(),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// A single vow line with its fade + rise animation, plus the seed companion
/// beneath line 1.
class _VowLine extends StatelessWidget {
  const _VowLine({
    required this.index,
    required this.revealedCount,
    required this.reducedMotion,
    required this.seedVisible,
    required this.breatheAnim,
  });

  final int index;
  final int revealedCount;
  final bool reducedMotion;
  final bool seedVisible;
  final Animation<double> breatheAnim;

  @override
  Widget build(BuildContext context) {
    final isRevealed = index <= revealedCount;
    // The most recently revealed line is "active" (ink, w700); older lines
    // soften to ink3/w600.
    final isActive = index == revealedCount;
    final line = _kVowLines[index];

    // The seed companion appears beneath line 1 (index 0).
    final showSeed = index == 0 && seedVisible;

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 700),
      switchInCurve: const Cubic(0.22, 0.94, 0.32, 1),
      switchOutCurve: const Cubic(0.22, 0.94, 0.32, 1),
      transitionBuilder: (child, anim) {
        if (reducedMotion) {
          return FadeTransition(opacity: anim, child: child);
        }
        return FadeTransition(
          opacity: anim,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 8 / 300),
              end: Offset.zero,
            ).animate(anim),
            child: child,
          ),
        );
      },
      child: isRevealed
          ? Padding(
              key: ValueKey('line_$index'),
              padding: const EdgeInsets.only(bottom: 24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildRichLine(context, line, isActive),
                  if (showSeed) ...[
                    const SizedBox(height: 16),
                    ScaleTransition(
                      scale: breatheAnim,
                      alignment: Alignment.bottomCenter,
                      child: CustomPaint(
                        size: const Size.square(76),
                        painter: const CompanionPainter(
                          stage: GrowthStage.seed,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            )
          : const SizedBox.shrink(),
    );
  }

  /// Builds the vow line, with '988' in coral w800 if present.
  Widget _buildRichLine(BuildContext context, String line, bool isActive) {
    final t = GQTheme.of(context);
    final color = isActive ? t.ink : t.ink3;
    final weight = isActive ? FontWeight.w700 : FontWeight.w600;
    final style = TextStyle(
      fontFamily: GQTypography.displayFamily,
      fontSize: 26,
      fontWeight: weight,
      letterSpacing: -0.4,
      height: 1.4,
      color: color,
    );

    // Special-case the 988 line: '988' in coral w800.
    if (line.contains('988')) {
      final parts = line.split('988');
      return RichText(
        textAlign: TextAlign.center,
        text: TextSpan(
          children: [
            TextSpan(text: parts[0], style: style),
            TextSpan(
              text: '988',
              style: style.copyWith(
                color: t.coral,
                fontWeight: FontWeight.w800,
              ),
            ),
            TextSpan(
              text: parts.length > 1 ? parts.sublist(1).join('988') : '',
              style: style,
            ),
          ],
        ),
      );
    }
    return Text(
      line,
      textAlign: TextAlign.center,
      style: style,
    );
  }
}
