import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../theme/gq_tokens.dart';

/// Design Authority D6 — the chip that replaces raw ChoiceChip/FilterChip.
///
/// A selectable pill (radius [GQRadii.button], 999 — fully rounded) with an
/// optional leading emoji/icon slot. D7: light haptic impact on select, and
/// the select spring (scale to 1.04 over [GQDurations.select]) rather than
/// a flat tap — this is the "selection states don't celebrate" fix the
/// design audit called out (picking a mood was a border-color change; this
/// gives every GQChip selection the same small, real motion).
class GQChip extends StatelessWidget {
  const GQChip({
    super.key,
    required this.label,
    required this.selected,
    required this.onSelected,
    this.emoji,
  });

  final String label;
  final bool selected;
  final ValueChanged<bool> onSelected;

  /// Leading emoji/glyph, rendered as plain text (not an Icon) so any emoji
  /// works without an icon-font mapping.
  final String? emoji;

  @override
  Widget build(BuildContext context) {
    return _SelectSpring(
      onTap: () {
        HapticFeedback.lightImpact();
        onSelected(!selected);
      },
      child: AnimatedContainer(
        duration: GQDurations.fade,
        curve: GQMotion.standardCurve,
        padding: const EdgeInsets.symmetric(horizontal: GQSpacing.lg, vertical: GQSpacing.sm),
        constraints: const BoxConstraints(minHeight: GQA11y.minTouchTarget),
        decoration: BoxDecoration(
          color: selected ? GQColors.primarySoft : GQColors.surface,
          borderRadius: BorderRadius.circular(GQRadii.button),
          border: Border.all(
            color: selected ? GQColors.primaryDk : GQColors.hair,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (emoji != null) ...[
              Text(emoji!, style: const TextStyle(fontSize: 16)),
              const SizedBox(width: GQSpacing.xs),
            ],
            Text(
              label,
              style: GQTypography.caption.copyWith(
                color: selected ? GQColors.primaryDk : GQColors.ink2,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Shared select-spring press wrapper (scale to 1.04, D7) — also used
/// internally by anything that wants the "this is a selection, not a tap"
/// motion without pulling in all of [GQCard].
class _SelectSpring extends StatefulWidget {
  const _SelectSpring({required this.child, required this.onTap});
  final Widget child;
  final VoidCallback onTap;

  @override
  State<_SelectSpring> createState() => _SelectSpringState();
}

class _SelectSpringState extends State<_SelectSpring> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _pressed = true),
      onTapCancel: () => setState(() => _pressed = false),
      onTapUp: (_) => setState(() => _pressed = false),
      onTap: widget.onTap,
      child: AnimatedScale(
        scale: _pressed ? 1.04 : 1.0,
        duration: GQDurations.select,
        curve: GQMotion.standardCurve,
        child: widget.child,
      ),
    );
  }
}
