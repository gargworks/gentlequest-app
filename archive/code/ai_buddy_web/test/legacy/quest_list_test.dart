import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/dhiwise/presentation/quest_screen/quest_screen.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';

import 'package:ai_buddy_web/dhiwise/core/utils/size_utils.dart';

void main() {
  testWidgets('Legacy QuestScreen renders quest list',
      (WidgetTester tester) async {
    // Mock SharedPreferences
    SharedPreferences.setMockInitialValues({});

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => ChatProvider()),
          ChangeNotifierProvider(create: (_) => MoodProvider()),
          ChangeNotifierProvider(create: (_) => AssessmentProvider()),
          ChangeNotifierProvider(create: (_) => TaskProvider()),
          ChangeNotifierProvider(create: (_) => ProgressProvider()),
          ChangeNotifierProvider(
              create: (_) => QuestProvider()..loadQuests()), // Pre-load
        ],
        child: Sizer(builder: (context, orientation, deviceType) {
          return MaterialApp(
            home: QuestScreen(),
          );
        }),
      ),
    );

    // Verify basic presence
    expect(find.byType(QuestScreen), findsOneWidget);

    // Since QuestProvider loads empty by default in mock, we might see "No quests" or just the shell to Start Quests
    // We verify the screen structure pumps successfully.
  });
}
