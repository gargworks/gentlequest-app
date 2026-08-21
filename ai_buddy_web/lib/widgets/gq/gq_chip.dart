import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../theme/gq_tokens.dart';

/// Compact horizontal pill (the original variant) or a full-width [block]
/// with its own radius/fill contract — see [GQChipVariant].
enum GQChipVariant { pill, block }

/// Design Authority D6 — the chip that replaces raw ChoiceChip/FilterChip.
///
/// [GQChipVariant.pill] (default): a compact stadium pill (radius
/// [GQRadii.button]) with an optional leading emoji/icon slot — context
/// chips, mood-entry tags.
///
/// [GQChipVariant.block]: a full-width option row (radius [GQRadii.card],
/// min-height 56) — WO-5.1's Likert options and any other single-column
/// choice list. Selected fills [GQColors.primaryDk] solid with white text
/// (a pill's soft-tint selection reads too quiet at this size); unselected
/// is [GQColors.surface] with a [GQColors.hair] border. Optional [caption]
/// renders as a small trailing label (e.g. a Likert numeric value) — the
/// tap target stays the whole chip, never the caption alone.
///
/// D7: light haptic impact on select, and the select spring (scale to 1.04
/// over [GQDurations.select]) rather than a flat tap — this is the
/// "selection states don't celebrate" fix the design audit called out
/// (picking a mood was a border-color change; this gives every GQChip
/// selection the same small, real motion).
class GQChip extends StatelessWidget {
  const GQChip({
    super.key,
    required this.label,
    required this.selected,
    required this.onSelected,
    this.emoji,
    this.variant = GQChipVariant.pill,
    this.caption,
  });

  final String label;
  final bool selected;
  final ValueChanged<bool> onSelected;

  /// Leading emoji/glyph, rendered as plain text (not an Icon) so any emoji
  /// works without an icon-font mapping.
  final String? emoji;

  final GQChipVariant variant;

  /// [GQChipVariant.block] only: an optional trailing small caption (e.g.
  /// a Likert option's raw numeric value) beside the label.
  final String? caption;

  @override
  Widget build(BuildContext context) {
    final isBlock = variant == GQChipVariant.block;
    return _SelectSpring(
      onTap: () {
        HapticFeedback.lightImpact();
        onSelected(!selected);
      },
      child: AnimatedContainer(
        duration: GQDurations.fade,
        curve: GQMotion.standardCurve,
        width: isBlock ? double.infinity : null,
        padding: EdgeInsets.symmetric(
          horizontal: GQSpacing.lg,
          vertical: isBlock ? GQSpacing.md : GQSpacing.sm,
        ),
        constraints: BoxConstraints(
          minHeight: isBlock ? 56.0 : GQA11y.minTouchTarget,
        ),
        decoration: BoxDecoration(
          color: isBlock
              ? (selected ? GQColors.primaryDk : GQColors.surface)
              : (selected ? GQColors.primarySoft : GQColors.surface),
          borderRadius: BorderRadius.circular(isBlock ? GQRadii.card : GQRadii.button),
          border: isBlock && selected
              ? null
              : Border.all(
                  color: selected ? GQColors.primaryDk : GQColors.hair,
                  width: selected ? 1.5 : 1,
                ),
        ),
        child: Row(
          mainAxisSize: isBlock ? MainAxisSize.max : MainAxisSize.min,
          children: [
            if (emoji != null) ...[
              Text(emoji!, style: const TextStyle(fontSize: 16)),
              const SizedBox(width: GQSpacing.xs),
            ],
            Flexible(
              child: Text(
                label,
                style: GQTypography.caption.copyWith(
                  color: isBlock
                      ? (selected ? Colors.white : GQColors.ink)
                      : (selected ? GQColors.primaryDk : GQColors.ink2),
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            if (isBlock && caption != null) ...[
              const SizedBox(width: GQSpacing.sm),
              Text(
                caption!,
                style: GQTypography.micro.copyWith(
                  color: selected ? Colors.white.withValues(alpha: 0.85) : GQColors.ink2,
                ),
              ),
            ],
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
