import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/gq/gq.dart';

// ─────────────────────────────────────────────────────────────────────────────
// C — Q9 crisis bridge sheet
// Soft pre-step; does NOT duplicate CrisisInterventionSheet.
// .talkNow branches to existing CrisisInterventionSheet from crisis_resources.dart
// ─────────────────────────────────────────────────────────────────────────────

enum BridgeAction { imSafe, talkNow, heavy }

class Q9CrisisBridgeSheet extends StatefulWidget {
  const Q9CrisisBridgeSheet({super.key});

  @override
  State<Q9CrisisBridgeSheet> createState() => _Q9CrisisBridgeSheetState();
}

class _Q9CrisisBridgeSheetState extends State<Q9CrisisBridgeSheet>
    with SingleTickerProviderStateMixin {
  // Cupped-hands animation: 3.4s ease-in-out ±2px Y (per HTML spec)
  late final AnimationController _handsCtrl;
  late final Animation<double> _handsY;

  bool _reduceMotion = false;
  // The first didChangeDependencies pass must ALWAYS apply, even when rm
  // equals the initial `false`. Without this the equality guard below
  // early-returns on first mount and the animation is never started at
  // all — the failure is invisible to tests because nothing asserts that
  // a perpetual animation is actually running.
  bool _motionGateInitialised = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // ADR-006: respect quiet-mode reduced motion.
    final rm = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (_motionGateInitialised && rm == _reduceMotion) return;
    _motionGateInitialised = true;
    _reduceMotion = rm;
    if (rm) {
      _handsCtrl.stop();
    } else {
      _handsCtrl.repeat(reverse: true);
    }
  }

  @override
  void initState() {
    super.initState();
    _handsCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3400),
    );
    _handsY = Tween<double>(begin: 0, end: -2).animate(
      CurvedAnimation(parent: _handsCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _handsCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(28),
        ),
        boxShadow: [
          BoxShadow(
            color: Color(0x59000000),
            blurRadius: 50,
            offset: Offset(0, -22),
            spreadRadius: -12,
          )
        ],
      ),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 22),
      // WO-8 AX3: scrollable. At large accessibility text scales the three
      // bridge options grow enough to push the always-present 988 pill below
      // the fold, making the emergency affordance unreachable on exactly the
      // surface that exists to offer it. Same fix, and same reasoning, as the
      // SingleChildScrollView added to CrisisInterventionSheet in WO-6.2.
      child: SingleChildScrollView(
        child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Drag handle
          Container(
            width: 42,
            height: 4,
            decoration: BoxDecoration(
              color: t.ink.withAlpha(46),
              borderRadius: BorderRadius.circular(99),
            ),
          ),
          const SizedBox(height: 12),

          // Animated cupped-hands icon
          AnimatedBuilder(
            animation: _handsY,
            builder: (context, child) {
              return Transform.translate(
                offset: Offset(0, _handsY.value),
                child: child,
              );
            },
            child: Container(
              width: 54,
              height: 54,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  // IMG-TINT: gradient stop paired with accentSoft (agent ruling 2026-05-22 keep raw)
                  colors: [const Color(0xFFFFF1E5), t.accentSoft],
                ),
              ),
              child: Icon(
                Icons.pan_tool_alt_rounded,
                color: t.coral,
                size: 26,
              ),
            ),
          ),
          const SizedBox(height: 10),

          // "A QUIET PAUSE" eyebrow — verbatim
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

          // Headline — verbatim from HTML
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

          // Body — verbatim from HTML
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 6),
            child: Text(
              'What you said matters. Before we keep going — are you safe right now?',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: t.ink2,
                height: 1.5,
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Option 1 — I'm safe (green)
          _BridgeOptionCard(
            iconEmoji: '✓',
            iconBg: GQColors.moodGreat.withAlpha(46),
            iconColor: GQColors.leafInk,
            title: "I'm safe — let's continue the check-in", // verbatim from HTML
            subtitle: 'Returns to the assessment, no judgement',
            style: _BridgeCardStyle.green,
            onTap: () {
              HapticFeedback.lightImpact();
              Navigator.of(context).pop(BridgeAction.imSafe);
            },
          ),
          const SizedBox(height: 8),

          // Option 2 — Talk now (primary)
          _BridgeOptionCard(
            iconEmoji: '💬',
            iconBg: Colors.white.withAlpha(51),
            iconColor: Colors.white,
            title: 'I want to talk to someone now', // verbatim from HTML
            subtitle: 'Pauses this. Opens crisis support sheet.',
            style: _BridgeCardStyle.primary,
            onTap: () {
              HapticFeedback.lightImpact();
              Navigator.of(context).pop(BridgeAction.talkNow);
            },
          ),
          const SizedBox(height: 8),

          // Option 3 — Just having a heavy moment (coral)
          _BridgeOptionCard(
            iconEmoji: '🤍',
            iconBg: t.coral.withAlpha(46),
            iconColor: t.coral,
            title: 'Just having a heavy moment', // verbatim from HTML
            subtitle: 'Continue. We\'ll check in tomorrow.',
            style: _BridgeCardStyle.coral,
            onTap: () {
              HapticFeedback.lightImpact();
              Navigator.of(context).pop(BridgeAction.heavy);
            },
          ),

          const SizedBox(height: 14),

          // 988 always-present deeplink
          GestureDetector(
            onTap: () => _launchUri988(context),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 11),
              decoration: BoxDecoration(
                color: t.dangerSoft,
                borderRadius: BorderRadius.circular(12),
                // dangerInk stays static — 988 CTA border, byte-identical by design.
                border: Border.all(color: GQColors.dangerInk.withValues(alpha: 0.2)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.phone_rounded,
                    color: t.coral,
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  // WO-8 AX3: Flexible, not a bare Text. In a Row an
                  // unconstrained Text will not wrap — at large accessibility
                  // text scales this label ran past the pill and clipped at
                  // the screen edge. A truncated 988 affordance on the Q9
                  // suicidal-ideation path is the worst clipping bug this app
                  // can have, so it wraps instead of overflowing.
                  Flexible(
                    child: Text(
                      'Call 988 now · always tap-ready', // verbatim from HTML
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                        color: t.coral,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      ),
    );
  }
}

Future<void> _launchUri988(BuildContext context) async {
  final uri = Uri.parse('tel:988');
  try {
    final launched = await canLaunchUrl(uri) &&
        await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (launched) return;
  } catch (_) {
    // fall through
  }
  await Clipboard.setData(const ClipboardData(text: '988'));
  if (context.mounted) {
    GQBanner.show(context, message: '988 copied to clipboard', category: GQBannerCategory.info);
  }
}

enum _BridgeCardStyle { green, primary, coral }

class _BridgeOptionCard extends StatelessWidget {
  final String iconEmoji;
  final Color iconBg;
  final Color iconColor;
  final String title;
  final String subtitle;
  final _BridgeCardStyle style;
  final VoidCallback onTap;

  const _BridgeOptionCard({
    required this.iconEmoji,
    required this.iconBg,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.style,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    Color bgColor;
    Color borderColor;
    Color titleColor;
    Color subtitleColor;

    switch (style) {
      case _BridgeCardStyle.green:
        // GQColors.moodGreat stays static — mood-scale hue, never shifts by mode.
        bgColor = GQColors.moodGreat.withAlpha(26); // rgba(156,196,135,0.10)
        borderColor = GQColors.moodGreat.withAlpha(77); // rgba(156,196,135,0.30)
        titleColor = t.ink;
        subtitleColor = t.ink2;
      case _BridgeCardStyle.primary:
        bgColor = t.primary;
        borderColor = t.primary;
        // White stays literal — painted directly on the primary fill above,
        // same discipline as the primaryDk CTA (contrast travels with the fill).
        titleColor = Colors.white;
        subtitleColor = Colors.white.withAlpha(217);
      case _BridgeCardStyle.coral:
        bgColor = t.coral.withAlpha(31); // gradient approx
        borderColor = t.coral.withAlpha(77);
        titleColor = t.ink;
        subtitleColor = t.ink2;
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: borderColor),
        ),
        child: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: iconBg,
                borderRadius: BorderRadius.circular(11),
              ),
              child: Center(
                child: Text(
                  iconEmoji,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: iconColor,
                  ),
                ),
              ),
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
                      fontSize: 13.5,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                      letterSpacing: -0.2,
                      height: 1.25,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                      color: subtitleColor,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
