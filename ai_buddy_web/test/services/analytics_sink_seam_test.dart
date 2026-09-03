import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/services/firebase_service.dart';

import '../helpers/recording_analytics_sink.dart';

/// Pins the seam itself, added 2026-09-03.
///
/// Every future analytics widget test rests on this, so the seam needs its own
/// opposed pair: it must OBSERVE when installed, and it must be INERT — and
/// specifically must not leak past anonymity — otherwise the tests built on it
/// are measuring the wrong thing.
void main() {
  tearDown(() => FirebaseService.sinkOverride = null);

  test('an installed sink observes logEvent, name and parameters', () async {
    final sink = RecordingAnalyticsSink();
    FirebaseService.sinkOverride = sink;

    await FirebaseService().logEvent('probe_event', {'k': 'v'});

    expect(sink.names, ['probe_event']);
    expect(sink.params.single, {'k': 'v'});
  });

  test('the richer wrappers are observed too, under their REAL GA4 names',
      () async {
    // logMoodEntry/logChatMessage/etc all funnel through logEvent, so one seam
    // covers them — and reports the name GA4 actually receives, not the Dart
    // method name.
    final sink = RecordingAnalyticsSink();
    FirebaseService.sinkOverride = sink;

    await FirebaseService().logCrisisResourceAccess();

    expect(sink.names, contains('crisis_resource_accessed'));
  });

  test('OPPOSED CONTROL: with no sink installed, nothing is recorded',
      () async {
    final sink = RecordingAnalyticsSink();
    FirebaseService.sinkOverride = null;

    await FirebaseService().logEvent('should_not_be_seen');

    expect(sink.names, isEmpty,
        reason: 'Without this, the first test could pass because the sink '
            'records unconditionally rather than because the seam routes to it.');
  });

  test('ANONYMITY WINS over the seam — a sink must never see suppressed events',
      () async {
    // The privacy promise outranks observability. If this ever fails, an
    // override can observe events the user asked nobody to see, and the
    // ordering inside logEvent has regressed.
    final sink = RecordingAnalyticsSink();
    FirebaseService.sinkOverride = sink;
    FirebaseService().setAnonymityMode(true);

    await FirebaseService().logEvent('must_be_suppressed');

    FirebaseService().setAnonymityMode(false);
    expect(sink.names, isEmpty,
        reason: 'Anonymity mode must suppress events BEFORE the test seam. '
            'Observability must never be a hole in a privacy guarantee.');
  });

  test('count() distinguishes fired-once from fired-many', () async {
    final sink = RecordingAnalyticsSink();
    FirebaseService.sinkOverride = sink;

    await FirebaseService().logEvent('x');
    await FirebaseService().logEvent('x');

    expect(sink.count('x'), 2,
        reason: 'Stage inflation is a real bug class here; the helper has to '
            'be able to see it.');
  });
}
