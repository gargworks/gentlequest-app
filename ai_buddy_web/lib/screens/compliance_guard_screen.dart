// compliance_guard_screen.dart — R1D10 base + R1D11 Compliance Extensions
// Design sources:
//   • docs/design/refs/htmls/GentleQuest_Compliance_Block.html       (R1D10)
//   • docs/design/refs/htmls/GentleQuest_Compliance_Extensions.html  (R1D11)
// Principles: P6 (crisis never blocks), P14 (compliance is local-first), P4 (amber not red)
//
// R1D11 adds three critical state variants layered on top of the base screen:
//   A — Crisis-keyword override: 200ms swap to 988 surface if crisis keywords
//       detected in the "Notify me" email field. Reuses R1D9 crisis surfaces.
//   B — Managed-device block: MDM-detected surface (UI only; backend stubbed).
//   C — Notify-me confirmation: post-submit animated confirmation state.

import 'package:flutter/material.dart';
import 'package:ai_buddy_web/services/compliance_service.dart';
// For Permission Enums
import 'package:url_launcher/url_launcher.dart'; // Added for Data Export & App Store links
import 'package:ai_buddy_web/services/crisis_keyword_detector.dart';
import 'package:ai_buddy_web/services/mdm_detection_service.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';

// ─── R1D11 overlay state ──────────────────────────────────────────────────────
// Tracks which R1D11 extension state (if any) is active on top of the base
// compliance flow.
enum _ExtensionState {
  none,     // standard compliance flow
  crisis,   // State A — crisis-keyword override
  mdm,      // State B — managed-device block
  notifyOk, // State C — notify-me confirmation
}

class ComplianceGuardScreen extends StatefulWidget {
  const ComplianceGuardScreen({super.key});

  @override
  State<ComplianceGuardScreen> createState() => _ComplianceGuardScreenState();
}

class _ComplianceGuardScreenState extends State<ComplianceGuardScreen>
    with TickerProviderStateMixin {
  final ComplianceService _complianceService = ComplianceService();
  ComplianceStatus _status = ComplianceStatus.loading;
  bool _isLoadingAction = false;

  // ── R1D11 extension state ──────────────────────────────────────────────────
  _ExtensionState _ext = _ExtensionState.none;

  // ── State A: crisis crossfade controller ──────────────────────────────────
  late final AnimationController _crisisSwapCtrl;
  late final Animation<double> _crisisSwapAnim;

  // ── State A: urgency ring pulse controller ────────────────────────────────
  late final AnimationController _urgencyPulseCtrl;

  // ── State C: envelope pulse controller ───────────────────────────────────
  late final AnimationController _envelopePulseCtrl;
  late final Animation<double> _envelopePulseAnim;

  // ── State C: notify-me form controller ───────────────────────────────────
  late final AnimationController _notifyConfirmCtrl;
  late final Animation<double> _notifyConfirmAnim;

  // ── Notify-me email field ─────────────────────────────────────────────────
  final TextEditingController _emailCtrl = TextEditingController();
  bool _isSubmittingEmail = false;

  // ── R1D10 — stored region name for blocked-region UI ─────────────────────
  String? _storedRegion;

  @override
  void initState() {
    super.initState();

    // State A — 200ms crossfade (GentleQuest_Compliance_Extensions.html)
    _crisisSwapCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.complianceCrisisSwap,
    );
    _crisisSwapAnim = CurvedAnimation(
      parent: _crisisSwapCtrl,
      curve: Curves.easeOut,
    );

    // State A — urgency ring pulse (2200ms, infinite)
    _urgencyPulseCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.urgencyRingPulse,
    );

    // State C — envelope single-pulse (900ms × 1)
    _envelopePulseCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.envelopePulse,
    );
    _envelopePulseAnim = Tween<double>(begin: 1.0, end: 1.05).animate(
      CurvedAnimation(parent: _envelopePulseCtrl, curve: Curves.easeOut),
    );

    // State C — 300ms crossfade from form → confirmation
    _notifyConfirmCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.notifyConfirmCrossfade,
    );
    _notifyConfirmAnim = CurvedAnimation(
      parent: _notifyConfirmCtrl,
      curve: Curves.easeIn,
    );

    _checkMdmThenStatus();
  }

  @override
  void dispose() {
    _crisisSwapCtrl.dispose();
    _urgencyPulseCtrl.dispose();
    _envelopePulseCtrl.dispose();
    _notifyConfirmCtrl.dispose();
    _emailCtrl.dispose();
    super.dispose();
  }

  // ── MDM check runs before standard compliance check (B overrides region) ──
  Future<void> _checkMdmThenStatus() async {
    final isMdm = await MdmDetectionService.isManagedDevice();
    if (!mounted) return;
    if (isMdm) {
      setState(() => _ext = _ExtensionState.mdm);
      return;
    }
    _checkStatus();
  }

  Future<void> _checkStatus() async {
    setState(() => _isLoadingAction = true);
    final status = await _complianceService.checkCompliance();
    if (!mounted) return;

    if (status == ComplianceStatus.allowed) {
      // Navigate to Home/Main
      Navigator.of(context).pushReplacementNamed('/main');
    } else {
      // Pre-fetch stored region so _buildBlockedScreen can template it
      final region = await _complianceService.getStoredRegion();
      if (!mounted) return;
      setState(() {
        _status = status;
        _storedRegion = region;
        _isLoadingAction = false;
      });
    }
  }

  Future<void> _handleAgeVerification(bool meetsMinAge) async {
    if (!meetsMinAge) {
      setState(() {
        _status = ComplianceStatus.blockedAge;
      });
      return;
    }

    await _complianceService.setAgeVerified(true);
    _checkStatus();
  }

  Future<void> _requestLocation() async {
    setState(() => _isLoadingAction = true);
    await _complianceService.requestLocationPermission();
    // After requesting, check again to trigger the full logic (get pos, reverse geocode)
    _checkStatus();
  }

  Future<void> _launchEmail() async {
    final Uri emailLaunchUri = Uri(
      scheme: 'mailto',
      path: 'privacy@gentlequest.app',
      query: _encodeQueryParameters(<String, String>{
        'subject': 'Data Export Request (Blocked Account)',
        'body': 'I am requesting a copy of my data under GDPR/CCPA rights.'
      }),
    );
    if (!await launchUrl(emailLaunchUri)) {
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(content: Text('Could not launch email client')),
         );
      }
    }
  }

  String? _encodeQueryParameters(Map<String, String> params) {
    return params.entries
        .map((e) => '${Uri.encodeComponent(e.key)}=${Uri.encodeComponent(e.value)}')
        .join('&');
  }

  // ── R1D11 — State A helpers ───────────────────────────────────────────────

  /// Called from the notify-me email text field's onChanged.
  /// If a crisis keyword is detected, swap to the 988 surface in 200ms (P6).
  void _onEmailChanged(String value) {
    if (_ext == _ExtensionState.crisis) return; // already showing crisis
    if (CrisisKeywordDetector.match(value)) {
      _activateCrisisOverride();
    }
  }

  void _activateCrisisOverride() {
    setState(() => _ext = _ExtensionState.crisis);
    _crisisSwapCtrl.forward();
    _urgencyPulseCtrl.repeat();
  }

  void _dismissCrisisOverride() {
    _urgencyPulseCtrl.stop();
    _crisisSwapCtrl.reverse().then((_) {
      if (mounted) setState(() => _ext = _ExtensionState.none);
    });
  }

  // ── R1D11 — State C helper ────────────────────────────────────────────────

  Future<void> _submitNotifyEmail() async {
    final email = _emailCtrl.text.trim();
    if (email.isEmpty) return;
    setState(() => _isSubmittingEmail = true);
    // TODO(backend): POST email to /api/compliance/notify-me
    // Stub: 300ms crossfade to confirmation after simulated submit.
    await Future<void>.delayed(GQDurations.notifyConfirmCrossfade);
    if (!mounted) return;
    setState(() {
      _isSubmittingEmail = false;
      _ext = _ExtensionState.notifyOk;
    });
    _notifyConfirmCtrl.forward();
    _envelopePulseCtrl.forward(); // single pulse (not repeat)
  }

  void _dismissNotifyConfirmation() {
    _notifyConfirmCtrl.reverse().then((_) {
      if (mounted) {
        setState(() => _ext = _ExtensionState.none);
        _emailCtrl.clear();
      }
    });
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    // R1D11 State B — MDM override (region-agnostic; highest priority after crisis)
    if (_ext == _ExtensionState.mdm) {
      return _buildManagedDeviceBlock();
    }

    // R1D11 State A — Crisis-keyword override (P6: always shows, even inside block)
    if (_ext == _ExtensionState.crisis) {
      return FadeTransition(
        opacity: _crisisSwapAnim,
        child: _buildCrisisOverride(),
      );
    }

    // R1D11 State C — Notify-me confirmation
    if (_ext == _ExtensionState.notifyOk) {
      return FadeTransition(
        opacity: _notifyConfirmAnim,
        child: _buildNotifyConfirmation(),
      );
    }

    // Standard compliance flow (R1D10 base)
    if (_status == ComplianceStatus.loading || _isLoadingAction) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    switch (_status) {
      case ComplianceStatus.ageVerificationRequired:
        return _buildAgeGate();
      case ComplianceStatus.locationPermissionRequired:
      case ComplianceStatus.locationServicesDisabled:
        return _buildLocationGate();
      case ComplianceStatus.conversionRequired:
        return _buildConversionScreen();
      case ComplianceStatus.blockedAge:
        final minAge = ComplianceService.minAgeForRegion(_storedRegion);
        return _buildBlockedScreen(
          "Come back when you're $minAge",
          "GentleQuest needs you to be $minAge or older in your region. We'll be here for you when the time comes — until then, please talk to a parent, school counselor, or a trusted adult if things feel heavy.",
        );
      case ComplianceStatus.blockedRegion:
        return _buildBlockedScreen(
          "Region Unavailable",
          "Due to strict local regulations regarding AI implementation (e.g., Illinois WOPR Act, Utah HB 452, EU AI Act), GentleQuest is not available in your jurisdiction.",
        );
      case ComplianceStatus.error:
        return _buildErrorScreen();
      default:
        return const Scaffold(body: SizedBox()); // Should have navigated
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // R1D11 State A — Crisis-keyword override
  // Verbatim copy from GentleQuest_Compliance_Extensions.html
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildCrisisOverride() {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF1F1), // soft coral atmosphere per HTML
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),

              // Urgency ring — soft pulse (not alarm). Coral-not-red (P4).
              Center(
                child: AnimatedBuilder(
                  animation: _urgencyPulseCtrl,
                  builder: (context, child) {
                    // Pulse: box-shadow expands from 0 to 16px and back
                    final t = _urgencyPulseCtrl.value;
                    final shadowRadius = t < 0.7
                        ? (t / 0.7) * 16.0
                        : ((1.0 - t) / 0.3) * 16.0;
                    final shadowOpacity = t < 0.7
                        ? 0.45 * (1.0 - (t / 0.7))
                        : 0.0;
                    return Container(
                      width: 74,
                      height: 74,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [Color(0xFFFFD9D9), Color(0xFFFFE8E8)],
                        ),
                        border: Border.all(
                          color: GQColors.coral.withAlpha(89), // 0.35 opacity
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: GQColors.coral
                                .withAlpha((shadowOpacity * 255).round()),
                            blurRadius: shadowRadius,
                          ),
                        ],
                      ),
                      child: child,
                    );
                  },
                  child: const Icon(
                    Icons.favorite_rounded,
                    color: Color(0xFFE0494C), // gq-accent-dk
                    size: 32,
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // Urgency block — verbatim copy (State A)
              const Text(
                'Right now, please call 988.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.displayFamily,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.4,
                  height: 1.18,
                  color: GQColors.ink,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Free, confidential, available 24/7.\nThey want to help.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  height: 1.6,
                  color: GQColors.ink2,
                ),
              ),

              const SizedBox(height: 20),

              // Primary CTA — Call 988 (tel:988)
              Semantics(
                button: true,
                label: 'Call 988 — free, confidential, available 24/7',
                child: GestureDetector(
                  onTap: () =>
                      _launchUri(context, Uri.parse('tel:988'), label: 'Call 988'),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    decoration: BoxDecoration(
                      color: GQColors.coral,
                      borderRadius: BorderRadius.circular(GQRadii.button),
                      boxShadow: [
                        BoxShadow(
                          color: GQColors.coral.withAlpha(153),
                          blurRadius: 32,
                          offset: const Offset(0, 14),
                        ),
                      ],
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.phone_rounded,
                            color: Colors.white, size: 18),
                        SizedBox(width: 8),
                        Text(
                          'Call 988',
                          style: TextStyle(
                            fontFamily: GQTypography.displayFamily,
                            fontSize: 17,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.2,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 10),

              // Secondary CTAs — Text 988 + Chat online
              Row(
                children: [
                  Expanded(
                    child: Semantics(
                      button: true,
                      label: 'Text 988',
                      child: GestureDetector(
                        onTap: () => _launchUri(
                            context, Uri.parse('sms:988'), label: 'Text 988'),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(GQRadii.button),
                            border: Border.all(color: GQColors.hair),
                          ),
                          child: const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.message_rounded,
                                  color: GQColors.ink, size: 14),
                              SizedBox(width: 6),
                              Text(
                                'Text 988',
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 13.5,
                                  fontWeight: FontWeight.w800,
                                  color: GQColors.ink,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Semantics(
                      button: true,
                      label: 'Chat online at 988lifeline.org',
                      child: GestureDetector(
                        onTap: () => _launchUri(
                          context,
                          Uri.parse('https://988lifeline.org/chat'),
                          label: 'Chat online',
                        ),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(GQRadii.button),
                            border: Border.all(color: GQColors.hair),
                          ),
                          child: const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.language_rounded,
                                  color: GQColors.ink, size: 14),
                              SizedBox(width: 6),
                              Text(
                                'Chat online',
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 13.5,
                                  fontWeight: FontWeight.w800,
                                  color: GQColors.ink,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 28),

              // "More resources" divider
              Row(
                children: [
                  Expanded(child: Container(height: 1, color: GQColors.hair)),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      'MORE RESOURCES',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.4,
                        color: GQColors.ink3,
                      ),
                    ),
                  ),
                  Expanded(child: Container(height: 1, color: GQColors.hair)),
                ],
              ),

              const SizedBox(height: 16),

              // Regional resource cards (verbatim labels per spec)
              _RegionalResourceCard(
                icon: Icons.message_rounded,
                iconBgColor: GQColors.primarySoft,
                iconColor: GQColors.primary,
                title: 'Crisis Text Line',
                subtitle: 'Text HOME to 741741',
                onTap: () => _launchUri(
                  context,
                  Uri.parse('sms:741741?body=HOME'),
                  label: 'Crisis Text Line',
                ),
              ),
              const SizedBox(height: 8),
              _RegionalResourceCard(
                icon: Icons.favorite_outlined,
                iconBgColor: GQColors.primarySoft,
                iconColor: GQColors.primary,
                title: 'NAMI Illinois',
                subtitle: 'Helpline · 800-950-6264',
                onTap: () => _launchUri(
                  context,
                  Uri.parse('tel:8009506264'),
                  label: 'NAMI Illinois',
                ),
              ),

              const SizedBox(height: 20),

              // Collapsible block reason — verbatim transition text (State A)
              _BlockReasonDisclosure(
                summaryText:
                    "When you're ready, here's why GentleQuest isn't available in your state",
                bodyText:
                    'Illinois law requires additional clinical licensure for AI mental-health services. We\'re working with state regulators and will be available as soon as we can be.',
                onDismiss: _dismissCrisisOverride,
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // R1D11 State B — Managed-device block (MDM detected)
  // UI only — backend detection stubbed; see mdm_detection_service.dart.
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildManagedDeviceBlock() {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),

              // Device-with-shield icon — calm lavender (not alarming)
              Center(
                child: Container(
                  width: 78,
                  height: 78,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(24),
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [GQColors.primarySoft, Color(0xFFE0E5FB)],
                    ),
                    border: Border.all(
                      color: GQColors.primary.withAlpha(46),
                    ),
                  ),
                  child: const Icon(
                    Icons.shield_outlined,
                    color: GQColors.primaryDk,
                    size: 36,
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // Heading — verbatim from HTML
              const Text(
                'This device limits some apps.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.displayFamily,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.4,
                  height: 1.2,
                  color: GQColors.ink,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Your school or workplace may restrict GentleQuest. Try one of these instead — they work everywhere.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  height: 1.6,
                  color: GQColors.ink2,
                ),
              ),

              const SizedBox(height: 24),

              // Universal resource list — SMS / Call / Web (no native deeplinks
              // that MDM would block)
              _UniversalResourceCard(
                icon: Icons.message_rounded,
                iconBgColor: GQColors.primarySoft,
                iconColor: GQColors.primary,
                tagText: 'SMS',
                tagBg: GQColors.primarySoft,
                tagColor: GQColors.primaryDk,
                title: 'Crisis Text Line',
                subtitle: 'Text HOME to 741741 · works on any phone',
                onTap: () => _launchUri(
                  context,
                  Uri.parse('sms:741741?body=HOME'),
                  label: 'Crisis Text Line',
                ),
              ),
              const SizedBox(height: 10),
              _UniversalResourceCard(
                icon: Icons.phone_rounded,
                iconBgColor: GQColors.accentSoft,
                iconColor: GQColors.coral,
                tagText: 'CALL',
                tagBg: GQColors.accentSoft,
                tagColor: const Color(0xFFB73E3E),
                title: '988 Lifeline',
                subtitle: 'Dial 988 · works on any phone, 24/7',
                onTap: () => _launchUri(
                  context,
                  Uri.parse('tel:988'),
                  label: '988 Lifeline',
                ),
              ),
              const SizedBox(height: 10),
              _UniversalResourceCard(
                icon: Icons.language_rounded,
                iconBgColor: const Color(0xFFE8F4EE),
                iconColor: const Color(0xFF3F8B6A),
                tagText: 'WEB',
                tagBg: const Color(0xFFE8F4EE),
                tagColor: const Color(0xFF3F8B6A),
                title: 'IASP Resources',
                subtitle: 'Find a local hotline anywhere in the world',
                onTap: () => _launchUri(
                  context,
                  Uri.parse('https://www.iasp.info/resources/Crisis_Centres/'),
                  label: 'IASP Resources',
                ),
              ),

              const SizedBox(height: 24),

              // Footer — personal device link
              Center(
                child: Semantics(
                  button: true,
                  label: 'Or use GentleQuest on your personal device',
                  child: GestureDetector(
                    onTap: () => _launchUri(
                      context,
                      Uri.parse('https://gentlequest.app/get'),
                      label: 'GentleQuest personal device',
                    ),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 11),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(GQRadii.button),
                        border: Border.all(color: GQColors.hair),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            'Or use GentleQuest on your personal device',
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 12.5,
                              fontWeight: FontWeight.w700,
                              color: GQColors.ink2,
                            ),
                          ),
                          SizedBox(width: 4),
                          Icon(Icons.chevron_right_rounded,
                              size: 14, color: GQColors.ink2),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // R1D11 State C — Notify-me confirmation
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildNotifyConfirmation() {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: Stack(
          children: [
            // Envelope icon — single animated pulse on enter
            Positioned(
              top: 200,
              left: 0,
              right: 0,
              child: Center(
                child: ScaleTransition(
                  scale: _envelopePulseAnim,
                  child: Container(
                    width: 88,
                    height: 88,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(24),
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
                    child: const Icon(Icons.mail_outline_rounded,
                        color: Colors.white, size: 40),
                  ),
                ),
              ),
            ),

            // Headline + body (verbatim from HTML)
            Positioned(
              top: 328,
              left: 28,
              right: 28,
              child: Column(
                children: [
                  const Text(
                    "You're on the list.",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontFamily: GQTypography.displayFamily,
                      fontSize: 30,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.5,
                      height: 1.15,
                      color: GQColors.ink,
                    ),
                  ),
                  const SizedBox(height: 12),
                  RichText(
                    textAlign: TextAlign.center,
                    text: const TextSpan(
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 14.5,
                        fontWeight: FontWeight.w500,
                        height: 1.6,
                        color: GQColors.ink2,
                      ),
                      children: [
                        TextSpan(text: "We'll email you "),
                        TextSpan(
                          text: 'once',
                          style: TextStyle(
                              fontWeight: FontWeight.w800, color: GQColors.ink),
                        ),
                        TextSpan(
                            text:
                                ' — when GentleQuest is available in Illinois.\nNo marketing, no follow-ups.'),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Promise pill — "Your email is encrypted at rest"
            Positioned(
              top: 484,
              left: 0,
              right: 0,
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 9),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(GQRadii.button),
                    border: Border.all(color: GQColors.hair),
                    boxShadow: [
                      BoxShadow(
                        color: GQColors.ink.withAlpha(26),
                        blurRadius: 14,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check_circle_outline_rounded,
                          color: Color(0xFF3F8B6A), size: 13),
                      SizedBox(width: 6),
                      Text(
                        'Your email is encrypted at rest',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 12.5,
                          fontWeight: FontWeight.w700,
                          color: GQColors.ink2,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // "Got it" CTA — routes back to compliance block
            Positioned(
              bottom: 108,
              left: 24,
              right: 24,
              child: Semantics(
                button: true,
                label: 'Got it — dismiss confirmation',
                child: GestureDetector(
                  onTap: _dismissNotifyConfirmation,
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    decoration: BoxDecoration(
                      color: GQColors.primary,
                      borderRadius: BorderRadius.circular(GQRadii.button),
                      boxShadow: [
                        BoxShadow(
                          color: GQColors.primary.withAlpha(153),
                          blurRadius: 28,
                          offset: const Offset(0, 12),
                        ),
                      ],
                    ),
                    child: const Text(
                      'Got it',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontFamily: GQTypography.displayFamily,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.2,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ),
            ),

            // Plain-language opt-out — verbatim from HTML
            const Positioned(
              bottom: 54,
              left: 28,
              right: 28,
              child: Text(
                'Want to remove yourself? Just reply "unsubscribe" to that email.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w600,
                  height: 1.55,
                  color: GQColors.ink3,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // R1D10 base screens (preserved — no drive-by refactors)
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildAgeGate() {
    // Region is set after the IP/GPS step in the compliance flow. On the
    // very first launch _storedRegion may be null — in that case use the
    // universal floor (13) since unknown-region falls through to the
    // permissive default per minAgeForRegion.
    final minAge = ComplianceService.minAgeForRegion(_storedRegion);
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.verified_user_outlined, size: 80, color: Color(0xFF667EEA)),
            const SizedBox(height: 24),
            Text(
              "One quick check",
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              // Copy was "built for adults · 18+" — softened so the
              // high-school target audience doesn't bounce on first touch.
              "GentleQuest is here for you. We just need to confirm you're $minAge or older to continue.",
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, color: Colors.black87),
            ),
            const SizedBox(height: 48),
            ElevatedButton(
              onPressed: () => _handleAgeVerification(true),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF667EEA),
                padding: const EdgeInsets.symmetric(vertical: 16),
                foregroundColor: Colors.white,
              ),
              child: Text("I am $minAge or older", style: const TextStyle(fontSize: 18)),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => _handleAgeVerification(false),
              child: Text("I am under $minAge", style: const TextStyle(fontSize: 16, color: Colors.grey)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLocationGate() {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.location_on_outlined, size: 80, color: Color(0xFFFF6B6B)),
            const SizedBox(height: 24),
            Text(
              "Regional Verification",
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Text(
              "Certain jurisdictions (e.g., IL, UT, WA) have restricted AI for mental health. We need to verify you are not physically located in a 'Red Zone'.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 10),
            const Text(
              "We perform a one-time check. We do not track you.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: Colors.grey),
            ),
            const SizedBox(height: 48),
            ElevatedButton(
              onPressed: _requestLocation,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFF6B6B),
                padding: const EdgeInsets.symmetric(vertical: 16),
                foregroundColor: Colors.white,
              ),
              child: const Text("Verify Location", style: TextStyle(fontSize: 18)),
            ),
            if (_status == ComplianceStatus.locationServicesDisabled)
              const Padding(
                padding: EdgeInsets.only(top: 16.0),
                child: Text(
                  "Please enable Location Services in your device settings to proceed.",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.red),
                ),
              ),
          ],
        ),
      ),
    );
  }

  // Retained because the ComplianceStatus.conversionRequired enum value
  // still exists for backwards compatibility, but no compliance code path
  // returns it as of 2026-05-21 — web is now first-class. If we ever
  // re-introduce a terminal "your platform can't be served" state, this
  // is the screen that renders it.
  //
  // Was a hard "Mobile App Required" block. Replaced with a soft message
  // pointing at the optional mobile-app promo sheet (which fires on chat
  // screen first mount on web). If someone *does* land here, give them a
  // useful action instead of a dead end.
  Widget _buildConversionScreen() {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.refresh,
                size: 80, color: Color(0xFF667EEA)),
            const SizedBox(height: 24),
            Text(
              "Something went sideways",
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Text(
              "We couldn't finish setting up your session. Please check your connection and try again.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _checkStatus,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF667EEA),
                padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 32),
                foregroundColor: Colors.white,
              ),
              child: const Text("Try again", style: TextStyle(fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBlockedScreen(String title, String message) {
    final bool isRegionBlock = title != "Age Requirement";
    // Use stored region name; fall back to "your state" if unavailable.
    final String regionName = _storedRegion ?? 'your state';

    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Sunrise gradient header (coral/amber — NOT red) ─────────────
              Container(
                height: 280,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Color(0xFFFFD085), GQColors.coral],
                  ),
                  borderRadius: BorderRadius.vertical(
                    bottom: Radius.circular(32),
                  ),
                ),
                child: SafeArea(
                  bottom: false,
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 72,
                          height: 72,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.25),
                          ),
                          child: const Icon(
                            Icons.wb_sunny_outlined,
                            color: Colors.white,
                            size: 38,
                          ),
                        ),
                        const SizedBox(height: 20),
                        const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 28),
                          child: Text(
                            'Some support is local-first.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontFamily: GQTypography.displayFamily,
                              fontSize: 24,
                              fontWeight: FontWeight.w800,
                              letterSpacing: -0.3,
                              height: 1.2,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 32),
                          child: Text(
                            isRegionBlock
                                ? "GentleQuest isn't available in $regionName yet —\nbut you have great options right where you are."
                                : message,
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 13.5,
                              fontWeight: FontWeight.w500,
                              height: 1.55,
                              color: Colors.white.withValues(alpha: 0.9),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 28),

              // ── "Right now in {state}" section header ────────────────────
              if (isRegionBlock) ...[
                Row(
                  children: [
                    Expanded(child: Container(height: 1, color: GQColors.hair)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: Text(
                        'RIGHT NOW IN ${regionName.toUpperCase()}',
                        style: const TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.4,
                          color: GQColors.ink3,
                        ),
                      ),
                    ),
                    Expanded(child: Container(height: 1, color: GQColors.hair)),
                  ],
                ),
                const SizedBox(height: 4),
                const Center(
                  child: Text(
                    'ALL FREE · 24/7',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                      color: GQColors.ink3,
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // 988 Lifeline — P6: always present on blocked-region path
                _LifelineCard988(
                  onTap: () => _launchUri(
                    context,
                    Uri.parse('tel:988'),
                    label: '988 Lifeline',
                  ),
                ),
                const SizedBox(height: 8),

                // Crisis Text Line
                _RegionalResourceCard(
                  icon: Icons.message_rounded,
                  iconBgColor: GQColors.primarySoft,
                  iconColor: GQColors.primary,
                  title: 'Crisis Text Line',
                  subtitle: 'Text HOME to 741741',
                  onTap: () => _launchUri(
                    context,
                    Uri.parse('sms:741741?body=HOME'),
                    label: 'Crisis Text Line',
                  ),
                ),
                const SizedBox(height: 8),

                // NAMI — label uses regionName where available
                _RegionalResourceCard(
                  icon: Icons.favorite_outlined,
                  iconBgColor: GQColors.primarySoft,
                  iconColor: GQColors.primary,
                  title: 'NAMI $regionName',
                  subtitle: 'Helpline · 800-950-6264',
                  onTap: () => _launchUri(
                    context,
                    Uri.parse('tel:8009506264'),
                    label: 'NAMI $regionName',
                  ),
                ),

                const SizedBox(height: 28),
              ],

              // ── Notify-me form (region block only) ───────────────────────
              if (isRegionBlock) ...[
                TextField(
                  controller: _emailCtrl,
                  onChanged: _onEmailChanged, // ← R1D11: crisis-keyword hook
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(
                    hintText: 'Your email',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(GQRadii.card),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 14),
                  ),
                ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: _isSubmittingEmail ? null : _submitNotifyEmail,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: GQColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 24, vertical: 14),
                    shape: const StadiumBorder(),
                  ),
                  child: _isSubmittingEmail
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Notify me when available'),
                ),
                const SizedBox(height: 24),

                // Data Export Link for CCPA/GDPR Compliance
                ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 300),
                  child: Center(
                    child: TextButton.icon(
                      onPressed: _launchEmail,
                      icon: const Icon(Icons.download),
                      label: const Text("Request My Data (Export)"),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  "Blocked users retain full rights to their data.",
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],

              // ── Age block — 988 nudge (P6) ───────────────────────────────
              if (!isRegionBlock) ...[
                const SizedBox(height: 8),
                const Text(
                  'Need Help?',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                _LifelineCard988(
                  onTap: () => _launchUri(
                    context,
                    Uri.parse('tel:988'),
                    label: '988 Lifeline',
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildErrorScreen() {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 60, color: Colors.orange),
            const SizedBox(height: 16),
            const Text("Verification Failed", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text(
              "We couldn't verify your location. This usually resolves on a second try.",
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _checkStatus,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF667EEA),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
              ),
              child: const Text("Try Again"),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: _checkStatus,
              child: const Text(
                "Having trouble? We can verify your region another way",
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF667EEA)),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              "Alternative verification uses your internet connection instead of GPS.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Private shared widgets (file-scoped; not exported)
// ─────────────────────────────────────────────────────────────────────────────

/// Shared 988 Lifeline card — used in both blocked-region (R1D10) and MDM
/// surfaces. Keeps P6 (crisis never blocks) consistent across all paths.
class _LifelineCard988 extends StatelessWidget {
  final VoidCallback onTap;

  const _LifelineCard988({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: '988 Lifeline — Dial 988 — free, confidential, 24/7',
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(color: GQColors.hair),
            boxShadow: [
              BoxShadow(
                color: GQColors.ink.withValues(alpha: 0.05),
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
                  color: GQColors.accentSoft,
                ),
                child: const Icon(
                  Icons.phone_rounded,
                  color: GQColors.coral,
                  size: 18,
                ),
              ),
              const SizedBox(width: 12),
              const Expanded(
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
                            color: GQColors.ink,
                          ),
                        ),
                        SizedBox(width: 6),
                        _TagPill(label: 'CALL', bg: GQColors.accentSoft,
                            fg: Color(0xFFB73E3E)),
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
                        color: GQColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded,
                  color: GQColors.ink3, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}

/// Tiny pill label used inside resource cards.
class _TagPill extends StatelessWidget {
  final String label;
  final Color bg;
  final Color fg;

  const _TagPill({required this.label, required this.bg, required this.fg});

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
class _RegionalResourceCard extends StatelessWidget {
  final IconData icon;
  final Color iconBgColor;
  final Color iconColor;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _RegionalResourceCard({
    required this.icon,
    required this.iconBgColor,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: '$title — $subtitle',
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: GQColors.hair),
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
                      style: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: GQColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded,
                  color: GQColors.ink3, size: 14),
            ],
          ),
        ),
      ),
    );
  }
}

/// Resource card row used in State B (universal list — no deeplinks blocked by MDM).
class _UniversalResourceCard extends StatelessWidget {
  final IconData icon;
  final Color iconBgColor;
  final Color iconColor;
  final String tagText;
  final Color tagBg;
  final Color tagColor;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _UniversalResourceCard({
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
    return Semantics(
      button: true,
      label: '$title — $subtitle',
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(color: GQColors.hair),
            boxShadow: [
              BoxShadow(
                color: GQColors.ink.withAlpha(13),
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
                          style: const TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 14,
                            fontWeight: FontWeight.w800,
                            color: GQColors.ink,
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
                      style: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        height: 1.4,
                        color: GQColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded,
                  color: GQColors.ink3, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}

/// Collapsible block-reason disclosure — State A only.
/// collapsed by default (urgent help is the focus).
class _BlockReasonDisclosure extends StatefulWidget {
  final String summaryText;
  final String bodyText;
  final VoidCallback? onDismiss;

  const _BlockReasonDisclosure({
    required this.summaryText,
    required this.bodyText,
    this.onDismiss,
  });

  @override
  State<_BlockReasonDisclosure> createState() =>
      _BlockReasonDisclosureState();
}

class _BlockReasonDisclosureState extends State<_BlockReasonDisclosure> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
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
                color: Colors.white.withAlpha(140),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                    color: GQColors.hair,
                    style: BorderStyle.solid),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      widget.summaryText,
                      style: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        height: 1.4,
                        color: GQColors.ink2,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(
                    _expanded
                        ? Icons.keyboard_arrow_up_rounded
                        : Icons.keyboard_arrow_down_rounded,
                    color: GQColors.ink3,
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
              style: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 12,
                fontWeight: FontWeight.w500,
                height: 1.6,
                color: GQColors.ink3,
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

Future<void> _launchUri(BuildContext context, Uri uri,
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
