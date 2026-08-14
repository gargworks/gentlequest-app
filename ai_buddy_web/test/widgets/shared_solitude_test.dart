import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/models/companion.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/widgets/body_double/shared_solitude_space.dart';

void main() {
  group('SharedSolitudeSpace', () {
    /// Build the space inside a provider tree with a seeded
    /// CompanionProvider so the companion painter renders a deterministic
    /// growth stage. Uses [tester.pump] (not pumpAndSettle) because the
    /// breathing / glow animations run infinitely and would never settle.
    Future<void> buildSpace(
      WidgetTester tester, {
      String intention = 'draft the two emails',
      Duration total = const Duration(minutes: 50),
      VoidCallback? onDone,
    }) async {
      SharedPreferences.setMockInitialValues({
        'gq.companion.v1': Companion.fresh().encode(),
      });
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider(
            create: (_) => CompanionProvider(),
            child: SharedSolitudeSpace(
              intention: intention,
              total: total,
              onDone: onDone ?? () {},
            ),
          ),
        ),
      );
      // Let the entry animation play forward.
      await tester.pump(const Duration(milliseconds: 2000));
    }

    testWidgets('renders companion at 88px', (tester) async {
      await buildSpace(tester);
      final companionFinder = find.byKey(const Key('shared_solitude_companion'));
      expect(companionFinder, findsOneWidget);
      final size = tester.getSize(companionFinder);
      expect(size.width, 88);
      expect(size.height, 88);
    });

    testWidgets("renders 'Others are here too.'", (tester) async {
      await buildSpace(tester);
      expect(find.text('Others are here too.'), findsOneWidget);
    });

    testWidgets("renders 'Step out' button", (tester) async {
      await buildSpace(tester);
      expect(find.byKey(const Key('shared_solitude_step_out')), findsOneWidget);
      expect(find.text('Step out'), findsOneWidget);
    });

    testWidgets('no countdown/clock visible by default', (tester) async {
      await buildSpace(tester);
      // The whisper pill is hidden by default.
      expect(find.byKey(const Key('shared_solitude_whisper')), findsNothing);
      // No return overlay lines by default.
      expect(find.byKey(const Key('shared_solitude_return_line1')),
          findsNothing);
      expect(find.byKey(const Key('shared_solitude_return_line2')),
          findsNothing);
      // No "I'm done" / "Stay a while longer" by default.
      expect(find.byKey(const Key('shared_solitude_im_done')), findsNothing);
      expect(find.byKey(const Key('shared_solitude_stay_longer')),
          findsNothing);
    });

    testWidgets('pull-down (tap top area) shows elapsed time pill',
        (tester) async {
      await buildSpace(tester);
      // Tap the top area to trigger the whisper.
      await tester.tapAt(const Offset(200, 40));
      await tester.pump();
      expect(find.byKey(const Key('shared_solitude_whisper')), findsOneWidget);
    });

    testWidgets("return state shows 'That's the time you set aside.' and "
        "'The room keeps no record.'", (tester) async {
      // Use a 1-second total so the tick reaches it immediately.
      await buildSpace(tester, total: const Duration(seconds: 1));
      // Tick past the duration to trigger the return.
      await tester.pump(const Duration(seconds: 2));
      // The return transition starts; lines fade in at 20s. Pump past that.
      await tester.pump(const Duration(seconds: 21));
      expect(find.byKey(const Key('shared_solitude_return_line1')),
          findsOneWidget);
      expect(find.byKey(const Key('shared_solitude_return_line2')),
          findsOneWidget);
      expect(find.text("That's the time you set aside."), findsOneWidget);
      expect(find.text('The room keeps no record.'), findsOneWidget);
    });

    testWidgets("return state shows 'I'm done' and 'Stay a while longer' "
        'buttons', (tester) async {
      await buildSpace(tester, total: const Duration(seconds: 1));
      await tester.pump(const Duration(seconds: 2));
      await tester.pump(const Duration(seconds: 21));
      expect(find.byKey(const Key('shared_solitude_im_done')), findsOneWidget);
      expect(find.byKey(const Key('shared_solitude_stay_longer')),
          findsOneWidget);
      expect(find.text("I'm done"), findsOneWidget);
      expect(find.text('Stay a while longer'), findsOneWidget);
    });
  });
}
