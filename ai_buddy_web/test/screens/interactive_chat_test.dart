import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/community_provider.dart';

Widget _buildTestApp() {
  return MultiProvider(
    providers: [
      ChangeNotifierProvider(create: (_) => ChatProvider()),
      ChangeNotifierProvider(
          create: (_) => MoodProvider(eagerLoad: false)),
      ChangeNotifierProvider(create: (_) => AssessmentProvider()),
      ChangeNotifierProvider(create: (_) => TaskProvider()),
      ChangeNotifierProvider(create: (_) => ProgressProvider()),
      ChangeNotifierProvider(create: (_) => QuestProvider()),
      ChangeNotifierProvider(create: (_) => CommunityProvider()),
    ],
    child: MaterialApp(
      home: InteractiveChatScreen(),
    ),
  );
}

void main() {
  testWidgets('InteractiveChatScreen has input field',
      (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(_buildTestApp());
    expect(find.byType(TextField), findsOneWidget);
  });

  testWidgets('Suggestion chips visible for new user',
      (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(_buildTestApp());
    // Let async greeting and flags load
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pump();

    // Should show conversation starter chips
    expect(find.text("I'm feeling anxious"), findsOneWidget);
    expect(find.text('Help me relax'), findsOneWidget);
    expect(find.text('I need to vent'), findsOneWidget);
    expect(find.text('Just chatting'), findsOneWidget);
  });

  testWidgets('Chat screen renders with greeting message',
      (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(_buildTestApp());
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pump();

    // ChatProvider inserts a greeting — screen should not be empty.
    // Verify the "Alex" header text exists (chat partner name).
    expect(find.text('Alex'), findsOneWidget);
  });
}
