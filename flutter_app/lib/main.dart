import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/dashboard_screen.dart';
import 'screens/research_viewer_screen.dart';
import 'screens/persona_list_screen.dart';
import 'screens/cvp_canvas_screen.dart';
import 'screens/roadmap_screen.dart';
import 'screens/task_board_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/project_chat_screen.dart';


void main() {
  runApp(const ProviderScope(child: IIPApp()));
}

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const DashboardScreen(),
    ),
    GoRoute(
      path: '/team/:teamId',
      builder: (context, state) {
        final teamId = int.parse(state.pathParameters['teamId']!);
        return ResearchViewerScreen(teamId: teamId);
      },
    ),
    GoRoute(
      path: '/team/:teamId/personas',
      builder: (context, state) {
        final teamId = int.parse(state.pathParameters['teamId']!);
        // We passed teamName as 'extra' in dashboard_screen.dart
        final teamName = state.extra as String? ?? 'Team $teamId';
        return PersonaListScreen(teamId: teamId, teamName: teamName);
      },
    ),
    GoRoute(
      path: '/team/:teamId/cvp',
      builder: (context, state) {
        final teamId = int.parse(state.pathParameters['teamId']!);
        final teamName = state.extra as String? ?? 'Team $teamId';
        return CVPCanvasScreen(teamId: teamId, teamName: teamName);
      },
    ),
    GoRoute(
      path: '/team/:teamId/roadmap',
      builder: (context, state) {
        final teamId = int.parse(state.pathParameters['teamId']!);
        return RoadmapScreen(teamId: teamId);
      },
    ),
    GoRoute(
      path: '/team/:teamId/tasks',
      builder: (context, state) {
        final teamId = int.parse(state.pathParameters['teamId']!);
        return TaskBoardScreen(teamId: teamId);
      },
    ),
    GoRoute(
      path: '/team/:teamId/chat',
      builder: (context, state) {
        final teamId = int.parse(state.pathParameters['teamId']!);
        final teamName = state.extra as String? ?? 'Team $teamId';
        return ChatScreen(teamId: teamId, teamName: teamName);
      },
    ),
    GoRoute(
      path: '/team/:teamId/project-chat',
      builder: (context, state) {
        final teamId = int.parse(state.pathParameters['teamId']!);
        final teamName = state.extra as String? ?? 'Team $teamId';
        return ProjectChatScreen(teamId: teamId, teamName: teamName);
      },
    ),
  ],
);


class IIPApp extends StatelessWidget {
  const IIPApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'IIP Innovation Coach',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6750A4),
          brightness: Brightness.light,
        ),
        textTheme: GoogleFonts.interTextTheme(),
      ),
      routerConfig: _router,
    );
  }
}
