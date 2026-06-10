import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/branded_splash.dart';

void main() {
  testWidgets('BrandedSplash renders wordmark + breath circle', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: BrandedSplash()));

    expect(find.text('GentleQuest'), findsOneWidget);
    expect(find.byType(CustomPaint), findsWidgets);

    // Assert the brand gradient, not the wrapper widget type — the splash
    // background has already drifted Container -> DecoratedBox once.
    final decorated = tester.widget<DecoratedBox>(
      find.descendant(of: find.byType(Scaffold), matching: find.byType(DecoratedBox)).first,
    );
    final deco = decorated.decoration as BoxDecoration;
    final gradient = deco.gradient as LinearGradient;
    expect(gradient.colors.first, const Color(0xFFF8F7FF));
    expect(gradient.colors.last, const Color(0xFFEEF0FE));
  });

  testWidgets('BrandedSplash animates without throwing', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: BrandedSplash()));

    await tester.pump(const Duration(milliseconds: 100));
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pump(const Duration(milliseconds: 1200));
    await tester.pump(const Duration(milliseconds: 2400));

    expect(find.text('GentleQuest'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('BrandedSplash disposes cleanly', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: BrandedSplash()));
    await tester.pump(const Duration(milliseconds: 200));

    await tester.pumpWidget(const MaterialApp(home: SizedBox()));

    expect(tester.takeException(), isNull);
  });
}
