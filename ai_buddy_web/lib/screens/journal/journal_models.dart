// Journal — data model + on-device persistence.
// Split from journal_screen.dart (R1D14); see that file for the screen entry.

import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../services/firebase_service.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Data model + on-device persistence (SharedPreferences).
// Backend /api/journal/* routes were removed in PR #167 (2026-07-02).
// Entries stay on the device — local SharedPreferences is the sole path.
// ─────────────────────────────────────────────────────────────────────────────

enum JournalMood { great, good, okay, meh, rough }

String _moodToKey(JournalMood? m) => switch (m) {
      JournalMood.great => 'great',
      JournalMood.good => 'good',
      JournalMood.okay => 'okay',
      JournalMood.meh => 'meh',
      JournalMood.rough => 'rough',
      null => '',
    };

JournalMood? _moodFromKey(String? k) => switch (k) {
      'great' => JournalMood.great,
      'good' => JournalMood.good,
      'okay' => JournalMood.okay,
      'meh' => JournalMood.meh,
      'rough' => JournalMood.rough,
      _ => null,
    };

/// JournalStorage — journal persistence, device-local via SharedPreferences.
///
/// The backend /api/journal/* routes were removed in PR #167 (2026-07-02).
/// All journal entries stay on the device — local SharedPreferences is the
/// sole storage path for everyone, regardless of auth state. This matches
/// the "Stays on your device. Never synced. Never shared." privacy promise
/// shown in the empty state.
class JournalStorage {
  static const _key = 'journal_entries_v1';

  // ── Local helpers ──────────────────────────────────────────────────

  static Future<List<JournalEntry>> _loadLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_key);
      if (raw == null || raw.isEmpty) return [];
      final List<dynamic> arr = jsonDecode(raw) as List<dynamic>;
      return arr
          .whereType<Map<String, dynamic>>()
          .map(JournalEntry.fromJson)
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<void> _saveLocal(List<JournalEntry> entries) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = jsonEncode(entries.map((e) => e.toJson()).toList());
      await prefs.setString(_key, raw);
    } catch (_) {
      // Silent — caller already has the entry in memory; next save will retry.
    }
  }

  // ── Public API ─────────────────────────────────────────────────────

  /// Load entries from local SharedPreferences.
  static Future<List<JournalEntry>> load() async {
    return _loadLocal();
  }

  /// Persist [entries] verbatim to local storage.
  static Future<void> save(List<JournalEntry> entries) async {
    await _saveLocal(entries);
  }

  /// Append a single entry to the persisted list. Writes locally
  /// immediately. Returns the updated list.
  ///
  /// Used by mood_reflection_sheet and JournalScreen's editor.
  static Future<List<JournalEntry>> append(JournalEntry entry) async {
    final entries = await _loadLocal();
    entries.insert(0, entry);
    await _saveLocal(entries);

    // Fires once per discrete save action (not on rebuild) — this is the
    // actual persistence point, called from the editor's Save button and
    // mood_reflection_sheet's journal prompt.
    unawaited(FirebaseService().logEvent('journal_entry_saved'));

    return entries;
  }

  /// Remove an entry from local storage.
  static Future<List<JournalEntry>> remove(String entryId) async {
    final entries = await _loadLocal();
    entries.removeWhere((e) => e.id == entryId);
    await _saveLocal(entries);
    return entries;
  }

  /// Returns up to [limit] entries from [window] that read as "standout
  /// moments" — the kind worth resurfacing on Weekly Review's standout
  /// card.
  ///
  /// Selection rules (P10 — pattern surfacing without diagnosing):
  ///   • Mood in {great, good} only. Resurface what worked, never what
  ///     hurt. R1D15 voice rules forbid re-surfacing heavy entries.
  ///   • Body length ≥ 40 chars — filters out micro-entries that don't
  ///     re-read as memorable.
  ///   • Ranked recent-first within the window. No recency curve.
  ///
  /// Returns an empty list (not null) when no entries qualify. Runs
  /// purely in-memory against load() — no network call, no analytics
  /// event fired (data minimization).
  ///
  /// Static rather than instance because JournalStorage is all-static;
  /// see JournalStorageReader contract doc in lib/services/.
  static Future<List<JournalEntry>> standoutMoments({
    required DateTimeRange window,
    int limit = 3,
  }) async {
    final entries = await load();
    final qualifying = entries.where((e) {
      if (e.createdAt.isBefore(window.start)) return false;
      if (e.createdAt.isAfter(window.end)) return false;
      if (e.mood != JournalMood.great && e.mood != JournalMood.good) {
        return false;
      }
      if (e.body.trim().length < 40) return false;
      return true;
    }).toList()
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return qualifying.take(limit).toList();
  }
}

class JournalEntry {
  JournalEntry({
    required this.id,
    required this.body,
    required this.createdAt,
    this.mood,
    this.tags = const [],
  });

  final String id;
  final String body;
  final DateTime createdAt;
  final JournalMood? mood;
  final List<String> tags;

  JournalEntry copyWith({
    String? body,
    JournalMood? mood,
    List<String>? tags,
  }) =>
      JournalEntry(
        id: id,
        body: body ?? this.body,
        createdAt: createdAt,
        mood: mood ?? this.mood,
        tags: tags ?? this.tags,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'body': body,
        'createdAt': createdAt.toIso8601String(),
        'mood': _moodToKey(mood),
        'tags': tags,
      };

  factory JournalEntry.fromJson(Map<String, dynamic> j) => JournalEntry(
        id: j['id'] as String,
        body: j['body'] as String,
        createdAt: DateTime.parse(j['createdAt'] as String),
        mood: _moodFromKey(j['mood'] as String?),
        tags: (j['tags'] as List<dynamic>? ?? [])
            .whereType<String>()
            .toList(),
      );
}
