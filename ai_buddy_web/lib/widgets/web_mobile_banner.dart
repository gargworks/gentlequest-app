import 'package:flutter/foundation.dart' show kIsWeb, visibleForTesting;
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../theme/gq_theme.dart';

/// Non-blocking dismissible banner shown at the top of the chat screen on
/// web only. Replaces the old blocking [WebMobilePromoSheet] modal popup.
///
/// Shows a subtle info banner: "GentleQuest is also available as a mobile
/// app" + "Get the app" link + dismiss X button. The user can ignore it
/// and chat normally — it does not block interaction.
///
/// Dismiss state is persisted to SharedPreferences (key:
/// `web_mobile_banner_dismissed_v1`) so it doesn't reappear after dismissal.
class WebMobileBanner extends StatefulWidget {
  const WebMobileBanner({
    super.key,
    @visibleForTesting this.isWebOverride,
  });

  /// When non-null, overrides the `kIsWeb` platform check (testing only).
  /// When null (production), the banner uses `kIsWeb` at build time.
  @visibleForTesting
  final bool? isWebOverride;

  static const String prefsKey = 'web_mobile_banner_dismissed_v1';

  /// Store URL for the mobile app. Override via build-time env:
  ///   --dart-define=APP_STORE_URL=https://apps.apple.com/app/...
  ///   --dart-define=PLAY_STORE_URL=https://play.google.com/store/apps/details?id=...
  static const String _appStoreUrl =
      String.fromEnvironment('APP_STORE_URL', defaultValue: '');
  static const String _playStoreUrl =
      String.fromEnvironment('PLAY_STORE_URL', defaultValue: '');

  static String get storeUrl {
    if (_playStoreUrl.isNotEmpty) return _playStoreUrl;
    if (_appStoreUrl.isNotEmpty) return _appStoreUrl;
    return 'https://play.google.com/store/apps/details?id=com.gentlequest.app';
  }

  @override
  State<WebMobileBanner> createState() => _WebMobileBannerState();
}

class _WebMobileBannerState extends State<WebMobileBanner> {
  bool _visible = true;

  @override
  void initState() {
    super.initState();
    _loadDismissState();
  }

  Future<void> _loadDismissState() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    final dismissed = prefs.getBool(WebMobileBanner.prefsKey) ?? false;
    if (dismissed) {
      setState(() => _visible = false);
    }
  }

  Future<void> _dismiss() async {
    setState(() => _visible = false);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(WebMobileBanner.prefsKey, true);
  }

  Future<void> _openStore() async {
    final uri = Uri.parse(WebMobileBanner.storeUrl);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    } catch (_) {
      // Silent — user can still see the link text.
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final isWeb = widget.isWebOverride ?? kIsWeb;
    if (!isWeb || !_visible) {
      return const SizedBox.shrink();
    }
    return Semantics(
      label:
          'GentleQuest is also available as a mobile app. Get the app or dismiss.',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: t.accentSoft,
          border: Border(
            bottom: BorderSide(color: t.hair),
          ),
        ),
        child: Row(
          children: [
            Icon(
              Icons.phone_iphone,
              size: 18,
              color: t.coral,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text.rich(
                TextSpan(
                  style: TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                    color: t.ink2,
                    height: 1.35,
                  ),
                  children: [
                    const TextSpan(
                        text:
                            'GentleQuest is also available as a mobile app. '),
                    WidgetSpan(
                      child: GestureDetector(
                        key: const Key('web_mobile_banner_get_app'),
                        onTap: _openStore,
                        child: Text(
                          'Get the app',
                          style: TextStyle(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w800,
                            color: t.primary,
                            decoration: TextDecoration.underline,
                            decorationColor: t.primary,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              key: const Key('web_mobile_banner_dismiss'),
              behavior: HitTestBehavior.opaque,
              onTap: _dismiss,
              child: Padding(
                padding: const EdgeInsets.all(4),
                child: Icon(
                  Icons.close,
                  size: 16,
                  color: t.ink3,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
