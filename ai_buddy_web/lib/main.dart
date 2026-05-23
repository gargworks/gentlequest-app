import 'package:ai_buddy_web/screens/dhiwise_chat_screen.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/screens/quest_preview_screen.dart';
import 'package:ai_buddy_web/screens/clinical_assessment_screen.dart';
import 'package:ai_buddy_web/screens/welcome_screen.dart';
import 'package:ai_buddy_web/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart'
    as dhiwise_wellness;
import 'dhiwise/core/utils/size_utils.dart' as dhiwise_sizer;
import 'package:ai_buddy_web/dhiwise/presentation/quest_screen/quest_screen.dart'
    as dhiwise_quest;

import 'package:flutter/material.dart';
import 'dart:async';
import 'package:sentry/sentry.dart' as sentry;
import 'package:provider/provider.dart';
import 'providers/chat_provider.dart';
import 'providers/mood_provider.dart';
import 'providers/assessment_provider.dart';
import 'providers/task_provider.dart';
import 'providers/progress_provider.dart';
import 'providers/quest_provider.dart';
import 'providers/community_provider.dart';
import 'navigation/route_observer.dart';
import 'navigation/home_shell.dart';
import 'navigation/home_tab_deeplink.dart';
import 'widgets/app_bottom_nav.dart' show AppTab;
import 'services/notification_service.dart';
import 'services/auth_service.dart';
import 'services/deep_link_service.dart';
import 'screens/legal/legal_screen.dart';
import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb, debugPrint;
import 'package:ai_buddy_web/services/firebase_service.dart';
import 'package:ai_buddy_web/services/app_rating_service.dart';
import 'package:upgrader/upgrader.dart';
import 'package:ai_buddy_web/screens/compliance_guard_screen.dart';

// Root navigator key to support global routing from notification taps
final GlobalKey<NavigatorState> rootNavigatorKey = GlobalKey<NavigatorState>();

// Deduplication window for deep-link payload handling
DateTime? _lastDeepLinkAt;
String? _lastDeepLinkPayload;

// Handle notification payloads centrally
void _handleNotificationPayload(String? payload) {
  if (payload == null) return;
  if (kDebugMode) {
    try {
      debugPrint('[DeepLink] payload received: $payload');
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
  // Route to Explore/Quest tab. Keep backwards compatibility for 'open_today'.
  if (payload == 'open_quest' || payload == 'open_today') {
    // Immediately signal HomeShell to switch to Quest tab if it's mounted
    try {
      homeTabDeepLink.request(AppTab.quest);
    } catch (_) {}

    final nav = rootNavigatorKey.currentState;
    if (nav == null) {
      // Try after first frame if navigator not ready yet
      WidgetsBinding.instance
          .addPostFrameCallback((_) => _handleNotificationPayload(payload));
      return;
    }
    // Ensure a HomeShell is the root and open with Quest tab
    nav.pushNamedAndRemoveUntil('/home', (route) => false,
        arguments: AppTab.quest);
  }
  if (payload == 'open_mood') {
    try {
      homeTabDeepLink.request(AppTab.mood);
    } catch (_) {}
    final nav = rootNavigatorKey.currentState;
    if (nav == null) {
      WidgetsBinding.instance
          .addPostFrameCallback((_) => _handleNotificationPayload(payload));
      return;
    }
    nav.pushNamedAndRemoveUntil('/home', (route) => false,
        arguments: AppTab.mood);
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

  if (dsn.isNotEmpty) {
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

  // Initialize deep link handling (app links / universal links)
  try {
    await DeepLinkService().initialize();
  } catch (e) {
    debugPrint('DeepLinkService initialization error: $e');
  }

  runApp(const MyApp());
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
        ChangeNotifierProvider(create: (_) => QuestProvider()..loadQuests()),
        ChangeNotifierProvider(create: (_) => CommunityProvider()),
      ],
      child: MaterialApp(
        title: 'Progress Without Pressure',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF667EEA),
            primary: const Color(0xFF667EEA),
            secondary: const Color(0xFFFF6B6B),
          ),
          useMaterial3: true,
          pageTransitionsTheme: const PageTransitionsTheme(
            builders: {
              TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
              TargetPlatform.android: CupertinoPageTransitionsBuilder(),
              TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
            },
          ),
        ),
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
            final initial = (args is AppTab) ? args : AppTab.talk;
            return HomeShell(initialTab: initial);
          },
          '/home/quest': (context) => HomeShell(initialTab: AppTab.quest),
          // Legacy landing route redirected to HomeShell Talk tab
          '/main': (context) => HomeShell(initialTab: AppTab.talk),
          '/dhiwise-chat': (context) => const MentalHealthChatScreen(),
          '/preview-quest': (context) => const QuestPreviewScreen(),
          '/interactive-chat': (context) => const InteractiveChatScreen(),
          '/privacy': (context) => const LegalScreen(
                title: 'Privacy Policy',
                assetPath: 'assets/legal/privacy.md',
              ),
          // New direct routes for clarity
          '/wellness-dashboard': (context) => dhiwise_sizer.Sizer(
                builder: (context, orientation, deviceType) =>
                    dhiwise_wellness.WellnessDashboardScreen(),
              ),
          '/quests-list': (context) => const dhiwise_quest.QuestScreen(),
          '/clinical-assessment': (context) => const ClinicalAssessmentScreen(),
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

  @override
  void initState() {
    super.initState();
    _checkWelcome();
  }

  Future<void> _checkWelcome() async {
    final seen = await WelcomeScreen.hasBeenSeen();
    if (!mounted) return;
    setState(() {
      _showWelcome = !seen;
      _resolved = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_resolved) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return _showWelcome ? const WelcomeScreen() : const ComplianceGuardScreen();
  }
}
