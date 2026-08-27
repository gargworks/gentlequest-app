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

Widget _buildTestApp() {
  return MultiProvider(
    providers: [
      ChangeNotifierProvider(create: (_) => ChatProvider()),
      ChangeNotifierProvider(
          create: (_) => MoodProvider(eagerLoad: false)),
      ChangeNotifierProvider(create: (_) => AssessmentProvider()),
      ChangeNotifierProvider(create: (_) => TaskProvider()),
      ChangeNotifierProvider(create: (_) => ProgressProvider()),
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

    // Should show R1D6 conversation starter chips. Order matches the
    // post-2026-05-21 reorder (lead with most-neutral; see
    // interactive_chat_screen.dart starters list).
    expect(find.text('Just need someone to listen'), findsOneWidget);
    expect(find.text('I want to vent a little'), findsOneWidget);
    expect(find.text("Today's been heavy"), findsOneWidget);
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
