import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/theme/gq_theme.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';

// WO-8 Part A — invariants for the mode-aware palette.
//
// Two failure modes are being guarded here, and they pull in opposite
// directions, which is why both halves are needed:
//
//   1. Landing dark mode QUIETLY CHANGES LIGHT MODE. The whole app ships in
//      light today; a stray edit to a light value is a live regression for
//      every user, not a dark-mode bug. The first group pins light to
//      GQColors exactly.
//   2. The extension is a NO-OP. If dark were accidentally built from the
//      light values, everything would still compile, analyze would stay
//      clean, and dark mode would simply render light — a silent nothing.
//      The second group asserts dark actually differs.
//
// Pinning light without asserting dark differs would pass against a no-op
// theme; asserting difference without pinning light would miss a light-mode
// regression. Neither test is redundant.
void main() {
  group('light mode is unchanged by dark-mode work', () {
    test('every light slot equals its GQColors constant', () {
      const l = GQTheme.light;

      expect(l.bg, GQColors.softBg);
      expect(l.surface, GQColors.surface);
      expect(l.surface2, GQColors.surface2);
      expect(l.ink, GQColors.ink);
      expect(l.ink2, GQColors.ink2);
      expect(l.ink3, GQColors.ink3);
      expect(l.hair, GQColors.hair);
      expect(l.primary, GQColors.primary);
      expect(l.primarySoft, GQColors.primarySoft);
      expect(l.coral, GQColors.coral);
      expect(l.accentSoft, GQColors.accentSoft);
      expect(l.inkOnCoral, GQColors.inkOnCoral);
      expect(l.amber, GQColors.amber);
      expect(l.amberSoft, GQColors.amberSoft);
      expect(l.inkOnAmber, GQColors.inkOnAmber);
      expect(l.successInk, GQColors.successInk);
      expect(l.successSoft, GQColors.successSoft);
      expect(l.dangerSoft, GQColors.dangerSoft);
      expect(l.warmSoft, GQColors.warmSoft);
      expect(l.illustrationOpacity, 1.0);
    });
  });

  group('dark mode is real, not a copy of light', () {
    test('surfaces and text actually invert', () {
      final d = GQTheme.dark;
      const l = GQTheme.light;

      expect(d.bg, isNot(l.bg));
      expect(d.surface, isNot(l.surface));
      expect(d.ink, isNot(l.ink));
      expect(d.ink2, isNot(l.ink2));
      expect(d.primary, isNot(l.primary),
          reason: 'dark uses the lifted primary for legibility');
    });

    test('illustration opacity is damped in dark', () {
      expect(GQTheme.dark.illustrationOpacity, lessThan(1.0));
    });

    test('ink3 is the one slot intentionally shared across modes', () {
      // Not an oversight: light-mode ink3 is barred below 14px (D3) because it
      // is too faint on white, but the same hex clears contrast on the dark
      // ground (~5.4:1) and is text-legal there. Same value, different rule.
      expect(GQTheme.dark.ink3, GQColors.ink3);
    });
  });

  group('CTA fills are invariant across modes', () {
    test('primaryDk and dangerInk are not reachable through the theme', () {
      // These carry white text (5.30:1 and 4.75:1) and one of them is the 988
      // crisis button. They have no slot in GQTheme deliberately, so there is
      // nowhere to put a dark variant — a future author must add a field to
      // vary them, which is a visible act in review rather than a one-character
      // edit. This test pins the values themselves so that even a change made
      // elsewhere has to walk past a failing assertion.
      expect(GQColors.primaryDk, const Color(0xFF4F63C9));
      expect(GQColors.dangerInk, const Color(0xFFC44A4A));
    });
  });

  group('resolution', () {
    testWidgets('of() returns the registered extension', (tester) async {
      late GQTheme resolved;
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(extensions: const <ThemeExtension<dynamic>>[GQTheme.light]),
          home: Builder(builder: (context) {
            resolved = GQTheme.of(context);
            return const SizedBox.shrink();
          }),
        ),
      );
      expect(resolved.bg, GQColors.softBg);
    });

    testWidgets('of() falls back to light with no extension registered',
        (tester) async {
      // A widget pumped bare in a test, or rendered in a detached overlay,
      // must degrade to today's appearance rather than throw.
      late GQTheme resolved;
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(builder: (context) {
            resolved = GQTheme.of(context);
            return const SizedBox.shrink();
          }),
        ),
      );
      expect(resolved.bg, GQColors.softBg);
      expect(resolved.illustrationOpacity, 1.0);
    });
  });

  group('lerp', () {
    test('endpoints are exact, so a mode switch cannot land off-palette', () {
      final mid = GQTheme.light.lerp(GQTheme.dark, 0.0) as GQTheme;
      expect(mid.bg, GQTheme.light.bg);

      final end = GQTheme.light.lerp(GQTheme.dark, 1.0) as GQTheme;
      expect(end.bg, GQTheme.dark.bg);
    });

    test('lerp against a foreign extension returns self rather than throwing',
        () {
      expect(GQTheme.light.lerp(null, 0.5), GQTheme.light);
    });
  });
}
