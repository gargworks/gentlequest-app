// Age Verification Blocked Screen — v1.4.0 Phase C terminal gate.
//
// Shown to users where Play Age Signals returned `AgeSignalStatus.verifiedUnder`
// in regions that require a verified age signal (e.g. Texas SB 2420). Terminal:
// no back, no skip — Close-app CTA + mailto support fallback.
//
// Boot wire: see SplashScreen in main.dart — this screen is reached after
// WelcomeScreen.hasBeenSeen() resolves true AND ComplianceService surfaces a
// `verifiedUnder` signal (Phase B wires the signal cache).
//
// Spec: docs/integration/PLAY_AGE_SIGNALS_v0_0_3.md
// Phase A (#139): PlayAgeSignalsService Dart + Android Kotlin.
// Phase B: ComplianceService.fetchAndCacheAgeSignal + requiresVerifiedSignal.
// Phase C (this PR): terminal UI + boot wire.

import 'dart:io' show Platform, exit;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show SystemNavigator;
import 'package:url_launcher/url_launcher.dart';

import 'package:ai_buddy_web/theme/gq_theme.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';

/// Support email surfaced on the terminal block screen.
/// Public address — safe for source.
const String _kSupportEmail = 'support@gentlequest.app';

/// Terminal "must be 18+" screen reached when the device's Play Age Signal
/// returns `verifiedUnder` and the user's region requires a verified signal.
///
/// Stateless by design — there is no state to advance. The only escape hatches
/// are (a) close the app, (b) email support to dispute the signal.
///
/// Design note: uses `assets/images/quests/tip_generic.svg` as a temporary
/// illustration placeholder. Flagged for a dedicated illustration pass before
/// public ship (see PR body).
class AgeVerificationBlockedScreen extends StatelessWidget {
  const AgeVerificationBlockedScreen({super.key});

  // Visible only for widget tests so we can assert the address without
  // duplicating the literal in test code.
  @visibleForTesting
  static String get supportEmail => _kSupportEmail;

  /// Test seam — when non-null, the Close-app CTA invokes this callback
  /// instead of [SystemNavigator.pop] / [exit]. Used by widget tests so
  /// tapping the CTA doesn't terminate the test process via exit(0). Never
  /// set in production code.
  @visibleForTesting
  static VoidCallback? debugCloseAppOverride;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: t.bg,
      // Terminal: no AppBar, no back affordance, no skip.
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 32.0),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                // Placeholder illustration — see design-pass flag in PR body.
                Center(
                  child: Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      color: t.accentSoft,
                      borderRadius: BorderRadius.circular(GQRadii.cardLg),
                    ),
                    child: Icon(
                      Icons.shield_outlined,
                      size: 64,
                      color: t.coral,
                    ),
                  ),
                ),
                const SizedBox(height: 32),
                // Headline.
                Text(
                  'Sorry — GentleQuest is for adults',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: GQTypography.displayFamily,
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                    color: t.ink,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 16),
                // Body.
                Text(
                  "This app requires verification that you're 18 or older. "
                  "The age signal from your device didn't confirm eligibility. "
                  'If you believe this is wrong, please reach out at '
                  '$_kSupportEmail.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 16,
                    color: t.ink2,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 40),
                // Primary CTA.
                ElevatedButton(
                  key: const Key('age_blocked_close_button'),
                  onPressed: () => _closeApp(),
                  style: ElevatedButton.styleFrom(
                    // primaryDk stays static — CTA fill w/ white text (theme exception).
                    backgroundColor: GQColors.primaryDk,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: const StadiumBorder(),
                    textStyle: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  child: const Text('Close app'),
                ),
                const SizedBox(height: 16),
                // Support mailto link.
                TextButton(
                  key: const Key('age_blocked_support_link'),
                  onPressed: () => _openSupportEmail(),
                  child: Text(
                    'Contact support',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 14,
                      color: t.primary,
                      decoration: TextDecoration.underline,
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

  /// Close the app cleanly. Android: SystemNavigator.pop (recommended); iOS:
  /// dart:io exit(0) (App Store still permits; reached only on terminal block).
  void _closeApp() {
    final override = debugCloseAppOverride;
    if (override != null) {
      override();
      return;
    }
    if (kIsWeb) {
      // No-op on web — the terminal screen still renders; user closes the tab.
      return;
    }
    if (Platform.isAndroid) {
      SystemNavigator.pop();
    } else {
      // iOS (and any other native target).
      exit(0);
    }
  }

  /// Launch a mailto: link to the support address.
  Future<void> _openSupportEmail() async {
    final Uri uri = Uri(
      scheme: 'mailto',
      path: _kSupportEmail,
      queryParameters: <String, String>{
        'subject': 'GentleQuest age verification — dispute',
      },
    );
    // Best-effort: if no mail client is available, silently no-op rather than
    // crashing the terminal screen.
    try {
      await launchUrl(uri);
    } catch (_) {
      // intentional no-op — terminal screen must not throw to user.
    }
  }
}
