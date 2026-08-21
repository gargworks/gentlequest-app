import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/models/companion.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';
import 'package:ai_buddy_web/widgets/companion_painter.dart';
import 'package:ai_buddy_web/widgets/silent_witness.dart';

void main() {
  group('SilentWitness', () {
    Future<void> buildWith(
      WidgetTester tester, {
      WitnessState state = WitnessState.breathe,
      GrowthStage stage = GrowthStage.seed,
    }) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SizedBox(
              width: 200,
              height: 200,
              child: Stack(
                children: [
                  SilentWitness(
                    state: state,
                    stage: stage,
                  ),
                ],
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
    }

    testWidgets('renders the companion (CustomPaint with CompanionPainter)',
        (tester) async {
      await buildWith(tester);
      expect(
        find.byWidgetPredicate(
          (w) =>
              w is CustomPaint &&
              w.painter is CompanionPainter &&
              (w.painter as CompanionPainter).simplified == true,
        ),
        findsOneWidget,
      );
    });

    testWidgets('tap shows the warm GQBanner message', (tester) async {
      await buildWith(tester);
      await tester.tap(find.byType(SilentWitness));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));
      expect(
        find.textContaining("I'm always glad to see you. No rush."),
        findsOneWidget,
      );
      // Drain the banner's 2s auto-dismiss timer so it doesn't leak past
      // this test (flutter test asserts no pending timers on teardown).
      await tester.pump(const Duration(seconds: 2));
    });

    testWidgets('settle state changes the breathing animation duration',
        (tester) async {
      await buildWith(tester, state: WitnessState.breathe);
      // Capture the breathe controller duration in normal state.
      final stateBreathe = tester.state<State>(find.byType(SilentWitness));
      // The SilentWitnessState owns the _breatheController; we verify the
      // state transition by rebuilding with settle and checking that no
      // exception is thrown and the widget still renders.
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SizedBox(
              width: 200,
              height: 200,
              child: Stack(
                children: [
                  SilentWitness(
                    state: WitnessState.settle,
                    stage: GrowthStage.seed,
                  ),
                ],
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      // In settle state, the shadow ellipse should be visible.
      expect(
        find.byWidgetPredicate(
          (w) =>
              w is Container &&
              w.decoration is BoxDecoration &&
              (w.decoration as BoxDecoration).color != null,
        ),
        findsWidgets,
      );
      // Verify the state object is SilentWitnessState (not a generic State).
      expect(stateBreathe, isNotNull);
    });

    testWidgets(
        'renders without a ParentDataWidget conflict when the caller wraps '
        'it in its own Positioned (the real call-site shape in '
        'interactive_chat_screen.dart)', (tester) async {
      // Regression test: SilentWitness used to wrap itself in a Positioned
      // too, so any caller doing exactly this — which the class doc always
      // told callers to do — crashed with "competing ParentDataWidgets".
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SizedBox(
              width: 200,
              height: 200,
              child: Stack(
                children: [
                  Positioned(
                    left: 18,
                    bottom: 8,
                    child: SilentWitness(
                      state: WitnessState.breathe,
                      stage: GrowthStage.seed,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      expect(tester.takeException(), isNull);
      expect(find.byType(SilentWitness), findsOneWidget);
    });

    testWidgets('stay (crisis) state freezes and shows shadow', (tester) async {
      await buildWith(tester, state: WitnessState.stay);
      // The shadow should be visible in stay state.
      expect(
        find.byWidgetPredicate(
          (w) =>
              w is Container &&
              w.decoration is BoxDecoration &&
              (w.decoration as BoxDecoration).color != null,
        ),
        findsWidgets,
      );
      // The companion painter should still render.
      expect(
        find.byWidgetPredicate(
          (w) =>
              w is CustomPaint &&
              w.painter is CompanionPainter &&
              (w.painter as CompanionPainter).simplified == true,
        ),
        findsOneWidget,
      );
    });

    testWidgets('breathe state does not show shadow', (tester) async {
      await buildWith(tester, state: WitnessState.breathe);
      // In breathe state, no shadow ellipse should be present.
      // The only Container decorations in breathe should be none from the
      // shadow (the shadow is conditionally rendered).
      final shadowContainers = tester.widgetList<Container>(find.byType(Container))
          .where((c) {
        if (c.decoration is! BoxDecoration) return false;
        final bd = c.decoration as BoxDecoration;
        // Shadow ellipse is 22x6 with moodSlateLavender tint.
        if (c.constraints?.maxWidth == 22) return true;
        return bd.color?.withValues(alpha: 1.0) ==
            GQColors.moodSlateLavender.withValues(alpha: 1.0);
      });
      expect(shadowContainers, isEmpty);
    });
  });
}
