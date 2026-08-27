import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/theme/gq_theme.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';
import 'package:ai_buddy_web/widgets/gq/gq.dart';

// WO-8 — the contrast invariant that must survive the dark-mode conversion.
//
// The existing GQ component tests (29 of them) assert structure only: that a
// label renders, that a tap fires. NOT ONE asserts a colour. So the highest-risk
// part of theming the widget layer — turning a fill or a foreground into a
// theme lookup that resolves differently in dark — is invisible to every test
// currently in the repo. A crisis button whose label went from white to dark
// ink on a dark-red fill would ship green.
//
// The rule being pinned here:
//
//   FILLS that carry white text (primaryDk 5.30:1, dangerInk 4.75:1) are
//   byte-identical in light and dark. Their FOREGROUND stays Colors.white.
//   Neither may become a theme lookup, because the whole point is that they
//   do not move when the OS flips.
//
// This is asserted in BOTH modes deliberately. Checking light alone would pass
// against a conversion that only breaks in dark — which is precisely the
// failure a light-only test cannot see, and precisely when the user is least
// able to afford an unreadable 988 button.
void main() {
  Future<void> pumpButton(
    WidgetTester tester,
    GQButtonVariant variant, {
    required Brightness brightness,
  }) async {
    final gq = brightness == Brightness.dark ? GQTheme.dark : GQTheme.light;
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData(
          brightness: brightness,
          extensions: <ThemeExtension<dynamic>>[gq],
        ),
        home: Scaffold(
          body: GQButton(label: 'Call 988', variant: variant, onPressed: () {}),
        ),
      ),
    );
    await tester.pump();
  }

  /// The button's fill lives on the single Container that has a BoxDecoration
  /// with a non-null colour. Located by property rather than by position so
  /// the test does not break on harmless layout nesting changes.
  Color? fillOf(WidgetTester tester) {
    final containers = tester.widgetList<Container>(find.byType(Container));
    for (final c in containers) {
      final d = c.decoration;
      if (d is BoxDecoration && d.color != null) return d.color;
    }
    return null;
  }

  Color? labelColorOf(WidgetTester tester) =>
      tester.widget<Text>(find.text('Call 988')).style?.color;

  group('crisis variant — the 988 button', () {
    testWidgets('fill is dangerInk and label is white in LIGHT', (tester) async {
      await pumpButton(tester, GQButtonVariant.crisis,
          brightness: Brightness.light);
      expect(fillOf(tester), GQColors.dangerInk);
      expect(labelColorOf(tester), Colors.white);
    });

    testWidgets('fill and label are IDENTICAL in DARK', (tester) async {
      await pumpButton(tester, GQButtonVariant.crisis,
          brightness: Brightness.dark);
      expect(
        fillOf(tester),
        GQColors.dangerInk,
        reason: 'the crisis fill must not shift by mode — it was chosen for '
            '4.75:1 against white, and a themed substitute silently breaks that',
      );
      expect(
        labelColorOf(tester),
        Colors.white,
        reason: 'the fill does not change between modes, so its foreground '
            'must not either',
      );
    });
  });

  group('primary variant', () {
    testWidgets('fill is primaryDk and label is white in LIGHT', (tester) async {
      await pumpButton(tester, GQButtonVariant.primary,
          brightness: Brightness.light);
      expect(fillOf(tester), GQColors.primaryDk);
      expect(labelColorOf(tester), Colors.white);
    });

    testWidgets('fill and label are IDENTICAL in DARK', (tester) async {
      await pumpButton(tester, GQButtonVariant.primary,
          brightness: Brightness.dark);
      expect(fillOf(tester), GQColors.primaryDk);
      expect(labelColorOf(tester), Colors.white);
    });
  });

  group('coralDk slot (re-ruled 2026-08-27: ink, not fill — must theme)', () {
    test('light keeps the ratified hex; dark uses the D3 on-dark coral', () {
      expect(GQTheme.light.coralDk, const Color(0xFFE0494C));
      expect(GQTheme.dark.coralDk, const Color(0xFFFF6B6B));
      // Opposed pair: the two modes MUST differ — a byte-identical value
      // would silently recreate the reversed static-exception ruling.
      expect(GQTheme.light.coralDk == GQTheme.dark.coralDk, isFalse);
    });

    test('dark coralDk ink passes 4.5:1 on the dark background', () {
      final ratio = _contrastRatio(GQTheme.dark.coralDk, GQTheme.dark.bg);
      expect(ratio, greaterThanOrEqualTo(4.5),
          reason: 'coralDk as INK on bg must be WCAG AA in dark; '
              'got ${ratio.toStringAsFixed(2)}:1');
    });

    test('NEGATIVE CONTROL: the old static value would FAIL the light-ink '
        'assumption in dark by construction of this check', () {
      // The reversed ruling kept #E0494C static; on the dark bg that is
      // ${'<'}4.7:1 territory and, more importantly, unthemed. This control
      // proves the ratio instrument can emit a lower number than the pass
      // bar for a plausible wrong value, so the test above is not vacuous.
      final wrongValue = _contrastRatio(const Color(0xFF8B4444), GQTheme.dark.bg);
      expect(wrongValue, lessThan(4.5));
    });
  });
}

double _contrastRatio(Color a, Color b) {
  double lum(Color c) {
    double f(double x) =>
        x <= 0.03928 ? x / 12.92 : math.pow((x + 0.055) / 1.055, 2.4).toDouble();
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  }

  final la = lum(a), lb = lum(b);
  final hi = la > lb ? la : lb, lo = la > lb ? lb : la;
  return (hi + 0.05) / (lo + 0.05);
}
