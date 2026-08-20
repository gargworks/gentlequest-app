import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/gq/gq_card.dart';

void main() {
  Widget host(Widget child) => MaterialApp(home: Scaffold(body: Center(child: child)));

  testWidgets('renders child and fires onTap', (tester) async {
    var tapped = false;
    await tester.pumpWidget(host(GQCard(onTap: () => tapped = true, child: const Text('Card content'))));
    expect(find.text('Card content'), findsOneWidget);
    await tester.tap(find.text('Card content'));
    await tester.pumpAndSettle();
    expect(tapped, isTrue);
  });

  testWidgets('non-tappable card (no onTap) renders without a GestureDetector tap handler', (tester) async {
    await tester.pumpWidget(host(const GQCard(child: Text('Static'))));
    expect(find.text('Static'), findsOneWidget);
  });

  testWidgets('isSelectable + selected draws without throwing', (tester) async {
    await tester.pumpWidget(host(GQCard(
      isSelectable: true,
      selected: true,
      onTap: () {},
      child: const Text('Selected'),
    )));
    expect(find.text('Selected'), findsOneWidget);
  });

  testWidgets('large uses the larger radius token without throwing', (tester) async {
    await tester.pumpWidget(host(const GQCard(large: true, child: Text('Large'))));
    expect(find.text('Large'), findsOneWidget);
  });
}
