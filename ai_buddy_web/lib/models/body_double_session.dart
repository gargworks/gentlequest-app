/// Body-doubling session configuration — v1.5.0 ADHD Update, Workstream 2a.
///
/// Captured once by `BodyDoubleStartSheet` and handed to the timer/check-in
/// flow owned by `InteractiveChatScreen`. Cheap-version model: no
/// persistence, no backend round-trip — the session lives entirely in the
/// chat screen's state for the duration of the run.
class BodyDoubleSessionConfig {
  const BodyDoubleSessionConfig({required this.task, required this.duration});

  /// Free-text task the user is doing (e.g. "tidy the kitchen"). Never sent
  /// to analytics — only rendered locally in companion chat messages.
  final String task;

  /// Planned session length, picked from [kBodyDoubleDurationPresetsMinutes].
  final Duration duration;
}

/// Preset session lengths offered in the start sheet. Minutes only — keeps
/// the picker to a single row of chips instead of a free-form input.
const List<int> kBodyDoubleDurationPresetsMinutes = [5, 10, 15, 25];
