import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/widgets/mood_reflection_sheet.dart';
import 'package:ai_buddy_web/widgets/mood_low_reflection_sheet.dart';

void main() {
  Widget host(Widget child) => MaterialApp(
        home: Scaffold(
          body: Builder(builder: (context) => child),
        ),
      );

  testWidgets('great-mood sheet has no streak/day-count badge (C4, non-negotiable)',
      (tester) async {
    await tester.pumpWidget(host(Builder(
      builder: (context) => ElevatedButton(
        onPressed: () => showMoodGreatReflectionSheet(context),
        child: const Text('open'),
      ),
    )));
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    expect(find.text('Love that. What worked today?'), findsOneWidget);
    // No streak surfaces of any kind.
    expect(find.textContaining('active days'), findsNothing);
    expect(find.textContaining('days total'), findsNothing);
    expect(find.text('🌱'), findsNothing);
    expect(find.text('🔥'), findsNothing);
  });

  testWidgets('great-mood sheet Save thought and Just close are present',
      (tester) async {
    await tester.pumpWidget(host(Builder(
      builder: (context) => ElevatedButton(
        onPressed: () => showMoodGreatReflectionSheet(context),
        child: const Text('open'),
      ),
    )));
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    expect(find.text('Save thought'), findsOneWidget);
    expect(find.text('Just close'), findsOneWidget);
  });

  testWidgets('low-mood sheet shows C2 exact copy and three actions',
      (tester) async {
    await tester.pumpWidget(host(Builder(
      builder: (context) => ElevatedButton(
        onPressed: () => showMoodLowReflectionSheet(context),
        child: const Text('open'),
      ),
    )));
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    expect(find.text('Logged. Heavy day, hm?'), findsOneWidget);
    expect(find.text('Talk to Alex for five minutes'), findsOneWidget);
    expect(find.text('Try one minute of breathing'), findsOneWidget);
    expect(find.text("Just close this — I'll come back"), findsOneWidget);
  });
}
