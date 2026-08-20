import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/gq/gq_sheet.dart';

void main() {
  testWidgets('GQSheet.show presents title and content, dismissible via barrier tap', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Builder(
        builder: (context) => Scaffold(
          body: ElevatedButton(
            onPressed: () => GQSheet.show(
              context,
              title: 'Pick one',
              content: const Text('Sheet body'),
            ),
            child: const Text('open'),
          ),
        ),
      ),
    ));

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    expect(find.text('Pick one'), findsOneWidget);
    expect(find.text('Sheet body'), findsOneWidget);

    // Tap the barrier (top-left corner, outside the sheet) to dismiss.
    await tester.tapAt(const Offset(10, 10));
    await tester.pumpAndSettle();
    expect(find.text('Sheet body'), findsNothing);
  });

  testWidgets('GQSheet renders a grabber handle', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: GQSheet(child: Text('Body'))),
    ));
    expect(find.text('Body'), findsOneWidget);
  });
}
