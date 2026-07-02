import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/models/body_double_session.dart';
import 'package:ai_buddy_web/widgets/body_double/body_double_start_sheet.dart';

Widget _harness(void Function(BodyDoubleSessionConfig?) onResult) {
  return MaterialApp(
    home: Scaffold(
      body: Builder(
        builder: (context) => ElevatedButton(
          onPressed: () async {
            final result = await showBodyDoubleStartSheet(context);
            onResult(result);
          },
          child: const Text('open sheet'),
        ),
      ),
    ),
  );
}

void main() {
  testWidgets('shows task field and duration presets, defaults to 10 min',
      (WidgetTester tester) async {
    await tester.pumpWidget(_harness((_) {}));
    await tester.tap(find.text('open sheet'));
    await tester.pumpAndSettle();

    expect(find.text('Focus together'), findsOneWidget);
    expect(find.byKey(const Key('body_double_task_field')), findsOneWidget);
    for (final minutes in kBodyDoubleDurationPresetsMinutes) {
      expect(find.text('$minutes min'), findsOneWidget);
    }
    expect(find.text('Start 10-minute session'), findsOneWidget);
  });

  testWidgets('Start returns the entered task and selected duration',
      (WidgetTester tester) async {
    BodyDoubleSessionConfig? result;
    await tester.pumpWidget(_harness((r) => result = r));
    await tester.tap(find.text('open sheet'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('body_double_task_field')),
      'tidy the kitchen',
    );
    await tester.tap(find.text('5 min'));
    await tester.pump();
    expect(find.text('Start 5-minute session'), findsOneWidget);

    await tester.tap(find.byKey(const Key('body_double_start_button')));
    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result!.task, 'tidy the kitchen');
    expect(result!.duration, const Duration(minutes: 5));
  });

  testWidgets('Start with an empty task falls back to a safe default',
      (WidgetTester tester) async {
    BodyDoubleSessionConfig? result;
    await tester.pumpWidget(_harness((r) => result = r));
    await tester.tap(find.text('open sheet'));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('body_double_start_button')));
    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result!.task, 'this');
  });

  testWidgets('Close button dismisses without a result',
      (WidgetTester tester) async {
    var called = false;
    BodyDoubleSessionConfig? result;
    await tester.pumpWidget(_harness((r) {
      called = true;
      result = r;
    }));
    await tester.tap(find.text('open sheet'));
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.close));
    await tester.pumpAndSettle();

    expect(called, isTrue);
    expect(result, isNull);
  });
}
