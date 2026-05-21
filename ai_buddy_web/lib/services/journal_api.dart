import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import 'session_manager.dart';

/// Thin client for `/api/journal/*`. Mirrors the backend's payload shape
/// (id / title / body / moodTag / createdAt / updatedAt). Returns
/// JournalApiEntry — a transport DTO. The screen-level JournalEntry
/// (defined in screens/journal_screen.dart) is constructed from these
/// in JournalStorage so the screen layer stays agnostic of HTTP.
class JournalApi {
  JournalApi._();

  static Dio? _dio;
  static Dio get _client {
    _dio ??= Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));
    return _dio!;
  }

  static Future<Map<String, dynamic>> _sessionHeaders() async {
    final sid = await SessionManager.getOrCreateSessionId();
    if (sid.isEmpty) return {};
    return {'X-Session-ID': sid};
  }

  /// GET /api/journal — returns server-side entries for the current
  /// session_id, ordered by created_at desc, up to [limit].
  static Future<List<JournalApiEntry>> list({int limit = 50}) async {
    final resp = await _client.get(
      '/api/journal',
      queryParameters: {'limit': limit},
      options: Options(headers: await _sessionHeaders()),
    );
    final List<dynamic> arr = resp.data as List<dynamic>;
    return arr
        .whereType<Map<String, dynamic>>()
        .map(JournalApiEntry.fromJson)
        .toList();
  }

  /// POST /api/journal — creates a new entry. Returns the server's
  /// canonical row (with server-assigned id + timestamps).
  static Future<JournalApiEntry> create({
    required String body,
    String? title,
    String? moodTag,
  }) async {
    final payload = <String, dynamic>{'body': body};
    if (title != null && title.trim().isNotEmpty) payload['title'] = title;
    if (moodTag != null && moodTag.isNotEmpty) payload['mood_tag'] = moodTag;
    final resp = await _client.post(
      '/api/journal',
      data: payload,
      options: Options(headers: await _sessionHeaders()),
    );
    return JournalApiEntry.fromJson(resp.data as Map<String, dynamic>);
  }

  /// DELETE /api/journal/{id}. Soft-delete server-side.
  static Future<void> delete(String id) async {
    await _client.delete(
      '/api/journal/$id',
      options: Options(headers: await _sessionHeaders()),
    );
  }
}

/// Transport DTO matching backend's `_entry_json` shape.
class JournalApiEntry {
  const JournalApiEntry({
    required this.id,
    required this.body,
    required this.createdAt,
    this.title,
    this.moodTag,
  });

  final String id;
  final String body;
  final DateTime createdAt;
  final String? title;
  final String? moodTag;

  factory JournalApiEntry.fromJson(Map<String, dynamic> j) {
    final createdRaw = j['createdAt'] as String?;
    DateTime created;
    try {
      created = createdRaw != null
          ? DateTime.parse(createdRaw)
          : DateTime.now();
    } catch (_) {
      if (kDebugMode) debugPrint('JournalApi: bad createdAt $createdRaw');
      created = DateTime.now();
    }
    return JournalApiEntry(
      id: j['id'] as String,
      body: j['body'] as String? ?? '',
      title: j['title'] as String?,
      moodTag: j['moodTag'] as String?,
      createdAt: created,
    );
  }
}
