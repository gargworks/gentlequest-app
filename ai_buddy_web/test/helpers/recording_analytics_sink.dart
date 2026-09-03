import 'package:ai_buddy_web/services/firebase_service.dart';

/// Records every analytics event fired during a test.
///
/// Install in setUp with `FirebaseService.sinkOverride = RecordingAnalyticsSink()`
/// and ALWAYS clear it in tearDown — the override is static, so a leak makes
/// one test observe another test's events.
class RecordingAnalyticsSink implements AnalyticsSink {
  final List<String> names = <String>[];
  final List<Map<String, dynamic>?> params = <Map<String, dynamic>?>[];

  @override
  Future<void> logEvent(String name, [Map<String, dynamic>? parameters]) async {
    names.add(name);
    params.add(parameters);
  }

  /// How many times [name] fired. The count matters as much as the presence:
  /// a stage that fires twice per user inflates against a once-per-user stage
  /// above it, which is a real bug this codebase has already shipped once.
  int count(String name) => names.where((n) => n == name).length;

  /// Names filtered to [wanted], preserving order — for asserting sequence
  /// without being brittle about unrelated events firing in between.
  List<String> only(Set<String> wanted) =>
      names.where(wanted.contains).toList(growable: false);

  void clear() {
    names.clear();
    params.clear();
  }
}
