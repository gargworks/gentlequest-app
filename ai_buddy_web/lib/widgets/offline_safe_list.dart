import 'package:flutter/material.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';

/// Cold-start offline body — shown when the device has no connectivity at
/// launch (State B). Replaces the chat message list.
///
/// Header: muted companion at 96px (radius-26 primarySoft tile), 20 gap,
/// title 23/w800/-0.4 tracking/line-height 1.2, 8 gap, subtitle 13.5/w600/ink3.
/// Header copy: "Alex is out of reach for a moment" /
/// "Not your fault, and nothing you wrote is gone."
///
/// Three rows, always this order, crisis last:
/// 1. "Breathe for a minute" — white fill, primary icon tile.
/// 2. "Write it down instead" — white fill, primary icon tile.
/// 3. "Crisis resources" — accentSoft fill, coral border, white icon tile,
///    coral icon, inkOnCoral text.
///
/// Row height 56 min, padding 13/14, radius 14, border 1px hair (white
/// rows), gap 8 between rows, trailing chevron 17/w700/ink3.
class OfflineSafeList extends StatelessWidget {
  final VoidCallback? onBreathe;
  final VoidCallback? onWrite;
  final VoidCallback? onCrisis;

  const OfflineSafeList({
    super.key,
    this.onBreathe,
    this.onWrite,
    this.onCrisis,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildHeader(context),
          const SizedBox(height: 28),
          _OfflineRow(
            title: 'Breathe for a minute',
            subtitle: 'A 60-second reset, no connection needed',
            icon: Icons.air,
            iconTileColor: GQColors.primarySoft,
            iconColor: GQColors.primary,
            fillColor: Colors.white,
            borderColor: GQColors.hair,
            titleColor: GQColors.ink,
            subtitleColor: GQColors.ink3,
            onTap: onBreathe,
          ),
          const SizedBox(height: 8),
          _OfflineRow(
            title: 'Write it down instead',
            subtitle: 'Your words are saved and will send when we\u2019re back',
            icon: Icons.edit_note_rounded,
            iconTileColor: GQColors.primarySoft,
            iconColor: GQColors.primary,
            fillColor: Colors.white,
            borderColor: GQColors.hair,
            titleColor: GQColors.ink,
            subtitleColor: GQColors.ink3,
            onTap: onWrite,
          ),
          const SizedBox(height: 8),
          _OfflineRow(
            title: 'Crisis resources',
            subtitle: 'Hotlines and text lines, available offline',
            icon: Icons.favorite_rounded,
            iconTileColor: Colors.white,
            iconColor: GQColors.coral,
            fillColor: GQColors.accentSoft,
            borderColor: GQColors.coral.withValues(alpha: 0.28),
            titleColor: GQColors.inkOnCoral,
            subtitleColor: GQColors.inkOnCoral.withValues(alpha: 0.80),
            onTap: onCrisis,
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Column(
      children: [
        // Muted companion — 96px, radius-26 primarySoft tile.
        Container(
          width: 96,
          height: 96,
          decoration: BoxDecoration(
            color: GQColors.primarySoft,
            borderRadius: BorderRadius.circular(26),
          ),
          child: const Center(
            child: Icon(
              Icons.spa_rounded,
              size: 44,
              color: GQColors.ink3,
            ),
          ),
        ),
        const SizedBox(height: 20),
        const Text(
          'Alex is out of reach for a moment',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 23,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.4,
            height: 1.2,
            color: GQColors.ink,
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Not your fault, and nothing you wrote is gone.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 13.5,
            fontWeight: FontWeight.w600,
            color: GQColors.ink3,
          ),
        ),
      ],
    );
  }
}

class _OfflineRow extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color iconTileColor;
  final Color iconColor;
  final Color fillColor;
  final Color borderColor;
  final Color titleColor;
  final Color subtitleColor;
  final VoidCallback? onTap;

  const _OfflineRow({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.iconTileColor,
    required this.iconColor,
    required this.fillColor,
    required this.borderColor,
    required this.titleColor,
    required this.subtitleColor,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: onTap != null,
      label: '$title. $subtitle',
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          constraints: const BoxConstraints(minHeight: 56),
          padding: const EdgeInsets.fromLTRB(14, 13, 14, 13),
          decoration: BoxDecoration(
            color: fillColor,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: borderColor, width: 1),
          ),
          child: Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: iconTileColor,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: Icon(icon, size: 20, color: iconColor),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: titleColor,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: subtitleColor,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                '\u203A',
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: GQColors.ink3,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
