// Settings — shared primitives (card, row, chevron, toggle, section label).
// Split from settings_screen.dart (R1D20).

import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';

// ─── Shared primitive widgets ─────────────────────────────────────────────────

/// Card container matching the HTML's `.settings-card` — rounded-18, white, hairline border.
class SettingsCard extends StatelessWidget {
  final List<Widget> children;
  const SettingsCard({super.key, required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: GQColors.hair, width: 1),
        borderRadius: BorderRadius.circular(18),
      ),
      padding: const EdgeInsets.all(6),
      child: Column(
        children: List.generate(children.length, (i) {
          final child = children[i];
          if (i == 0) return child;
          return Column(
            mainAxisSize: MainAxisSize.min,
            children: [
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

/// A single row inside a SettingsCard.
class SettingsRow extends StatelessWidget {
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
  Widget build(BuildContext context) {
    final row = Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: iconBg,
              borderRadius: BorderRadius.circular(9),
            ),
            child: Center(child: iconWidget),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: titleColor ?? GQColors.ink,
                        height: 1.25)),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(subtitle!,
                      style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: subtitleColor ?? GQColors.ink2,
                          height: 1.35)),
                ],
              ],
            ),
          ),
          if (trailing != null) ...[
            const SizedBox(width: 8),
            trailing!,
          ],
        ],
      ),
    );

    if (onTap == null) return row;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: row,
    );
  }
}

/// Chevron trailing widget.
class Chevron extends StatelessWidget {
  const Chevron({super.key});

  @override
  Widget build(BuildContext context) {
    return const Icon(Icons.chevron_right_rounded,
        size: 16, color: GQColors.ink3);
  }
}

/// Token-styled toggle. `locked` = always-on, non-interactive.
class GQToggle extends StatelessWidget {
  final bool value;
  final bool locked;
  final ValueChanged<bool>? onChanged;

  const GQToggle({
    super.key,
    required this.value,
    this.locked = false,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Transform.scale(
      scale: 0.85,
      child: Switch.adaptive(
        value: value || locked,
        onChanged: locked ? null : onChanged,
        activeColor: GQColors.primary,
        activeTrackColor: GQColors.primary,
        inactiveThumbColor: Colors.white,
        inactiveTrackColor: GQColors.ink3.withValues(alpha: 0.32),
        thumbColor: WidgetStateProperty.resolveWith((states) {
          return Colors.white;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (locked) return GQColors.primary.withValues(alpha: 0.8);
          if (states.contains(WidgetState.selected)) return GQColors.primary;
          return GQColors.ink3.withValues(alpha: 0.32);
        }),
      ),
    );
  }
}

/// Section label matching HTML `.section-label`.
class SectionLabel extends StatelessWidget {
  final String label;
  final Color? color;

  const SectionLabel({super.key, required this.label, this.color});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 6, bottom: 8),
      child: Text(
        label,
        style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            color: color ?? GQColors.ink2,
            letterSpacing: 0.7),
      ),
    );
  }
}

