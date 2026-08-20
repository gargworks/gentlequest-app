import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/gq/gq_empty_state.dart';

void main() {
  Widget host(Widget child) => MaterialApp(home: Scaffold(body: child));

  testWidgets('renders illustration and line', (tester) async {
    await tester.pumpWidget(host(const GQEmptyState(
      illustration: Icon(Icons.eco),
      line: 'No entries yet',
    )));
    expect(find.byIcon(Icons.eco), findsOneWidget);
    expect(find.text('No entries yet'), findsOneWidget);
  });

  testWidgets('action renders and fires only when both label and callback are given', (tester) async {
    var tapped = false;
    await tester.pumpWidget(host(GQEmptyState(
      illustration: const Icon(Icons.eco),
      line: 'Empty',
      actionLabel: 'Add one',
      onAction: () => tapped = true,
    )));
    await tester.tap(find.text('Add one'));
    await tester.pumpAndSettle();
    expect(tapped, isTrue);
  });

  testWidgets('no action label/callback renders no action control', (tester) async {
    await tester.pumpWidget(host(const GQEmptyState(illustration: Icon(Icons.eco), line: 'Empty')));
    expect(find.byType(TextButton), findsNothing);
  });
}
