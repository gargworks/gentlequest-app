
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/features/leopard/widgets/leopard_gate.dart';
import 'package:ai_buddy_web/features/leopard/widgets/leopard_access_gate.dart';
import 'package:ai_buddy_web/config/feature_flags.dart';

// Mocking FeatureFlags is tricky as they are static const.
// For this test, we accept that 'enableLeopardMode' is FALSE by default (Dead Switch).
// We verify that the Dead Switch works.

import 'package:provider/provider.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/community_provider.dart';

void main() {
  testWidgets('LeopardGate respects Dead Switch (Default State)', (WidgetTester tester) async {
    // Build our app and trigger a frame.
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
          home: LeopardGate(),
        ),
      ),
    );

    // EXPECTATION: When enableLeopardMode is false (default), 
    // it should render the WellnessDashboardScreen (legacy), not the Gate or Shell.
    
    // Check that Access Gate is NOT present
    expect(find.byType(LeopardAccessGate), findsNothing);
  });
}
