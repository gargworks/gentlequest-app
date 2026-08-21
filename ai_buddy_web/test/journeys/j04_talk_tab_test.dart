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

    // "profile avatar icon" tests removed (WO-6.1): the avatar entry point
    // and profile_nav_sheet.dart it opened were deleted — the You tab is
    // now the only way into Profile. Removed rather than left to flap.

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
