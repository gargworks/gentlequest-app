// crisis_resources.dart — R1D9 Crisis Intervention
// Design source: docs/design/refs/htmls/GentleQuest_Crisis_Intervention.html
// Principles: P1, P2, P4, P6 (crisis never blocks — 988 always reachable).
//
// Three surfaces:
//   A — CrisisInterventionSheet  (risk: medium/high)   — slides over chat
//   B — AcuteCrisisTakeover      (risk: crisis)         — full-screen
//   C — CrisisFollowUpCard       (post-flag ≤ 24h)      — inline dashboard card
//
// Legacy widget CrisisResourcesWidget preserved for existing call sites.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/message.dart';
import '../screens/profile_screen.dart' show ProfileScreen;
import '../services/firebase_service.dart';
import '../theme/gq_tokens.dart';

// ─────────────────────────────────────────────────────────────────────────────
// A — Soft Intervention Sheet (risk: medium / high)
// isDismissible: false — never auto-dismisses; user must act or tap opt-out.
// ─────────────────────────────────────────────────────────────────────────────

/// Show the soft crisis sheet over the current route.
/// Returns the user's choice as a [CrisisSheetChoice].
///
/// Fires `crisis_intervention_sheet_shown` analytics on open and
/// `crisis_intervention_choice` (with the user's selection) on close. These
/// events are what tell us, post-launch, whether the crisis flow is being
/// reached for real users and which paths they actually take.
Future<CrisisSheetChoice?> showCrisisInterventionSheet(
  BuildContext context, {
  RiskLevel risk = RiskLevel.medium,
  String source = 'unspecified',
}) async {
  FirebaseService().logEvent('crisis_intervention_sheet_shown', {
    'risk': risk.toString().split('.').last,
    'source': source,
  });
  final choice = await showModalBottomSheet<CrisisSheetChoice>(
    context: context,
    isDismissible: false,
    enableDrag: false,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    barrierColor: GQColors.ink.withAlpha(153), // 0.6 opacity
    builder: (ctx) => CrisisInterventionSheet(risk: risk),
  );
  if (choice != null) {
    FirebaseService().logEvent('crisis_intervention_choice', {
      'choice': choice.toString().split('.').last,
      'risk': risk.toString().split('.').last,
      'source': source,
    });
  }
  return choice;
}

enum CrisisSheetChoice { call988, text741741, keepChatting, ventingOptOut }

/// State A — Soft intervention sheet.
/// Verbatim copy from GentleQuest_Crisis_Intervention.html.
class CrisisInterventionSheet extends StatelessWidget {
  final RiskLevel risk;
  const CrisisInterventionSheet({super.key, this.risk = RiskLevel.medium});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'Crisis support options',
      child: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(GQRadii.sheetLg),
          ),
        ),
        padding: const EdgeInsets.fromLTRB(20, 14, 20, 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // drag indicator
            Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: GQColors.ink.withAlpha(46),
                borderRadius: BorderRadius.circular(99),
              ),
            ),
            const SizedBox(height: 16),

            // cupped-hands icon
            _CrisisIconBubble(size: 64, iconSize: 32),
            const SizedBox(height: 12),

            // headline — verbatim
            const Text(
              "I'm staying with you.",
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: GQTypography.displayFamily,
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                letterSpacing: -0.4,
              ),
            ),
            const SizedBox(height: 6),

            // body — verbatim
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 24),
              child: Text(
                "What you're feeling is real, and you don't have to be alone right now.",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w500,
                  color: GQColors.ink2,
                  height: 1.45,
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Option 1 — Call 988 (primary CTA)
            Semantics(
              button: true,
              label: 'Talk to someone now — Call 988, free, 24/7, confidential',
              child: _OptionCard(
                onTap: () {
                  Navigator.of(context).pop(CrisisSheetChoice.call988);
                  _launchUri(context, Uri.parse('tel:988'), label: 'Call 988');
                },
                backgroundColor: GQColors.dangerInk,
                borderColor: Colors.transparent,
                iconBg: Colors.white.withAlpha(46),
                icon: _phoneIcon(Colors.white),
                titleColor: Colors.white,
                subtitleColor: Colors.white.withAlpha(217),
                title: 'Talk to someone now',
                subtitle: 'Call 988 · free, 24/7, confidential',
              ),
            ),
            const SizedBox(height: 10),

            // Option 2 — Text 741741
            Semantics(
              button: true,
              label: 'Text someone now — Text HOME to 741741, Crisis Text Line',
              child: _OptionCard(
                onTap: () {
                  Navigator.of(context).pop(CrisisSheetChoice.text741741);
                  _launchUri(
                    context,
                    Uri.parse('sms:741741?body=HOME'),
                    label: 'Crisis Text Line',
                  );
                },
                backgroundColor: GQColors.primarySoft,
                borderColor: GQColors.primary.withAlpha(51),
                iconBg: Colors.white,
                icon: _messageIcon(GQColors.primaryDk),
                titleColor: GQColors.ink,
                subtitleColor: GQColors.ink2,
                title: 'Text someone now',
                subtitle: 'Text HOME to 741741 · Crisis Text Line',
              ),
            ),
            const SizedBox(height: 10),

            // Option 3 — Keep chatting
            Semantics(
              button: true,
              label: "Keep chatting with me",
              child: _OptionCard(
                onTap: () =>
                    Navigator.of(context).pop(CrisisSheetChoice.keepChatting),
                backgroundColor: Colors.white,
                borderColor: GQColors.hair,
                iconBg: GQColors.primarySoft,
                icon: const Text('💬', style: TextStyle(fontSize: 18)),
                titleColor: GQColors.ink,
                subtitleColor: GQColors.ink3,
                title: 'Keep chatting with me',
                subtitle: "I'll stay with you. Take your time.",
              ),
            ),
            const SizedBox(height: 16),

            // Non-shaming opt-out — verbatim
            Semantics(
              button: true,
              label: "I'm safe — was just venting",
              child: TextButton(
                onPressed: () =>
                    Navigator.of(context).pop(CrisisSheetChoice.ventingOptOut),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: const Text(
                  "I'm safe — was just venting",
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: GQColors.ink2,
                    decoration: TextDecoration.underline,
                    decorationColor: Color(0x668B86AB),
                    decorationStyle: TextDecorationStyle.solid,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// B — Acute Crisis Takeover (risk: crisis / imminent)
// Full-screen. All nav locked. Tiny "Step back to chat" at bottom.
// 988 CTA is wired to tel:988. Text 988 wired to sms:988. Chat → URL.
// ─────────────────────────────────────────────────────────────────────────────

class AcuteCrisisTakeover extends StatefulWidget {
  final VoidCallback? onStepBack;
  final bool hasSafetyPlan;

  const AcuteCrisisTakeover({
    super.key,
    this.onStepBack,
    this.hasSafetyPlan = false,
  });

  @override
  State<AcuteCrisisTakeover> createState() => _AcuteCrisisTakeoverState();
}

class _AcuteCrisisTakeoverState extends State<AcuteCrisisTakeover>
    with SingleTickerProviderStateMixin {
  late final AnimationController _heartCtrl;
  late final Animation<double> _heartScale;

  @override
  void initState() {
    super.initState();
    _heartCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.heartPulse,
    )..repeat(reverse: true);
    _heartScale = Tween<double>(begin: 1.0, end: 1.06).animate(
      CurvedAnimation(parent: _heartCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _heartCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false, // nav locked per spec
      child: Scaffold(
        body: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              stops: [0.0, 0.55, 1.0],
              colors: [Color(0xFFF0EEFE), Color(0xFFFBE9E2), GQColors.warm1],
            ),
          ),
          child: SafeArea(
            child: Stack(
              children: [
                // soft halo behind icon
                Positioned(
                  top: 88,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: Container(
                      width: 280,
                      height: 280,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: RadialGradient(colors: [
                          GQColors.warm2.withAlpha(115),
                          GQColors.warm2.withAlpha(0),
                        ]),
                      ),
                    ),
                  ),
                ),

                // pulsing heart icon
                Positioned(
                  top: 108,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: ScaleTransition(
                      scale: _heartScale,
                      child: Container(
                        width: 88,
                        height: 88,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: const RadialGradient(
                            center: Alignment(-0.4, -0.4),
                            colors: [GQColors.warm1, GQColors.moodCoralPeach,
                                     GQColors.coral],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: GQColors.coral.withAlpha(128),
                              blurRadius: 40,
                              offset: const Offset(0, 18),
                            ),
                          ],
                        ),
                        child: const Icon(Icons.favorite_rounded,
                            color: Colors.white, size: 40),
                      ),
                    ),
                  ),
                ),

                // headline block — verbatim
                Positioned(
                  top: 218,
                  left: 24,
                  right: 24,
                  child: Column(
                    children: [
                      const Text(
                        'Right now, please\nstay with me.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontFamily: GQTypography.displayFamily,
                          fontSize: 30,
                          fontWeight: FontWeight.w800,
                          color: GQColors.ink,
                          letterSpacing: -0.6,
                          height: 1.1,
                        ),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        "I want to make sure you're okay. The fastest way is calling 988 — they want to help.",
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 14.5,
                          fontWeight: FontWeight.w600,
                          color: GQColors.ink2,
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),

                // Huge CTA — Call 988 (tel:988)
                Positioned(
                  top: 404,
                  left: 20,
                  right: 20,
                  child: Semantics(
                    button: true,
                    label: 'Call 988 now — Suicide and Crisis Lifeline, available 24/7',
                    child: GestureDetector(
                      onTap: () =>
                          _launchUri(context, Uri.parse('tel:988'), label: 'Call 988'),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 18, vertical: 24),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(24),
                          gradient: const LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [GQColors.moodCoralPeach, GQColors.coral],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: GQColors.coral.withAlpha(140),
                              blurRadius: 48,
                              offset: const Offset(0, 22),
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 48,
                              height: 48,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.white.withAlpha(51),
                              ),
                              child: const Icon(Icons.phone_rounded,
                                  color: Colors.white, size: 24),
                            ),
                            const SizedBox(width: 14),
                            const Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Call 988 now',
                                  style: TextStyle(
                                    fontFamily: GQTypography.displayFamily,
                                    fontSize: 22,
                                    fontWeight: FontWeight.w800,
                                    color: Colors.white,
                                    letterSpacing: -0.3,
                                    height: 1.1,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'Suicide & Crisis Lifeline · 24/7',
                                  style: TextStyle(
                                    fontFamily: GQTypography.bodyFamily,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white,
                                    height: 1.0,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),

                // Secondary row: Text 988 + Chat online
                Positioned(
                  top: 558,
                  left: 20,
                  right: 20,
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Semantics(
                              button: true,
                              label: 'Text 988',
                              child: _SecondaryBtn(
                                onTap: () => _launchUri(
                                  context,
                                  Uri.parse('sms:988'),
                                  label: 'Text 988',
                                ),
                                icon: const Icon(Icons.message_rounded,
                                    color: GQColors.primaryDk, size: 20),
                                label: 'Text 988',
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Semantics(
                              button: true,
                              label: '988lifeline.org — chat online',
                              child: _SecondaryBtn(
                                onTap: () => _launchUri(
                                  context,
                                  Uri.parse('https://988lifeline.org/chat/'),
                                  label: '988lifeline.org',
                                ),
                                icon: const Icon(Icons.language_rounded,
                                    color: GQColors.primaryDk, size: 20),
                                label: '988lifeline.org',
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (widget.hasSafetyPlan) ...[
                        const SizedBox(height: 8),
                        Semantics(
                          button: true,
                          label: 'I have a safety plan I want to use',
                          child: GestureDetector(
                            onTap: () => Navigator.of(context).push(
                                MaterialPageRoute(
                                    builder: (_) => const ProfileScreen())),
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 14, vertical: 13),
                              decoration: BoxDecoration(
                                color: Colors.white.withAlpha(179),
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: GQColors.hair),
                              ),
                              child: const Row(
                                children: [
                                  Text('🗺️', style: TextStyle(fontSize: 16)),
                                  SizedBox(width: 10),
                                  Text(
                                    'I have a safety plan I want to use',
                                    style: TextStyle(
                                      fontFamily: GQTypography.bodyFamily,
                                      fontSize: 13,
                                      fontWeight: FontWeight.w800,
                                      color: GQColors.ink,
                                    ),
                                  ),
                                  Spacer(),
                                  Icon(Icons.chevron_right_rounded,
                                      color: GQColors.ink2, size: 16),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),

                // Deliberately tiny step-back — 11pt, no bg
                Positioned(
                  bottom: 34,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: Semantics(
                      button: true,
                      label: 'Step back to chat',
                      child: TextButton(
                        onPressed: widget.onStepBack,
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 8),
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          minimumSize: Size.zero,
                        ),
                        child: const Text(
                          'Step back to chat',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: GQColors.ink2,
                          ),
                        ),
                      ),
                    ),
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

// ─────────────────────────────────────────────────────────────────────────────
// C — Follow-up check card (post-flag ≤ 24h)
// Dismissible (tap behind). Emoji picker routes to chat or dashboard.
// ─────────────────────────────────────────────────────────────────────────────

enum FollowUpMoodChoice { heavy, off, okay, better }

class CrisisFollowUpCard extends StatefulWidget {
  final int hoursSince;
  final void Function(FollowUpMoodChoice)? onMoodSelected;
  final VoidCallback? onTalkToSomeone;

  const CrisisFollowUpCard({
    super.key,
    required this.hoursSince,
    this.onMoodSelected,
    this.onTalkToSomeone,
  });

  @override
  State<CrisisFollowUpCard> createState() => _CrisisFollowUpCardState();
}

class _CrisisFollowUpCardState extends State<CrisisFollowUpCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _heartCtrl;
  late final Animation<double> _heartScale;

  @override
  void initState() {
    super.initState();
    _heartCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.heartPulse,
    )..repeat(reverse: true);
    _heartScale = Tween<double>(begin: 1.0, end: 1.06).animate(
      CurvedAnimation(parent: _heartCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _heartCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: GQColors.primary.withAlpha(46)),
        boxShadow: [
          BoxShadow(
            color: GQColors.primary.withAlpha(46),
            blurRadius: 50,
            offset: const Offset(0, 24),
          ),
        ],
      ),
      padding: const EdgeInsets.fromLTRB(20, 22, 20, 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // pulsing heart
          ScaleTransition(
            scale: _heartScale,
            child: Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const RadialGradient(
                  center: Alignment(-0.4, -0.4),
                  colors: [GQColors.warm1, GQColors.moodCoralPeach],
                ),
                boxShadow: [
                  BoxShadow(
                    color: GQColors.moodCoralPeach.withAlpha(102),
                    blurRadius: 28,
                    offset: const Offset(0, 12),
                  ),
                ],
              ),
              child: const Icon(Icons.favorite_rounded,
                  color: Colors.white, size: 30),
            ),
          ),
          const SizedBox(height: 16),

          // headline — verbatim
          const Text(
            'Just checking in.\nHow are you, right now?',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: GQTypography.displayFamily,
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
              letterSpacing: -0.4,
              height: 1.2,
            ),
          ),
          const SizedBox(height: 8),

          // body — verbatim
          const Text(
            'No need to explain. Even one word is enough.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: GQColors.ink2,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 20),

          // 4 emoji buttons (56pt cells, 32px glyph per spec)
          Semantics(
            label: 'How are you feeling?',
            child: Row(
              children: [
                _EmojiChoice(
                  emoji: '😔',
                  label: 'Heavy',
                  labelColor: GQColors.ink2,
                  bg: GQColors.primarySoft,
                  borderColor: GQColors.hair,
                  onTap: () =>
                      widget.onMoodSelected?.call(FollowUpMoodChoice.heavy),
                ),
                const SizedBox(width: 6),
                _EmojiChoice(
                  emoji: '😶',
                  label: 'Off',
                  labelColor: GQColors.ink2,
                  bg: GQColors.primarySoft,
                  borderColor: GQColors.hair,
                  onTap: () =>
                      widget.onMoodSelected?.call(FollowUpMoodChoice.off),
                ),
                const SizedBox(width: 6),
                _EmojiChoice(
                  emoji: '🙂',
                  label: 'Okay',
                  labelColor: GQColors.ink2,
                  bg: GQColors.primarySoft,
                  borderColor: GQColors.hair,
                  onTap: () =>
                      widget.onMoodSelected?.call(FollowUpMoodChoice.okay),
                ),
                const SizedBox(width: 6),
                _EmojiChoice(
                  emoji: '🌱',
                  label: 'Better',
                  labelColor: const Color(0xFF9A6049),
                  bg: GQColors.warmSoft,
                  borderColor: GQColors.moodCoralPeach.withAlpha(64),
                  onTap: () =>
                      widget.onMoodSelected?.call(FollowUpMoodChoice.better),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Divider + "Talk to someone" — always available (P6)
          Container(
            decoration: const BoxDecoration(
              border: Border(
                top: BorderSide(color: GQColors.hair, style: BorderStyle.solid),
              ),
            ),
            padding: const EdgeInsets.only(top: 16),
            child: Semantics(
              button: true,
              label: 'Talk to someone — always here',
              child: GestureDetector(
                onTap: widget.onTalkToSomeone ??
                    () => _launchUri(context, Uri.parse('tel:988'),
                        label: 'Call 988'),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.phone_rounded,
                        color: GQColors.primaryDk, size: 16),
                    SizedBox(width: 8),
                    Text(
                      'Talk to someone — always here',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                        color: GQColors.primaryDk,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Legacy widget — preserved for existing call sites in home_shell.dart and
// interactive_chat_screen.dart. Delegates to the new surfaces for medium+.
// ─────────────────────────────────────────────────────────────────────────────

class CrisisResourcesWidget extends StatelessWidget {
  final RiskLevel riskLevel;
  final String? crisisMsg;
  final List<Map<String, dynamic>>? crisisNumbers;

  const CrisisResourcesWidget({
    super.key,
    required this.riskLevel,
    this.crisisMsg,
    this.crisisNumbers,
  });

  @override
  Widget build(BuildContext context) {
    // crisis level → show inline fallback card (AcuteCrisisTakeover is
    // shown as a full-screen route; this is the inline fallback).
    if (riskLevel == RiskLevel.crisis || riskLevel == RiskLevel.high) {
      return _LegacyCrisisCard(
        riskLevel: riskLevel,
        crisisMsg: crisisMsg,
        crisisNumbers: crisisNumbers,
        accentColor: GQColors.coral,
        accentBg: GQColors.accentSoft,
      );
    }
    if (riskLevel == RiskLevel.medium) {
      return _LegacyCrisisCard(
        riskLevel: riskLevel,
        crisisMsg: crisisMsg,
        crisisNumbers: crisisNumbers,
        accentColor: GQColors.primary,
        accentBg: GQColors.primarySoft,
      );
    }
    // low / none — compact resource card
    return _LegacyCrisisCard(
      riskLevel: riskLevel,
      crisisMsg: crisisMsg,
      crisisNumbers: crisisNumbers,
      accentColor: GQColors.ink3,
      accentBg: GQColors.softBg,
    );
  }
}

class _LegacyCrisisCard extends StatelessWidget {
  final RiskLevel riskLevel;
  final String? crisisMsg;
  final List<Map<String, dynamic>>? crisisNumbers;
  final Color accentColor;
  final Color accentBg;

  const _LegacyCrisisCard({
    required this.riskLevel,
    this.crisisMsg,
    this.crisisNumbers,
    required this.accentColor,
    required this.accentBg,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: accentBg,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: accentColor.withAlpha(51)),
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.favorite_rounded, color: accentColor, size: 18),
              const SizedBox(width: 8),
              Text(
                _getTitle(),
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: accentColor,
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            crisisMsg ?? _getMessage(),
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _getGeographySpecificResources().map((resource) {
              return ElevatedButton.icon(
                onPressed: () =>
                    _launchUri(context, Uri.parse(resource.url), label: resource.label),
                icon: Icon(resource.icon),
                label: Text(resource.label),
                style: ElevatedButton.styleFrom(
                  backgroundColor: accentColor,
                  foregroundColor: Colors.white,
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  String _getTitle() {
    switch (riskLevel) {
      case RiskLevel.high:
      case RiskLevel.crisis:
        return 'Immediate Help Available';
      case RiskLevel.medium:
        return 'Support Resources';
      case RiskLevel.low:
        return 'Helpful Resources';
      default:
        return '';
    }
  }

  String _getMessage() {
    switch (riskLevel) {
      case RiskLevel.high:
      case RiskLevel.crisis:
        return "If you're in crisis, please reach out. Help is available 24/7.";
      case RiskLevel.medium:
        return "It sounds like you're going through a difficult time. These resources might help.";
      case RiskLevel.low:
        return 'Here are some resources that might be helpful.';
      default:
        return '';
    }
  }

  List<CrisisResource> _getGeographySpecificResources() {
    final resources = <CrisisResource>[];

    if (crisisNumbers != null && crisisNumbers!.isNotEmpty) {
      for (final number in crisisNumbers!) {
        final name = number['name'] as String? ?? 'Crisis Helpline';
        final phoneNumber =
            (number['number'] as String?) ?? (number['phone'] as String?);
        final textNumber = number['text'] as String?;
        final url = number['url'] as String?;

        if (phoneNumber != null) {
          resources.add(CrisisResource(
              label: name, url: 'tel:$phoneNumber', icon: Icons.phone));
        } else if (textNumber != null) {
          resources.add(CrisisResource(
              label: name, url: 'sms:$textNumber', icon: Icons.message));
        } else if (url != null) {
          resources.add(
              CrisisResource(label: name, url: url, icon: Icons.link));
        }
      }
    }

    if (resources.isEmpty) {
      return _getDefaultResources();
    }
    return resources;
  }

  List<CrisisResource> _getDefaultResources() {
    final resources = <CrisisResource>[];

    if (riskLevel == RiskLevel.high || riskLevel == RiskLevel.crisis) {
      resources.addAll([
        CrisisResource(label: 'Call 988', url: 'tel:988', icon: Icons.phone),
        CrisisResource(
          label: '988 Lifeline Chat',
          url: 'https://988lifeline.org/chat/',
          icon: Icons.chat,
        ),
      ]);
    }

    resources.addAll([
      CrisisResource(
          label: 'Crisis Text Line', url: 'sms:741741', icon: Icons.message),
      CrisisResource(
        label: 'Find a Therapist',
        url: 'https://www.psychologytoday.com/us/therapists',
        icon: Icons.person,
      ),
    ]);

    return resources;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared private helpers
// ─────────────────────────────────────────────────────────────────────────────

class _CrisisIconBubble extends StatelessWidget {
  final double size;
  final double iconSize;
  const _CrisisIconBubble({required this.size, required this.iconSize});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const RadialGradient(
          center: Alignment(-0.4, -0.4),
          colors: [GQColors.warm1, GQColors.warm2, GQColors.moodCoralPeach],
        ),
        boxShadow: [
          BoxShadow(
            color: GQColors.moodCoralPeach.withAlpha(115),
            blurRadius: 28,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Icon(Icons.pan_tool_alt_rounded, color: Colors.white, size: iconSize),
    );
  }
}

class _OptionCard extends StatelessWidget {
  final VoidCallback onTap;
  final Color backgroundColor;
  final Color borderColor;
  final Color iconBg;
  final Widget icon;
  final Color titleColor;
  final Color subtitleColor;
  final String title;
  final String subtitle;

  const _OptionCard({
    required this.onTap,
    required this.backgroundColor,
    required this.borderColor,
    required this.iconBg,
    required this.icon,
    required this.titleColor,
    required this.subtitleColor,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        constraints: const BoxConstraints(minHeight: 56),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: Border.all(color: borderColor),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(shape: BoxShape.circle, color: iconBg),
              child: Center(child: icon),
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
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                      color: titleColor,
                      height: 1.2,
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

class _SecondaryBtn extends StatelessWidget {
  final VoidCallback onTap;
  final Widget icon;
  final String label;

  const _SecondaryBtn({
    required this.onTap,
    required this.icon,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: GQColors.hair),
        ),
        child: Column(
          children: [
            icon,
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmojiChoice extends StatelessWidget {
  final String emoji;
  final String label;
  final Color labelColor;
  final Color bg;
  final Color borderColor;
  final VoidCallback onTap;

  const _EmojiChoice({
    required this.emoji,
    required this.label,
    required this.labelColor,
    required this.bg,
    required this.borderColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Semantics(
        button: true,
        label: label,
        child: GestureDetector(
          onTap: onTap,
          child: Container(
            constraints: const BoxConstraints(minHeight: 56),
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: bg,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: borderColor),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(emoji, style: const TextStyle(fontSize: 32, height: 1)),
                const SizedBox(height: 4),
                Text(
                  label,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: labelColor,
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

// ─────────────────────────────────────────────────────────────────────────────
// Shared URL launcher (preserves existing web fallback logic)
// ─────────────────────────────────────────────────────────────────────────────

Future<void> _launchUri(BuildContext context, Uri uri, {String? label}) async {
  // Cache messenger before any async gap.
  final messenger = ScaffoldMessenger.maybeOf(context);
  // Track which scheme the user invoked from crisis surfaces so we know
  // (a) whether the platform allowed the launch and (b) which resource
  // they tried. Powers the post-launch dashboard for the crisis flow.
  FirebaseService().logEvent('crisis_resource_launch_attempt', {
    'scheme': uri.scheme,
    'label': label ?? 'unspecified',
  });
  try {
    final launched = await canLaunchUrl(uri) &&
        await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (launched) {
      FirebaseService().logEvent('crisis_resource_launch_success', {
        'scheme': uri.scheme,
        'label': label ?? 'unspecified',
      });
      return;
    }
  } catch (_) {
    // fall through to clipboard fallback
  }
  FirebaseService().logEvent('crisis_resource_launch_fallback_clipboard', {
    'scheme': uri.scheme,
    'label': label ?? 'unspecified',
  });

  if (uri.scheme == 'tel') {
    final number = uri.path;
    await Clipboard.setData(ClipboardData(text: number));
    if (!kIsWeb) return;
    messenger?.showSnackBar(
      SnackBar(content: Text('Phone number copied: $number')),
    );
    return;
  }
  if (uri.scheme == 'sms') {
    final number = uri.path;
    await Clipboard.setData(ClipboardData(text: number));
    if (!kIsWeb) return;
    final res = (label != null && label.isNotEmpty) ? ' for $label' : '';
    messenger?.showSnackBar(
      SnackBar(content: Text('SMS number$res copied: $number')),
    );
    return;
  }
  final urlStr = uri.toString();
  await Clipboard.setData(ClipboardData(text: urlStr));
  if (kIsWeb) {
    messenger?.showSnackBar(SnackBar(content: Text('Link copied: $urlStr')));
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared icon helpers (avoid importing SVG; use Material icons)
// ─────────────────────────────────────────────────────────────────────────────

Widget _phoneIcon(Color color) =>
    Icon(Icons.phone_rounded, color: color, size: 18);

Widget _messageIcon(Color color) =>
    Icon(Icons.message_rounded, color: color, size: 18);

// ─────────────────────────────────────────────────────────────────────────────
// CrisisResource — data class (unchanged; preserved for legacy widget)
// ─────────────────────────────────────────────────────────────────────────────

class CrisisResource {
  final String label;
  final String url;
  final IconData icon;

  const CrisisResource({
    required this.label,
    required this.url,
    required this.icon,
  });
}
