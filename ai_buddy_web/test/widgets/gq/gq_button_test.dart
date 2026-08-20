import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/gq/gq_button.dart';

void main() {
  Widget host(Widget child) => MaterialApp(home: Scaffold(body: Center(child: child)));

  testWidgets('tap fires onPressed', (tester) async {
    var tapped = false;
    await tester.pumpWidget(host(GQButton(label: 'Go', onPressed: () => tapped = true)));
    await tester.tap(find.text('Go'));
    await tester.pumpAndSettle();
    expect(tapped, isTrue);
  });

  testWidgets('null onPressed renders disabled and does not fire on tap', (tester) async {
    await tester.pumpWidget(host(const GQButton(label: 'Disabled', onPressed: null)));
    await tester.tap(find.text('Disabled'));
    await tester.pumpAndSettle();
    // No exception, no crash — a disabled button silently ignores the tap.
    expect(find.text('Disabled'), findsOneWidget);
  });

  testWidgets('isLoading suppresses tap and shows a progress indicator', (tester) async {
    var tapped = false;
    await tester.pumpWidget(host(GQButton(label: 'Save', onPressed: () => tapped = true, loading: true)));
    await tester.tap(find.byType(GQButton));
    // Not pumpAndSettle: CircularProgressIndicator animates indefinitely.
    await tester.pump();
    expect(tapped, isFalse);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('every variant renders without throwing', (tester) async {
    for (final variant in GQButtonVariant.values) {
      await tester.pumpWidget(host(GQButton(label: variant.name, onPressed: () {}, variant: variant)));
      await tester.pump();
      expect(find.text(variant.name), findsOneWidget);
    }
  });
}
