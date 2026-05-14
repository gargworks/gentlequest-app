import 'package:flutter/material.dart';
import '../theme/gq_tokens.dart';

/// AIThinkingIndicator — State A (R1D7 Chat Active States)
///
/// 3-dot wave pill shown in the AI chat bubble position while waiting for
/// a response. Dots use GQColors.primary (#667EEA) with 800ms stagger wave.
/// Entry animation: 200ms fade-in.
///
/// Design source: GentleQuest_Chat_Active_States.html — Mockup A.
class AIThinkingIndicator extends StatefulWidget {
  const AIThinkingIndicator({super.key});

  @override
  State<AIThinkingIndicator> createState() => _AIThinkingIndicatorState();
}

class _AIThinkingIndicatorState extends State<AIThinkingIndicator>
    with SingleTickerProviderStateMixin {
  // 800ms wave — matches HTML @keyframes gqDot 800ms ease-in-out infinite
  late final AnimationController _ctrl = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 800),
  )..repeat();

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.of(context).accessibleNavigation;

    return AnimatedOpacity(
      opacity: 1.0,
      duration: const Duration(milliseconds: 200), // 200ms fade-in entry
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(18),
            topRight: Radius.circular(18),
            bottomRight: Radius.circular(18),
            bottomLeft: Radius.circular(6),
          ),
          border: Border.all(color: GQColors.hair),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0A1F1B3A),
              blurRadius: 2,
              offset: Offset(0, 1),
            ),
          ],
        ),
        child: Semantics(
          label: 'Alex is thinking',
          child: reduceMotion
              ? _staticDots()
              : AnimatedBuilder(
                  animation: _ctrl,
                  builder: (context, _) => _waveDots(_ctrl.value),
                ),
        ),
      ),
    );
  }

  Widget _staticDots() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (i) {
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 2.5),
          width: 6,
          height: 6,
          decoration: const BoxDecoration(
            color: GQColors.primary,
            shape: BoxShape.circle,
          ),
        );
      }),
    );
  }

  Widget _waveDots(double t) {
    // Stagger: dot i delays by (i+1)*100ms = phase offset 0.1, 0.2, 0.3
    // Maps HTML: .d1 100ms, .d2 200ms, .d3 300ms
    double dotOpacity(int i) {
      final phase = (t + (i + 1) * 0.1) % 1.0;
      // 0–0.3: peak at 0.3 (translateY(-3px) opacity 1)
      // 0.6–1.0: valley (opacity 0.45)
      if (phase < 0.3) {
        return 0.45 + (0.55 * (phase / 0.3));
      } else if (phase < 0.6) {
        return 1.0 - (0.55 * ((phase - 0.3) / 0.3));
      }
      return 0.45;
    }

    double dotOffset(int i) {
      final phase = (t + (i + 1) * 0.1) % 1.0;
      if (phase < 0.3) {
        return -3.0 * (phase / 0.3);
      } else if (phase < 0.6) {
        return -3.0 * (1.0 - (phase - 0.3) / 0.3);
      }
      return 0.0;
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (i) {
        return Transform.translate(
          offset: Offset(0, dotOffset(i)),
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 2.5),
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              color: GQColors.primary.withValues(alpha: dotOpacity(i)),
              shape: BoxShape.circle,
            ),
          ),
        );
      }),
    );
  }
}
