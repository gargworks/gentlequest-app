import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/models/companion.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/widgets/companion_painter.dart';
import 'package:ai_buddy_web/widgets/companion_widget.dart';

void main() {
  group('CompanionWidget', () {
    /// Build a tree with a CompanionProvider seeded from [companion] so the
    /// widget under test renders deterministic state. Each testWidgets gets
    /// its own fresh SharedPreferences cache.
    ///
    /// Uses [tester.pump] instead of [tester.pumpAndSettle] because the
    /// breathing animation runs continuously and would prevent
    /// pumpAndSettle from ever settling.
    Future<void> buildWith(
      WidgetTester tester,
      Companion companion,
    ) async {
      SharedPreferences.setMockInitialValues({
        'gq.companion.v1': companion.encode(),
      });
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChangeNotifierProvider(
              create: (_) => CompanionProvider(),
              child: const CompanionWidget(),
            ),
          ),
        ),
      );
      // Let the provider's async _load() complete and the widget rebuild.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
    }

    Companion companionForStage(GrowthStage stage) {
      final xp = growthStageThresholds[stage]!;
      return Companion(
        level: Companion.levelForXp(xp),
        growthStage: stage,
        totalCheckIns: 10,
        totalActiveDays: 3,
        lifetimeXp: xp,
        name: 'Quest',
        mood: CompanionMood.content,
      );
    }

    /// Finder that matches a CustomPaint whose painter is a
    /// CompanionPainter for the given [stage].
    Finder painterForStage(GrowthStage stage) => find.byWidgetPredicate(
          (w) =>
              w is CustomPaint &&
              w.painter is CompanionPainter &&
              (w.painter as CompanionPainter).stage == stage,
        );

    // ── CompanionPainter per stage — one testWidgets per stage ─────────────

    testWidgets('renders CompanionPainter for seed stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.seed));
      expect(painterForStage(GrowthStage.seed), findsWidgets);
    });

    testWidgets('renders CompanionPainter for sprout stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.sprout));
      expect(painterForStage(GrowthStage.sprout), findsWidgets);
    });

    testWidgets('renders CompanionPainter for sapling stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.sapling));
      expect(painterForStage(GrowthStage.sapling), findsWidgets);
    });

    testWidgets('renders CompanionPainter for young stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.young));
      expect(painterForStage(GrowthStage.young), findsWidgets);
    });

    testWidgets('renders CompanionPainter for mature stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.mature));
      expect(painterForStage(GrowthStage.mature), findsWidgets);
    });

    // ── Tap interaction ─────────────────────────────────────────────────────

    testWidgets('tapping the companion shows an encouraging SnackBar', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.seed));

      // Tap the card (InkWell wraps the whole row).
      await tester.tap(find.byType(CompanionWidget));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // A SnackBar should appear with a non-empty message.
      final snackBar = tester.widget<SnackBar>(find.byType(SnackBar));
      expect(snackBar, isNotNull);
      // The SnackBar content is a Row with a CustomPaint + an Expanded Text.
      // Verify it has some text content (the encouraging message).
      final textWidgets = tester
          .widgetList<Text>(find.byType(Text))
          .where((t) => t.data != null && t.data!.isNotEmpty)
          .toList();
      expect(textWidgets, isNotEmpty);
    });

    // ── Anti-streak: total active days, not streak ──────────────────────────

    testWidgets('shows total active days (not a streak)', (tester) async {
      final c = companionForStage(GrowthStage.sprout).copyWith(totalActiveDays: 7);
      await buildWith(tester, c);

      expect(find.textContaining('7 active days'), findsOneWidget);
      // Anti-streak design: the word "streak" must never appear.
      expect(find.textContaining('streak'), findsNothing);
    });

    // ── Active days (not progress bar) ──────────────────────────────────────

    testWidgets('shows active days text (not XP bar)', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.seed));
      // Lv badge and XP progress bar removed per Fable #1a design spec
      expect(find.byType(LinearProgressIndicator), findsNothing);
      // Card shows stage name + active days instead
      expect(find.textContaining('active days'), findsOneWidget);
    });
  });
}
