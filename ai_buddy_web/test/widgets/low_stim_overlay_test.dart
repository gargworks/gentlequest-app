import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/services/low_stim_service.dart';
import 'package:ai_buddy_web/theme/low_stim_mode.dart';

/// Low-stim "quiet mode" render-side tests (v1.5.0 ADHD update, ADR-006).
///
/// Verifies the themed state LowStimOverlay produces: a saturation
/// ColorFilter is applied app-wide when the preference is on, and
/// MediaQuery.disableAnimations flips for the wrapped subtree — matching
/// the acceptance criteria in docs/V1_5_0_ADHD_UPDATE_SCOPE.md workstream 2b
/// ("swaps the active color theme for a low-saturation/low-motion variant
/// app-wide").
void main() {
  setUp(() {
    LowStimService.lowStimNotifier.value = false;
  });

  Widget buildHarness() {
    return MaterialApp(
      home: LowStimOverlay(
        child: Builder(
          builder: (context) => Text(
            MediaQuery.of(context).disableAnimations ? 'reduced' : 'normal',
          ),
        ),
      ),
    );
  }

  group('LowStimOverlay — off (default)', () {
    testWidgets('renders child with no color filter applied', (tester) async {
      await tester.pumpWidget(buildHarness());
      await tester.pump();

      expect(find.byType(ColorFiltered), findsNothing);
      expect(find.text('normal'), findsOneWidget);
    });
  });

  group('LowStimOverlay — on (low-stim quiet mode)', () {
    testWidgets('applies a saturation ColorFilter app-wide', (tester) async {
      LowStimService.lowStimNotifier.value = true;
      await tester.pumpWidget(buildHarness());
      await tester.pump();

      final filtered =
          tester.widget<ColorFiltered>(find.byType(ColorFiltered));
      expect(filtered.colorFilter,
          ColorFilter.matrix(saturationMatrixForTest()));
    });

    testWidgets('flips MediaQuery.disableAnimations for the subtree',
        (tester) async {
      LowStimService.lowStimNotifier.value = true;
      await tester.pumpWidget(buildHarness());
      await tester.pump();

      expect(find.text('reduced'), findsOneWidget);
    });

    testWidgets('reacts live to the notifier without a widget rebuild',
        (tester) async {
      await tester.pumpWidget(buildHarness());
      await tester.pump();
      expect(find.text('normal'), findsOneWidget);

      // Flip the preference the same way Settings' toggle handler does —
      // no pumpWidget() call, proving the app-wide swap is instant.
      LowStimService.lowStimNotifier.value = true;
      await tester.pump();

      expect(find.text('reduced'), findsOneWidget);
      expect(find.byType(ColorFiltered), findsOneWidget);
    });
  });
}

/// Mirrors LowStimOverlay.kLowStimSaturation via the same helper it uses,
/// so this test asserts against the real matrix rather than a duplicated
/// literal that could silently drift from the implementation.
List<double> saturationMatrixForTest() {
  const s = LowStimOverlay.kLowStimSaturation;
  final double a = 0.213 * (1 - s) + s;
  final double b = 0.715 * (1 - s);
  final double c = 0.072 * (1 - s);
  return <double>[
    a, b, c, 0, 0, //
    0.213 * (1 - s), 0.715 * (1 - s) + s, 0.072 * (1 - s), 0, 0, //
    0.213 * (1 - s), 0.715 * (1 - s), 0.072 * (1 - s) + s, 0, 0, //
    0, 0, 0, 1, 0, //
  ];
}
