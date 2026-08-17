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
  testWidgets('shows task field and duration presets, defaults to 50 min',
      (WidgetTester tester) async {
    await tester.pumpWidget(_harness((_) {}));
    await tester.tap(find.text('open sheet'));
    await tester.pumpAndSettle();

    expect(find.text('Sit with company'), findsOneWidget);
    expect(find.byKey(const Key('body_double_task_field')), findsOneWidget);
    expect(find.text('25 min'), findsOneWidget);
    expect(find.text('50 min'), findsOneWidget);
    expect(find.text('When I leave'), findsOneWidget);
    expect(find.text('Sit down'), findsOneWidget);
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
    await tester.tap(find.text('25 min'));
    await tester.pump();

    await tester.tap(find.byKey(const Key('body_double_start_button')));
    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result!.task, 'tidy the kitchen');
    expect(result!.duration, const Duration(minutes: 25));
    expect(result!.wantsLive, isFalse);
  });

  testWidgets('Picking "With someone" tags the session as live-interest',
      (WidgetTester tester) async {
    BodyDoubleSessionConfig? result;
    await tester.pumpWidget(_harness((r) => result = r));
    await tester.tap(find.text('open sheet'));
    await tester.pumpAndSettle();

    // Not shown until the live chip is picked — no false promise up front.
    expect(find.textContaining("Live rooms aren't open yet"), findsNothing);

    await tester.tap(find.byKey(const Key('body_double_live_chip')));
    await tester.pump();
    expect(find.textContaining("Live rooms aren't open yet"), findsOneWidget);

    await tester.ensureVisible(find.byKey(const Key('body_double_start_button')));
    await tester.tap(find.byKey(const Key('body_double_start_button')));
    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result!.wantsLive, isTrue);
  });

  testWidgets('"Just me" stays selected by default and can be re-picked',
      (WidgetTester tester) async {
    BodyDoubleSessionConfig? result;
    await tester.pumpWidget(_harness((r) => result = r));
    await tester.tap(find.text('open sheet'));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('body_double_live_chip')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('body_double_solo_chip')));
    await tester.pump();
    expect(find.textContaining("Live rooms aren't open yet"), findsNothing);

    await tester.tap(find.byKey(const Key('body_double_start_button')));
    await tester.pumpAndSettle();

    expect(result!.wantsLive, isFalse);
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
