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

  testWidgets('block variant renders full width with a caption and fires onSelected', (tester) async {
    bool? result;
    await tester.pumpWidget(host(SizedBox(
      width: 300,
      child: GQChip(
        variant: GQChipVariant.block,
        label: 'Not at all',
        caption: '0',
        selected: false,
        onSelected: (v) => result = v,
      ),
    )));
    expect(find.text('Not at all'), findsOneWidget);
    expect(find.text('0'), findsOneWidget);
    await tester.tap(find.text('Not at all'));
    await tester.pumpAndSettle();
    expect(result, isTrue);
  });

  testWidgets('block variant selected state renders without throwing', (tester) async {
    await tester.pumpWidget(host(SizedBox(
      width: 300,
      child: GQChip(
        variant: GQChipVariant.block,
        label: 'Nearly every day',
        selected: true,
        onSelected: (_) {},
      ),
    )));
    expect(find.text('Nearly every day'), findsOneWidget);
  });
}
