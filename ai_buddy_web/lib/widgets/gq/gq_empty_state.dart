import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';
import 'gq_button.dart';

/// Design Authority D6 — "empty states are Center(child: Text(...)) or
/// nothing. Emptiness is where warmth is most needed and the app is
/// coldest there."
///
/// One shape for every empty state: an illustration slot (any widget —
/// this doesn't prescribe the flat-geometric illustration style, it just
/// gives it a consistent home), a line of copy, and an optional action.
/// Screens should stop hand-rolling `Center(child: Text('No entries yet'))`.
class GQEmptyState extends StatelessWidget {
  const GQEmptyState({
    super.key,
    required this.illustration,
    required this.line,
    this.sub,
    this.actionLabel,
    this.onAction,
  });

  /// The illustration slot. Pass any widget — an Icon, a custom painter, an
  /// SVG. Sized to a consistent 96x96 box.
  final Widget illustration;

  final String line;

  /// Optional second line, quieter than [line] — e.g. reassurance that
  /// nothing was lost, or a hint at what caused the empty/error state.
  final String? sub;

  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: GQSpacing.xxl, vertical: GQSpacing.xxxl),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(width: 96, height: 96, child: illustration),
          const SizedBox(height: GQSpacing.xl),
          Text(
            line,
            textAlign: TextAlign.center,
            style: GQTypography.body.copyWith(color: GQColors.ink2),
          ),
          if (sub != null) ...[
            const SizedBox(height: GQSpacing.xs),
            Text(
              sub!,
              textAlign: TextAlign.center,
              // D3: ink3 never sets text below 14px — caption (13px) pairs
              // with ink2 even for de-emphasized copy like this.
              style: GQTypography.caption.copyWith(color: GQColors.ink2),
            ),
          ],
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: GQSpacing.xl),
            GQButton(
              label: actionLabel!,
              onPressed: onAction,
              variant: GQButtonVariant.ghost,
              fullWidth: false,
            ),
          ],
        ],
      ),
    );
  }
}
