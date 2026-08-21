import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/screens/mood_tracker_screen.dart';

/// WO-5.2 A4 regression test: the 800ms auto-advance is deleted, not
/// tuned. A mood tap must select only -- it must never, on its own,
/// submit or dismiss the sheet. Only the "Log this" CTA commits.
void main() {
  Widget buildScreen() {
    return MultiProvider(
      providers: [ChangeNotifierProvider(create: (_) => MoodProvider())],
      child: const MaterialApp(home: MoodTrackerScreen()),
    );
  }

  testWidgets('the 5 D2 canonical mood labels are present, no 6th option',
      (tester) async {
    await tester.pumpWidget(buildScreen());
    await tester.pumpAndSettle();
    await tester.tap(find.text('How are you, right now?'));
    await tester.pumpAndSettle();

    for (final label in ['Rough', 'Meh', 'Okay', 'Good', 'Great']) {
      expect(find.text(label), findsOneWidget, reason: 'missing label $label');
    }
    // No sixth option / no "Angry" anywhere.
    expect(find.text('Angry'), findsNothing);
  });

  testWidgets('Log this CTA is disabled until a mood is tapped, no countdown UI ever appears',
      (tester) async {
    await tester.pumpWidget(buildScreen());
    await tester.pumpAndSettle();
    await tester.tap(find.text('How are you, right now?'));
    await tester.pumpAndSettle();

    expect(find.text('Log this'), findsOneWidget);
    // No auto-advance countdown/cancel UI exists anywhere in the tree.
    expect(find.textContaining('Submitting in'), findsNothing);
    expect(find.text('Cancel'), findsNothing);

    // Tap a mood tile.
    await tester.tap(find.text('Good'));
    await tester.pump();

    // 900ms > the old 800ms auto-advance window -- sheet must still be
    // open and showing the CTA, not auto-dismissed/auto-submitted.
    await tester.pump(const Duration(milliseconds: 900));
    expect(find.text('Log this'), findsOneWidget);
    expect(find.text('Good'), findsOneWidget);
  });

  testWidgets('explicit Skip — just close affordance is present and closes the sheet',
      (tester) async {
    await tester.pumpWidget(buildScreen());
    await tester.pumpAndSettle();
    await tester.tap(find.text('How are you, right now?'));
    await tester.pumpAndSettle();

    expect(find.text('Skip — just close'), findsOneWidget);
    await tester.tap(find.text('Skip — just close'));
    await tester.pumpAndSettle();
    expect(find.text('Log this'), findsNothing);
  });
}
