import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/widgets/ai_thinking_indicator.dart';

// ADR-006 quiet mode — does the reduced-motion gate actually gate anything?
//
// This file exists because of a real regression caught during the WO-8
// reduced-motion sweep. Sixteen widgets were correctly converted to read
// `MediaQuery.disableAnimations` in didChangeDependencies, but the guard
// was written as:
//
//     if (rm == _reduceMotion) return;   // _reduceMotion starts false
//
// On first mount with quiet mode OFF, `rm` is also false, so the guard
// early-returned and `.repeat()` was never reached — every one of those
// animations silently stopped starting at all. The full suite stayed green
// throughout, because nothing anywhere asserted that a perpetual animation
// actually runs. Analyze stayed at baseline too. The defect was invisible
// to every instrument pointed at it.
//
// So this is an OPPOSED PAIR, deliberately. Asserting only "motion stops in
// quiet mode" would have passed against the broken build — a gate that
// blocks everything looks identical to a gate that works, unless you also
// assert the open case. The first test here is the one that fails on the
// regression; the second is the one that fails if the gate is a no-op.
//
// hasScheduledFrame is the signal: a repeating AnimationController keeps
// requesting frames, so it is true while animating and false once idle.
void main() {
  Future<void> pumpIndicator(
    WidgetTester tester, {
    required bool disableAnimations,
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: MediaQueryData(disableAnimations: disableAnimations),
          child: const Scaffold(body: AIThinkingIndicator()),
        ),
      ),
    );
    // One pump past mount so didChangeDependencies has run and the
    // controller has settled into its steady state.
    await tester.pump(const Duration(milliseconds: 16));
  }

  testWidgets('animation RUNS when quiet mode is off (the regression guard)',
      (tester) async {
    await pumpIndicator(tester, disableAnimations: false);

    expect(
      tester.binding.hasScheduledFrame,
      isTrue,
      reason: 'the thinking indicator must actually animate in the default '
          'case — this is the assertion the early-return regression broke, '
          'and the one a stop-only test would have missed',
    );
  });

  testWidgets('animation STOPS when quiet mode is on', (tester) async {
    await pumpIndicator(tester, disableAnimations: true);

    expect(
      tester.binding.hasScheduledFrame,
      isFalse,
      reason: 'ADR-006 quiet mode promises reduced motion; a perpetual '
          'animation still requesting frames means the promise is not kept',
    );
  });
}
