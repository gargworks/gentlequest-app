import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/body_double/body_double_timer_bar.dart';

void main() {
  testWidgets('BodyDoubleTimerBar renders task, countdown, and progress',
      (WidgetTester tester) async {
    var endTapped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: BodyDoubleTimerBar(
            task: 'tidy the kitchen',
            remaining: const Duration(minutes: 2, seconds: 30),
            total: const Duration(minutes: 5),
            onEndSession: () => endTapped = true,
          ),
        ),
      ),
    );

    expect(find.text('tidy the kitchen'), findsOneWidget);
    expect(find.text('02:30'), findsOneWidget);
    expect(find.text('End session'), findsOneWidget);

    final progressBar = tester.widget<LinearProgressIndicator>(
      find.byType(LinearProgressIndicator),
    );
    // 2:30 remaining of 5:00 total => 50% elapsed.
    expect(progressBar.value, closeTo(0.5, 0.001));

    await tester.tap(find.text('End session'));
    await tester.pump();
    expect(endTapped, isTrue);
  });

  testWidgets('BodyDoubleTimerBar clamps negative remaining to 00:00',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: BodyDoubleTimerBar(
            task: 'stretch',
            remaining: const Duration(seconds: -1),
            total: const Duration(minutes: 5),
            onEndSession: () {},
          ),
        ),
      ),
    );

    expect(find.text('00:00'), findsOneWidget);
  });
}
