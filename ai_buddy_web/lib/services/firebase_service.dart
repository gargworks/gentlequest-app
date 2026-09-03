import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/firebase_options.dart';
/// SharedPreferences key for the anonymity-mode flag. When true, all analytics
/// + crashlytics calls in [FirebaseService] become no-ops, and the currently
/// set Firebase user-id is cleared. Mirrored in [analytics_service.dart] so
/// the backend analytics endpoint is also suppressed.
const String kAnonymityModeKey = 'anonymity_mode_v1';

late final FirebaseOptions firebaseOptions;

/// The narrow slice of analytics a test needs to observe.
///
/// Added 2026-09-03. `FirebaseService` is a process-wide singleton reached as
/// `FirebaseService().logEvent(...)` from 64 call sites, and `logEvent`
/// early-returns when `!_initialized` — which is always true under
/// `flutter test`, because Firebase never boots there. The consequence was
/// that NO test could observe whether an analytics event actually fired, so
/// the analytics tests were logic mirrors plus source greps, and a regression
/// in the real code path could pass them.
///
/// Deliberately narrow: only `logEvent`. Every richer wrapper on
/// FirebaseService (logMoodEntry, logChatMessage, logExerciseCompleted,
/// logCrisisResourceAccess) funnels through `logEvent` with the real GA4 event
/// name, so observing that one method observes all of them — and observes them
/// under the name GA4 actually receives, which is the name that matters.
abstract interface class AnalyticsSink {
  Future<void> logEvent(String name, [Map<String, dynamic>? parameters]);
}

class FirebaseService implements AnalyticsSink {
  static final FirebaseService _instance = FirebaseService._internal();
  factory FirebaseService() => _instance;
  FirebaseService._internal();

  /// Test-only: when set, `logEvent` delegates here instead of Firebase.
  ///
  /// Tests MUST null this in tearDown — it is static, so a leak would make one
  /// test's sink observe another test's events.
  @visibleForTesting
  static AnalyticsSink? sinkOverride;

  late FirebaseAnalytics _analytics;
  FirebaseCrashlytics? _crashlytics; // Nullable - not available on web
  bool _initialized = false;

  /// In-memory cache of the anonymity-mode flag. Hydrated from
  /// SharedPreferences at [initialize], updated via [setAnonymityMode].
  /// When true: every event/screen-view/user-id/property setter is a no-op.
  bool _anonymityOn = false;

  FirebaseAnalytics get analytics => _analytics;

  /// True if anonymity mode is currently active (analytics suspended).
  bool get isAnonymityOn => _anonymityOn;

  /// Toggle anonymity mode. Persists to SharedPreferences and, when turning
  /// ON, clears the currently-set Firebase user-id so no further events can
  /// be back-tied to the prior anonymous-but-stable user-id. Settings UI
  /// must call this whenever the user flips the Anonymity toggle.
  Future<void> setAnonymityMode(bool value) async {
    _anonymityOn = value;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(kAnonymityModeKey, value);
    } catch (e) {
      debugPrint('[firebase] persist anonymity flag failed: $e');
    }
    if (value && _initialized) {
      try {
        await _analytics.setUserId(id: null);
      } catch (e) {
        debugPrint('[firebase] clear userId on anonymity-on failed: $e');
      }
    }
    // SDK-level collection switch, not just the wrapper gate. The wrapper's
    // early-return only suppresses events WE log; once a GA4 property is
    // linked (2026-08-27), the SDK also emits AUTOMATIC events
    // (first_open, session_start, user_engagement) that never pass through
    // logEvent(). The shipped privacy policy promises analytics is
    // "suppressed entirely" under Anonymity Mode, so the collection switch
    // itself must follow the toggle or the promise silently breaks.
    if (_initialized) {
      try {
        await _analytics.setAnalyticsCollectionEnabled(!value);
      } catch (e) {
        debugPrint('[firebase] setAnalyticsCollectionEnabled failed: $e');
      }
    }
  }

  Future<void> _loadAnonymityMode() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _anonymityOn = prefs.getBool(kAnonymityModeKey) ?? false;
    } catch (_) {
      _anonymityOn = false;
    }
  }

  Future<void> setFirebaseOptions() async {
    firebaseOptions = DefaultFirebaseOptions.currentPlatform;
  }

  Future<void> initialize() async {
    if (_initialized) return;

    try {
      // Ultra-Defensive Initialization logic to prevent SIGABRT on iOS/Android
      // 1. Check if Dart already knows about an app
      if (Firebase.apps.isEmpty) {
        if (kIsWeb) {
          await Firebase.initializeApp(options: firebaseOptions);
          debugPrint('Firebase initialized successfully (Web)');
        } else {
          try {
            // 2. Attempt automatic no-options init (uses GoogleService-Info.plist or google-services.json)
            // This is the most stable method for mobile apps with bundled config files.
            await Firebase.initializeApp();
            debugPrint('Firebase initialized successfully (Mobile-Auto)');
          } catch (e) {
            debugPrint(
                'Automatic Firebase initialization skipped or failed: $e');
            // 3. Fallback to manual options if no config file is found or it fails
            try {
              await Firebase.initializeApp(options: firebaseOptions);
              debugPrint('Firebase initialized successfully (Mobile-Manual)');
            } catch (innerE) {
              if (innerE.toString().contains('duplicate-app') ||
                  innerE.toString().contains('already exists')) {
                debugPrint('Firebase already initialized (Mobile-Inner-Catch)');
              } else {
                rethrow;
              }
            }
          }
        }
      } else {
        debugPrint('Firebase already initialized (Detected via apps list)');
      }
    } catch (e) {
      // 4. Ultimate safety: If we still get a "duplicate-app" error, ignore it.
      if (e.toString().contains('duplicate-app') ||
          e.toString().contains('already exists')) {
        debugPrint('Firebase already initialized (Detected via final catch)');
      } else {
        debugPrint('Fallback: Firebase initialization reported: $e');
      }
    }

    try {
      _analytics = FirebaseAnalytics.instance;

      // FirebaseCrashlytics is NOT supported on web - only initialize on mobile
      if (!kIsWeb) {
        _crashlytics = FirebaseCrashlytics.instance;

        // Configure Crashlytics (mobile only)
        await _crashlytics!.setCrashlyticsCollectionEnabled(!kDebugMode);

        // Set up Flutter error handling (mobile only)
        FlutterError.onError = _crashlytics!.recordFlutterFatalError;

        // Set up async error handling (mobile only)
        PlatformDispatcher.instance.onError = (error, stack) {
          _crashlytics!.recordError(error, stack, fatal: true);
          return true;
        };
      }

      _initialized = true;

      // Hydrate anonymity flag BEFORE logging app_open so the gate respects
      // the user's prior choice on cold boot. setUserId on the next event is
      // also gated by this flag (no userId leak post-anonymity-on).
      await _loadAnonymityMode();

      // Align the SDK's own collection switch with the hydrated anonymity
      // choice on every cold boot. Without this, a user who enabled
      // Anonymity Mode would still emit the SDK's AUTOMATIC events
      // (first_open, session_start) — the wrapper gate below never sees
      // those. Enabled-by-default for everyone else, matching the shipped
      // opt-out privacy model.
      try {
        await _analytics.setAnalyticsCollectionEnabled(!_anonymityOn);
      } catch (e) {
        debugPrint('[firebase] setAnalyticsCollectionEnabled at init failed: $e');
      }

      // Log app open
      await logEvent('app_open');
    } catch (e) {
      debugPrint('Firebase instance registration failed: $e');
      // We don't rethrow to ensure app boots even if analytics has issues
    }
  }

  // Analytics Events
  @override
  Future<void> logEvent(String name, [Map<String, dynamic>? parameters]) async {
    // Order here is load-bearing, and it is NOT the order the seam was
    // originally scoped with.
    //
    // Anonymity is checked FIRST, before the test seam. Anonymity mode is a
    // privacy promise to the user, not a delivery detail: when it is on,
    // nothing observes events — not Firebase, and not a sink. Putting the
    // override above this check would have meant an override could see events
    // the user asked nobody to see, and would have made "anonymity suppresses
    // analytics" untestable through the seam meant to test analytics.
    //
    // The _initialized check stays BELOW the seam, because that flag is the
    // only reason tests cannot observe anything: it is false under
    // `flutter test` and there is no safe way to force it true (the real
    // `_analytics` field is `late` and would throw).
    if (_anonymityOn) return;

    final sink = sinkOverride;
    if (sink != null) {
      await sink.logEvent(name, parameters);
      return;
    }

    if (!_initialized) return;

    try {
      Map<String, Object>? typedParams;
      if (parameters != null) {
        final map = <String, Object>{};
        parameters.forEach((key, value) {
          if (value != null) {
            map[key] = value as Object;
          }
        });
        if (map.isNotEmpty) {
          typedParams = map;
        }
      }

      await _analytics.logEvent(
        name: name,
        parameters: typedParams,
      );
    } catch (e) {
      debugPrint('[firebase] logEvent($name) failed: $e');
    }
  }

  Future<void> logScreenView(String screenName) async {
    if (!_initialized || _anonymityOn) return;
    try {
      await _analytics.logScreenView(
        screenName: screenName,
        screenClass: screenName,
      );
    } catch (e) {
      debugPrint('[firebase] logScreenView failed: $e');
    }
  }

  Future<void> setUserId(String? userId) async {
    if (!_initialized || _anonymityOn) return;
    try {
      await _analytics.setUserId(id: userId);
    } catch (e) {
      debugPrint('[firebase] setUserId failed: $e');
    }
  }

  Future<void> setUserProperty(String name, String? value) async {
    if (!_initialized || _anonymityOn) return;
    try {
      await _analytics.setUserProperty(name: name, value: value);
    } catch (e) {
      debugPrint('[firebase] setUserProperty failed: $e');
    }
  }

  // Crashlytics (mobile only - no-op on web)
  Future<void> recordError(
    dynamic exception,
    StackTrace? stack, {
    bool fatal = false,
  }) async {
    if (!_initialized || _crashlytics == null) return;
    try {
      await _crashlytics!.recordError(exception, stack, fatal: fatal);
    } catch (e) {
      debugPrint('[firebase] recordError failed: $e');
    }
  }

  Future<void> log(String message) async {
    if (!_initialized || _crashlytics == null) return;
    try {
      _crashlytics!.log(message);
    } catch (e) {
      debugPrint('[firebase] log failed: $e');
    }
  }

  Future<void> setCustomKey(String key, dynamic value) async {
    if (!_initialized || _crashlytics == null) return;
    try {
      _crashlytics!.setCustomKey(key, value);
    } catch (e) {
      debugPrint('[firebase] setCustomKey failed: $e');
    }
  }

  // Common events for mental health app
  Future<void> logMoodEntry(String mood, int score) async {
    await logEvent('mood_tracked', {
      'mood_type': mood,
      'mood_score': score,
    });
  }

  Future<void> logChatMessage(String messageType) async {
    await logEvent('chat_message', {
      'message_type': messageType,
    });
  }

  Future<void> logCrisisResourceAccess() async {
    await logEvent('crisis_resource_accessed');
  }

  Future<void> logExerciseCompleted(String exerciseType) async {
    await logEvent('exercise_completed', {
      'exercise_type': exerciseType,
    });
  }
}
