import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/screens/settings_screen.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/community_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'test_helpers.dart';

void main() {
  group('J08: Profile avatar → settings navigation', () {
    setUp(setUpBypassedPrefs);

    Widget buildChatScreen() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => ChatProvider()),
          ChangeNotifierProvider(create: (_) => MoodProvider()),
          ChangeNotifierProvider(create: (_) => QuestProvider()),
          ChangeNotifierProvider(create: (_) => CommunityProvider()),
          ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ],
        child: const MaterialApp(
          home: InteractiveChatScreen(),
        ),
      );
    }

    testWidgets('Chat header contains profile avatar icon', (tester) async {
      await tester.pumpWidget(buildChatScreen());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byIcon(Icons.account_circle_outlined), findsOneWidget);
    });

    testWidgets('Profile avatar tap does not crash', (tester) async {
      await tester.pumpWidget(buildChatScreen());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      final avatar = find.byIcon(Icons.account_circle_outlined);
      expect(avatar, findsOneWidget);
      await tester.tap(avatar);
      // Use pump with duration — bottom sheet may have animations that won't settle
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump(const Duration(milliseconds: 500));

      expect(tester.takeException(), isNull);
    });

    testWidgets('SettingsScreen renders without crash', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: SettingsScreen()));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byType(SettingsScreen), findsOneWidget);
    });
  });
}
