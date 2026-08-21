// Settings — shared primitives (card, row, chevron, toggle, section label).
// Split from settings_screen.dart (R1D20). Token-swept WO-5.3 Part F.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../theme/gq_tokens.dart';

// ─── Shared primitive widgets ─────────────────────────────────────────────────

/// Card container matching the HTML's `.settings-card` — rounded-20, white,
/// hairline border, soft long-throw shadow.
class SettingsCard extends StatelessWidget {
  final List<Widget> children;
  const SettingsCard({super.key, required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: GQColors.hair, width: 1),
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        boxShadow: [
          BoxShadow(
            color: GQColors.ink.withValues(alpha: 0.08),
            blurRadius: 26,
            offset: const Offset(0, 12),
            spreadRadius: -10,
          ),
        ],
      ),
      padding: const EdgeInsets.all(6),
      child: Column(
        children: List.generate(children.length, (i) {
          final child = children[i];
          if (i == 0) return child;
          return Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Auto-divider stays a hairline, never a gray slab.
              Divider(
                  height: 1,
                  thickness: 1,
                  color: GQColors.hair,
                  indent: 0,
                  endIndent: 0),
              child,
            ],
          );
        }),
      ),
    );
  }
}

/// A single row inside a SettingsCard. Min height 56 (44pt touch target +
/// padding). Tap feedback: 200ms scale to .99 ([GQDurations.tap]).
class SettingsRow extends StatefulWidget {
  final Color iconBg;
  final Widget iconWidget;
  final String title;
  final Color? titleColor;
  final String? subtitle;
  final Color? subtitleColor;
  final Widget? trailing;
  final VoidCallback? onTap;

  const SettingsRow({
    super.key,
    required this.iconBg,
    required this.iconWidget,
    required this.title,
    this.titleColor,
    this.subtitle,
    this.subtitleColor,
    this.trailing,
    this.onTap,
  });

  @override
  State<SettingsRow> createState() => _SettingsRowState();
}

class _SettingsRowState extends State<SettingsRow> {
  bool _pressed = false;

  void _setPressed(bool value) {
    if (widget.onTap == null) return;
    setState(() => _pressed = value);
  }

  @override
  Widget build(BuildContext context) {
    final row = ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 56),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: widget.iconBg,
                borderRadius: BorderRadius.circular(GQRadii.chip),
              ),
              child: Center(child: widget.iconWidget),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(widget.title,
                      style: GQTypography.body.copyWith(
                          fontWeight: FontWeight.w700,
                          color: widget.titleColor ?? GQColors.ink)),
                  if (widget.subtitle != null) ...[
                    const SizedBox(height: 2),
                    Text(widget.subtitle!,
                        style: GQTypography.caption.copyWith(
                            color: widget.subtitleColor ?? GQColors.ink2,
                            height: 1.35)),
                  ],
                ],
              ),
            ),
            if (widget.trailing != null) ...[
              const SizedBox(width: 8),
              widget.trailing!,
            ],
          ],
        ),
      ),
    );

    if (widget.onTap == null) return row;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapDown: (_) => _setPressed(true),
      onTapCancel: () => _setPressed(false),
      onTapUp: (_) => _setPressed(false),
      onTap: widget.onTap,
      child: AnimatedScale(
        scale: _pressed ? 0.99 : 1.0,
        duration: GQDurations.tap,
        curve: GQMotion.standardCurve,
        child: row,
      ),
    );
  }
}

/// Chevron trailing widget. [GQColors.ink3] is legal here — a decorative
/// glyph, not text (D3 only bars ink3 as text below 14px).
class Chevron extends StatelessWidget {
  const Chevron({super.key});

  @override
  Widget build(BuildContext context) {
    return const Icon(Icons.chevron_right_rounded,
        size: 18, color: GQColors.ink3);
  }
}

/// Token-styled toggle (renamed from `GQToggle`, WO-5.3 Part A3 — collided
/// with the real GQ widget-layer suite's naming; this one is settings-local
/// and predates it). `locked` = always-on, non-interactive (P13: locked
/// after a heavy moment, stays visually "on"). A plain disabled toggle
/// (`onChanged: null`, not locked) renders a hair track + ink3 thumb instead.
class SettingsToggle extends StatelessWidget {
  final bool value;
  final bool locked;
  final ValueChanged<bool>? onChanged;

  const SettingsToggle({
    super.key,
    required this.value,
    this.locked = false,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final disabled = onChanged == null && !locked;
    return Transform.scale(
      scale: 0.85,
      child: Switch.adaptive(
        value: value || locked,
        onChanged: locked || onChanged == null
            ? null
            : (v) {
                HapticFeedback.selectionClick();
                onChanged!(v);
              },
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (disabled) return GQColors.ink3;
          return Colors.white;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (locked) return GQColors.primary.withValues(alpha: 0.8);
          if (disabled) return GQColors.hair;
          if (states.contains(WidgetState.selected)) return GQColors.primary;
          return GQColors.ink3.withValues(alpha: 0.32);
        }),
      ),
    );
  }
}

/// Section label matching HTML `.section-label`. [GQSpacing.xl] above,
/// [GQSpacing.sm] below — owns its own rhythm; callers don't add a
/// SizedBox before it.
class SectionLabel extends StatelessWidget {
  final String label;
  final Color? color;

  const SectionLabel({super.key, required this.label, this.color});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(
          left: 6, top: GQSpacing.xl, bottom: GQSpacing.sm),
      child: Text(
        label,
        // D3: micro is an 11px style — pair with ink2, never ink3.
        style: GQTypography.micro.copyWith(color: color ?? GQColors.ink2),
      ),
    );
  }
}
