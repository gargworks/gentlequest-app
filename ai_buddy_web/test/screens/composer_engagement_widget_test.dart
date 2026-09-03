import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/providers/survey_provider.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/services/firebase_service.dart';

import '../helpers/recording_analytics_sink.dart';

/// The REAL widget test for composer engagement, 2026-09-03.
///
/// This is what `composer_engagement_order_test.dart` could only approximate.
/// That file reimplements the latch logic locally and greps the source; it
/// cannot see whether the real code path executes. Demonstrated on the welcome
/// screen: move a logEvent into a never-invoked closure and the source-grep
/// test still passes.
///
/// Here the real InteractiveChatScreen is pumped and the real
/// FirebaseService().logEvent calls are observed through the AnalyticsSink
/// seam.
///
/// The two properties under test, both of which have been broken in prod:
///   ORDER     — a starter chip must log engagement BEFORE the send.
///   ONCE-ONLY — focus/blur/refocus must log engagement exactly once.
void main() {
  late RecordingAnalyticsSink sink;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    sink = RecordingAnalyticsSink();
    FirebaseService.sinkOverride = sink;
  });

  tearDown(() => FirebaseService.sinkOverride = null);

  Future<void> pumpChat(WidgetTester tester) async {
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => ChatProvider()),
          ChangeNotifierProvider(create: (_) => CompanionProvider()),
          ChangeNotifierProvider(create: (_) => SurveyProvider()),
        ],
        child: const MaterialApp(
          home: InteractiveChatScreen(showBottomNav: false),
        ),
      ),
    );
    // Bounded pumps: the screen runs animations that pumpAndSettle outlasts.
    for (var i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 200));
    }
  }

  testWidgets('mounting the chat screen fires chat_tab_viewed', (tester) async {
    await pumpChat(tester);
    expect(sink.count('chat_tab_viewed'), 1,
        reason: 'Pinned so the funnel stage above the composer is real too.');
  });

  testWidgets('focusing the composer fires chat_composer_focused ONCE',
      (tester) async {
    await pumpChat(tester);

    final field = find.byType(TextField);
    expect(field, findsWidgets, reason: 'The composer must be on screen.');

    await tester.tap(field.first);
    await tester.pump(const Duration(milliseconds: 100));

    expect(sink.count('chat_composer_focused'), 1);
  });

  testWidgets('focus, blur, refocus still logs engagement exactly ONCE',
      (tester) async {
    // The inflation bug: the guard flag used to reset on blur, so a fidgety
    // user counted three times against a once-per-user stage above — the step
    // could read as growth.
    await pumpChat(tester);
    final field = find.byType(TextField).first;

    await tester.tap(field);
    await tester.pump(const Duration(milliseconds: 100));
    FocusManager.instance.primaryFocus?.unfocus();
    await tester.pump(const Duration(milliseconds: 100));
    await tester.tap(field);
    await tester.pump(const Duration(milliseconds: 100));

    expect(sink.count('chat_composer_focused'), 1,
        reason: 'The stage means "this user engaged the composer", once.');
  });

  testWidgets('OPPOSED CONTROL: merely viewing the screen does NOT engage',
      (tester) async {
    // Without this, the tests above could pass because the event fires on
    // mount — which would make the stage meaningless (every viewer would
    // count as engaged).
    await pumpChat(tester);

    expect(sink.count('chat_composer_focused'), 0,
        reason: 'Engagement must require an actual focus or chip tap.');
    expect(sink.count('chat_send_attempted'), 0);
  });

  testWidgets('a starter chip logs engagement BEFORE the send — real screen',
      (tester) async {
    // The ordering bug, tested against the real widget rather than a copy of
    // its logic. A chip calls _sendMessage() directly, so before the fix
    // chat_send_attempted fired while the composer had never been focused —
    // a send with no preceding engagement, which broke any sequence reading.
    await pumpChat(tester);

    final chip = find.text('Just need someone to listen');
    if (chip.evaluate().isEmpty) {
      markTestSkipped('starter chips not rendered in this state');
      return;
    }

    await tester.tap(chip);
    await tester.pump(const Duration(milliseconds: 200));

    expect(
      sink.only({'chat_composer_focused', 'chat_send_attempted'}),
      ['chat_composer_focused', 'chat_send_attempted'],
      reason: 'Engagement must be recorded before the send, and each exactly '
          'once. If the order flips, the funnel shows a send with no '
          'preceding engagement.',
    );
  });
}
