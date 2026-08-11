// R1D14 — Journal
// Design source: docs/design/refs/htmls/GentleQuest_Journal.html
// REVIEW.md tier: R1D14 (Tier 2)
//
// Three views (now split into lib/screens/journal/):
//   A — Empty state  (entries.isEmpty)          journal/journal_empty_state.dart
//   B — Entry view   (read/edit a single entry) journal/journal_entry_view.dart
//   C — Timeline     (chronological, by week)   journal/journal_timeline_view.dart
// Data model + persistence:                     journal/journal_models.dart
// Shared helpers (mood color/label, formats):   journal/journal_shared.dart
//
// Backend persistence: entries are dual-written — local SharedPreferences
// always, server /api/journal/* when signed in. See JournalStorage docs.
//
// Font notes [assumed]: Fraunces (serif, entry body) and Caveat (handwritten,
// chip starters / notebook scribble) are not included as Flutter font assets.
// System default (sans-serif) is used as the cross-platform fallback until the
// fonts are added to pubspec.yaml + assets/fonts/. Flag for Lokesh review.

import 'package:flutter/material.dart';

import '../theme/gq_tokens.dart';
import 'journal/journal_empty_state.dart';
import 'journal/journal_entry_view.dart';
import 'journal/journal_models.dart';
import 'journal/journal_timeline_view.dart';

// Re-export the section libraries so existing `import 'journal_screen.dart'`
// consumers (weekly_review, auth_service, mood_reflection_sheet, tests) keep
// seeing the same public symbols as before the lib/screens/journal/ split.
export 'journal/journal_empty_state.dart';
export 'journal/journal_entry_view.dart';
export 'journal/journal_models.dart';
export 'journal/journal_shared.dart';
export 'journal/journal_timeline_view.dart';

// ─────────────────────────────────────────────────────────────────────────────
// JournalScreen — root screen
// Routes to empty state (A) or timeline (C) based on entry count.
// ─────────────────────────────────────────────────────────────────────────────

class JournalScreen extends StatefulWidget {
  const JournalScreen({super.key});

  @override
  State<JournalScreen> createState() => _JournalScreenState();
}

class _JournalScreenState extends State<JournalScreen> {
  List<JournalEntry> _entries = [];
  bool _loaded = false;

  @override
  void initState() {
    super.initState();
    _loadEntries();
  }

  Future<void> _loadEntries() async {
    final loaded = await JournalStorage.load();
    if (!mounted) return;
    setState(() {
      _entries = loaded;
      _loaded = true;
    });
  }

  Future<void> _addEntry(String body) async {
    if (body.trim().isEmpty) return;
    final localEntry = JournalEntry(
      id: DateTime.now().toIso8601String(),
      body: body.trim(),
      createdAt: DateTime.now(),
    );
    // Optimistic local insert for instant feedback.
    setState(() => _entries.insert(0, localEntry));
    try {
      final updated = await JournalStorage.append(localEntry);
      if (!mounted) return;
      setState(() => _entries = updated);
    } catch (_) {
      // Rollback the optimistic insert so the UI doesn't show an entry
      // that wasn't persisted. Without this, the entry would vanish on
      // next load with no explanation (M4 — silent data loss).
      if (!mounted) return;
      setState(() => _entries.removeWhere((e) => e.id == localEntry.id));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Couldn't save just now — please try again."),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _deleteEntry(String id) async {
    // Optimistic remove for instant UI feedback. On server-side failure
    // for a signed-in user, the row would reappear on next load() merge —
    // catch that here, restore the entry locally, and tell the user so
    // they can retry rather than silently drift between local + server.
    final idx = _entries.indexWhere((e) => e.id == id);
    if (idx < 0) return;
    final saved = _entries[idx];
    setState(() => _entries.removeAt(idx));
    try {
      await JournalStorage.remove(id);
    } catch (_) {
      if (!mounted) return;
      setState(() => _entries.insert(idx, saved));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Couldn't delete just now — try again in a moment."),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _openEditor({String? prefill}) async {
    final result = await Navigator.of(context).push<String>(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) =>
            JournalEditorSheet(initialText: prefill ?? ''),
        transitionsBuilder: (_, anim, __, child) {
          final slide = Tween<Offset>(
            begin: const Offset(0, 1),
            end: Offset.zero,
          ).animate(CurvedAnimation(parent: anim, curve: Curves.easeOut));
          final fade = Tween<double>(begin: 0, end: 1)
              .animate(CurvedAnimation(parent: anim, curve: Curves.easeIn));
          return SlideTransition(
            position: slide,
            child: FadeTransition(opacity: fade, child: child),
          );
        },
        transitionDuration: const Duration(milliseconds: 220),
      ),
    );
    if (result != null) _addEntry(result);
  }

  @override
  Widget build(BuildContext context) {
    // First frame after navigation: show a placeholder while SharedPreferences
    // load. Without this, the screen briefly flashes the empty state even when
    // entries exist on device — a small but jarring blink.
    if (!_loaded) {
      return Scaffold(
        backgroundColor: GQColors.softBg,
        body: const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      );
    }
    if (_entries.isEmpty) {
      return JournalEmptyState(onStartEntry: _openEditor);
    }
    return JournalTimelineView(
      entries: _entries,
      onOpenEditor: _openEditor,
      onDeleteEntry: _deleteEntry,
    );
  }
}
