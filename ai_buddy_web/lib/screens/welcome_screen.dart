import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/auth/login_screen.dart';
import 'package:ai_buddy_web/screens/compliance_guard_screen.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';

// ─────────────────────────────────────────────────────────────────────────────
// R1D1 — Onboarding redesign
// Design: docs/design/refs/htmls/GentleQuest_Onboarding.html
// Spec:   docs/design/refs/REVIEW.md § R1D1
// Tier:   0
// ─────────────────────────────────────────────────────────────────────────────

/// One-time welcome screen shown before compliance gate.
/// Three sequential states managed via [_WelcomeState]:
///   1. Welcome screen (full-bleed hero + headline + trust chips + CTA)
///   2. Age modal (bottom sheet over dimmed welcome)
///   3. Under-18 dignity path (resource list, warm handoff)
class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({super.key});

  static const String _kSeenKey = 'has_seen_welcome_v1';

  /// Check if user has seen the welcome screen before.
  static Future<bool> hasBeenSeen() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kSeenKey) ?? false;
  }

  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

enum _WelcomeState { welcome, ageModal, under18 }

class _WelcomeScreenState extends State<WelcomeScreen>
    with TickerProviderStateMixin {
  _WelcomeState _state = _WelcomeState.welcome;

  // Breathing animation for the hero illustration.
  late final AnimationController _breatheCtrl;
  late final Animation<double> _breatheAnim;

  // Staggered fade-in-up for welcome screen children.
  late final AnimationController _fadeCtrl;
  late final List<Animation<double>> _fadeAnims;

  // Modal slide-up.
  late final AnimationController _modalCtrl;
  late final Animation<Offset> _modalSlide;
  late final Animation<double> _backdropFade;

  // Under-18 screen fade.
  late final AnimationController _u18Ctrl;
  late final Animation<double> _u18Fade;

  @override
  void initState() {
    super.initState();

    // Breathe — 5.6s loop per design spec.
    _breatheCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    )..repeat(reverse: true);
    _breatheAnim = Tween<double>(begin: 1.0, end: 1.04).animate(
      CurvedAnimation(parent: _breatheCtrl, curve: Curves.easeInOut),
    );

    // Staggered fade-in for 5 welcome children (wordmark, headline, sub, chips, CTA).
    _fadeCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..forward();
    _fadeAnims = List.generate(5, (i) {
      final start = (i * 80) / 900.0;
      final end = math.min(start + 0.55, 1.0);
      return CurvedAnimation(
        parent: _fadeCtrl,
        curve: Interval(start, end, curve: Curves.easeOut),
      );
    });

    // Modal sheet — 700ms slide-up per design.
    _modalCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _modalSlide = Tween<Offset>(
      begin: const Offset(0, 1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _modalCtrl, curve: Curves.easeOut));
    _backdropFade = CurvedAnimation(parent: _modalCtrl, curve: Curves.easeIn);

    // Under-18 page fade.
    _u18Ctrl = AnimationController(
      vsync: this,
      duration: GQDurations.fade,
    );
    _u18Fade = CurvedAnimation(parent: _u18Ctrl, curve: Curves.easeIn);
  }

  @override
  void dispose() {
    _breatheCtrl.dispose();
    _fadeCtrl.dispose();
    _modalCtrl.dispose();
    _u18Ctrl.dispose();
    super.dispose();
  }

  Future<void> _showAgeModal() async {
    setState(() => _state = _WelcomeState.ageModal);
    await _modalCtrl.forward();
  }

  Future<void> _confirmAdult() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(WelcomeScreen._kSeenKey, true);
    if (mounted) {
      Navigator.of(context).pushReplacement(
        PageRouteBuilder(
          transitionDuration: GQDurations.fade,
          pageBuilder: (_, __, ___) => const ComplianceGuardScreen(),
          transitionsBuilder: (_, anim, __, child) =>
              FadeTransition(opacity: anim, child: child),
        ),
      );
    }
  }

  Future<void> _showUnder18() async {
    await _modalCtrl.reverse();
    setState(() => _state = _WelcomeState.under18);
    _u18Ctrl.forward();
  }

  void _backFromUnder18() {
    _u18Ctrl.reverse().then((_) {
      if (mounted) setState(() => _state = _WelcomeState.welcome);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    switch (_state) {
      case _WelcomeState.welcome:
        return _WelcomeContent(
          breatheAnim: _breatheAnim,
          fadeAnims: _fadeAnims,
          onContinue: _showAgeModal,
        );
      case _WelcomeState.ageModal:
        return Stack(
          children: [
            _WelcomeContent(
              breatheAnim: _breatheAnim,
              fadeAnims: _fadeAnims,
              dimmed: true,
              onContinue: _showAgeModal,
            ),
            FadeTransition(
              opacity: _backdropFade,
              child: GestureDetector(
                onTap: () {}, // prevent pass-through
                child: const ColoredBox(
                  color: Color(0x52281C3A), // rgba(31,27,58,0.32) approx
                  child: SizedBox.expand(),
                ),
              ),
            ),
            SlideTransition(
              position: _modalSlide,
              child: _AgeModal(
                onConfirmAdult: _confirmAdult,
                onNotYet: _showUnder18,
              ),
            ),
          ],
        );
      case _WelcomeState.under18:
        return FadeTransition(
          opacity: _u18Fade,
          child: _Under18Screen(onBack: _backFromUnder18),
        );
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Screen 1 — Welcome
// Copy verbatim: "A quiet place, whenever you need it."
//                "Private. Judgment-free."
//                "Here when you need it — and not when you don't."
// ─────────────────────────────────────────────────────────────────────────────

class _WelcomeContent extends StatelessWidget {
  const _WelcomeContent({
    required this.breatheAnim,
    required this.fadeAnims,
    this.dimmed = false,
    required this.onContinue,
  });

  final Animation<double> breatheAnim;
  final List<Animation<double>> fadeAnims;
  final bool dimmed;
  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: GQColors.softBg,
      child: SafeArea(
        child: Stack(
          children: [
            // Ambient gradient blobs (P1 — warmth).
            Positioned(
              top: -60,
              left: -60,
              child: _AmbientBlob(
                size: 260,
                color: const Color(0xFFD9DEFC),
                opacity: dimmed ? 0.35 : 0.70,
              ),
            ),
            Positioned(
              top: 140,
              right: -90,
              child: _AmbientBlob(
                size: 240,
                color: const Color(0xFFFFD9D9),
                opacity: dimmed ? 0.35 : 0.70,
              ),
            ),
            // Hero illustration — breathing circles.
            Positioned(
              top: 120,
              left: 0,
              right: 0,
              child: Center(
                child: AnimatedBuilder(
                  animation: breatheAnim,
                  builder: (_, __) => Transform.scale(
                    scale: breatheAnim.value,
                    child: const _BreathingIllustration(),
                  ),
                ),
              ),
            ),
            // Content column.
            Positioned.fill(
              child: Column(
                children: [
                  const Spacer(flex: 5), // push content below hero
                  // Wordmark.
                  _FadeInUp(
                    animation: fadeAnims[0],
                    child: Text(
                      'GentleQuest',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.4,
                        color: GQColors.primary,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  // Headline — verbatim copy.
                  _FadeInUp(
                    animation: fadeAnims[1],
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 32),
                      child: Text(
                        // VERBATIM: R1D1 spec + HTML
                        'A quiet place,\nwhenever you need it.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontFamily: GQTypography.displayFamily,
                          fontSize: 34,
                          fontWeight: FontWeight.w800,
                          height: 1.1,
                          letterSpacing: -0.6,
                          color: GQColors.ink,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Subhead — verbatim copy (two-line).
                  _FadeInUp(
                    animation: fadeAnims[2],
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 40),
                      child: Text(
                        // VERBATIM: R1D1 spec
                        'Private. Judgment-free.\nHere when you need it — and not when you don’t.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                          height: 1.55,
                          color: GQColors.ink2,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  // Trust chips — verbatim: "Private" · "No judgment" · "Free"
                  _FadeInUp(
                    animation: fadeAnims[3],
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: const [
                        _TrustChip(emoji: '🔒', label: 'Private'),
                        SizedBox(width: 8),
                        _TrustChip(emoji: '🤝', label: 'No judgment'),
                        SizedBox(width: 8),
                        _TrustChip(emoji: '☁️', label: 'No pressure'),
                      ],
                    ),
                  ),
                  const Spacer(flex: 2),
                  // Primary CTA + sign-in sub-link.
                  _FadeInUp(
                    animation: fadeAnims[4],
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: Column(
                        children: [
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: dimmed ? null : onContinue,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: GQColors.primary,
                                foregroundColor: Colors.white,
                                disabledBackgroundColor: GQColors.primary
                                    .withAlpha(180),
                                padding: const EdgeInsets.symmetric(
                                    vertical: 18),
                                shape: const StadiumBorder(),
                                elevation: 0,
                                shadowColor: Colors.transparent,
                              ),
                              child: Text(
                                'Continue',
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 17,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 0.2,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          // "Already with us? Sign in" — wires to the
                          // passwordless magic-link LoginScreen. Was an
                          // inert RichText (looked tappable, did nothing)
                          // until 2026-05-21.
                          GestureDetector(
                            behavior: HitTestBehavior.opaque,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => const LoginScreen(),
                                ),
                              );
                            },
                            child: RichText(
                              text: TextSpan(
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: GQColors.ink3,
                                ),
                                children: [
                                  const TextSpan(text: 'Already with us? '),
                                  TextSpan(
                                    text: 'Sign in',
                                    style: TextStyle(
                                      color: GQColors.primary,
                                      fontWeight: FontWeight.w700,
                                      decoration: TextDecoration.underline,
                                      decorationColor: GQColors.primary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Screen 2 — Age modal (bottom sheet)
// Copy verbatim: "Quick check before we begin —"
//                "Are you 18 or older?"
//                "Not yet" / "Yes, I am"
//                "YOUR ANSWER STAYS ON THIS DEVICE"
// ─────────────────────────────────────────────────────────────────────────────

class _AgeModal extends StatelessWidget {
  const _AgeModal({
    required this.onConfirmAdult,
    required this.onNotYet,
  });

  final VoidCallback onConfirmAdult;
  final VoidCallback onNotYet;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.bottomCenter,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: const BorderRadius.vertical(
            top: Radius.circular(GQRadii.sheetLg),
          ),
          boxShadow: [
            BoxShadow(
              color: GQColors.ink.withAlpha(64),
              blurRadius: 60,
              offset: const Offset(0, -20),
            ),
          ],
        ),
        padding: const EdgeInsets.fromLTRB(24, 28, 24, 36),
        child: SafeArea(
          top: false,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Grabber.
              Container(
                width: 44,
                height: 5,
                decoration: BoxDecoration(
                  color: const Color(0xFFE5E2EE),
                  borderRadius: BorderRadius.circular(100),
                ),
              ),
              const SizedBox(height: 24),
              // Icon.
              Container(
                width: 64,
                height: 64,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [GQColors.primarySoft, GQColors.accentSoft],
                  ),
                  shape: BoxShape.circle,
                ),
                child: const Center(
                  child: Text('🌱', style: TextStyle(fontSize: 32)),
                ),
              ),
              const SizedBox(height: 20),
              // Heading — verbatim from HTML.
              Text(
                'Quick check before we begin —',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.displayFamily,
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  height: 1.2,
                  letterSpacing: -0.3,
                  color: GQColors.ink,
                ),
              ),
              const SizedBox(height: 10),
              // Sub-heading — was "Are you 18 or older?" verbatim. Age gate
              // lowered to 13+ on 2026-05-21 per app's original high-school
              // objective; copy updated to match.
              Text(
                'Are you 13 or older?',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  height: 1.4,
                  color: GQColors.ink,
                ),
              ),
              const SizedBox(height: 28),
              // Two equal-weight buttons.
              Row(
                children: [
                  // "Not yet" — secondary, outlined.
                  Expanded(
                    child: OutlinedButton(
                      onPressed: onNotYet,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: GQColors.ink,
                        side: const BorderSide(color: GQColors.hair, width: 1.5),
                        padding: const EdgeInsets.symmetric(vertical: 18),
                        shape: const StadiumBorder(),
                      ),
                      child: Text(
                        // VERBATIM: HTML screen 02
                        'Not yet',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  // "Yes, I am" — primary.
                  Expanded(
                    child: ElevatedButton(
                      onPressed: onConfirmAdult,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: GQColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 18),
                        shape: const StadiumBorder(),
                        elevation: 0,
                      ),
                      child: Text(
                        // VERBATIM: HTML screen 02
                        'Yes, I am',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              // Microcopy (P5 — privacy visible).
              Text(
                // VERBATIM: HTML — "We're built for adults…"
                "We’re built for adults — that’s how we keep things safe.\n"
                "If you’re under 13, here’s where to find support tailored for you →",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  height: 1.55,
                  color: GQColors.ink2,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 20),
              // Trust line — verbatim.
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.shield_outlined,
                    size: 12,
                    color: GQColors.ink3,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    // VERBATIM: HTML
                    'YOUR ANSWER STAYS ON THIS DEVICE',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.3,
                      color: GQColors.ink3,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Screen 3 — Under-18 dignity path
// Copy verbatim: "Thank you for being honest."
//                "Come back when you're 18 — we'll be here."
// ─────────────────────────────────────────────────────────────────────────────

class _Under18Screen extends StatelessWidget {
  const _Under18Screen({required this.onBack});

  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Back button (P2 — skip anything).
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
                child: GestureDetector(
                  onTap: onBack,
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                      border: Border.all(color: GQColors.hair, width: 1),
                    ),
                    child: Icon(
                      Icons.chevron_left,
                      color: GQColors.ink2,
                      size: 22,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              // Hero.
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 28),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 72,
                      height: 72,
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [GQColors.primarySoft, GQColors.accentSoft],
                        ),
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Icon(
                          Icons.favorite,
                          color: GQColors.coral,
                          size: 32,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      // VERBATIM: HTML screen 03
                      'Thank you\nfor being honest.',
                      style: TextStyle(
                        fontFamily: GQTypography.displayFamily,
                        fontSize: 30,
                        fontWeight: FontWeight.w800,
                        height: 1.15,
                        letterSpacing: -0.4,
                        color: GQColors.ink,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      // VERBATIM: HTML screen 03
                      'GentleQuest is built for adults — but you deserve real support today. '
                      'These services are free, confidential, and made for you.',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 16,
                        height: 1.6,
                        color: GQColors.ink2,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              // Resource cards.
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  children: const [
                    _ResourceCard(
                      iconBg: GQColors.primarySoft,
                      iconColor: GQColors.primary,
                      usePhoneIcon: false,
                      useChatIcon: true,
                      title: 'Crisis Text Line',
                      tag: 'TEXT',
                      tagBg: GQColors.primarySoft,
                      tagColor: GQColors.primary,
                      // VERBATIM: HTML
                      actionLabel: 'Text HOME to 741741',
                      meta: 'Free · 24/7 · Trained counselors',
                    ),
                    SizedBox(height: 10),
                    _ResourceCard(
                      iconBg: GQColors.accentSoft,
                      iconColor: GQColors.coral,
                      usePhoneIcon: true,
                      useChatIcon: false,
                      title: 'Teen Line',
                      tag: 'CALL · TEXT',
                      tagBg: GQColors.accentSoft,
                      tagColor: GQColors.coral,
                      // VERBATIM: HTML
                      actionLabel: 'Call 800-852-8336',
                      meta: 'Teens helping teens · 6–10pm PT',
                    ),
                    SizedBox(height: 10),
                    _ResourceCard(
                      iconBg: GQColors.primarySoft,
                      iconColor: GQColors.primary,
                      usePhoneIcon: false,
                      useChatIcon: false,
                      title: 'JED Foundation',
                      tag: 'RESOURCES',
                      tagBg: GQColors.primarySoft,
                      tagColor: GQColors.primary,
                      // VERBATIM: HTML
                      actionLabel: 'jedfoundation.org',
                      meta: 'Mental health for teens & young adults',
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),
              // Closing message.
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 28),
                child: Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [GQColors.primarySoft, GQColors.accentSoft],
                    ),
                    borderRadius:
                        BorderRadius.circular(GQRadii.cardLg),
                    border: Border.all(color: GQColors.hair),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      RichText(
                        text: TextSpan(
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 15,
                            height: 1.55,
                            fontWeight: FontWeight.w600,
                            color: GQColors.ink,
                          ),
                          children: [
                            // Age gate lowered to 13+ on 2026-05-21 per
                            // app's original "high school students"
                            // objective; copy reworded from verbatim HTML
                            // "Come back when you're 18 — we'll be here."
                            const TextSpan(
                                text: 'Come back when you’re 13 — '),
                            TextSpan(
                              text: 'we’ll be here.',
                              style: TextStyle(
                                color: GQColors.primary,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'We can remind you on your birthday, if you’d like.',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: GQColors.ink2,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              // Remind me CTA (P2 — save-exit-always).
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 28),
                child: SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: () {
                      // [assumed] Birthday reminder: stub — notification
                      // scheduling is out of scope for R1D1 (Tier 3 R1D18).
                      // Shows a snackbar acknowledgement for now.
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text("We’ll remind you — thanks for letting us know."),
                          duration: Duration(seconds: 3),
                        ),
                      );
                    },
                    style: OutlinedButton.styleFrom(
                      foregroundColor: GQColors.primary,
                      side: const BorderSide(color: GQColors.primary, width: 1.5),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: const StadiumBorder(),
                    ),
                    child: Text(
                      // VERBATIM: HTML
                      'Remind me on my 18th',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 48),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared sub-widgets
// ─────────────────────────────────────────────────────────────────────────────

/// Ambient gaussian blob for background atmosphere.
class _AmbientBlob extends StatelessWidget {
  const _AmbientBlob({
    required this.size,
    required this.color,
    required this.opacity,
  });

  final double size;
  final Color color;
  final double opacity;

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: opacity,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}

/// Layered radial-gradient circles — the "breathing" hero illustration.
class _BreathingIllustration extends StatelessWidget {
  const _BreathingIllustration();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 200,
      height: 200,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Outer ring — indigo tint.
          Container(
            width: 200,
            height: 200,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                center: const Alignment(-0.3, -0.4),
                colors: [
                  GQColors.primary.withAlpha(89),
                  GQColors.primary.withAlpha(13),
                ],
              ),
            ),
          ),
          // Mid ring — coral tint.
          Container(
            width: 144,
            height: 144,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                center: const Alignment(0.2, -0.4),
                colors: [
                  GQColors.coral.withAlpha(77),
                  GQColors.coral.withAlpha(13),
                ],
              ),
            ),
          ),
          // Core — primary→coral gradient.
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [GQColors.primary, GQColors.coral],
              ),
              boxShadow: [
                BoxShadow(
                  color: GQColors.primary.withAlpha(115),
                  blurRadius: 40,
                  offset: const Offset(0, 16),
                ),
              ],
            ),
            // Headphone / wave mark (P9 — companion framing).
            child: Icon(
              Icons.headphones_rounded,
              color: Colors.white,
              size: 32,
            ),
          ),
        ],
      ),
    );
  }
}

/// Pill trust chip used in the welcome hero row.
class _TrustChip extends StatelessWidget {
  const _TrustChip({required this.emoji, required this.label});

  final String emoji;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.button),
        border: Border.all(color: GQColors.hair),
        boxShadow: [
          BoxShadow(
            color: GQColors.ink.withAlpha(10),
            blurRadius: 2,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 12)),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: GQColors.ink2,
            ),
          ),
        ],
      ),
    );
  }
}

/// Single resource card for the under-18 dignity path.
class _ResourceCard extends StatelessWidget {
  const _ResourceCard({
    required this.iconBg,
    required this.iconColor,
    required this.usePhoneIcon,
    required this.useChatIcon,
    required this.title,
    required this.tag,
    required this.tagBg,
    required this.tagColor,
    required this.actionLabel,
    required this.meta,
  });

  final Color iconBg;
  final Color iconColor;
  final bool usePhoneIcon;
  final bool useChatIcon;
  final String title;
  final String tag;
  final Color tagBg;
  final Color tagColor;
  final String actionLabel;
  final String meta;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        border: Border.all(color: GQColors.hair),
        boxShadow: [
          BoxShadow(
            color: GQColors.ink.withAlpha(8),
            blurRadius: 2,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: iconBg, shape: BoxShape.circle),
            child: Icon(
              usePhoneIcon
                  ? Icons.phone_outlined
                  : useChatIcon
                      ? Icons.chat_bubble_outline_rounded
                      : Icons.check_circle_outline_rounded,
              color: iconColor,
              size: 22,
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
                      title,
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: tagBg,
                        borderRadius: BorderRadius.circular(GQRadii.button),
                      ),
                      child: Text(
                        tag,
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.4,
                          color: tagColor,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  actionLabel,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink2,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  meta,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink3,
                  ),
                ),
              ],
            ),
          ),
          Icon(Icons.open_in_new_rounded, size: 14, color: GQColors.ink3),
        ],
      ),
    );
  }
}

/// Wraps a child in an opacity+translateY fade-in-up driven by [animation].
class _FadeInUp extends StatelessWidget {
  const _FadeInUp({required this.animation, required this.child});

  final Animation<double> animation;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: animation,
      builder: (_, __) => Opacity(
        opacity: animation.value,
        child: Transform.translate(
          offset: Offset(0, (1 - animation.value) * 8),
          child: child,
        ),
      ),
    );
  }
}
