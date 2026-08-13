import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/screens/onboarding_vow_screen.dart';

void main() {
  group('OnboardingVowScreen', () {
    Future<void> buildWith(WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({});
      await tester.pumpWidget(
        const MaterialApp(
          home: OnboardingVowScreen(),
        ),
      );
      // Pump a few frames so the initial state settles.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));
    }

    testWidgets('all 5 vow lines are present in the widget tree',
        (tester) async {
      await buildWith(tester);
      // The vow lines are defined as constants; verify they are reachable
      // by advancing the animation to completion (Skip) and checking text.
      await tester.tap(find.text('Skip'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.text('This is your companion.'), findsOneWidget);
      expect(find.text('It will wait for you.'), findsOneWidget);
      expect(find.text('It never punishes.'), findsOneWidget);
      expect(find.text('What you say here stays here.'), findsOneWidget);
      // The 988 line is rendered as RichText (988 in coral), so we check
      // for its parts via RichText content rather than find.textContaining.
      final richTexts = tester.widgetList<RichText>(find.byType(RichText));
      bool found988Line = false;
      for (final rt in richTexts) {
        final span = rt.text;
        if (span is TextSpan) {
          final fullText = _spanToText(span);
          if (fullText.contains('If it gets bad') &&
              fullText.contains('is always one tap away')) {
            found988Line = true;
          }
        }
      }
      expect(found988Line, isTrue);
    });

    testWidgets('Begin button is present after Skip', (tester) async {
      await buildWith(tester);
      await tester.tap(find.text('Skip'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.text('Begin'), findsOneWidget);
    });

    testWidgets('Skip button is present from first frame', (tester) async {
      await buildWith(tester);
      expect(find.text('Skip'), findsOneWidget);
    });

    testWidgets('seed companion is present after Skip', (tester) async {
      await buildWith(tester);
      await tester.tap(find.text('Skip'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      // The seed is rendered via CompanionPainter inside a CustomPaint.
      expect(
        find.byWidgetPredicate(
          (w) =>
              w is CustomPaint &&
              w.painter != null &&
              w.painter.toString().contains('CompanionPainter'),
        ),
        findsOneWidget,
      );
    });

    testWidgets('988 appears in coral color (the only color in the sequence)',
        (tester) async {
      await buildWith(tester);
      await tester.tap(find.text('Skip'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      // Find the RichText containing '988' and verify the 988 TextSpan
      // uses the coral color.
      final richTexts = tester.widgetList<RichText>(find.byType(RichText));
      bool foundCoral988 = false;
      for (final rt in richTexts) {
        final span = rt.text;
        if (span is TextSpan) {
          span.visitChildren((child) {
            if (child is TextSpan &&
                child.text == '988' &&
                child.style?.color == const Color(0xFFFF6B6B)) {
              foundCoral988 = true;
            }
            return true;
          });
        }
      }
      expect(foundCoral988, isTrue);
    });

    testWidgets('gradient background is present', (tester) async {
      await buildWith(tester);
      final container = tester.widget<Container>(find.byType(Container).first);
      final decoration = container.decoration;
      expect(decoration, isA<BoxDecoration>());
      final bd = decoration as BoxDecoration;
      expect(bd.gradient, isA<LinearGradient>());
      final lg = bd.gradient as LinearGradient;
      expect(lg.colors.length, 3);
    });
  });
}

/// Recursively flattens a TextSpan tree into a single string.
String _spanToText(TextSpan span) {
  final buf = StringBuffer(span.text ?? '');
  for (final child in span.children ?? <InlineSpan>[]) {
    if (child is TextSpan) {
      buf.write(_spanToText(child));
    }
  }
  return buf.toString();
}
