import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/models/companion.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/widgets/companion_widget.dart';

/// Stage → emoji map mirrored from companion_widget.dart (kept private there,
/// so we restate it here for assertions).
const Map<GrowthStage, String> _kStageEmoji = {
  GrowthStage.seed: '🌱',
  GrowthStage.sprout: '🌿',
  GrowthStage.sapling: '🌳',
  GrowthStage.young: '🦊',
  GrowthStage.mature: '🦉',
};

void main() {
  group('CompanionWidget', () {
    /// Build a tree with a CompanionProvider seeded from [companion] so the
    /// widget under test renders deterministic state. Each testWidgets gets
    /// its own fresh SharedPreferences cache.
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
      await tester.pumpAndSettle();
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

    // ── Emoji per stage — one testWidgets per stage (fresh prefs cache) ──────

    testWidgets('renders 🌱 for seed stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.seed));
      expect(find.text(_kStageEmoji[GrowthStage.seed]!), findsWidgets);
    });

    testWidgets('renders 🌿 for sprout stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.sprout));
      expect(find.text(_kStageEmoji[GrowthStage.sprout]!), findsWidgets);
    });

    testWidgets('renders 🌳 for sapling stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.sapling));
      expect(find.text(_kStageEmoji[GrowthStage.sapling]!), findsWidgets);
    });

    testWidgets('renders 🦊 for young stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.young));
      expect(find.text(_kStageEmoji[GrowthStage.young]!), findsWidgets);
    });

    testWidgets('renders 🦉 for mature stage', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.mature));
      expect(find.text(_kStageEmoji[GrowthStage.mature]!), findsWidgets);
    });

    // ── Tap interaction ─────────────────────────────────────────────────────

    testWidgets('tapping the companion shows an encouraging SnackBar', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.seed));

      // Tap the card (InkWell wraps the whole row).
      await tester.tap(find.byType(CompanionWidget));
      await tester.pumpAndSettle();

      // A SnackBar should appear with a non-empty message.
      final snackBar = tester.widget<SnackBar>(find.byType(SnackBar));
      expect(snackBar, isNotNull);
      // The SnackBar content is a Row with an emoji Text + an Expanded Text.
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

    // ── Growth progress bar ─────────────────────────────────────────────────

    testWidgets('growth progress bar is visible', (tester) async {
      await buildWith(tester, companionForStage(GrowthStage.seed));
      expect(find.byType(LinearProgressIndicator), findsOneWidget);
    });
  });
}
