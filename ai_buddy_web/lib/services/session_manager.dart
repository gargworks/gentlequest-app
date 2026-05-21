import 'dart:async';
import 'dart:math' as math;
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';
import 'storage/kv_storage.dart';

/// Centralized session ID coordinator to deduplicate network calls to
/// `/api/get_or_create_session` across services.
///
/// Storage layering (read order on first access):
///   1. In-memory (`_sessionId`) — fast path
///   2. FlutterSecureStorage at `gq_session_id_v1`
///      (Android: encryptedSharedPreferences; iOS/macOS: Keychain)
///   3. Legacy fallbacks read once for migration:
///        - FlutterSecureStorage at the old `session_id` key
///        - SharedPreferences at `session_id` (pre-KvStorage era)
///      If either has a value, copy into secure storage at the v1 key,
///      delete the legacy copies, and never read the legacy keys again.
/// On web, FlutterSecureStorage isn't a real secure surface — KvStorage
/// already shims to SharedPreferences on web, which is the best we can do
/// in a browser. Mobile is where the value lives.
class SessionManager {
  /// Legacy key — read once for migration, then deleted.
  static const String _legacySessionKey = 'session_id';

  /// Canonical key (post-migration). Bumped to v1 to make the migration
  /// trigger trivially observable.
  static const String _sessionKey = 'gq_session_id_v1';

  /// Mobile-only secure storage handle. On Android this opts into
  /// `EncryptedSharedPreferences` (AES-256 backed by AndroidKeyStore);
  /// on iOS/macOS it uses Keychain (first_unlock). On web/desktop the
  /// plugin falls back, so we still wrap reads in try/catch.
  static const FlutterSecureStorage _secure = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static String? _sessionId;
  static Completer<String>? _inflight;
  static bool _migrationChecked = false;

  /// Returns an in-memory session id if present, else loads from secure storage,
  /// else performs a single, deduplicated network call to create one.
  static Future<String> getOrCreateSessionId() async {
    // Fast path: in-memory
    if (_sessionId != null && _sessionId!.trim().isNotEmpty) return _sessionId!;

    // Try persisted storage (secure storage → migration fallback)
    try {
      final existing = await _loadPersisted();
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
        await _writePersisted(_sessionId!);
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
      await _deletePersisted();
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
      await _writePersisted(fresh);
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
      await _writePersisted(canonical);
    } catch (e) {
      if (kDebugMode) {
        debugPrint('SessionManager: adoptCanonical write error: $e');
      }
    }
  }

  static String _fallbackSessionId() =>
      DateTime.now().millisecondsSinceEpoch.toString();

  // ─── Persistence internals ──────────────────────────────────────────

  /// Read from secure storage, falling back once to legacy locations.
  ///
  /// On web FlutterSecureStorage isn't truly secure, so we stick with
  /// KvStorage (which is SharedPreferences on web) and skip the
  /// secure-storage hop entirely. Mobile is where the secrecy matters.
  static Future<String?> _loadPersisted() async {
    if (kIsWeb) {
      return KvStorage.read(_sessionKey).then((v) async {
        if (v != null && v.trim().isNotEmpty) return v;
        // Migrate from legacy key on web too (KvStorage on web == prefs).
        final legacy = await KvStorage.read(_legacySessionKey);
        if (legacy != null && legacy.trim().isNotEmpty) {
          await KvStorage.write(_sessionKey, legacy);
          await KvStorage.delete(_legacySessionKey);
          return legacy;
        }
        return null;
      });
    }

    // Mobile / desktop: encrypted-shared-preferences (Android) or Keychain.
    String? current;
    try {
      current = await _secure.read(key: _sessionKey);
    } catch (e) {
      if (kDebugMode) debugPrint('SessionManager: secure read error: $e');
      current = null;
    }
    if (current != null && current.trim().isNotEmpty) return current;

    // One-time migration sweep (lazy, runs on first read miss).
    if (!_migrationChecked) {
      _migrationChecked = true;
      final migrated = await _migrateLegacyToSecure();
      if (migrated != null && migrated.trim().isNotEmpty) return migrated;
    }
    return null;
  }

  /// Read from any of the legacy locations and, if found, copy into
  /// secure storage at the v1 key and delete the legacy copy. Returns
  /// the migrated value, or null if nothing legacy existed.
  static Future<String?> _migrateLegacyToSecure() async {
    // Path 1: legacy FlutterSecureStorage key (`session_id`).
    // Before this change, KvStorage on IO used FlutterSecureStorage()
    // without aOptions and stored under 'session_id'.
    String? legacy;
    try {
      legacy = await _secure.read(key: _legacySessionKey);
    } catch (e) {
      if (kDebugMode) {
        debugPrint('SessionManager: legacy secure read error: $e');
      }
      legacy = null;
    }
    // Also try the default (non-encryptedSharedPreferences) handle in case
    // the prior install used the plain backend — values written without
    // aOptions live in a different Android SharedPreferences file.
    if (legacy == null || legacy.trim().isEmpty) {
      try {
        const plain = FlutterSecureStorage();
        legacy = await plain.read(key: _legacySessionKey);
      } catch (_) {
        legacy = null;
      }
    }

    // Path 2: SharedPreferences at the legacy key (very old pre-KvStorage
    // installs, or web→mobile re-installs that synced prefs).
    if (legacy == null || legacy.trim().isEmpty) {
      try {
        final prefs = await SharedPreferences.getInstance();
        legacy = prefs.getString(_legacySessionKey);
      } catch (_) {
        legacy = null;
      }
    }

    if (legacy == null || legacy.trim().isEmpty) return null;

    // Copy into v1 secure storage, then clear the legacy copies. Best
    // effort — a failure to delete the legacy row is acceptable (the
    // _migrationChecked flag prevents re-running this in-session).
    try {
      await _secure.write(key: _sessionKey, value: legacy);
    } catch (e) {
      if (kDebugMode) {
        debugPrint('SessionManager: migrate write error: $e');
      }
      // If we couldn't write to the new key, don't delete the legacy one
      // — losing the session id silently would be worse than carrying
      // the legacy storage location for one more session.
      return legacy;
    }
    try {
      await _secure.delete(key: _legacySessionKey);
    } catch (_) {}
    try {
      const plain = FlutterSecureStorage();
      await plain.delete(key: _legacySessionKey);
    } catch (_) {}
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_legacySessionKey);
    } catch (_) {}
    return legacy;
  }

  static Future<void> _writePersisted(String value) async {
    if (kIsWeb) {
      await KvStorage.write(_sessionKey, value);
      return;
    }
    await _secure.write(key: _sessionKey, value: value);
  }

  static Future<void> _deletePersisted() async {
    if (kIsWeb) {
      await KvStorage.delete(_sessionKey);
      return;
    }
    try {
      await _secure.delete(key: _sessionKey);
    } catch (e) {
      if (kDebugMode) debugPrint('SessionManager: secure delete error: $e');
    }
  }
}
