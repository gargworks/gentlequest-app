import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/gq/gq_chip.dart';

void main() {
  Widget host(Widget child) => MaterialApp(home: Scaffold(body: Center(child: child)));

  testWidgets('tapping an unselected chip calls onSelected(true)', (tester) async {
    bool? result;
    await tester.pumpWidget(host(GQChip(label: 'Mood', selected: false, onSelected: (v) => result = v)));
    await tester.tap(find.text('Mood'));
    await tester.pumpAndSettle();
    expect(result, isTrue);
  });

  testWidgets('tapping a selected chip calls onSelected(false)', (tester) async {
    bool? result;
    await tester.pumpWidget(host(GQChip(label: 'Mood', selected: true, onSelected: (v) => result = v)));
    await tester.tap(find.text('Mood'));
    await tester.pumpAndSettle();
    expect(result, isFalse);
  });

  testWidgets('emoji renders as plain text alongside the label', (tester) async {
    await tester.pumpWidget(host(GQChip(label: 'Sunny', selected: false, emoji: '☀️', onSelected: (_) {})));
    expect(find.text('☀️'), findsOneWidget);
    expect(find.text('Sunny'), findsOneWidget);
  });
}
