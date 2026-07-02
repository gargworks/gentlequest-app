import 'package:flutter/material.dart';

import '../dhiwise/helpers/color_filters_backup.dart' show saturationMatrix;
import '../services/low_stim_service.dart';

/// Low-stim "quiet mode" — v1.5.0 ADHD update (ADR-006),
/// docs/V1_5_0_ADHD_UPDATE_SCOPE.md workstream 2b: "one settings toggle
/// swaps the active color theme for a low-saturation/low-motion variant
/// app-wide."
///
/// This intentionally does NOT introduce a parallel theming system.
/// theme/gq_tokens.dart (GQColors) stays the single source of truth for
/// color values — full ThemeData/ColorScheme migration is still a
/// downstream task per that file's own header comment, and most call sites
/// reference `GQColors.*` as compile-time `const`, so swapping the palette
/// at the token level isn't feasible without a much larger refactor.
/// Instead this widget filters the *rendered* output app-wide:
///   • [ColorFiltered] applies a saturation-reduction matrix (reusing the
///     `saturationMatrix()` helper already in the codebase, previously
///     unused/"kept for future design experiments").
///   • [MediaQuery.disableAnimations] is flipped on for the subtree, which
///     is the same reduced-motion signal the app already checks in
///     `wellness_dashboard_screen.dart` (`_showCheckRipple`) — extending
///     that existing pattern rather than inventing a new one.
///
/// Wrapped once around MaterialApp's routed content (`builder:` in
/// main.dart), so it's live app-wide the instant the preference flips —
/// no new screens, no per-screen wiring.
class LowStimOverlay extends StatelessWidget {
  const LowStimOverlay({super.key, required this.child});

  final Widget child;

  /// Desaturation factor passed to [saturationMatrix]: 1.0 = untouched,
  /// 0.0 = full grayscale. 0.5 keeps hues distinguishable (mood colors,
  /// the coral CTA) while visibly muting the palette — a conservative,
  /// system-consistent choice since the scope brief doesn't specify an
  /// exact value.
  static const double kLowStimSaturation = 0.5;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: LowStimService.lowStimNotifier,
      // Passed through as `child` so the routed app subtree itself never
      // rebuilds when the preference flips — only the filter wrapper does.
      child: child,
      builder: (context, lowStim, cachedChild) {
        final content = cachedChild ?? const SizedBox.shrink();
        if (!lowStim) return content;

        Widget result = ColorFiltered(
          colorFilter: ColorFilter.matrix(
            saturationMatrix(kLowStimSaturation),
          ),
          child: content,
        );

        final mq = MediaQuery.maybeOf(context);
        if (mq != null) {
          result = MediaQuery(
            data: mq.copyWith(disableAnimations: true),
            child: result,
          );
        }
        return result;
      },
    );
  }
}
