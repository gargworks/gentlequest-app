// Journal — data model + on-device/server persistence.
// Split from journal_screen.dart (R1D14); see that file for the screen entry.

import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../services/auth_service.dart';
import '../../services/firebase_service.dart';
import '../../services/journal_api.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Data model + on-device persistence (SharedPreferences).
// Backend journaling API not yet wired — entries stay on the device.
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

/// JournalStorage — journal persistence with optional server sync.
///
/// Anonymous users: device-local via SharedPreferences only. Preserves
/// the verbatim "Stays on your device. Never synced." promise from the
/// empty-state design.
///
/// Signed-in users: dual-write — local SharedPreferences as the offline
/// cache, backend `/api/journal/*` as the cross-device source of truth.
/// The canonical session_id mechanism (see services/auth_service.dart
/// + services/session_manager.dart) means every device signed into the
/// same account shares server-side rows automatically.
class JournalStorage {
  static const _key = 'journal_entries_v1';
  static const _kMigratedKey = 'journal_local_migrated_to_server_v1';

  /// How long load() will wait for the server before returning local-only.
  /// Long enough for typical mobile latencies; short enough that a flaky
  /// network doesn't block the screen on cold-open.
  static const Duration _serverPullTimeout = Duration(milliseconds: 1500);

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

  /// Load entries. Anonymous → local only. Signed-in → local + a
  /// short-timeout server pull, merged by id (server wins on tie).
  ///
  /// Always returns the freshest available list; callers don't need to
  /// know whether the network was reachable.
  static Future<List<JournalEntry>> load() async {
    final local = await _loadLocal();
    if (!AuthService.instance.isSignedIn) return local;
    try {
      final remote = await JournalApi.list(limit: 100)
          .timeout(_serverPullTimeout);
      final merged = _mergeById(local, remote);
      await _saveLocal(merged);
      return merged;
    } catch (e) {
      if (kDebugMode) debugPrint('JournalStorage.load server pull failed: $e');
      return local;
    }
  }

  /// Persist [entries] verbatim. Backend isn't touched here — server-side
  /// state is mutated only through `append` / `remove`. Used when the
  /// caller has already reconciled (e.g. after a server pull in load()).
  static Future<void> save(List<JournalEntry> entries) async {
    await _saveLocal(entries);
  }

  /// Append a single entry to the persisted list. Writes locally
  /// immediately, then (if signed in) creates the entry server-side and
  /// replaces the local row's id with the server-assigned canonical id.
  /// Returns the updated list.
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

    if (AuthService.instance.isSignedIn) {
      try {
        final remote = await JournalApi.create(
          body: entry.body,
          moodTag: _moodToKey(entry.mood).isEmpty ? null : _moodToKey(entry.mood),
        );
        final idx = entries.indexWhere((e) => e.id == entry.id);
        if (idx >= 0) {
          // Replace the local entry with the server-canonical one so future
          // patches / deletes hit the right row.
          entries[idx] = JournalEntry(
            id: remote.id,
            body: remote.body,
            createdAt: remote.createdAt,
            mood: _moodFromKey(remote.moodTag),
            tags: entries[idx].tags,
          );
          await _saveLocal(entries);
        }
      } catch (e) {
        if (kDebugMode) debugPrint('JournalStorage.append server post failed: $e');
        // Local copy retained; will get pushed up on next migrate call.
      }
    }
    return entries;
  }

  /// Soft-delete an entry. Removes locally and (if signed in) sends
  /// DELETE to the server. Server failures are non-fatal.
  static Future<List<JournalEntry>> remove(String entryId) async {
    final entries = await _loadLocal();
    entries.removeWhere((e) => e.id == entryId);
    await _saveLocal(entries);
    if (AuthService.instance.isSignedIn) {
      // Only attempt server delete if the id LOOKS server-assigned
      // (uuid v4 shape — 36 chars with dashes). Local ids are ISO-8601
      // timestamps and won't exist server-side until migrate() runs.
      if (entryId.length == 36 && entryId.contains('-')) {
        try {
          await JournalApi.delete(entryId);
        } catch (e) {
          if (kDebugMode) {
            debugPrint('JournalStorage.remove server delete failed: $e');
          }
        }
      }
    }
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

  /// One-time migration: push every local-only entry to the server.
  /// Called right after a successful magic-link verify so the user's
  /// pre-login journal entries follow them across devices.
  ///
  /// Idempotent via a SharedPreferences flag so re-running on subsequent
  /// sign-ins doesn't double-upload.
  static Future<void> migrateLocalToServer() async {
    if (!AuthService.instance.isSignedIn) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      if (prefs.getBool(_kMigratedKey) ?? false) return;
      final local = await _loadLocal();
      if (local.isEmpty) {
        await prefs.setBool(_kMigratedKey, true);
        return;
      }
      // Push oldest first so server timeline reads in the same order.
      final reversed = local.reversed.toList();
      final replaced = <JournalEntry>[];
      bool everyEntryMigrated = true;
      for (final entry in reversed) {
        // Skip rows that already look server-assigned (uuid-shaped id).
        if (entry.id.length == 36 && entry.id.contains('-')) {
          replaced.insert(0, entry);
          continue;
        }
        try {
          final remote = await JournalApi.create(
            body: entry.body,
            moodTag: _moodToKey(entry.mood).isEmpty
                ? null
                : _moodToKey(entry.mood),
          );
          replaced.insert(
            0,
            JournalEntry(
              id: remote.id,
              body: remote.body,
              createdAt: remote.createdAt,
              mood: _moodFromKey(remote.moodTag),
              tags: entry.tags,
            ),
          );
        } catch (e) {
          if (kDebugMode) {
            debugPrint('JournalStorage.migrate: skip $e (entry stays local)');
          }
          // Local copy retained; will retry next sign-in.
          replaced.insert(0, entry);
          everyEntryMigrated = false;
        }
      }
      await _saveLocal(replaced);
      // Only mark migrated when EVERY non-uuid entry made it to the server.
      // Otherwise leave the flag false so the next sign-in retries the
      // still-local rows. Was previously set unconditionally → orphaned
      // entries forever.
      if (everyEntryMigrated) {
        await prefs.setBool(_kMigratedKey, true);
      }
    } catch (e) {
      if (kDebugMode) {
        debugPrint('JournalStorage.migrate top-level failure: $e');
      }
    }
  }

  /// Reset the migrate flag — called on sign-out so the NEXT sign-in
  /// (potentially a different user on this device) re-migrates from
  /// whatever's still on disk at that time.
  static Future<void> resetMigrationFlag() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_kMigratedKey);
    } catch (_) {}
  }

  // ── Merge ──────────────────────────────────────────────────────────

  /// Merge local + remote by id. If both sides have the same id, prefer
  /// the remote copy (server is source of truth when reachable).
  /// Entries unique to one side carry through.
  static List<JournalEntry> _mergeById(
    List<JournalEntry> local,
    List<JournalApiEntry> remote,
  ) {
    final remoteById = <String, JournalApiEntry>{
      for (final r in remote) r.id: r,
    };
    final out = <JournalEntry>[];
    final seen = <String>{};
    for (final r in remote) {
      seen.add(r.id);
      out.add(JournalEntry(
        id: r.id,
        body: r.body,
        createdAt: r.createdAt,
        mood: _moodFromKey(r.moodTag),
      ));
    }
    for (final l in local) {
      if (remoteById.containsKey(l.id)) continue; // remote wins
      if (seen.contains(l.id)) continue;
      out.add(l);
      seen.add(l.id);
    }
    out.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return out;
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
