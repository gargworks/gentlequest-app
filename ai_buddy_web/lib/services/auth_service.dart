import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import 'firebase_service.dart';
import 'session_manager.dart';

/// Passwordless magic-link auth client.
///
/// Pairs with backend `routes/auth.py`. Three endpoints:
///   POST /api/auth/magic-link  request a one-time login link
///   POST /api/auth/verify      exchange the token for a bound session
///   GET  /api/auth/me          who is the current X-Session-ID bound to?
///
/// Local state cached in SharedPreferences so app cold-starts know who's
/// logged in without a round-trip:
///   user_email_v1   — set on verify success; null while anonymous
///   user_id_v1      — same lifecycle as user_email_v1
class AuthService {
  AuthService._();
  static final AuthService instance = AuthService._();

  static const _kEmailKey = 'user_email_v1';
  static const _kUserIdKey = 'user_id_v1';

  final Dio _dio = Dio(BaseOptions(
    baseUrl: ApiConfig.baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 15),
    headers: {'Content-Type': 'application/json'},
  ));

  int? _userId;
  String? _email;
  bool _hydrated = false;

  /// Broadcasts when the device's session-binding changes: post-verify
  /// (signed in, canonical adopted) and post-signOut (anonymous, fresh
  /// session). Providers that show server-backed lists (chat history,
  /// mood entries, journal) subscribe so they refetch instead of
  /// silently showing stale data from the previous session.
  ///
  /// Broadcast stream so multiple providers can listen independently.
  final StreamController<void> _sessionChanged =
      StreamController<void>.broadcast();
  Stream<void> get onSessionChanged => _sessionChanged.stream;

  void _emitSessionChanged() {
    if (!_sessionChanged.isClosed) _sessionChanged.add(null);
  }

  /// Returns true if the current X-Session-ID has a user account bound.
  /// `hydrate()` should be called once on app start so this returns the
  /// cached value without a round-trip.
  bool get isSignedIn => _userId != null;
  String? get email => _email;
  int? get userId => _userId;

  /// Read the cached identity from SharedPreferences. Called once at
  /// app start (main.dart) so the UI doesn't flicker.
  Future<void> hydrate() async {
    if (_hydrated) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      _email = prefs.getString(_kEmailKey);
      _userId = prefs.getInt(_kUserIdKey);
    } catch (_) {
      // Anonymous state is the safe default if prefs fail.
    } finally {
      _hydrated = true;
    }
  }

  /// Send a magic link to the email. Always returns success regardless of
  /// whether the email is known — the backend deliberately doesn't reveal
  /// account existence (textbook auth pitfall).
  Future<void> requestMagicLink(String email) async {
    await _dio.post(
      '/api/auth/magic-link',
      data: {'email': email.trim().toLowerCase()},
      options: Options(headers: await _sessionHeaders()),
    );
  }

  /// Exchange a raw token (from the magic-link deep link) for the bound
  /// user identity. Persists to SharedPreferences on success so future
  /// app cold-starts know who's logged in.
  ///
  /// Phase 1.5 cross-device sync: the verify response includes the user's
  /// CANONICAL session_id. The verifying device adopts that id via
  /// SessionManager.adoptCanonicalSessionId, so multiple devices signed
  /// into the same account hit the same server-side data (chat history,
  /// mood, assessments) without a device_sessions junction table.
  ///
  /// Throws [AuthException] on a 4xx with the backend's error message,
  /// or [DioException] on network failures.
  Future<AuthIdentity> verifyToken(String rawToken) async {
    try {
      final resp = await _dio.post(
        '/api/auth/verify',
        data: {'token': rawToken.trim()},
        options: Options(headers: await _sessionHeaders()),
      );
      final data = resp.data as Map<String, dynamic>;
      final user = data['user'] as Map<String, dynamic>;
      final id = user['id'] as int;
      final emailValue = user['email'] as String;
      final canonical = data['session_id'] as String?;
      if (canonical != null && canonical.isNotEmpty) {
        await SessionManager.adoptCanonicalSessionId(canonical);
      }
      await _persist(id: id, email: emailValue);
      // Notify subscribers so server-backed providers (ChatProvider,
      // MoodProvider) refetch their lists under the new canonical
      // session id.
      _emitSessionChanged();
      return AuthIdentity(id: id, email: emailValue);
    } on DioException catch (e) {
      final body = e.response?.data;
      final msg = body is Map<String, dynamic>
          ? (body['error']?.toString() ?? 'verification failed')
          : 'verification failed';
      throw AuthException(msg);
    }
  }

  /// Sign out by:
  ///   1. Asking the server to revoke the session→user binding
  ///      (`POST /api/auth/signOut`). This is the device-loss-recovery
  ///      story: without it, the User row keeps pointing at the device's
  ///      session id, so anyone with that session id could still hit
  ///      `/api/auth/me` and impersonate.
  ///   2. Dropping the locally cached identity (SharedPreferences).
  ///   3. Resetting the journal-migration flag.
  ///   4. Rotating the local session id to a fresh anonymous one.
  ///   5. Emitting `onSessionChanged` so server-backed providers refetch.
  ///
  /// Network failure on step 1 is non-fatal — being locally signed out
  /// matters more for user trust than waiting for a flaky network. The
  /// server-side binding is then stale until the user signs in again,
  /// at which point a new session id is bound and the old one is
  /// orphaned (still revocable via the cancel-account flow if needed).
  Future<void> signOut() async {
    // Step 1: server-side revoke. Best-effort — log + continue on
    // failure rather than trapping the user in a signed-in UI.
    try {
      await _dio.post(
        '/api/auth/signOut',
        options: Options(headers: await _sessionHeaders()),
      );
    } catch (e) {
      if (kDebugMode) {
        debugPrint('AuthService: server signOut failed (continuing): $e');
      }
      // Surface to analytics so a flaky endpoint shows up as a metric,
      // not a silent failure mode.
      try {
        await FirebaseService().logEvent('auth_signout_server_failed', {
          'error': e.toString(),
        });
      } catch (_) {}
    }

    // Step 2: drop local identity cache.
    _userId = null;
    _email = null;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_kEmailKey);
      await prefs.remove(_kUserIdKey);
    } catch (e) {
      if (kDebugMode) {
        debugPrint('AuthService: signOut prefs clear failed: $e');
      }
      try {
        await FirebaseService().logEvent('auth_persist_failed', {
          'phase': 'signout_clear',
          'error': e.toString(),
        });
      } catch (_) {}
    }
    // Step 3: drop the previous user's canonical session_id so
    // subsequent API calls don't keep hitting their server-side data.
    // Replace with a fresh anonymous session id so anonymous use post
    // sign-out works immediately. The previous user's server-side data
    // is still bound to their account — signing back in re-adopts a
    // canonical session id (which may differ now that we unbound).
    await SessionManager.regenerateAnonymousSessionId();
    // Step 4: notify subscribers so any open chat / mood views clear
    // their server-backed state and re-pull under the new anonymous
    // session.
    _emitSessionChanged();
  }

  Future<Map<String, dynamic>> _sessionHeaders() async {
    final sid = await SessionManager.getOrCreateSessionId();
    if (sid.isEmpty) return {};
    return {'X-Session-ID': sid};
  }

  Future<void> _persist({required int id, required String email}) async {
    _userId = id;
    _email = email;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_kUserIdKey, id);
      await prefs.setString(_kEmailKey, email);
    } catch (e, st) {
      // Previously silently swallowed — meaning a broken device store
      // (full disk / corrupt prefs / sandbox revocation) looked like a
      // successful sign-in but lost identity on the next cold start.
      // Now surface to debug logs + analytics so it shows up in the
      // metrics dashboard rather than as a "huh, kept getting signed
      // out" user-trust hit.
      debugPrint('AuthService._persist failed: $e\n$st');
      try {
        await FirebaseService().logEvent('auth_persist_failed', {
          'phase': 'verify_persist',
          'error': e.toString(),
        });
      } catch (_) {
        // Firebase itself isn't critical to the auth flow; if it's down
        // we still want the debugPrint above to surface the original
        // failure.
      }
    }
  }
}

class AuthIdentity {
  const AuthIdentity({required this.id, required this.email});
  final int id;
  final String email;
}

class AuthException implements Exception {
  AuthException(this.message);
  final String message;
  @override
  String toString() => 'AuthException: $message';
}
