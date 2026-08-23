import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';

/// Design Authority D6/D7 — the button that replaces raw ElevatedButton.
///
/// Four variants:
///   - [GQButtonVariant.primary] — fills [GQColors.primaryDk] (5.30:1 white
///     text, D3). The default for positive actions.
///   - [GQButtonVariant.crisis] — fills [GQColors.dangerInk] (4.75:1). For
///     crisis and destructive actions specifically — not a generic "warning"
///     button. See D3: coral cannot carry white text at any shade tested.
///   - [GQButtonVariant.ghost] — outlined, transparent fill, primaryDk text.
///   - [GQButtonVariant.text] — no fill, no border, primaryDk text only.
///
/// Motion: [GQDurations.tap] (200ms, scale to .98) on press, using
/// [GQMotion.standardCurve]. Haptics: light impact on tap by default, per
/// D7's haptics map ("light impact on mood/chip select") extended to button
/// taps generally — never on a disabled/loading press, and never as a
/// punishment buzz. Set [haptic] to false for pure-navigation affordances
/// (a button whose only effect is a push) — haptics mark consequence, not
/// motion; if every tap buzzes, none of them mean anything.
///
/// Touch target: [GQA11y.minTouchTarget] (44pt) is enforced via minHeight.
class GQButton extends StatefulWidget {
  const GQButton({
    super.key,
    required this.label,
    this.onPressed,
    this.variant = GQButtonVariant.primary,
    this.size = GQButtonSize.medium,
    this.loading = false,
    this.leadingIcon,
    this.fullWidth = true,
    this.haptic = true,
  });

  final String label;

  /// Null (or [loading] true) renders the button disabled.
  final VoidCallback? onPressed;

  final GQButtonVariant variant;
  final GQButtonSize size;

  /// Shows a spinner in place of [label] and suppresses taps. The button
  /// keeps its size (no layout jump between loading and label states).
  final bool loading;

  final IconData? leadingIcon;

  final bool fullWidth;

  /// False for pure-navigation taps (no consequence beyond a push). See the
  /// class doc.
  final bool haptic;

  @override
  State<GQButton> createState() => _GQButtonState();
}

class _GQButtonState extends State<GQButton> {
  bool _pressed = false;

  bool get _enabled => widget.onPressed != null && !widget.loading;

  void _setPressed(bool value) {
    if (!_enabled) return;
    setState(() => _pressed = value);
  }

  @override
  Widget build(BuildContext context) {
    final theme = GQTheme.of(context);
    final colors = _colorsFor(widget.variant, _enabled, theme);
    final height = switch (widget.size) {
      GQButtonSize.small => 40.0,
      GQButtonSize.medium => 52.0,
      GQButtonSize.large => 56.0,
    };

    return GestureDetector(
      onTapDown: (_) => _setPressed(true),
      onTapCancel: () => _setPressed(false),
      onTapUp: (_) => _setPressed(false),
      onTap: _enabled
          ? () {
              if (widget.haptic) HapticFeedback.lightImpact();
              widget.onPressed!();
            }
          : null,
      child: AnimatedScale(
        scale: _pressed ? 0.98 : 1.0,
        duration: GQDurations.tap,
        curve: GQMotion.standardCurve,
        child: Container(
          constraints: BoxConstraints(
            minHeight: height.clamp(GQA11y.minTouchTarget, double.infinity),
          ),
          width: widget.fullWidth ? double.infinity : null,
          padding: const EdgeInsets.symmetric(horizontal: GQSpacing.xl),
          decoration: BoxDecoration(
            color: colors.fill,
            borderRadius: BorderRadius.circular(GQRadii.button),
            border: colors.border != null
                ? Border.all(color: colors.border!, width: 1.5)
                : null,
          ),
          child: Center(
            child: widget.loading
                ? SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      valueColor: AlwaysStoppedAnimation(colors.foreground),
                    ),
                  )
                : Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (widget.leadingIcon != null) ...[
                        Icon(widget.leadingIcon, size: 18, color: colors.foreground),
                        const SizedBox(width: GQSpacing.sm),
                      ],
                      Flexible(
                        child: Text(
                          widget.label,
                          style: GQTypography.body.copyWith(
                            color: colors.foreground,
                            fontWeight: FontWeight.w700,
                          ),
                          overflow: TextOverflow.ellipsis,
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

enum GQButtonVariant { primary, crisis, ghost, text }

enum GQButtonSize { small, medium, large }

class _ButtonColors {
  const _ButtonColors({required this.fill, required this.foreground, this.border});
  final Color fill;
  final Color foreground;
  final Color? border;
}

_ButtonColors _colorsFor(GQButtonVariant variant, bool enabled, GQTheme theme) {
  final disabledFill = theme.ink3.withValues(alpha: 0.16);
  final disabledFg = theme.ink3;

  switch (variant) {
    case GQButtonVariant.primary:
      return enabled
          ? const _ButtonColors(fill: GQColors.primaryDk, foreground: Colors.white)
          : _ButtonColors(fill: disabledFill, foreground: disabledFg);
    case GQButtonVariant.crisis:
      return enabled
          ? const _ButtonColors(fill: GQColors.dangerInk, foreground: Colors.white)
          : _ButtonColors(fill: disabledFill, foreground: disabledFg);
    case GQButtonVariant.ghost:
      return enabled
          ? const _ButtonColors(
              fill: Colors.transparent,
              foreground: GQColors.primaryDk,
              border: GQColors.primaryDk,
            )
          : _ButtonColors(fill: Colors.transparent, foreground: disabledFg, border: theme.hair);
    case GQButtonVariant.text:
      return enabled
          ? const _ButtonColors(fill: Colors.transparent, foreground: GQColors.primaryDk)
          : _ButtonColors(fill: Colors.transparent, foreground: disabledFg);
  }
}
