import 'package:flutter/material.dart';
import 'package:ai_buddy_web/theme/gq_theme.dart';

/// A compact pill shown on the right side of the app bar while the
/// companion is reconnecting.
///
/// - Height 26, padding 11h, stadium radius, fill amberSoft, border 1px
///   amber at 0.25 alpha.
/// - Leading 6px amber dot, 6px gap, label 12/w700/inkOnAmber.
/// - Copy: "Reconnecting" while retrying.
/// - Hidden when online (returns [SizedBox.shrink]).
/// - In the unreachable state the pill is NOT shown either — the app bar
///   label changes from "YOU'RE WITH" to "CAN'T REACH" and the name colour
///   drops to ink2 (handled by the app bar, not this widget).
class ConnectionPill extends StatelessWidget {
  final bool visible;

  const ConnectionPill({super.key, required this.visible});

  @override
  Widget build(BuildContext context) {
    if (!visible) return const SizedBox.shrink();

    final t = GQTheme.of(context);
    return Container(
      height: 26,
      padding: const EdgeInsets.symmetric(horizontal: 11),
      decoration: BoxDecoration(
        color: t.amberSoft,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(
          color: t.amber.withValues(alpha: 0.25),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              color: t.amber,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            'Reconnecting',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: t.inkOnAmber,
            ),
          ),
        ],
      ),
    );
  }
}
