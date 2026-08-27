import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/mood_tracker_screen.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';

void main() {
  testWidgets('Legacy MoodTrackerScreen renders correctly',
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
        ],
        child: MaterialApp(
          home: MoodTrackerScreen(),
        ),
      ),
    );

    // Verify basic presence
    expect(find.byType(MoodTrackerScreen), findsOneWidget);

    // WO-5.2 Part B renamed the screen title from "Mood Tracker" to an
    // invitation ("Let's check in") -- deliberate, D6's "screen titles are
    // questions or invitations, never feature names." A loose
    // find.textContaining('Mood') no longer matches anything on first
    // render by design; assert the real current header instead.
    expect(find.text("Let's check in"), findsOneWidget);
  });
}
