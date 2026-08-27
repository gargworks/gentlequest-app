// Compliance guard — shared widgets (lifeline card, tag pill, resource cards,
// block-reason disclosure) + URL launcher.
// Split from compliance_guard_screen.dart (R1D10 base + R1D11 extensions).

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../theme/gq_tokens.dart';
import '../../theme/gq_theme.dart';

/// surfaces. Keeps P6 (crisis never blocks) consistent across all paths.
class LifelineCard988 extends StatelessWidget {
  final VoidCallback onTap;

  const LifelineCard988({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      button: true,
      label: '988 Lifeline — Dial 988 — free, confidential, 24/7',
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: t.surface,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(color: t.hair),
            boxShadow: [
              BoxShadow(
                color: t.ink.withValues(alpha: 0.05),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  color: t.accentSoft,
                ),
                child: Icon(
                  Icons.phone_rounded,
                  color: t.coral,
                  size: 18,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          '988 Lifeline',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 14,
                            fontWeight: FontWeight.w800,
                            color: t.ink,
                          ),
                        ),
                        SizedBox(width: 6),
                        TagPill(label: 'CALL', bg: t.accentSoft,
                            fg: t.coralDk),
                      ],
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Dial 988 · free, confidential, 24/7',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        height: 1.4,
                        color: t.ink2,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded,
                  color: t.ink2, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}

/// Tiny pill label used inside resource cards.
class TagPill extends StatelessWidget {
  final String label;
  final Color bg;
  final Color fg;

  const TagPill(
      {super.key, required this.label, required this.bg, required this.fg});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 9.5,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.3,
          color: fg,
        ),
      ),
    );
  }
}

/// Resource card row used in State A (regional list).
class RegionalResourceCard extends StatelessWidget {
  final IconData icon;
  final Color iconBgColor;
  final Color iconColor;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const RegionalResourceCard({
    super.key,
    required this.icon,
    required this.iconBgColor,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      button: true,
      label: '$title — $subtitle',
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: t.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: t.hair),
          ),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(10),
                  color: iconBgColor,
                ),
                child: Icon(icon, color: iconColor, size: 16),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: t.ink,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      subtitle,
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: t.ink2,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded,
                  color: t.ink2, size: 14),
            ],
          ),
        ),
      ),
    );
  }
}

/// Resource card row used in State B (universal list — no deeplinks blocked by MDM).
class UniversalResourceCard extends StatelessWidget {
  final IconData icon;
  final Color iconBgColor;
  final Color iconColor;
  final String tagText;
  final Color tagBg;
  final Color tagColor;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const UniversalResourceCard({
    super.key,
    required this.icon,
    required this.iconBgColor,
    required this.iconColor,
    required this.tagText,
    required this.tagBg,
    required this.tagColor,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      button: true,
      label: '$title — $subtitle',
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: t.surface,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(color: t.hair),
            boxShadow: [
              BoxShadow(
                color: t.ink.withAlpha(13),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  color: iconBgColor,
                ),
                child: Icon(icon, color: iconColor, size: 18),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          title,
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 14,
                            fontWeight: FontWeight.w800,
                            color: t.ink,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: tagBg,
                            borderRadius: BorderRadius.circular(99),
                          ),
                          child: Text(
                            tagText,
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 9.5,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.3,
                              color: tagColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        height: 1.4,
                        color: t.ink2,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded,
                  color: t.ink2, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}

/// Collapsible block-reason disclosure — State A only.
/// collapsed by default (urgent help is the focus).
class BlockReasonDisclosure extends StatefulWidget {
  final String summaryText;
  final String bodyText;
  final VoidCallback? onDismiss;

  const BlockReasonDisclosure({
    super.key,
    required this.summaryText,
    required this.bodyText,
    this.onDismiss,
  });

  @override
  State<BlockReasonDisclosure> createState() =>
      _BlockReasonDisclosureState();
}

class _BlockReasonDisclosureState extends State<BlockReasonDisclosure> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Summary row (tap to expand)
        Semantics(
          button: true,
          label: widget.summaryText,
          child: GestureDetector(
            onTap: () => setState(() => _expanded = !_expanded),
            child: Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: 14, vertical: 13),
              decoration: BoxDecoration(
                color: t.surface.withAlpha(140),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                    color: t.hair,
                    style: BorderStyle.solid),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      widget.summaryText,
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        height: 1.4,
                        color: t.ink2,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(
                    _expanded
                        ? Icons.keyboard_arrow_up_rounded
                        : Icons.keyboard_arrow_down_rounded,
                    color: t.ink2,
                    size: 14,
                  ),
                ],
              ),
            ),
          ),
        ),

        if (_expanded) ...[
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: Text(
              widget.bodyText,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 12,
                fontWeight: FontWeight.w500,
                height: 1.6,
                color: t.ink2,
              ),
            ),
          ),
        ],
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// URL launcher (same pattern as crisis_resources.dart)
// ─────────────────────────────────────────────────────────────────────────────

Future<void> launchUri(BuildContext context, Uri uri,
    {String? label}) async {
  final messenger = ScaffoldMessenger.maybeOf(context);
  try {
    final launched = await canLaunchUrl(uri) &&
        await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (launched) return;
  } catch (_) {
    // fall through to clipboard fallback
  }

  if (uri.scheme == 'tel') {
    final number = uri.path;
    if (messenger != null) {
      messenger.showSnackBar(
        SnackBar(content: Text('Phone number: $number')),
      );
    }
    return;
  }
  if (uri.scheme == 'sms') {
    final number = uri.path;
    if (messenger != null) {
      messenger.showSnackBar(
        SnackBar(content: Text('Text: $number')),
      );
    }
    return;
  }
  final urlStr = uri.toString();
  if (messenger != null) {
    messenger.showSnackBar(SnackBar(content: Text('Link: $urlStr')));
  }
}
