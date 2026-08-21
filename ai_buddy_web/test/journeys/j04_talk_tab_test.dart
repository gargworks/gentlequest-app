import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'test_helpers.dart';

void main() {
  group('J04: Talk tab — InteractiveChatScreen', () {
    setUp(setUpBypassedPrefs);

    Widget buildChat() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => ChatProvider()),
          ChangeNotifierProvider(create: (_) => MoodProvider()),
          ChangeNotifierProvider(create: (_) => QuestProvider()),
          ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ],
        child: const MaterialApp(home: InteractiveChatScreen()),
      );
    }

    testWidgets('InteractiveChatScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildChat());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.byType(InteractiveChatScreen), findsOneWidget);
    });

    testWidgets('text input field is present', (tester) async {
      await tester.pumpWidget(buildChat());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.byType(TextField), findsAtLeast(1));
    });

    testWidgets('profile avatar icon is present in header', (tester) async {
      await tester.pumpWidget(buildChat());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byIcon(Icons.account_circle_outlined), findsOneWidget);
    });

    testWidgets('profile avatar tap does not crash', (tester) async {
      await tester.pumpWidget(buildChat());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.byIcon(Icons.account_circle_outlined));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('voice input accessibility label is present', (tester) async {
      await tester.pumpWidget(buildChat());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(
        find.bySemanticsLabel('Start voice input'),
        findsOneWidget,
      );
    });
  });
}
