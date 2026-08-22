import 'package:ai_buddy_web/models/message.dart';
import 'package:ai_buddy_web/screens/rumination_reset_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  Widget host({
    required LoopResetReporter reporter,
    LoopResetCrisisHandler? crisisHandler,
  }) {
    return MaterialApp(
      home: RuminationResetScreen(
        reportOutcome: reporter,
        showCrisis: crisisHandler,
      ),
    );
  }

  Future<void> tapVisible(WidgetTester tester, Finder finder) async {
    await tester.ensureVisible(finder);
    await tester.pump();
    await tester.tap(finder);
    await tester.pumpAndSettle();
  }

  Future<void> enterConcreteFacts(WidgetTester tester, {String? event}) async {
    await tester.enterText(
      find.byKey(const ValueKey('event_field')),
      event ?? 'The meeting ended at 3 PM after my proposal was declined.',
    );
    await tester.enterText(
      find.byKey(const ValueKey('control_field')),
      'I can send one clear follow-up question.',
    );
    await tester.enterText(
      find.byKey(const ValueKey('outcome_field')),
      'Know the next decision criterion.',
    );
  }

  testWidgets('finite flow reports structured start and completion',
      (tester) async {
    final reports = <String>[];
    await tester.pumpWidget(host(
      reporter: (outcome, seconds) async => reports.add('$outcome:$seconds'),
    ));

    await tester.tap(find.text('Start the reset'));
    await tester.pumpAndSettle();
    await enterConcreteFacts(tester);
    await tapVisible(tester, find.text('Choose one exit'));

    await tapVisible(tester, find.text('Do one small thing'));
    await tester.enterText(
      find.byKey(const ValueKey('resolution_field')),
      'Send the one-sentence follow-up question.',
    );
    await tapVisible(tester, find.text('Use this exit'));

    expect(
        find.text('Send the one-sentence follow-up question.'), findsOneWidget);
    expect(find.textContaining('continue exploring'), findsNothing);

    await tapVisible(tester, find.text('Leave and do it'));

    expect(reports.map((entry) => entry.split(':').first),
        containsAllInOrder(['started', 'completed']));
  });

  testWidgets('close reports skip without requiring reflection',
      (tester) async {
    final reports = <String>[];
    await tester.pumpWidget(host(
      reporter: (outcome, seconds) async => reports.add(outcome),
    ));

    await tester.tap(find.text('Close'));
    await tester.pumpAndSettle();

    expect(reports, ['skipped']);
  });

  testWidgets('system back reports skip and exits', (tester) async {
    final reports = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: Builder(
        builder: (context) => ElevatedButton(
          onPressed: () => Navigator.of(context).push<void>(
            MaterialPageRoute(
              builder: (_) => RuminationResetScreen(
                reportOutcome: (outcome, seconds) async => reports.add(outcome),
              ),
            ),
          ),
          child: const Text('open'),
        ),
      ),
    ));

    await tester.tap(find.text('open'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    await tester.tap(find.text('Start the reset'));
    await tester.pumpAndSettle();
    await tester.pageBack();
    await tester.pumpAndSettle();

    expect(find.text('open'), findsOneWidget);
    expect(reports, containsAllInOrder(['started', 'skipped']));
  });

  testWidgets('concrete fields must all be present', (tester) async {
    final reports = <String>[];
    await tester.pumpWidget(host(
      reporter: (outcome, seconds) async => reports.add(outcome),
    ));

    await tester.tap(find.text('Start the reset'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('event_field')),
      'One observable fact.',
    );
    await tester.tap(find.text('Choose one exit'));
    await tester.pump();

    expect(find.byKey(const ValueKey('concrete')), findsOneWidget);
    expect(find.textContaining('fill in all three'), findsOneWidget);
    await tester.pump(const Duration(seconds: 5));
  });

  testWidgets('tier one language preempts the exercise', (tester) async {
    final reports = <String>[];
    RiskLevel? risk;
    await tester.pumpWidget(host(
      reporter: (outcome, seconds) async => reports.add(outcome),
      crisisHandler: (context, value) async => risk = value,
    ));

    await tester.tap(find.text('Start the reset'));
    await tester.pumpAndSettle();
    await enterConcreteFacts(tester, event: 'I want to kill myself tonight.');
    await tapVisible(tester, find.text('Choose one exit'));

    expect(risk, RiskLevel.crisis);
    expect(reports, containsAllInOrder(['started', 'skipped']));
    expect(find.byKey(const ValueKey('resolution')), findsNothing);
  });

  testWidgets('tier two language uses the high-risk intervention',
      (tester) async {
    final reports = <String>[];
    RiskLevel? risk;
    await tester.pumpWidget(host(
      reporter: (outcome, seconds) async => reports.add(outcome),
      crisisHandler: (context, value) async => risk = value,
    ));

    await tester.tap(find.text('Start the reset'));
    await tester.pumpAndSettle();
    await enterConcreteFacts(tester,
        event: 'I feel hopeless after the meeting.');
    await tapVisible(tester, find.text('Choose one exit'));

    expect(risk, RiskLevel.high);
    expect(reports, contains('skipped'));
  });

  testWidgets('free text remains outside the outcome reporter', (tester) async {
    final outcomes = <String>[];
    await tester.pumpWidget(host(
      reporter: (outcome, seconds) async => outcomes.add(outcome),
    ));

    await tester.tap(find.text('Start the reset'));
    await tester.pumpAndSettle();
    await enterConcreteFacts(tester, event: 'private-event-token');
    await tapVisible(tester, find.text('Choose one exit'));
    await tapVisible(tester, find.text('Name what is missing'));
    await tester.enterText(
      find.byKey(const ValueKey('resolution_field')),
      'private-missing-fact-token',
    );
    await tapVisible(tester, find.text('Use this exit'));
    await tapVisible(tester, find.text('Leave and do it'));

    expect(outcomes.join(' '), isNot(contains('private-event-token')));
    expect(outcomes.join(' '), isNot(contains('private-missing-fact-token')));
  });
}
