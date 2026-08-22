/// Silent Witness — the companion's quiet presence in the chat room.
///
/// A small (28-30px) simplified companion anchored bottom-left, above the
/// input bar. Three behaviors:
///   • breathe — normal 5.6s loop, scale 1.0 → 1.035, origin bottom-center.
///   • settle — breathing stretches to 8.4s, amplitude drops to 1.018, the
///     whole form leans 1.6° toward the input. Transitions over 600ms
///     (GQDurations.companionStageChange), ease-out. Reverts after 10s of
///     non-heavy typing.
///   • stay (crisis) — transform frozen; no new tween targets it while a
///     crisis surface is mounted.
///
/// Tap shows a warm GQBanner: "I'm always glad to see you. No rush."
/// A 22px soft shadow ellipse appears under it in settle / crisis states.
library;

import 'package:flutter/material.dart';

import '../models/companion.dart';
import '../theme/gq_tokens.dart';
import 'companion_painter.dart';
import 'gq/gq.dart';

/// The three behavioral states the witness can be in.
enum WitnessState { breathe, settle, stay }

/// A silent companion witness anchored bottom-left above the input bar.
///
/// Renders a [CompanionPainter] in simplified mode at ~28px. The caller
/// must wrap this in its own [Positioned] inside a [Stack] — this widget
/// owns only its animation + tap behavior, not its placement. (It used to
/// also wrap itself in a Positioned, which crashed with "competing
/// ParentDataWidgets" the moment a caller did what this doc always said to
/// do and positioned it externally too.)
class SilentWitness extends StatefulWidget {
  const SilentWitness({
    super.key,
    this.state = WitnessState.breathe,
    this.stage = GrowthStage.seed,
  });

  /// Current behavioral state. The parent drives this from heavy-language
  /// detection (settle) and crisis-surface mounting (stay).
  final WitnessState state;

  /// Growth stage to paint. Defaults to [GrowthStage.seed].
  final GrowthStage stage;

  @override
  State<SilentWitness> createState() => SilentWitnessState();
}

class SilentWitnessState extends State<SilentWitness>
    with TickerProviderStateMixin {
  late final AnimationController _breatheController;
  late Animation<double> _breatheAnimation;
  late final AnimationController _leanController;
  late Animation<double> _leanAnimation;

  /// Current lean angle in degrees (0 = upright, 1.6 = settled toward input).
  double _leanDeg = 0.0;

  /// Whether the soft shadow ellipse is shown (settle / stay only).
  bool get _showShadow =>
      widget.state == WitnessState.settle ||
      widget.state == WitnessState.stay;

  @override
  void initState() {
    super.initState();
    _breatheController = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    );
    _leanController = AnimationController(
      vsync: this,
      duration: GQDurations.companionStageChange,
    );
    _breatheAnimation = _buildBreatheAnimation(WitnessState.breathe);
    _leanAnimation = Tween<double>(begin: 0.0, end: 1.6).animate(
      CurvedAnimation(parent: _leanController, curve: Curves.easeOut),
    )..addListener(() {
        if (mounted) setState(() => _leanDeg = _leanAnimation.value);
      });
    // Return-after-absence: start mid-cycle (phase -2.8s = half-breath).
    _breatheController.value = 0.5;
    _breatheController.repeat(reverse: true);
  }

  Animation<double> _buildBreatheAnimation(WitnessState s) {
    final (duration, endScale) = switch (s) {
      WitnessState.settle => (
          const Duration(milliseconds: 8400),
          1.018,
        ),
      _ => (GQDurations.breathe, 1.035),
    };
    _breatheController.duration = duration;
    return Tween<double>(begin: 1.0, end: endScale).animate(
      CurvedAnimation(parent: _breatheController, curve: Curves.easeInOut),
    );
  }

  @override
  void didUpdateWidget(covariant SilentWitness oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.state != widget.state) {
      _onStateChanged(oldWidget.state, widget.state);
    }
  }

  void _onStateChanged(WitnessState oldState, WitnessState newState) {
    switch (newState) {
      case WitnessState.breathe:
        // Revert lean + restore normal breathing.
        _leanController.reverse();
        _breatheAnimation = _buildBreatheAnimation(WitnessState.breathe);
        _breatheController.repeat(reverse: true);
        setState(() {});
      case WitnessState.settle:
        // Stretch breathing to 8.4s, drop amplitude, lean 1.6° toward input.
        // Transition over 600ms ease-out.
        _breatheAnimation = _buildBreatheAnimation(WitnessState.settle);
        _breatheController.repeat(reverse: true);
        _leanController.forward(from: _leanController.value);
        setState(() {});
      case WitnessState.stay:
        // Crisis: freeze the transform. Stop breathing, no new tween targets.
        _breatheController.stop();
        _leanController.stop();
        setState(() {});
    }
  }

  @override
  void dispose() {
    _breatheController.dispose();
    _leanController.dispose();
    super.dispose();
  }

  void _showWitnessBanner(BuildContext context) {
    GQBanner.show(
      context,
      message: "I'm always glad to see you. No rush.",
      category: GQBannerCategory.warm,
      duration: const Duration(seconds: 2),
    );
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () => _showWitnessBanner(context),
      child: SizedBox(
        width: 30,
        height: 44,
        child: Stack(
          clipBehavior: Clip.none,
          alignment: Alignment.bottomLeft,
          children: [
            // Soft shadow ellipse — settle / stay only.
            if (_showShadow)
              Positioned(
                left: 4,
                bottom: 0,
                child: Container(
                  width: 22,
                  height: 6,
                  decoration: BoxDecoration(
                    color: GQIllustration.companionSlateLavender.withValues(alpha: 0.5),
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              ),
            // Companion form — lean applied via transform, scale via
            // breathing. Origin is bottom-center so the lean pivots from
            // the ground.
            Transform.translate(
              offset: const Offset(0, 0),
              child: Transform(
                alignment: Alignment.bottomCenter,
                transform: Matrix4.rotationZ(_leanDeg * 3.14159265 / 180),
                child: ScaleTransition(
                  scale: _breatheAnimation,
                  alignment: Alignment.bottomCenter,
                  child: CustomPaint(
                    size: const Size.square(30),
                    painter: CompanionPainter(
                      stage: widget.stage,
                      simplified: true,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
