import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Sean-Ellis PMF survey state.
///
/// Tracks:
///   • how many chat sessions the user has completed (incremented by the chat
///     screen after each AI reply lands)
///   • whether the survey sheet has already been shown to this user
///   • the user's recorded answer (one of the four Sean-Ellis options)
///
/// Persistence is via SharedPreferences so the "show once" guarantee survives
/// app restarts. Keys are namespaced with `_v1` so future revisions can
/// invalidate cleanly.
class SurveyProvider extends ChangeNotifier {
  SurveyProvider();

  // ── SharedPreferences keys ──────────────────────────────────────────────
  static const _kSessionCount = 'gq_chat_session_count_v1';
  static const _kSurveyShown = 'sean_ellis_survey_shown_v1';
  static const _kSurveyAnswer = 'sean_ellis_survey_answer_v1';

  /// Minimum chat sessions before the survey is eligible to show.
  static const int minSessionsForSurvey = 3;

  // ── State ───────────────────────────────────────────────────────────────
  int _sessionCount = 0;
  bool _shown = false;
  String? _answer;

  int get sessionCount => _sessionCount;
  bool get shown => _shown;
  String? get answer => _answer;

  /// Hydrate from SharedPreferences. Safe to call at app start; no-op if the
  /// keys are absent (fresh install).
  Future<void> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _sessionCount = prefs.getInt(_kSessionCount) ?? 0;
      _shown = prefs.getBool(_kSurveyShown) ?? false;
      _answer = prefs.getString(_kSurveyAnswer);
      notifyListeners();
    } catch (e) {
      if (kDebugMode) debugPrint('[survey_provider] load failed: $e');
    }
  }

  /// Increment the chat-session counter and persist. Called by the chat
  /// screen after each AI reply lands.
  Future<void> incrementSessionCount() async {
    _sessionCount += 1;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_kSessionCount, _sessionCount);
    } catch (e) {
      if (kDebugMode) debugPrint('[survey_provider] persist count failed: $e');
    }
  }

  /// True when the user has had >= [minSessionsForSurvey] chat sessions AND
  /// the survey has not yet been shown to them.
  bool shouldShowSurvey() {
    return !_shown && _sessionCount >= minSessionsForSurvey;
  }

  /// Mark the survey as shown so it never re-appears for this user.
  Future<void> markShown() async {
    if (_shown) return;
    _shown = true;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_kSurveyShown, true);
    } catch (e) {
      if (kDebugMode) debugPrint('[survey_provider] persist shown failed: $e');
    }
  }

  /// Record the user's Sean-Ellis answer and persist it.
  Future<void> recordAnswer(String answer) async {
    _answer = answer;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_kSurveyAnswer, answer);
    } catch (e) {
      if (kDebugMode) debugPrint('[survey_provider] persist answer failed: $e');
    }
  }

  /// Test helper: reset all survey state. Not used in production paths.
  @visibleForTesting
  Future<void> reset() async {
    _sessionCount = 0;
    _shown = false;
    _answer = null;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_kSessionCount);
      await prefs.remove(_kSurveyShown);
      await prefs.remove(_kSurveyAnswer);
    } catch (e) {
      if (kDebugMode) debugPrint('[survey_provider] reset failed: $e');
    }
  }
}
