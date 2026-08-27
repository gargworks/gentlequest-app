import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/screens/clinical_assessment_screen.dart';
import 'package:ai_buddy_web/screens/welcome_screen.dart';
import 'package:ai_buddy_web/screens/onboarding_vow_screen.dart';

import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'dart:async';
import 'package:sentry/sentry.dart' as sentry;
import 'package:provider/provider.dart';
import 'providers/chat_provider.dart';
import 'providers/mood_provider.dart';
import 'providers/assessment_provider.dart';
import 'providers/task_provider.dart';
import 'providers/progress_provider.dart';
import 'providers/companion_provider.dart';
import 'providers/survey_provider.dart';
import 'navigation/route_observer.dart';
import 'navigation/home_shell.dart';
import 'navigation/home_tab_deeplink.dart';
import 'widgets/app_bottom_nav.dart' show AppTab;
import 'services/notification_service.dart';
import 'services/notification_payload_router.dart';
import 'services/auth_service.dart';
import 'services/deep_link_service.dart';
import 'services/pref_migrator.dart';
import 'services/low_stim_service.dart';
import 'config/profile_config.dart';
import 'screens/legal/legal_screen.dart';
import 'theme/gq_theme.dart';
import 'theme/gq_tokens.dart';
import 'theme/low_stim_mode.dart';
import 'widgets/branded_splash.dart';
import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb, debugPrint;
import 'package:ai_buddy_web/services/firebase_service.dart';
import 'package:ai_buddy_web/services/app_rating_service.dart';
import 'package:upgrader/upgrader.dart';
import 'package:ai_buddy_web/screens/compliance_guard_screen.dart';
import 'package:ai_buddy_web/screens/age_verification_blocked_screen.dart';
import 'package:ai_buddy_web/services/compliance_service.dart';
import 'package:ai_buddy_web/services/play_age_signals_service.dart';
import 'package:ai_buddy_web/screens/debug/gq_component_gallery_screen.dart';

// Root navigator key to support global routing from notification taps
final GlobalKey<NavigatorState> rootNavigatorKey = GlobalKey<NavigatorState>();

// Deduplication window for deep-link payload handling
DateTime? _lastDeepLinkAt;
String? _lastDeepLinkPayload;

// Handle notification payloads centrally.
//
// Payloads arrive as `gq://<host>?source=...` from every scheduled
// notification, but the routing below matches bare tokens. Those two sets did
// not overlap at all until 2026-08-20, so tapping ANY scheduled notification
// did nothing. normalizeNotificationPayload bridges them; the mapping and its
// drift test live in services/notification_payload_router.dart.
void _handleNotificationPayload(String? rawPayload) {
  if (rawPayload == null) return;
  final payload = normalizeNotificationPayload(rawPayload);
  if (kDebugMode) {
    try {
      debugPrint('[DeepLink] payload received: $rawPayload -> $payload');
    } catch (_) {}
  }
  // Deduplicate identical payloads fired in quick succession (e.g., resume + tap)
  final now = DateTime.now();
  if (_lastDeepLinkPayload == payload && _lastDeepLinkAt != null) {
    final diffMs = now.difference(_lastDeepLinkAt!).inMilliseconds;
    if (diffMs < 2000) {
      if (kDebugMode) {
        try {
          debugPrint('[DeepLink] duplicate ignored (${diffMs}ms)');
        } catch (_) {}
      }
      return;
    }
  }
  _lastDeepLinkPayload = payload;
  _lastDeepLinkAt = now;
  // D5's 4-tab IA retired the standalone Quest and Mood tabs — both land on
  // Home now (Quest via a "quest" quick-lane surfaced there once it ships;
  // mood check-in is Home's "Today's one thing" zone). Keep the payload
  // names for backwards compatibility with already-scheduled notifications.
  if (payload == 'open_quest' || payload == 'open_today') {
    try {
      homeTabDeepLink.request(AppTab.home);
    } catch (_) {}

    final nav = rootNavigatorKey.currentState;
    if (nav == null) {
      // Try after first frame if navigator not ready yet
      WidgetsBinding.instance
          .addPostFrameCallback((_) => _handleNotificationPayload(payload));
      return;
    }
    nav.pushNamedAndRemoveUntil('/home', (route) => false,
        arguments: AppTab.home);
  }
  if (payload == 'open_mood') {
    try {
      homeTabDeepLink.request(AppTab.home);
    } catch (_) {}
    final nav = rootNavigatorKey.currentState;
    if (nav == null) {
      WidgetsBinding.instance
          .addPostFrameCallback((_) => _handleNotificationPayload(payload));
      return;
    }
    nav.pushNamedAndRemoveUntil('/home', (route) => false,
        arguments: AppTab.home);
  }
  if (payload == 'open_talk') {
    try {
      homeTabDeepLink.request(AppTab.talk);
    } catch (_) {}
    final nav = rootNavigatorKey.currentState;
    if (nav == null) {
      WidgetsBinding.instance
          .addPostFrameCallback((_) => _handleNotificationPayload(payload));
      return;
    }
    nav.pushNamedAndRemoveUntil('/home', (route) => false,
        arguments: AppTab.talk);
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase (handles analytics & crashlytics)
  // Wrapped in try-catch for resilience - app should still run if Firebase fails
  try {
    await FirebaseService().setFirebaseOptions();
    await FirebaseService().initialize();
  } catch (e) {
    debugPrint('Firebase initialization error: $e');
  }

  const dsn = String.fromEnvironment('SENTRY_DSN_FRONTEND', defaultValue: '');
  const env = String.fromEnvironment('SENTRY_ENV', defaultValue: 'local');
  const version = String.fromEnvironment('APP_VERSION', defaultValue: '1.0.0');
  const tracesStr = String.fromEnvironment(
    'SENTRY_TRACES_SAMPLE_RATE',
    defaultValue: '0',
  );
  final traces = double.tryParse(tracesStr) ?? 0.0;

  // Detect placeholder DSN — crash data is being silently lost if this fires.
  // Operator action: replace SENTRY_DSN_FRONTEND in .env with a real DSN
  // from sentry.io, then rebuild + redeploy.
  if (dsn.contains('placeholder') || dsn.contains('123456')) {
    debugPrint('[sentry] WARNING: DSN is a placeholder. Crashes are NOT being '
        'reported. Set SENTRY_DSN_FRONTEND to a real DSN in .env.');
  } else if (dsn.isNotEmpty) {
    try {
      await sentry.Sentry.init((options) {
        options.dsn = dsn;
        options.environment = env;
        options.release = version;
        options.tracesSampleRate = traces;
      });
    } catch (e) {
      debugPrint('Sentry initialization error: $e');
    }
  }

  // Set tap handler for notification deep-linking
  NotificationService.onSelectNotification = (payload) {
    _handleNotificationPayload(payload);
  };

  // Initialize app rating service (mobile only - no-op on web)
  // Wrapped in try-catch for resilience
  if (!kIsWeb) {
    try {
      await AppRatingService().incrementSessionCount();
    } catch (e) {
      debugPrint('AppRatingService initialization error: $e');
    }
  }

  // Hydrate cached auth identity from SharedPreferences before any UI
  // mounts so the Settings/Profile screens know who's signed in without
  // a network round-trip flicker.
  try {
    await AuthService.instance.hydrate();
  } catch (e) {
    debugPrint('AuthService hydrate error: $e');
  }

  // Migrate legacy onboarding pref keys onto canonical scheduler keys +
  // re-arm notification schedulers from persisted opt-in state. Without
  // this, users who toggled ON in a prior session can have a phantom
  // toggle (pref says enabled, no schedule actually pending). See
  // .brain/audits/2026-05-24_gq_v1.3.0_honesty_audit.md §1+§2.
  try {
    await PrefMigrator.run();
  } catch (e) {
    debugPrint('PrefMigrator error: $e');
  }

  // Hydrate ProfileConfig (nickname / pronoun / avatar / tone) from the
  // profile_*_v1 SharedPreferences keys. Previously these were written by
  // profile_screen but never read into the static globals chat reads, so
  // setting nickname/avatar/tone did nothing downstream. See audit §3–§6.
  try {
    await ProfileConfig.hydrateFromPrefs();
  } catch (e) {
    debugPrint('ProfileConfig hydrate error: $e');
  }

  // Initialize deep link handling (app links / universal links)
  try {
    await DeepLinkService().initialize();
  } catch (e) {
    debugPrint('DeepLinkService initialization error: $e');
  }

  // Hydrate low-stim "quiet mode" (v1.5.0 ADHD update, ADR-006) from
  // SharedPreferences before first paint so the app-wide filter in
  // LowStimOverlay is correct from frame one, not just after Settings loads.
  try {
    await LowStimService.hydrate();
  } catch (e) {
    debugPrint('LowStimService hydrate error: $e');
  }

  runApp(const MyApp());
}

/// WO-8 Part A — one ThemeData builder for both brightnesses, so light and
/// dark cannot drift apart in structure (only in the values that are meant to
/// differ). The GQ semantic palette rides in `extensions` rather than being
/// mapped onto ColorScheme slots — see [GQTheme] for why.
ThemeData _gqThemeData(Brightness brightness) {
  final gq = brightness == Brightness.dark ? GQTheme.dark : GQTheme.light;
  return ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: GQColors.primary,
      primary: GQColors.primary,
      secondary: GQColors.coral,
      brightness: brightness,
    ),
    useMaterial3: true,
    scaffoldBackgroundColor: gq.bg,
    extensions: <ThemeExtension<dynamic>>[gq],
    pageTransitionsTheme: const PageTransitionsTheme(
      builders: {
        TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
        TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
        // WO-8 Part C: Android was previously mapped to the Cupertino builder
        // too, giving it an iOS slide on every push. Restored to the Material
        // default so navigation feels native per-platform. This is visible to
        // existing Android users — an intended change, not a cleanup.
        TargetPlatform.android: ZoomPageTransitionsBuilder(),
      },
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ChatProvider()),
        ChangeNotifierProvider(create: (_) => MoodProvider()),
        ChangeNotifierProvider(create: (_) => AssessmentProvider()),
        ChangeNotifierProvider(create: (_) => TaskProvider()),
        ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ChangeNotifierProvider(create: (_) => CompanionProvider()),
        ChangeNotifierProvider(create: (_) => SurveyProvider()..load()),
      ],
      child: MaterialApp(
        title: 'GentleQuest',
        debugShowCheckedModeBanner: false,
        theme: _gqThemeData(Brightness.light),
        darkTheme: _gqThemeData(Brightness.dark),
        // WO-8: dark mode is PLUMBED but not yet ACTIVATED.
        //
        // The GQ widget layer still reads static GQColors constants rather
        // than Theme.of, so flipping this to ThemeMode.system today would
        // produce a half-dark app: themed surfaces going dark underneath
        // hardcoded near-white cards and near-black text. That is strictly
        // worse than staying light.
        //
        // This becomes ThemeMode.system in the same change that converts the
        // components — activation is a deliberate step, not a side effect of
        // landing the infrastructure.
        themeMode: ThemeMode.light,
        // Low-stim "quiet mode" (v1.5.0 ADHD update, ADR-006): wraps every
        // routed screen (this is MaterialApp's routing-content builder slot,
        // above Navigator) with a saturation/motion filter that reacts
        // instantly to LowStimService's notifier — see theme/low_stim_mode.dart.
        builder: (context, child) =>
            LowStimOverlay(child: child ?? const SizedBox.shrink()),
        navigatorKey: rootNavigatorKey,
        navigatorObservers: [routeObserver, AnalyticsRouteObserver()],
        // UpgradeAlert is for mobile app store version checks - skip on web
        home: kIsWeb
            ? const SplashScreen()
            : UpgradeAlert(
                upgrader: Upgrader(
                  minAppVersion: '1.0.0',
                  messages: UpgraderMessages(
                    code: 'en',
                  ),
                ),
                barrierDismissible: true,
                showIgnore: true,
                showLater: true,
                child: const SplashScreen(),
              ),
        routes: {
          '/home': (context) {
            final args = ModalRoute.of(context)?.settings.arguments;
            final initial = (args is AppTab) ? args : AppTab.home;
            return HomeShell(initialTab: initial);
          },
          // Legacy route name; HomeShell normalizes the retired Quest tab to Home.
          '/home/quest': (context) => HomeShell(initialTab: AppTab.quest),
          // Legacy landing route redirected to HomeShell Home tab
          '/main': (context) => const HomeShell(),
          '/interactive-chat': (context) => const InteractiveChatScreen(),
          '/privacy': (context) => const LegalScreen(
                title: 'Privacy Policy',
                assetPath: 'assets/legal/privacy.md',
              ),
          '/clinical-assessment': (context) => const ClinicalAssessmentScreen(),
          // Design Authority WO-4 acceptance criterion: debug-only component
          // gallery. Not linked from any in-app navigation — reach via
          // Navigator.pushNamed(context, '/debug/gq-gallery').
          '/debug/gq-gallery': (context) => const GQComponentGalleryScreen(),
        },
      ),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  bool _resolved = false;
  bool _showWelcome = false;
  // Onboarding Vow — shown once before the welcome screen for new users.
  bool _showVow = false;
  // v1.4.0 Phase C — terminal block when device returns verifiedUnder in a
  // region that requires a verified signal (Texas SB 2420 today).
  bool _ageBlocked = false;

  @override
  void initState() {
    super.initState();
    _checkWelcome();
  }

  Future<void> _checkWelcome() async {
    // v1.4.5: On web, the page load IS the splash — no artificial delay.
    // On mobile, keep 800ms for the branded splash to feel intentional.
    final splashDelay = kIsWeb
        ? const Duration(milliseconds: 200)
        : const Duration(milliseconds: 800);
    final results = await Future.wait<dynamic>([
      WelcomeScreen.hasBeenSeen(),
      OnboardingVowScreen.hasBeenSeen(),
      Future<void>.delayed(splashDelay),
    ]);
    if (!mounted) return;
    final seen = results[0] as bool;
    final vowSeen = results[1] as bool;

    // v1.4.0 Phase C — verified-signal gate. Only runs once welcome is past
    // and only in regions that require a verified signal (Phase B decides).
    // Wrapped in try/catch so a misbehaving Phase B implementation can never
    // brick boot; we fall through to the existing compliance flow on error.
    bool ageBlocked = false;
    if (seen) {
      try {
        final requiresVerified =
            await ComplianceService.requiresVerifiedSignal();
        if (requiresVerified) {
          final signal = await ComplianceService.fetchAndCacheAgeSignal();
          if (signal == AgeSignalStatus.verifiedUnder) {
            ageBlocked = true;
          }
        }
      } catch (e) {
        debugPrint('[SplashScreen] age-signal gate threw, falling through: $e');
      }
    }

    if (!mounted) return;
    setState(() {
      // Vow shows first for new users who haven't seen it AND haven't seen
      // the welcome screen yet. If welcome was already seen, the vow was
      // too (or the user upgraded — either way, don't re-show).
      _showVow = !vowSeen && !seen;
      _showWelcome = !seen;
      _ageBlocked = ageBlocked;
      _resolved = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_resolved) {
      return const BrandedSplash();
    }
    if (_ageBlocked) {
      return const AgeVerificationBlockedScreen();
    }
    // Onboarding Vow shows before the welcome screen for first-time users.
    if (_showVow) {
      return const OnboardingVowScreen();
    }
    return _showWelcome ? const WelcomeScreen() : const ComplianceGuardScreen();
  }
}
