import 'dart:async';
import 'dart:math' as math;
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../config/api_config.dart';
import 'storage/kv_storage.dart';

/// Centralized session ID coordinator to deduplicate network calls to
/// `/api/get_or_create_session` across services.
class SessionManager {
  static const String _sessionKey = 'session_id';
  static String? _sessionId;
  static Completer<String>? _inflight;

  /// Returns an in-memory session id if present, else loads from secure storage,
  /// else performs a single, deduplicated network call to create one.
  static Future<String> getOrCreateSessionId() async {
    // Fast path: in-memory
    if (_sessionId != null && _sessionId!.trim().isNotEmpty) return _sessionId!;

    // Try persisted storage
    try {
      final existing = await KvStorage.read(_sessionKey);
      if (existing != null && existing.trim().isNotEmpty) {
        _sessionId = existing;
        return _sessionId!;
      }
    } catch (e) {
      if (kDebugMode) debugPrint('SessionManager: storage read error: $e');
    }

    // If another caller is already creating a session, await it
    if (_inflight != null) {
      return _inflight!.future;
    }

    // Create once and share
    _inflight = Completer<String>();
    try {
      final dio = Dio(
        BaseOptions(
          baseUrl: ApiConfig.baseUrl,
          connectTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 30),
          sendTimeout: const Duration(seconds: 30),
          headers: const {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        ),
      );
      final resp = await dio.get('/api/get_or_create_session');
      final sid =
          (resp.data is Map) ? resp.data['session_id'] as String? : null;
      _sessionId =
          (sid != null && sid.trim().isNotEmpty) ? sid : _fallbackSessionId();
      try {
        await KvStorage.write(_sessionKey, _sessionId);
      } catch (e) {
        if (kDebugMode) debugPrint('SessionManager: storage write error: $e');
      }
      _inflight!.complete(_sessionId!);
    } catch (e) {
      if (kDebugMode) debugPrint('SessionManager: network error: $e');
      _sessionId = _fallbackSessionId();
      _inflight!.complete(_sessionId!);
    } finally {
      _inflight = null;
    }
    return _sessionId!;
  }

  /// Returns the current in-memory session id if already loaded.
  static String? peekSessionId() => _sessionId;

  /// Clears the cached session id (both memory and storage).
  static Future<void> clear() async {
    _sessionId = null;
    _inflight = null;
    try {
      await KvStorage.delete(_sessionKey);
    } catch (e) {
      if (kDebugMode) debugPrint('SessionManager: clear error: $e');
    }
  }

  /// Generate a fresh anonymous session id and adopt it. Called on sign-out
  /// so the device stops carrying the previous user's canonical session
  /// (which was bound to their server-side data). Without this, anonymous
  /// use post-sign-out — or a different user signing in on the same device
  /// — would briefly hit the previous user's rows.
  ///
  /// Generates locally via UUID-v4-ish syntax and persists immediately;
  /// the next API call will get a fresh server row on /api/get_or_create_session
  /// at the X-Session-ID provided.
  static Future<void> regenerateAnonymousSessionId() async {
    final fresh = _localUuidV4();
    _sessionId = fresh;
    _inflight = null;
    try {
      await KvStorage.write(_sessionKey, fresh);
    } catch (e) {
      if (kDebugMode) {
        debugPrint('SessionManager: regenerate write error: $e');
      }
    }
  }

  /// Pseudo-UUIDv4 without pulling in a uuid package — good enough as a
  /// device-local opaque identifier. Backend treats X-Session-ID as an
  /// opaque token, not a verified UUID, except in session_helpers which
  /// validates UUID shape and falls back to its own uuid4 on mismatch.
  static String _localUuidV4() {
    final r = math.Random.secure();
    int n() => r.nextInt(0xFFFFFFFF);
    final hex = StringBuffer();
    for (var i = 0; i < 4; i++) {
      hex.write(n().toRadixString(16).padLeft(8, '0'));
    }
    final s = hex.toString();
    return '${s.substring(0, 8)}-${s.substring(8, 12)}-4${s.substring(13, 16)}-'
        '${(8 + r.nextInt(4)).toRadixString(16)}${s.substring(17, 20)}-'
        '${s.substring(20, 32)}';
  }

  /// Replace the device's session id with a canonical one returned by the
  /// server (e.g. after passwordless sign-in via AuthService.verifyToken).
  /// All subsequent API calls will carry the new id, so multiple devices
  /// signed into the same account hit the same server-side rows without a
  /// device_sessions junction table.
  ///
  /// Invalidates the in-flight session-create future so any pending callers
  /// pick up the new id instead of the device's old anonymous one.
  static Future<void> adoptCanonicalSessionId(String canonical) async {
    if (canonical.trim().isEmpty) return;
    _sessionId = canonical;
    _inflight = null;
    try {
      await KvStorage.write(_sessionKey, canonical);
    } catch (e) {
      if (kDebugMode) {
        debugPrint('SessionManager: adoptCanonical write error: $e');
      }
    }
  }

  static String _fallbackSessionId() =>
      DateTime.now().millisecondsSinceEpoch.toString();
}
