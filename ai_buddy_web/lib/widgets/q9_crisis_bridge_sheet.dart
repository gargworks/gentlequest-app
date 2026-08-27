import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../theme/gq_theme.dart';
import '../theme/gq_tokens.dart';

/// Outcomes of the Q9 crisis-bridge sheet.
///
/// Q9 of PHQ-9 ("thoughts that you would be better off dead, or of
/// hurting yourself in some way") with score >= 1 triggers this soft
/// bridge BEFORE the user advances/submits the assessment. The bridge
/// never blocks — the user's answer is already in [_responses] when
/// the sheet appears, so no path can lose data.
///
/// - [keepGoing]   user confirms they're safe; return to assessment
/// - [talkNow]     user wants crisis support; submit then open resources
/// - [heavyMoment] user wants to continue but flagged the moment;
///                 schedules a 24h check-in (TODO)
enum Q9BridgeAction { keepGoing, talkNow, heavyMoment }

/// Soft bridge shown after PHQ-9 Q9 is answered with score >= 1.
/// Composes existing crisis-resources affordances; never blocks the
/// underlying assessment (answer is already committed to memory).
///
/// Principles: P1 warmth · P2 skip-anything · P6 crisis-never-blocks
///             · P10 reflection-over-interrogation.
class Q9CrisisBridgeSheet extends StatelessWidget {
  const Q9CrisisBridgeSheet({super.key});

  static Future<Q9BridgeAction?> show(BuildContext context) {
    return showModalBottomSheet<Q9BridgeAction>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      isDismissible: false,
      enableDrag: false,
      builder: (_) => const Q9CrisisBridgeSheet(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return AnimatedPadding(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeOutCubic,
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius:
              BorderRadius.vertical(top: Radius.circular(GQRadii.sheet)),
        ),
        padding: const EdgeInsets.fromLTRB(20, 14, 20, 28),
        child: SafeArea(
          top: false,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: t.hair,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 14),
              Container(
                width: 54,
                height: 54,
                // GQIllustration.warm1/warm2 stay static — illustration gradient
                // tokens, out of scope for this GQColors conversion.
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [GQIllustration.warm1, GQIllustration.warm2],
                  ),
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.favorite_border, color: t.coral, size: 26),
              ),
              const SizedBox(height: 10),
              Text(
                'A QUIET PAUSE',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  color: t.ink2,
                  letterSpacing: 0.7,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Thank you for being honest with that one.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.displayFamily,
                  fontSize: 21,
                  fontWeight: FontWeight.w800,
                  color: t.ink,
                  letterSpacing: -0.5,
                  height: 1.25,
                ),
              ),
              const SizedBox(height: 8),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                child: Text(
                  "What you said matters. Before we keep going — "
                  "are you safe right now?",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    color: t.ink2,
                    fontWeight: FontWeight.w600,
                    height: 1.5,
                  ),
                ),
              ),
              const SizedBox(height: 14),
              _BridgeOption(
                icon: Icons.check_rounded,
                iconBg: GQColors.moodGreat.withValues(alpha: 0.15),
                iconFg: GQColors.leafInk,
                title: "I'm safe — let's continue the check-in",
                sub: 'Returns to the assessment, no judgement',
                onTap: () => Navigator.of(context).pop(Q9BridgeAction.keepGoing),
              ),
              const SizedBox(height: 8),
              _BridgeOption(
                icon: Icons.chat_bubble_outline,
                primary: true,
                title: 'I want to talk to someone now',
                sub: 'Pauses this. Opens crisis support.',
                onTap: () => Navigator.of(context).pop(Q9BridgeAction.talkNow),
              ),
              const SizedBox(height: 8),
              _BridgeOption(
                icon: Icons.favorite_outline,
                iconBg: t.accentSoft,
                iconFg: t.coral,
                title: 'Just having a heavy moment',
                sub: "Continue. We'll check in tomorrow.",
                onTap: () =>
                    Navigator.of(context).pop(Q9BridgeAction.heavyMoment),
              ),
              const SizedBox(height: 14),
              _AlwaysReachable988Pill(onTap: () async {
                final uri = Uri.parse('tel:988');
                if (await canLaunchUrl(uri)) launchUrl(uri);
              }),
            ],
          ),
        ),
      ),
    );
  }
}

class _BridgeOption extends StatelessWidget {
  const _BridgeOption({
    required this.icon,
    required this.title,
    required this.sub,
    required this.onTap,
    this.iconBg,
    this.iconFg,
    this.primary = false,
  });

  final IconData icon;
  final Color? iconBg;
  final Color? iconFg;
  final String title;
  final String sub;
  final bool primary;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final bg = primary ? t.primary : t.bg;
    // White stays literal on the primary branch — painted directly on the
    // primary fill, same discipline as the primaryDk CTA (contrast travels
    // with the fill). primaryDk itself stays static per the work order.
    final fg = primary ? Colors.white : t.ink;
    final subFg = primary ? Colors.white.withValues(alpha: 0.85) : t.ink2;
    final ibg = primary
        ? Colors.white.withValues(alpha: 0.22)
        : (iconBg ?? t.primarySoft);
    final ifg = primary ? Colors.white : (iconFg ?? GQColors.primaryDk);

    return InkWell(
      borderRadius: BorderRadius.circular(GQRadii.card),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: primary ? null : Border.all(color: t.hair, width: 1.5),
          boxShadow: primary
              ? [
                  BoxShadow(
                    color: t.primary.withValues(alpha: 0.25),
                    blurRadius: 16,
                    offset: const Offset(0, 10),
                  )
                ]
              : null,
        ),
        child: Row(children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
                color: ibg, borderRadius: BorderRadius.circular(11)),
            alignment: Alignment.center,
            child: Icon(icon, size: 17, color: ifg),
          ),
          const SizedBox(width: 11),
          Expanded(
              child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w800,
                    color: fg,
                    height: 1.25,
                  )),
              const SizedBox(height: 2),
              Text(sub,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: subFg,
                    height: 1.4,
                  )),
            ],
          )),
        ]),
      ),
    );
  }
}

class _AlwaysReachable988Pill extends StatelessWidget {
  const _AlwaysReachable988Pill({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 11, horizontal: 12),
        decoration: BoxDecoration(
          color: t.coral.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: t.coral.withValues(alpha: 0.20)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.phone, size: 14, color: t.coral),
            const SizedBox(width: 6),
            Text(
              'Call 988 now · always tap-ready',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: t.coral,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
