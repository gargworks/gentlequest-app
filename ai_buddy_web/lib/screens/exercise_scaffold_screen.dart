import 'package:flutter/material.dart';
import '../theme/gq_theme.dart';
import '../widgets/exercise_card_scaffold.dart';

/// ExerciseScaffoldScreen — R1D16 Exercise Cards (standalone fullscreen route)
///
/// Wraps [ExerciseCardScaffold] with fullscreen chrome: status-bar-aware
/// gradient background + safe-area padding.  Launched via Navigator.push from
/// the Library card tap, inline "Open fullscreen" CTA, or chat deep-link.
///
/// Design source: docs/design/refs/htmls/GentleQuest_Exercise_Cards.html
/// Mockup A/B/C — Standalone fullscreen (left panel of each pair).
///
/// Principle alignment: P2 (back always available), P3 (one CTA), P7 (skip),
/// P11 (inline → standalone upgrade path).
class ExerciseScaffoldScreen extends StatelessWidget {
  const ExerciseScaffoldScreen({
    super.key,
    required this.type,
  });

  final ExerciseType type;

  /// Convenience push helper — avoids boilerplate at call sites.
  static Future<void> show(BuildContext context, ExerciseType type) {
    return Navigator.of(context).push<void>(
      PageRouteBuilder(
        pageBuilder: (ctx, anim, _) =>
            ExerciseScaffoldScreen(type: type),
        transitionsBuilder: (ctx, anim, _, child) {
          return SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 1),
              end: Offset.zero,
            ).animate(CurvedAnimation(
              parent: anim,
              curve: Curves.easeOutCubic,
            )),
            child: child,
          );
        },
        transitionDuration: const Duration(milliseconds: 320),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: t.bg,
      body: Stack(
        children: [
          // Soft gradient background per HTML: radial gradient #EEF0FE → #F8F7FF → #FBF1F4
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  center: const Alignment(0, -0.3),
                  radius: 1.1,
                  colors: [
                    t.primarySoft, // EEF0FE
                    t.bg, // F8F7FF
                    const Color(0xFFFBF1F4), // warm tint per HTML
                  ],
                  stops: const [0.0, 0.60, 1.0],
                ),
              ),
            ),
          ),
          // Safe area + content
          SafeArea(
            child: ExerciseCardScaffold(
              type: type,
              exerciseContext: ExerciseContext.standalone,
              onDone: () => Navigator.of(context).maybePop(),
              onSkip: () => Navigator.of(context).maybePop(),
            ),
          ),
        ],
      ),
    );
  }
}
