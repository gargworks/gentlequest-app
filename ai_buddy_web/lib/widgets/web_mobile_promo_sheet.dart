import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../screens/auth/login_screen.dart';
import '../services/auth_service.dart';
import '../services/firebase_service.dart';
import '../theme/gq_tokens.dart';

/// One-time bottom sheet shown on web after compliance passes, offering the
/// mobile app for users who'd prefer the native experience.
///
/// Was a hard "Mobile App Required" block at the compliance step. That cost
/// the entire web acquisition surface. Now it's a non-blocking promo — user
/// can install the mobile app via store links OR just keep using the web
/// build. Shown once per device (tracked via SharedPreferences) so we don't
/// nag.
///
/// Updated 2026-05-21: passwordless sign-in now ships (see AuthService,
/// /api/auth/*). If the user signs in here on web, then installs the
/// mobile app and verifies the same email, the mobile device adopts the
/// canonical session_id and the conversation history follows.
class WebMobilePromoSheet extends StatelessWidget {
  const WebMobilePromoSheet({super.key});

  static const String _prefsKey = 'web_mobile_promo_shown_v1';

  /// Shows the sheet at most once per device. No-op on non-web platforms.
  /// Safe to call from a post-frame callback on chat screen first mount.
  ///
  /// Conversion-ramp policy: we only persist the "seen" flag on EXPLICIT
  /// dismiss (the "Continue on web" / store-link / sign-in buttons pop with
  /// `result == true`). Outside-tap barrier dismiss resolves to `null` and
  /// is treated as accidental — the sheet will re-show on next launch so we
  /// don't burn the only conversion impression on a stray tap.
  static Future<void> maybeShow(BuildContext context) async {
    if (!kIsWeb) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      if (prefs.getBool(_prefsKey) ?? false) return;
      if (!context.mounted) return;
      final result = await showModalBottomSheet<bool>(
        context: context,
        showDragHandle: true,
        isScrollControlled: true,
        isDismissible: true, // outside-tap allowed but not treated as informed
        backgroundColor: Colors.white,
        builder: (ctx) => const WebMobilePromoSheet(),
      );
      FirebaseService().logEvent('web_mobile_promo_shown', {
        'dismissed_explicitly': result == true,
      });
      if (result == true) {
        await prefs.setBool(_prefsKey, true);
      }
    } catch (_) {
      // Non-fatal — sheet won't render if prefs fail; user keeps using web.
    }
  }

  Future<void> _openStore(BuildContext context, _Store store) async {
    FirebaseService().logEvent('web_mobile_promo_click', {
      'store': store.name,
    });
    final uri = Uri.parse(store.url);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    } catch (_) {
      // Silent — user can copy the link from the visible button text
      // if launch fails (rare on browsers with popup blockers).
    }
    if (context.mounted) Navigator.of(context).maybePop(true);
  }

  Future<void> _openSignIn(BuildContext context) async {
    FirebaseService().logEvent('web_mobile_promo_signin_click');
    Navigator.of(context).maybePop(true);
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final alreadySignedIn = AuthService.instance.isSignedIn;
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.mobile_friendly,
                size: 56, color: GQColors.primary),
            const SizedBox(height: 16),
            const Text(
              'Continue on your phone',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: GQTypography.displayFamily,
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                letterSpacing: -0.3,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              alreadySignedIn
                  ? 'Install the mobile app and sign in with the same '
                      'email to pick this conversation back up. Voice '
                      'input and daily check-in reminders work natively '
                      'on mobile too.'
                  : 'Install the mobile app, then sign in with your '
                      'email to keep this conversation. Voice input '
                      'and daily check-in reminders work natively on '
                      'mobile. Anonymous use stays supported.',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 14,
                color: GQColors.ink2,
                height: 1.45,
              ),
            ),
            const SizedBox(height: 22),
            if (!alreadySignedIn) ...[
              _StoreButton(
                label: 'Sign in to sync first',
                icon: Icons.mail_outline,
                onTap: () => _openSignIn(context),
              ),
              const SizedBox(height: 10),
            ],
            _StoreButton(
              label: 'Get it on the App Store',
              icon: Icons.apple,
              onTap: () => _openStore(context, _Store.appStore),
              outlined: true,
            ),
            const SizedBox(height: 10),
            _StoreButton(
              label: 'Get it on Google Play',
              icon: Icons.shop,
              onTap: () => _openStore(context, _Store.playStore),
              outlined: true,
            ),
            const SizedBox(height: 16),
            TextButton(
              // Explicit "I've seen this, don't show again" — pop with `true`
              // so maybeShow() persists the seen flag. Outside-tap dismiss
              // returns null and re-shows on next launch.
              onPressed: () => Navigator.of(context).maybePop(true),
              child: const Text(
                'Continue on web',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: GQColors.ink2,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

enum _Store {
  appStore,
  playStore;

  /// Store landing URL.
  ///
  /// App Store: Apple's `/app/<slug>/id<numericId>` deep link is the
  /// preferred form, but we don't have the published numeric id until
  /// the app is approved + live in App Store Connect. Until then we
  /// use the search URL as a graceful fallback — it lands users on a
  /// real, useful page rather than a 404.
  ///
  /// Play Store: `details?id=<bundleId>` works pre-publish (Play
  /// returns "not available" for unpublished bundles, which is
  /// acceptable) so we use the bundle id directly.
  ///
  /// Override via env at build time:
  ///   --dart-define=APP_STORE_URL=https://apps.apple.com/app/...
  ///   --dart-define=PLAY_STORE_URL=https://play.google.com/store/apps/details?id=...
  String get url {
    const appStoreOverride =
        String.fromEnvironment('APP_STORE_URL', defaultValue: '');
    const playStoreOverride =
        String.fromEnvironment('PLAY_STORE_URL', defaultValue: '');
    return switch (this) {
      _Store.appStore => appStoreOverride.isNotEmpty
          ? appStoreOverride
          : 'https://apps.apple.com/search?term=GentleQuest',
      _Store.playStore => playStoreOverride.isNotEmpty
          ? playStoreOverride
          : 'https://play.google.com/store/apps/details?id=com.gentlequest.app',
    };
  }
}

class _StoreButton extends StatelessWidget {
  const _StoreButton({
    required this.label,
    required this.icon,
    required this.onTap,
    this.outlined = false,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;

  /// Outlined variant — primary tint on a soft surface, used for the
  /// secondary store buttons when the sign-in CTA is the dominant action.
  final bool outlined;

  @override
  Widget build(BuildContext context) {
    final bg = outlined ? GQColors.primarySoft : GQColors.primary;
    final fg = outlined ? GQColors.primary : Colors.white;
    return Material(
      color: bg,
      borderRadius: BorderRadius.circular(GQRadii.button),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(GQRadii.button),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 20, color: fg),
              const SizedBox(width: 10),
              Text(
                label,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                  color: fg,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
