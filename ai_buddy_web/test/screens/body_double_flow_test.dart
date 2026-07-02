import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/widgets/body_double/body_double_timer_bar.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/providers/task_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/community_provider.dart';

// v1.5.0 ADHD Update — Body-doubling MVP (Workstream 2a) widget tests.
//
// Exercises the full flow entirely inside InteractiveChatScreen (no new
// screen/nav tab, per the scope brief's acceptance criteria): header icon
// -> start sheet -> pinned timer bar + start check-in -> midpoint check-in
// -> either natural completion (warm close-out) or early end (kind,
// no-guilt abandon message).

Widget _buildTestApp() {
  return MultiProvider(
    providers: [
      ChangeNotifierProvider(create: (_) => ChatProvider()),
      ChangeNotifierProvider(create: (_) => MoodProvider(eagerLoad: false)),
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

Future<void> _pumpChatScreen(WidgetTester tester) async {
  // Pre-acknowledge the Safety & Legal sheet (legal_ack_v1) — otherwise
  // InteractiveChatScreen's _ensureLegalAck() pops a requireAcknowledge
  // modal on first mount that intercepts every subsequent tap, including
  // the body-doubling entry icon.
  SharedPreferences.setMockInitialValues({'legal_ack_v1': true});
  await tester.pumpWidget(_buildTestApp());
  await tester.pump(const Duration(milliseconds: 500));
  await tester.pump();
}

// NOTE: deliberately avoids pumpAndSettle() throughout this file. The chat
// screen's greeting header runs a perpetually-repeating BreathingOrb
// animation (R1D6, 5.6s pulse `..repeat()`), so pumpAndSettle() never
// converges and times out. Bounded pump(duration) calls are used instead —
// same pattern as the existing interactive_chat_test.dart.
Future<void> _startSession(
  WidgetTester tester, {
  String task = 'tidy the kitchen',
  String minutesLabel = '5 min',
}) async {
  await tester.tap(find.byKey(const Key('body_double_entry_button')));
  await tester.pump(); // open the modal route
  await tester.pump(const Duration(milliseconds: 300)); // sheet entrance anim

  await tester.enterText(
    find.byKey(const Key('body_double_task_field')),
    task,
  );
  await tester.tap(find.text(minutesLabel));
  await tester.pump();
  await tester.tap(find.byKey(const Key('body_double_start_button')));
  await tester.pump(); // pop the modal route
  await tester.pump(const Duration(milliseconds: 300)); // sheet exit anim
}

void main() {
  testWidgets(
      'starting a session shows the pinned timer bar and a start check-in',
      (WidgetTester tester) async {
    await _pumpChatScreen(tester);

    await _startSession(tester);

    expect(find.byType(BodyDoubleTimerBar), findsOneWidget);
    expect(find.text('tidy the kitchen'), findsOneWidget);
    expect(find.text('05:00'), findsOneWidget);
    expect(
      find.textContaining("I'm with you for the next 5 minutes"),
      findsOneWidget,
    );
  });

  testWidgets(
      'tapping the entry icon again while running does not open a second sheet',
      (WidgetTester tester) async {
    await _pumpChatScreen(tester);
    await _startSession(tester);

    await tester.tap(find.byKey(const Key('body_double_entry_button')));
    await tester.pump();

    expect(
      find.text('A focus session is already running.'),
      findsOneWidget,
    );
    // Still exactly one timer bar — no second session was queued/stacked.
    expect(find.byType(BodyDoubleTimerBar), findsOneWidget);

    // Clean up: let the session finish naturally so no Timer is left
    // pending when the test ends.
    await tester.pump(const Duration(minutes: 5));
    await tester.pump();
  });

  testWidgets('fires a midpoint check-in partway through the session',
      (WidgetTester tester) async {
    await _pumpChatScreen(tester);
    await _startSession(tester);

    await tester.pump(const Duration(seconds: 150)); // halfway through 5 min

    expect(find.textContaining('Halfway there'), findsOneWidget);
    expect(find.text('02:30'), findsOneWidget);
    // Completion copy must not have fired yet.
    expect(find.textContaining("Time's up!"), findsNothing);

    // Run the session out so no Timer is left pending at test end.
    await tester.pump(const Duration(seconds: 150));
    await tester.pump();
  });

  testWidgets(
      'natural completion clears the bar, resets the icon, and posts a warm close-out',
      (WidgetTester tester) async {
    await _pumpChatScreen(tester);
    await _startSession(tester);

    await tester.pump(const Duration(minutes: 5));
    await tester.pump();

    expect(find.byType(BodyDoubleTimerBar), findsNothing);
    expect(find.textContaining("Time's up!"), findsOneWidget);
    expect(find.textContaining('Nice work sticking with me'), findsOneWidget);
  });

  testWidgets('ending a session early posts a kind, no-guilt abandon message',
      (WidgetTester tester) async {
    await _pumpChatScreen(tester);
    await _startSession(tester);

    await tester.pump(const Duration(seconds: 30));
    await tester.tap(find.text('End session'));
    await tester.pump();

    expect(find.byType(BodyDoubleTimerBar), findsNothing);
    expect(find.textContaining('No worries — we stopped early'), findsOneWidget);
    // No shame/streak language, and no false "you finished" close-out.
    expect(find.textContaining("Time's up!"), findsNothing);
  });
}
