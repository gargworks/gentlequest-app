import 'package:ai_buddy_web/features/leopard/leopard_shell.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/community_provider.dart';
import 'package:ai_buddy_web/navigation/route_observer.dart';
import 'package:ai_buddy_web/services/notification_service.dart';
import 'package:ai_buddy_web/services/firebase_service.dart';

// LEOPARD SEAL: Shadow Entry Point.
// This allows us to run the "Leopard" features without touching prod code.

final GlobalKey<NavigatorState> rootNavigatorKey = GlobalKey<NavigatorState>();

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase (Reuse Prod Logic)
  try {
    await FirebaseService().setFirebaseOptions();
    await FirebaseService().initialize();
  } catch (e) {
    debugPrint('Firebase initialization error: $e');
  }

  // Reuse Prod Services
  NotificationService.onSelectNotification = (payload) {
    debugPrint("Leopard Notification Clicked: $payload");
  };

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ChatProvider()),
        ChangeNotifierProvider(create: (_) => MoodProvider()),
        ChangeNotifierProvider(create: (_) => AssessmentProvider()),
        ChangeNotifierProvider(create: (_) => TaskProvider()),
        ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ChangeNotifierProvider(create: (_) => QuestProvider()..loadQuests()),
        ChangeNotifierProvider(create: (_) => CommunityProvider()),
      ],
      child: MaterialApp(
        title: 'GentleQuest // LEOPARD', // Debug Title
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF667EEA),
            brightness:
                Brightness.dark, // Leopard Seal Default is Dark Mode (Gym)
          ),
          useMaterial3: true,
        ),
        navigatorKey: rootNavigatorKey,
        navigatorObservers: [routeObserver],
        // LEOPARD SWITCH: Redirect to the Skunkworks Shell
        home: const LeopardShell(),
      ),
    );
  }
}
