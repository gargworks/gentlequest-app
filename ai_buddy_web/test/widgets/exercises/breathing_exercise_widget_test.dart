import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/exercises/breathing_exercise_widget.dart';
import 'package:ai_buddy_web/models/interactive_exercise.dart';

void main() {
  testWidgets('BreathingExerciseWidget renders and starts', (WidgetTester tester) async {
    final exercise = BreathingExercise(
      name: 'Test Breath',
      description: 'Relax',
      steps: [
        BreathingStep(action: 'breathe_in', duration: 1, instruction: 'In'),
        BreathingStep(action: 'hold', duration: 1, instruction: 'Hold'),
        BreathingStep(action: 'breathe_out', duration: 1, instruction: 'Out'),
      ],
      cycles: 1,
      totalTimeSeconds: 3,
    );

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: BreathingExerciseWidget(exercise: exercise),
      ),
    ));

    // Verify initial state
    expect(find.text('Test Breath'), findsOneWidget);
    expect(find.text('Relax'), findsOneWidget);
    expect(find.text('Start (3s)'), findsOneWidget);

    // Tap start
    await tester.tap(find.text('Start (3s)'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    // Verify active state
    expect(find.text('Cycle 1 of 1'), findsOneWidget); // Progress indicator
    expect(find.text('In'), findsOneWidget); // Instruction
  });
}
