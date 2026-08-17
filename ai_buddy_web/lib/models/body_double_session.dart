/// Body-doubling session configuration — v1.5.0 ADHD Update, Workstream 2a.
///
/// Captured once by `BodyDoubleStartSheet` and handed to the timer/check-in
/// flow owned by `InteractiveChatScreen`. Cheap-version model: no
/// persistence, no backend round-trip — the session lives entirely in the
/// chat screen's state for the duration of the run.
class BodyDoubleSessionConfig {
  const BodyDoubleSessionConfig({
    required this.task,
    required this.duration,
    this.wantsLive = false,
  });

  /// Free-text task the user is doing (e.g. "tidy the kitchen"). Never sent
  /// to analytics — only rendered locally in companion chat messages.
  final String task;

  /// Planned session length, picked from [kBodyDoubleDurationPresetsMinutes].
  final Duration duration;

  /// Fake-door signal: the user picked "With someone" over "Just me" in the
  /// start sheet. No real matching exists yet — this only tags the session
  /// for the `body_double_live_interest` event so we can measure demand
  /// before building a matching backend. The room itself is unaffected;
  /// this never becomes a real live session on its own.
  final bool wantsLive;
}

/// Preset session lengths offered in the start sheet. Minutes only — keeps
/// the picker to a single row of chips instead of a free-form input.
const List<int> kBodyDoubleDurationPresetsMinutes = [5, 10, 15, 25];
