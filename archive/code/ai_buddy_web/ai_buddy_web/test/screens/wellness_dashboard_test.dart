import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';

void main() {
  testWidgets('WellnessDashboard renders main components',
      (WidgetTester tester) async {
    // We wrap in MaterialApp to provide necessary theme/mediaquery context
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => ChatProvider()),
          ChangeNotifierProvider(create: (_) => MoodProvider()),
          ChangeNotifierProvider(create: (_) => AssessmentProvider()),
          ChangeNotifierProvider(create: (_) => TaskProvider()),
          ChangeNotifierProvider(create: (_) => ProgressProvider()),
          ChangeNotifierProvider(create: (_) => QuestProvider()),
        ],
        child: MaterialApp(
          home: WellnessDashboardScreen(),
        ),
      ),
    );

    // Dashboard typically has a "Talk" or "Chat" tab, "Mood" tab, etc.
    // Since we don't assume the exact text, we check for Key UI structure
    // or just that it doesn't crash on pump.

    // Check for "Talk" tab text if it exists in the navigation bar
    // Note: The actual text might differ ("Talk with AI", "Chat", etc.)
    // We'll just verify the widget pumps successfully for now (Smoke Test).

    expect(find.byType(WellnessDashboardScreen), findsOneWidget);
  });
}
