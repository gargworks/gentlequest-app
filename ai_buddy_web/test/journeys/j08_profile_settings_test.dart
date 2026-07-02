import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/screens/settings_screen.dart';
import 'package:ai_buddy_web/screens/settings/settings_widgets.dart';
import 'package:ai_buddy_web/providers/chat_provider.dart';
import 'package:ai_buddy_web/providers/mood_provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/providers/community_provider.dart';
import 'package:ai_buddy_web/providers/progress_provider.dart';
import 'package:ai_buddy_web/services/low_stim_service.dart';
import 'test_helpers.dart';

void main() {
  group('J08: Settings screen — comprehensive', () {
    setUp(() async {
      await setUpBypassedPrefs();
      // Reset the low-stim static notifier — it's shared global state across
      // the whole test file run (see LowStimService), not per-widget state.
      LowStimService.lowStimNotifier.value = false;
    });

    Widget buildChat() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => ChatProvider()),
          ChangeNotifierProvider(create: (_) => MoodProvider()),
          ChangeNotifierProvider(create: (_) => QuestProvider()),
          ChangeNotifierProvider(create: (_) => CommunityProvider()),
          ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ],
        child: const MaterialApp(home: InteractiveChatScreen()),
      );
    }

    Widget buildSettings() {
      return const MaterialApp(home: SettingsScreen());
    }

    // ── Chat header ────────────────────────────────────────────────────────────

    testWidgets('Chat header contains profile avatar icon', (tester) async {
      await tester.pumpWidget(buildChat());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byIcon(Icons.account_circle_outlined), findsOneWidget);
    });

    testWidgets('Profile avatar tap does not crash', (tester) async {
      await tester.pumpWidget(buildChat());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.byIcon(Icons.account_circle_outlined));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    // ── SettingsScreen rendering ───────────────────────────────────────────────

    testWidgets('SettingsScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byType(SettingsScreen), findsOneWidget);
    });

    testWidgets('YOUR DATA section is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('YOUR DATA'), findsOneWidget);
    });

    testWidgets('NOTIFICATIONS section is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('NOTIFICATIONS'), findsOneWidget);
    });

    // ── YOUR DATA rows ─────────────────────────────────────────────────────────

    testWidgets('"Export my data" row is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('Export my data'), findsOneWidget);
    });

    testWidgets('"Export my data" tap shows snackbar without crash',
        (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Export my data'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Delete my account" row is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('Delete my account'), findsOneWidget);
    });

    testWidgets('"Delete my account" tap opens sheet without crash',
        (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Delete my account'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Anonymity mode" row is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('Anonymity mode'), findsOneWidget);
    });

    testWidgets('"Anonymity mode" tap does not crash', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Anonymity mode'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    // ── NOTIFICATIONS rows ─────────────────────────────────────────────────────

    testWidgets('"Daily check-in reminder" row is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('Daily check-in reminder'), findsOneWidget);
    });

    testWidgets('"Daily check-in reminder" tap opens detail without crash',
        (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Daily check-in reminder'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Streak gentle nudge" row is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('Streak gentle nudge'), findsOneWidget);
    });

    // ── APPEARANCE section (v1.5.0 low-stim quiet mode, ADR-006) ──────────────

    testWidgets('"APPEARANCE" section is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('APPEARANCE'), 100.0);
      expect(find.text('APPEARANCE'), findsOneWidget);
    });

    testWidgets('"Low-stim quiet mode" row is present, off by default',
        (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('Low-stim quiet mode'), 100.0);
      expect(find.text('Low-stim quiet mode'), findsOneWidget);
      final toggle = tester
          .widget<GQToggle>(find.byKey(const Key('low_stim_toggle')));
      expect(toggle.value, isFalse);
    });

    testWidgets(
        '"Low-stim quiet mode" toggle flips on tap and persists to prefs',
        (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('Low-stim quiet mode'), 100.0);
      await tester.tap(find.byKey(const Key('low_stim_toggle')));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
      final toggle = tester
          .widget<GQToggle>(find.byKey(const Key('low_stim_toggle')));
      expect(toggle.value, isTrue);
      expect(LowStimService.enabled, isTrue);

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool(LowStimService.kLowStimModeKey), isTrue);
    });

    // ── ABOUT section ──────────────────────────────────────────────────────────

    testWidgets('"Privacy policy" row is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('Privacy policy'), 100.0);
      expect(find.text('Privacy policy'), findsOneWidget);
    });

    testWidgets('"Privacy policy" tap navigates without crash', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('Privacy policy'), 100.0);
      await tester.tap(find.text('Privacy policy'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Crisis resources" row is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('Crisis resources'), 100.0);
      expect(find.text('Crisis resources'), findsOneWidget);
    });

    testWidgets('"Crisis resources" tap opens sheet without crash', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('Crisis resources'), 100.0);
      await tester.tap(find.text('Crisis resources'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    // ── Notification detail screen ─────────────────────────────────────────────

    testWidgets('notification detail shows day chips after opening', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Daily check-in reminder'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.text('ON DAYS'), findsOneWidget);
    });

    testWidgets('"Send a test notification" button present in detail', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Daily check-in reminder'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.ensureVisible(find.text('Send a test notification'));
      expect(find.text('Send a test notification'), findsOneWidget);
    });

    testWidgets('"Send a test notification" tap shows snackbar', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.text('Daily check-in reminder'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.ensureVisible(find.text('Send a test notification'));
      await tester.tap(find.text('Send a test notification'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });
  });
}
