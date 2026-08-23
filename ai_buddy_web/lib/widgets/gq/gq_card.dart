import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';

/// Design Authority D6 — the card that replaces raw Card(elevation: 4).
///
/// The design audit's "elevation soup" finding: mocks use one soft,
/// long-throw shadow recipe (`0 12px 26px -10px rgba(102,126,234,.55)`);
/// shipped screens used Material's default elevation, "the harsh, tight,
/// gray Android shadow." This card hard-codes the mock recipe as the only
/// legal shadow — screens should never set their own BoxShadow.
///
/// Radius: [GQRadii.card] (16) by default, [GQRadii.cardLg] (20) via
/// [large]. Optional [onTap] gets the D7 selection spring: scale to 1.04
/// over [GQDurations.select] (220ms) plus a light haptic by default — for
/// cards that function as selectable choices (e.g. a mood option), not
/// generic navigation taps, which should feel like [GQButton]'s tap (0.98
/// scale), not a selection (1.04 scale). Pass [isSelectable] to opt into the
/// select spring instead of a flat press.
///
/// Set [haptic] to false for pure-navigation cards (a card whose only
/// effect is a push) — haptics mark consequence, not motion; if every tap
/// buzzes, none of them mean anything.
class GQCard extends StatefulWidget {
  const GQCard({
    super.key,
    required this.child,
    this.onTap,
    this.large = false,
    this.isSelectable = false,
    this.selected = false,
    this.padding = const EdgeInsets.all(GQSpacing.lg),
    this.color,
    this.haptic = true,
  });

  final Widget child;
  final VoidCallback? onTap;
  final bool large;

  /// If true, [onTap] triggers the D7 select spring (scale to 1.04) instead
  /// of a flat tap. Use for cards that ARE the choice (mood option, chip-like
  /// card), not cards that merely navigate somewhere.
  final bool isSelectable;

  /// Only meaningful with [isSelectable]: draws a primary-tinted border/ring
  /// when true, matching the "selection states celebrate" requirement (D7 —
  /// the design audit flagged mood selection shipping as a flat border-color
  /// change instead of a real celebration).
  final bool selected;

  final EdgeInsets padding;
  final Color? color;

  /// False for pure-navigation taps (no consequence beyond a push). See the
  /// class doc.
  final bool haptic;

  @override
  State<GQCard> createState() => _GQCardState();
}

class _GQCardState extends State<GQCard> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final theme = GQTheme.of(context);
    final radius = widget.large ? GQRadii.cardLg : GQRadii.card;
    final tappable = widget.onTap != null;
    final cardColor = widget.color ?? theme.surface;

    double scale = 1.0;
    if (tappable && _pressed) {
      scale = widget.isSelectable ? 1.04 : 0.98;
    }

    return GestureDetector(
      onTapDown: tappable ? (_) => setState(() => _pressed = true) : null,
      onTapCancel: tappable ? () => setState(() => _pressed = false) : null,
      onTapUp: tappable ? (_) => setState(() => _pressed = false) : null,
      onTap: tappable
          ? () {
              if (widget.haptic) HapticFeedback.lightImpact();
              widget.onTap!();
            }
          : null,
      child: AnimatedScale(
        scale: scale,
        duration: widget.isSelectable ? GQDurations.select : GQDurations.tap,
        curve: GQMotion.standardCurve,
        child: AnimatedContainer(
          duration: GQDurations.fade,
          padding: widget.padding,
          decoration: BoxDecoration(
            color: cardColor,
            borderRadius: BorderRadius.circular(radius),
            border: widget.isSelectable && widget.selected
                ? Border.all(color: GQColors.primaryDk, width: 2)
                : Border.all(color: theme.hair, width: 1),
            boxShadow: [
              // The mocks' one shadow recipe: soft, long-throw, low alpha.
              // 0 12px 26px -10px rgba(102,126,234,.55) —
              // Flutter has no negative spread, so a smaller blur at a
              // downward offset with the same color/alpha approximates it
              // without the harsh, tight Material elevation shadow.
              // Derived from the theme's primary so the shadow tracks the
              // mode while remaining the same alpha recipe.
              BoxShadow(
                color: theme.primary.withValues(alpha: 0.55), // rgba(102,126,234,.55) in light
                blurRadius: 16,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: widget.child,
        ),
      ),
    );
  }
}
