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
import 'package:ai_buddy_web/theme/gq_theme.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';
import 'compliance/compliance_widgets.dart';

// No re-exports: every symbol extracted to compliance/compliance_widgets.dart
// was private pre-split, so no external consumer can depend on them.

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

    // Honesty audit §9: there is no /api/compliance/notify-me backend.
    // The earlier 300ms stub showed a "we'll email you once" confirmation
    // and then silently dropped the email. The honest minimum is to open
    // the user's mail app pre-filled to the operator inbox, so when they
    // tap send the request actually lands somewhere. Form is gated to
    // region-block only (isRegionBlock=true), so under-13 users never
    // see this surface.
    final region = (_storedRegion ?? 'unknown region').trim();
    final subject = 'GentleQuest notify-me — $region';
    final body =
        'Please notify me when GentleQuest becomes available in $region.\n\n'
        'My email: $email\n'
        'Region (from device): $region\n\n'
        '— Sent from GentleQuest compliance gate';
    final uri = Uri(
      scheme: 'mailto',
      path: 'hi@eidetic.works',
      queryParameters: {'subject': subject, 'body': body},
    );

    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    } catch (e) {
      debugPrint('compliance_notify_email: launchUrl failed — $e');
    }

    if (!mounted) return;
    setState(() {
      _isSubmittingEmail = false;
      _ext = _ExtensionState.notifyOk;
    });
    _notifyConfirmCtrl.forward();
    _envelopePulseCtrl.forward();
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
          isRegionBlock: false,
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
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: const Color(0xFFFFF1F1), // IMG-TINT: soft coral atmosphere per HTML (agent ruling 2026-05-22 keep raw)
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
                    final pulseT = _urgencyPulseCtrl.value;
                    final shadowRadius = pulseT < 0.7
                        ? (pulseT / 0.7) * 16.0
                        : ((1.0 - pulseT) / 0.3) * 16.0;
                    final shadowOpacity = pulseT < 0.7
                        ? 0.45 * (1.0 - (pulseT / 0.7))
                        : 0.0;
                    return Container(
                      width: 74,
                      height: 74,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          // IMG-TINT: atmospheric coral gradient (agent ruling 2026-05-22 keep raw)
                          colors: [Color(0xFFFFD9D9), Color(0xFFFFE8E8)],
                        ),
                        border: Border.all(
                          color: t.coral.withAlpha(89), // 0.35 opacity
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: t.coral
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
                    color: GQColors.coralDk,
                    size: 32,
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // Urgency block — verbatim copy (State A)
              Text(
                'Right now, please call 988.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.displayFamily,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.4,
                  height: 1.18,
                  color: t.ink,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Free, confidential, available 24/7.\nThey want to help.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  height: 1.6,
                  color: t.ink2,
                ),
              ),

              const SizedBox(height: 20),

              // Primary CTA — Call 988 (tel:988)
              Semantics(
                button: true,
                label: 'Call 988 — free, confidential, available 24/7',
                child: GestureDetector(
                  onTap: () =>
                      launchUri(context, Uri.parse('tel:988'), label: 'Call 988'),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    decoration: BoxDecoration(
                      color: GQColors.dangerInk,
                      borderRadius: BorderRadius.circular(GQRadii.button),
                      boxShadow: [
                        BoxShadow(
                          color: GQColors.dangerInk.withAlpha(153),
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
                        onTap: () => launchUri(
                            context, Uri.parse('sms:988'), label: 'Text 988'),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          decoration: BoxDecoration(
                            color: t.surface,
                            borderRadius: BorderRadius.circular(GQRadii.button),
                            border: Border.all(color: t.hair),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.message_rounded,
                                  color: t.ink, size: 14),
                              SizedBox(width: 6),
                              Text(
                                'Text 988',
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 13.5,
                                  fontWeight: FontWeight.w800,
                                  color: t.ink,
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
                        onTap: () => launchUri(
                          context,
                          Uri.parse('https://988lifeline.org/chat'),
                          label: 'Chat online',
                        ),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          decoration: BoxDecoration(
                            color: t.surface,
                            borderRadius: BorderRadius.circular(GQRadii.button),
                            border: Border.all(color: t.hair),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.language_rounded,
                                  color: t.ink, size: 14),
                              SizedBox(width: 6),
                              Text(
                                'Chat online',
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 13.5,
                                  fontWeight: FontWeight.w800,
                                  color: t.ink,
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
                  Expanded(child: Container(height: 1, color: t.hair)),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      'MORE RESOURCES',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.4,
                        color: t.ink2,
                      ),
                    ),
                  ),
                  Expanded(child: Container(height: 1, color: t.hair)),
                ],
              ),

              const SizedBox(height: 16),

              // Regional resource cards (verbatim labels per spec)
              RegionalResourceCard(
                icon: Icons.message_rounded,
                iconBgColor: t.primarySoft,
                iconColor: t.primary,
                title: 'Crisis Text Line',
                subtitle: 'Text HOME to 741741',
                onTap: () => launchUri(
                  context,
                  Uri.parse('sms:741741?body=HOME'),
                  label: 'Crisis Text Line',
                ),
              ),
              const SizedBox(height: 8),
              RegionalResourceCard(
                icon: Icons.favorite_outlined,
                iconBgColor: t.primarySoft,
                iconColor: t.primary,
                title: 'NAMI Illinois',
                subtitle: 'Helpline · 800-950-6264',
                onTap: () => launchUri(
                  context,
                  Uri.parse('tel:8009506264'),
                  label: 'NAMI Illinois',
                ),
              ),

              const SizedBox(height: 20),

              // Collapsible block reason — verbatim transition text (State A)
              BlockReasonDisclosure(
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
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: t.bg,
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
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      // IMG-TINT: second stop pairs primarySoft into a softer periwinkle (agent ruling 2026-05-22 keep raw)
                      colors: [t.primarySoft, const Color(0xFFE0E5FB)],
                    ),
                    border: Border.all(
                      color: t.primary.withAlpha(46),
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
              Text(
                'This device limits some apps.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.displayFamily,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.4,
                  height: 1.2,
                  color: t.ink,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Your school or workplace may restrict GentleQuest. Try one of these instead — they work everywhere.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  height: 1.6,
                  color: t.ink2,
                ),
              ),

              const SizedBox(height: 24),

              // Universal resource list — SMS / Call / Web (no native deeplinks
              // that MDM would block)
              UniversalResourceCard(
                icon: Icons.message_rounded,
                iconBgColor: t.primarySoft,
                iconColor: t.primary,
                tagText: 'SMS',
                tagBg: t.primarySoft,
                tagColor: GQColors.primaryDk,
                title: 'Crisis Text Line',
                subtitle: 'Text HOME to 741741 · works on any phone',
                onTap: () => launchUri(
                  context,
                  Uri.parse('sms:741741?body=HOME'),
                  label: 'Crisis Text Line',
                ),
              ),
              const SizedBox(height: 10),
              UniversalResourceCard(
                icon: Icons.phone_rounded,
                iconBgColor: t.accentSoft,
                iconColor: t.coral,
                tagText: 'CALL',
                tagBg: t.accentSoft,
                tagColor: GQColors.coralDk,
                title: '988 Lifeline',
                subtitle: 'Dial 988 · works on any phone, 24/7',
                onTap: () => launchUri(
                  context,
                  Uri.parse('tel:988'),
                  label: '988 Lifeline',
                ),
              ),
              const SizedBox(height: 10),
              UniversalResourceCard(
                icon: Icons.language_rounded,
                iconBgColor: t.successSoft,
                iconColor: t.successInk,
                tagText: 'WEB',
                tagBg: t.successSoft,
                tagColor: t.successInk,
                title: 'IASP Resources',
                subtitle: 'Find a local hotline anywhere in the world',
                onTap: () => launchUri(
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
                    onTap: () => launchUri(
                      context,
                      Uri.parse('https://gentlequest.app/get'),
                      label: 'GentleQuest personal device',
                    ),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 11),
                      decoration: BoxDecoration(
                        color: t.surface,
                        borderRadius: BorderRadius.circular(GQRadii.button),
                        border: Border.all(color: t.hair),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            'Or use GentleQuest on your personal device',
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 12.5,
                              fontWeight: FontWeight.w700,
                              color: t.ink2,
                            ),
                          ),
                          SizedBox(width: 4),
                          Icon(Icons.chevron_right_rounded,
                              size: 14, color: t.ink2),
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
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: t.bg,
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
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [t.primary, t.coral],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: t.primary.withAlpha(115),
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
                  Text(
                    "You're on the list.",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontFamily: GQTypography.displayFamily,
                      fontSize: 30,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.5,
                      height: 1.15,
                      color: t.ink,
                    ),
                  ),
                  const SizedBox(height: 12),
                  RichText(
                    textAlign: TextAlign.center,
                    text: TextSpan(
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 14.5,
                        fontWeight: FontWeight.w500,
                        height: 1.6,
                        color: t.ink2,
                      ),
                      children: [
                        TextSpan(text: "Your request opened in your mail app — "),
                        TextSpan(
                          text: 'tap send',
                          style: TextStyle(
                              fontWeight: FontWeight.w800, color: t.ink),
                        ),
                        TextSpan(
                            text:
                                ' to deliver it.\nWe\'ll reply once when GentleQuest opens here.\nNo marketing, no follow-ups.'),
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
                    color: t.surface,
                    borderRadius: BorderRadius.circular(GQRadii.button),
                    border: Border.all(color: t.hair),
                    boxShadow: [
                      BoxShadow(
                        color: t.ink.withAlpha(26),
                        blurRadius: 14,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check_circle_outline_rounded,
                          color: t.successInk, size: 13),
                      SizedBox(width: 6),
                      Text(
                        'Your email is encrypted at rest',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 12.5,
                          fontWeight: FontWeight.w700,
                          color: t.ink2,
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
                      color: GQColors.primaryDk,
                      borderRadius: BorderRadius.circular(GQRadii.button),
                      boxShadow: [
                        BoxShadow(
                          color: GQColors.primaryDk.withAlpha(153),
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
            Positioned(
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
                  color: t.ink2,
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
    final t = GQTheme.of(context);
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
            Icon(Icons.verified_user_outlined, size: 80, color: t.primary),
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
                backgroundColor: GQColors.primaryDk,
                padding: const EdgeInsets.symmetric(vertical: 16),
                foregroundColor: Colors.white,
              ),
              child: Text("I am $minAge or older", style: const TextStyle(fontSize: 18)),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => _handleAgeVerification(false),
              child: Text("I am under $minAge", style: TextStyle(fontSize: 16, color: t.ink3)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLocationGate() {
    final t = GQTheme.of(context);
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Icon(Icons.location_on_outlined, size: 80, color: t.coral),
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
            Text(
              "We perform a one-time check. We do not track you.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: t.ink3),
            ),
            const SizedBox(height: 48),
            ElevatedButton(
              onPressed: _requestLocation,
              style: ElevatedButton.styleFrom(
                backgroundColor: GQColors.primaryDk,
                padding: const EdgeInsets.symmetric(vertical: 16),
                foregroundColor: Colors.white,
              ),
              child: const Text("Verify Location", style: TextStyle(fontSize: 18)),
            ),
            if (_status == ComplianceStatus.locationServicesDisabled)
              Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: Text(
                  "Please enable Location Services in your device settings to proceed.",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: t.coral),
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
    final t = GQTheme.of(context);
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.refresh,
                size: 80, color: t.primary),
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
                backgroundColor: GQColors.primaryDk,
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

  Widget _buildBlockedScreen(String title, String message,
      {bool isRegionBlock = true}) {
    final t = GQTheme.of(context);
    // Use stored region name; fall back to "your region" — not "your state",
    // since the user might be in the UK / EU / India / etc.
    final String regionName = _storedRegion ?? 'your region';

    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Sunrise gradient header (coral/amber — NOT red) ─────────────
              Container(
                height: 280,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    // IMG-TINT: gold→coral header gradient (agent ruling 2026-05-22 keep raw — first stop is decorative gold accent)
                    colors: [const Color(0xFFFFD085), t.coral],
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
                            color: t.surface.withValues(alpha: 0.25),
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
                    Expanded(child: Container(height: 1, color: t.hair)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: Text(
                        'RIGHT NOW IN ${regionName.toUpperCase()}',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.4,
                          color: t.ink2,
                        ),
                      ),
                    ),
                    Expanded(child: Container(height: 1, color: t.hair)),
                  ],
                ),
                const SizedBox(height: 4),
                Center(
                  child: Text(
                    'ALL FREE · 24/7',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                      color: t.ink2,
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // 988 Lifeline — P6: always present on blocked-region path
                LifelineCard988(
                  onTap: () => launchUri(
                    context,
                    Uri.parse('tel:988'),
                    label: '988 Lifeline',
                  ),
                ),
                const SizedBox(height: 8),

                // Crisis Text Line
                RegionalResourceCard(
                  icon: Icons.message_rounded,
                  iconBgColor: t.primarySoft,
                  iconColor: t.primary,
                  title: 'Crisis Text Line',
                  subtitle: 'Text HOME to 741741',
                  onTap: () => launchUri(
                    context,
                    Uri.parse('sms:741741?body=HOME'),
                    label: 'Crisis Text Line',
                  ),
                ),
                const SizedBox(height: 8),

                // NAMI — label uses regionName where available
                RegionalResourceCard(
                  icon: Icons.favorite_outlined,
                  iconBgColor: t.primarySoft,
                  iconColor: t.primary,
                  title: 'NAMI $regionName',
                  subtitle: 'Helpline · 800-950-6264',
                  onTap: () => launchUri(
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
                    backgroundColor: GQColors.primaryDk,
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
                Text(
                  "Blocked users retain full rights to their data.",
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: t.ink2),
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
                LifelineCard988(
                  onTap: () => launchUri(
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
    final t = GQTheme.of(context);
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 60, color: t.amber),
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
                backgroundColor: GQColors.primaryDk,
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
                style: TextStyle(color: GQColors.primaryDk),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              "Alternative verification uses your internet connection instead of GPS.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: t.ink2),
            ),
          ],
        ),
      ),
    );
  }
}

