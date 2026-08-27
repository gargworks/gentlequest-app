import 'package:app_links/app_links.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import '../routes/app_routes.dart';
import 'auth_service.dart';
import 'firebase_service.dart';

class DeepLinkService {
  static final DeepLinkService _instance = DeepLinkService._internal();
  factory DeepLinkService() => _instance;
  DeepLinkService._internal();

  // Mobile uses the app_links plugin for `gentlequest://` custom-scheme
  // intents. Web parses `Uri.base` instead (window.location) because
  // app_links has no cold-start hook for the browser surface — the
  // magic-link land at `https://gentlequest.app/auth/verify?token=...`
  // via the backend's smart-redirect (`/auth/redirect` UA-sniff route).
  AppLinks? _appLinks;

  /// In-flight + already-consumed auth tokens. Magic-link clicks on cold-
  /// start fire both `getInitialLink()` AND `uriLinkStream`, so without
  /// de-dup the same token is verified twice — the second verify hits the
  /// backend's single-use guard and surfaces a scary "Sign-in failed"
  /// SnackBar right after the success one.
  final Set<String> _consumedTokens = {};

  Future<void> initialize() async {
    if (kIsWeb) {
      // Web cold-start: there is no app_links uriLinkStream on the
      // browser surface; the URL the user landed on is the only signal.
      // `Uri.base` resolves to `window.location` without pulling in
      // dart:html (which would break non-web builds).
      _handleWebColdStart();
      return;
    }

    _appLinks = AppLinks();

    // Handle initial link if app was launched from a deep link
    final initialLink = await _appLinks!.getInitialLink();
    if (initialLink != null) {
      _handleDeepLink(initialLink.toString());
    }

    // Listen for links when app is already running
    _appLinks!.uriLinkStream.listen((uri) {
      _handleDeepLink(uri.toString());
    });
  }

  /// Cold-start URL parse for the Flutter web build.
  ///
  /// The backend's `/auth/redirect` router lands desktop users on
  /// `https://gentlequest.app/auth/verify?token=<raw>`. We sniff for
  /// that path here and fire the same `verifyToken` call the mobile
  /// path uses, then strip the token from the visible URL so a
  /// browser back/refresh doesn't replay the (now-burned) single-use
  /// claim and surface a "Sign-in failed" SnackBar.
  void _handleWebColdStart() {
    try {
      final uri = Uri.base;
      final token = uri.queryParameters['token'];
      // Accept any path on the web origin that carries `?token=...`
      // (the smart-redirect always lands on `/auth/verify`, but a
      // few mail clients rewrite paths — be permissive).
      final isAuthPath = uri.path == '/auth/verify' ||
          uri.path.endsWith('/auth/verify') ||
          uri.path == '/auth-verify' ||
          uri.path.endsWith('/auth-verify');
      if (token == null || token.isEmpty || !isAuthPath) {
        return;
      }
      FirebaseService().logEvent('deep_link_opened', {
        // Strip query parameters before logging to avoid capturing auth tokens
        // in Firebase Analytics. Auth tokens appear in ?token= param on this path.
        'url': uri.replace(queryParameters: {}).toString(),
        'surface': 'web',
      });
      _handleAuthVerify(token);
      // Best-effort URL cleanup: replace the current history entry
      // with a tokenless URL so refresh/back doesn't re-verify.
      // We use Uri manipulation only — no dart:html import — and
      // skip the rewrite if `window.history` isn't reachable.
      _scrubTokenFromUrl(uri);
    } catch (e) {
      debugPrint('Web cold-start auth parse failed: $e');
    }
  }

  void _scrubTokenFromUrl(Uri original) {
    // Intentionally a soft no-op for now: rewriting window.history from
    // Dart requires either dart:html (breaks mobile build) or the
    // package:web shim (new pubspec dep — explicitly forbidden by the
    // ownership scope). The token is single-use server-side, so a
    // refresh just shows the "Sign-in failed" SnackBar once. Acceptable.
    // If we later add package:web for other reasons, hook the rewrite
    // here. Reference URL we'd write:
    //   original.replace(queryParameters: {}).toString()
  }

  void _handleDeepLink(String link) {
    debugPrint('Deep link received: $link');
    // Strip query parameters before logging — same fix the web cold-start
    // path already carries above. Auth magic links arrive on THIS path too
    // (gentlequest://auth/verify?token=...), and logging the raw link put
    // the auth token into Firebase Analytics (PRIVACY_DISCLOSURE_AUDIT H2,
    // fixed for web 2026-07, native path missed until 2026-08-27).
    final uriForLog = Uri.tryParse(link);
    FirebaseService().logEvent('deep_link_opened', {
      'url': uriForLog?.replace(queryParameters: {}).toString() ?? 'unparseable',
    });

    final uri = Uri.parse(link);
    final path = uri.path;
    final queryParams = uri.queryParameters;

    // Auth magic-link: gentlequest://auth/verify?token=<raw>
    // Host parsing varies — some platforms put 'auth' in host, others
    // in the leading path segment — accept both shapes.
    final host = uri.host;
    if ((host == 'auth' && path == '/verify') ||
        path == '/auth/verify') {
      final token = queryParams['token'];
      if (token != null && token.isNotEmpty) {
        _handleAuthVerify(token);
      }
      return;
    }

    // Route to appropriate screen based on path
    switch (path) {
      case '/chat':
        _navigateTo(AppRoutes.interactiveChat, queryParams);
        break;
      case '/mood':
        _navigateTo(AppRoutes.moodTracker, queryParams);
        break;
      case '/quest':
        _navigateTo(AppRoutes.questScreen, queryParams);
        break;
      case '/wellness':
        // '/wellness-dashboard' is not a registered route (Phase 3 dead-code
        // sweep archived the dhiwise wellness dashboard). Normalize to home,
        // same as the '/quest' case above.
        _navigateTo(AppRoutes.home, queryParams);
        break;
      case '/crisis':
        // AppRoutes.crisisResources ('/crisis') is not registered in
        // main.dart's routes table and there is no onUnknownRoute handler —
        // navigating there would crash. Normalize to home until a real
        // crisis deep-link destination exists; which screen that should be
        // is a clinical routing decision, not a code one — tracked in repo
        // issues.
        _navigateTo(AppRoutes.home, queryParams);
        break;
      case '/assessment':
        if (queryParams.containsKey('id')) {
          _navigateTo(AppRoutes.assessment, queryParams);
        }
        break;
      case '/share':
        // Handle shared content
        _handleSharedContent(queryParams);
        break;
      default:
        // Default to home
        _navigateTo(AppRoutes.home, queryParams);
    }
  }

  void _navigateTo(String route, Map<String, String> params) {
    // Get the current context from your navigation key
    final context = AppRoutes.navigatorKey.currentContext;
    if (context != null) {
      Navigator.of(context).pushNamed(route, arguments: params);
    }
  }

  Future<void> _handleAuthVerify(String rawToken) async {
    // Cold-start fires getInitialLink + uriLinkStream for the same URL;
    // single-use tokens fail on the second verify. Skip if already
    // consumed this session.
    if (_consumedTokens.contains(rawToken)) return;
    _consumedTokens.add(rawToken);
    final context = AppRoutes.navigatorKey.currentContext;
    try {
      final identity = await AuthService.instance.verifyToken(rawToken);
      FirebaseService().logEvent('auth_magic_link_verified', {
        // Do NOT log user_id — it is a persistent identifier that would
        // contradict our "no personal data" privacy claim. Log success only.
        'auth_success': true,
      });
      if (context != null && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Signed in as ${identity.email}'),
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } on AuthException catch (e) {
      FirebaseService().logEvent('auth_magic_link_verify_failed', {
        'reason': e.message,
      });
      if (context != null && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Sign-in failed · ${e.message}'),
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    } catch (_) {
      // Network failure / non-auth error — silent. User can retry from
      // Settings → Sign in.
    }
  }

  void _handleSharedContent(Map<String, String> params) {
    // Handle content shared to the app
    final type = params['type'];
    final content = params['content'];

    if (type == 'mood' && content != null) {
      // Navigate to mood tracker with pre-filled mood
      _navigateTo(AppRoutes.moodTracker, {'preset': content});
    } else if (type == 'crisis') {
      // Same unregistered-route crash risk as the '/crisis' deep-link case
      // above — normalize to home; tracked in repo issues.
      _navigateTo(AppRoutes.home, {});
    }

    FirebaseService().logEvent('content_shared', {
      'type': type ?? 'unknown',
      'has_content': content != null,
    });
  }

  // Generate shareable links
  static String generateShareLink(String path, [Map<String, String>? params]) {
    const baseUrl = 'https://gentlequest.app';
    final uri = Uri.parse('$baseUrl$path');

    if (params != null && params.isNotEmpty) {
      return uri.replace(queryParameters: params).toString();
    }

    return uri.toString();
  }
}
