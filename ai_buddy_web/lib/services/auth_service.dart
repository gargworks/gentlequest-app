import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
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
      return AuthIdentity(id: id, email: emailValue);
    } on DioException catch (e) {
      final body = e.response?.data;
      final msg = body is Map<String, dynamic>
          ? (body['error']?.toString() ?? 'verification failed')
          : 'verification failed';
      throw AuthException(msg);
    }
  }

  /// Sign out by dropping the cached identity. Server-side the session
  /// remains bound (so signing back in on the same device reattaches the
  /// history); a true "wipe device session" is a separate destructive
  /// action covered by Delete-my-account in Settings.
  Future<void> signOut() async {
    _userId = null;
    _email = null;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_kEmailKey);
      await prefs.remove(_kUserIdKey);
    } catch (_) {
      // best effort
    }
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
    } catch (e) {
      if (kDebugMode) debugPrint('AuthService persist failed: $e');
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
