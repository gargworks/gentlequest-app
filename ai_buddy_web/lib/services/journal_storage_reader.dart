import 'package:flutter/material.dart';

import '../screens/journal_screen.dart' show JournalEntry;

/// Read-only contract surface for journal entries. Lets callers like
/// Weekly Review query journal data without depending on
/// JournalStorage's full read/write/sync API surface — and lets tests
/// inject a fixed entry list without mocking SharedPreferences or the
/// network.
///
/// Note: JournalStorage in journal_screen.dart is all-static, so it
/// does NOT formally implement this interface (Dart can't satisfy an
/// abstract instance method with a static of the same name). The
/// interface lives as a design-intent contract + test-stub fixture.
/// Production callers use the static JournalStorage.standoutMoments(...)
/// directly. Future refactor could converge them via OPTION B (instance
/// methods on JournalStorage) or OPTION C (wrapper adapter); for now
/// the contract is conceptual.
///
/// See Chunk 5 (feat/journal-standout-moments) spec for the bifurcation
/// rationale.
abstract class JournalStorageReader {
  /// Returns the merged local+remote entry list, most-recent first.
  /// Same semantics as the existing JournalStorage.load() — this is
  /// just the read-only subset extracted for callers that don't need
  /// to write.
  Future<List<JournalEntry>> load();

  /// Returns up to [limit] entries from [window] that read as
  /// "standout moments" — the kind worth resurfacing on Sunday's
  /// Weekly Review card.
  ///
  /// Selection rules (P10 — pattern surfacing without diagnosing):
  ///   • Mood in {great, good} only. We resurface what worked,
  ///     never what hurt. Resurfacing a heavy entry on Sunday
  ///     evening can re-trigger; R1D15 voice rules forbid it.
  ///   • Body length ≥ 40 chars — filters out micro-entries that
  ///     don't re-read as memorable.
  ///   • Ranked recent-first within the window. No recency curve.
  ///
  /// Returns an empty list (not null) when no entries qualify, so
  /// callers can render the mood-derived fallback card without a
  /// null-check ladder. Runs purely in-memory against load() — no
  /// network call, no analytics event fired.
  Future<List<JournalEntry>> standoutMoments({
    required DateTimeRange window,
    int limit = 3,
  });
}
