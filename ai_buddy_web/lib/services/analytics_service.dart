import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:math' as math;

import '../config/api_config.dart';
import 'firebase_service.dart' show kAnonymityModeKey;
import 'session_manager.dart';

const String _analyticsConsentKey = 'analytics_consent';

final Dio _dio = Dio(
  BaseOptions(
    baseUrl: ApiConfig.baseUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
    sendTimeout: const Duration(seconds: 30),
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  ),
);

String _newRequestId() {
  final ts = DateTime.now().microsecondsSinceEpoch;
  final rnd = math.Random().nextInt(0x7fffffff);
  return 'req-$ts-$rnd';
}

Future<bool> _isAnalyticsEnabled() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    // Anonymity mode wins over consent: when on, every analytics event is
    // suppressed regardless of prior consent state. Matches the FirebaseService
    // gate at logEvent/logScreenView so both surfaces (Firebase + backend
    // /api/analytics/log) honor the same single source of truth.
    if (prefs.getBool(kAnonymityModeKey) ?? false) return false;
    return prefs.getBool(_analyticsConsentKey) ?? false;
  } catch (_) {
    return false;
  }
}

Future<void> logAnalyticsEvent(String eventType,
    {Map<String, dynamic>? metadata}) async {
  try {
    if (!(await _isAnalyticsEnabled())) return;
    // Centralized session ID (deduplicated) via SessionManager
    final sid = await SessionManager.getOrCreateSessionId();
    await _dio.post(
      '/api/analytics/log',
      data: {
        'event_type': eventType,
        if (metadata != null) 'metadata': metadata,
      },
      options: Options(headers: {
        'X-Session-ID': sid,
        'X-Analytics-Consent': 'true',
        'X-Request-ID': _newRequestId(),
      }),
    );
  } catch (e) {
    // Swallow errors silently for analytics
    if (kDebugMode) debugPrint('analytics: log error: $e');
  }
}

/// Submit in-app user feedback (star rating + optional free text) to the
/// backend /api/feedback endpoint.
///
/// Gated on ANONYMITY MODE ONLY — not analytics consent. Feedback is an
/// explicit user act (the user typed text and pressed submit), which is its
/// own consent to transmit that content. A user who declined passive
/// telemetry but explicitly submits feedback should still have it sent.
/// The anonymity-mode promise stays absolute: anonymity ON = never transmit.
///
/// Returns [true] if the POST was sent (regardless of server response code),
/// [false] if suppressed by anonymity mode or network error. The UI uses
/// this to show an honest SnackBar ("Thank you!" vs "Saved on your device").
Future<bool> submitFeedback({
  required int rating,
  String? text,
  String trigger = 'after_3rd_checkin',
}) async {
  try {
    // Anonymity-mode-only gate: anonymity ON = never transmit (absolute promise).
    // Analytics consent is NOT checked here — feedback is explicit user act.
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool(kAnonymityModeKey) ?? false) return false;

    final sid = await SessionManager.getOrCreateSessionId();
    await _dio.post(
      '/api/feedback',
      data: {
        'rating': rating,
        'trigger': trigger,
        if (text != null && text.trim().isNotEmpty) 'text': text.trim(),
      },
      options: Options(headers: {
        'X-Session-ID': sid,
        'X-Request-ID': _newRequestId(),
      }),
    );
    return true;
  } catch (e) {
    if (kDebugMode) debugPrint('analytics: feedback submit error: $e');
    return false;
  }
}
