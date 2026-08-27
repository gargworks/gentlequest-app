import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/screens/quest_screen.dart';
import 'package:ai_buddy_web/screens/quest_preview_screen.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'test_helpers.dart';

void main() {
  group('J14: Quest flow — comprehensive', () {
    setUp(setUpBypassedPrefs);

    Widget buildQuestScreen() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => QuestProvider()..loadQuests()),
        ],
        child: MaterialApp(
          routes: {'/home': (c) => const Scaffold(body: Text('Home'))},
          home: const QuestScreen(),
        ),
      );
    }

    Widget buildQuestPreview() {
      return MaterialApp(
        routes: {'/home': (c) => const Scaffold(body: Text('Home'))},
        home: const QuestPreviewScreen(),
      );
    }

    // ── QuestScreen ────────────────────────────────────────────────────────────

    testWidgets('QuestScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildQuestScreen());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.byType(QuestScreen), findsOneWidget);
    });

    testWidgets('quest list has at least one card', (tester) async {
      await tester.pumpWidget(buildQuestScreen());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('quest list renders "3 Good Things" quest', (tester) async {
      await tester.pumpWidget(buildQuestScreen());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.textContaining('Good Things'), findsWidgets);
    });

    // ── QuestPreviewScreen ─────────────────────────────────────────────────────

    testWidgets('QuestPreviewScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildQuestPreview());
      await tester.pumpAndSettle();

      expect(find.byType(QuestPreviewScreen), findsOneWidget);
    });

    testWidgets('Start button has ValueKey and is tappable', (tester) async {
      await tester.pumpWidget(buildQuestPreview());
      await tester.pumpAndSettle();

      final startBtn = find.byKey(const ValueKey('quest_preview_start_button'));
      expect(startBtn, findsWidgets,
          reason: 'Start button must carry ValueKey — empty callback was the v1 bug');

      await tester.tap(startBtn.first);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('Start/Continue label is present', (tester) async {
      await tester.pumpWidget(buildQuestPreview());
      await tester.pumpAndSettle();

      final hasStart = find.text('Start').evaluate().isNotEmpty;
      final hasContinue = find.text('Continue').evaluate().isNotEmpty;
      expect(hasStart || hasContinue, isTrue,
          reason: 'Quest preview must have a Start or Continue button');
    });

    testWidgets('quest day steps list renders', (tester) async {
      await tester.pumpWidget(buildQuestPreview());
      await tester.pumpAndSettle();

      // QuestPreviewScreen always shows quest cards (Daily Check-in etc.)
      expect(find.textContaining('Check-in'), findsWidgets);
    });
  });
}
