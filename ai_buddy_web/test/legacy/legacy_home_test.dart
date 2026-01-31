
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/navigation/home_shell.dart';
import 'package:ai_buddy_web/widgets/app_bottom_nav.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/community_provider.dart';

void main() {
  testWidgets('Legacy HomeShell renders 3 main tabs', (WidgetTester tester) async {
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
          ChangeNotifierProvider(create: (_) => QuestProvider()),
          ChangeNotifierProvider(create: (_) => CommunityProvider()),
        ],
        child: MaterialApp(
          home: HomeShell(initialTab: AppTab.talk),
        ),
      ),
    );

    // Verify Bottom Navigation is present
    expect(find.byType(AppBottomNav), findsOneWidget);

    // Verify Tabs exist (Icon data may vary, but we can look for the navigation bar items)
    // We expect 3 distinct navigation destinations for the legacy app
    expect(find.byIcon(Icons.chat_bubble_outline), findsOneWidget); // Talk
    expect(find.byIcon(Icons.mood), findsOneWidget); // Mood
    // Quest is hidden in legacy mode by default?
    // Wait, AppBottomNav says: if (FeatureFlags.enableLeopardMode) ... Quest
    // In legacy mode, Is Quest tab visible?
    
    // Let's check FeatureFlags.enableLeopardMode is false.
    // If false, Quest tab is NOT in the row.
    // Community is index 2?
    
    // Actually, "Legacy Mode" usually means "The Old World" which had Quests?
    // If standard prod app has no quests in the nav bar, then we should expect 3 tabs (Talk, Mood, Community).
    // Let's verify checking for Community instead of Quest if Quest is hidden.
    
    expect(find.byIcon(Icons.people_outline), findsOneWidget); // Community
  });
}
