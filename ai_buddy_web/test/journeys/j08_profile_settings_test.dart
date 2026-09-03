import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/settings_screen.dart';
import 'package:ai_buddy_web/screens/settings/notification_detail_screen.dart';
import 'package:ai_buddy_web/screens/settings/settings_widgets.dart';
import 'package:ai_buddy_web/services/low_stim_service.dart';
import 'test_helpers.dart';

// WO-6.1: the "Chat header contains profile avatar icon" / "Profile avatar
// tap" tests that used to live here were removed — the avatar entry point
// and profile_nav_sheet.dart it opened were deleted, the You tab is now the
// only way into Profile. Removed rather than left to flap.

void main() {
  group('J08: Settings screen — comprehensive', () {
    setUp(() async {
      await setUpBypassedPrefs();
      // Reset the low-stim static notifier — it's shared global state across
      // the whole test file run (see LowStimService), not per-widget state.
      LowStimService.lowStimNotifier.value = false;
    });

    Widget buildSettings() {
      return const MaterialApp(home: SettingsScreen());
    }

    // Notification detail screen (View D) — reached from Settings by tapping
    // "Daily check-in reminder", but only when signed in (UC-S5 fix,
    // 2026-06-12: signed-out taps now open LoginScreen instead). Pumping the
    // screen directly tests its real current content/behavior without
    // faking AuthService's private sign-in state.
    Widget buildNotificationDetail() {
      return const MaterialApp(home: NotificationDetailScreen());
    }

    // ── SettingsScreen rendering ───────────────────────────────────────────────

    testWidgets('SettingsScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.byType(SettingsScreen), findsOneWidget);
    });

    testWidgets('PRIVACY section is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('PRIVACY'), findsOneWidget);
    });

    testWidgets('NOTIFICATIONS section is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      // The "Share usage analytics" row (analytics_consent UI) pushed this
      // section below the default 800x600 test surface's cache extent.
      await tester.scrollUntilVisible(find.text('NOTIFICATIONS'), 100.0);
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

      await tester.scrollUntilVisible(find.text('Daily check-in reminder'), 100.0);
      expect(find.text('Daily check-in reminder'), findsOneWidget);
    });

    testWidgets('"Daily check-in reminder" tap opens detail without crash',
        (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('Daily check-in reminder'), 100.0);
      await tester.tap(find.text('Daily check-in reminder'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Gentle nudge" row is present', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(find.text('Gentle nudge'), 100.0);
      expect(find.text('Gentle nudge'), findsOneWidget);
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
          .widget<SettingsToggle>(find.byKey(const Key('low_stim_toggle')));
      expect(toggle.value, isFalse);
    });

    testWidgets(
        '"Low-stim quiet mode" toggle flips on tap and persists to prefs',
        (tester) async {
      // WO-5.3 grew this screen's content (PRIVACY section, banners), so
      // the toggle no longer fits the default 800x600 test surface without
      // scrolling — and this ListView virtualizes its children (SliverList
      // culls anything outside the viewport's cache extent even when built
      // from a plain `children:` list), so scrolling to it and back off
      // unmounts other rows unpredictably. Simplest robust fix: give the
      // test surface enough height that nothing needs to scroll at all.
      await tester.binding.setSurfaceSize(const Size(800, 1400));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.tap(find.byKey(const Key('low_stim_toggle')));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
      final toggle = tester
          .widget<SettingsToggle>(find.byKey(const Key('low_stim_toggle')));
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
      await tester.ensureVisible(find.text('Privacy policy'));
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
      await tester.ensureVisible(find.text('Crisis resources'));
      await tester.tap(find.text('Crisis resources'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    // ── Notification detail screen ─────────────────────────────────────────────

    testWidgets('notification detail shows day chips after opening', (tester) async {
      await tester.pumpWidget(buildNotificationDetail());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(find.text('ON DAYS'), findsOneWidget);
    });

    testWidgets('"Send a test notification" button present in detail', (tester) async {
      await tester.pumpWidget(buildNotificationDetail());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Send a test notification'));
      expect(find.text('Send a test notification'), findsOneWidget);
    });

    testWidgets('"Send a test notification" tap shows snackbar', (tester) async {
      await tester.pumpWidget(buildNotificationDetail());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.ensureVisible(find.text('Send a test notification'));
      await tester.tap(find.text('Send a test notification'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets(
        'analytics toggle copy names its real scope, not all analytics',
        (tester) async {
      // This toggle writes analytics_consent, which gates ONLY the backend
      // /api/analytics/log stream. Firebase/GA4 is gated by anonymity mode
      // alone (firebase_service.dart:177), so events keep flowing there while
      // this is off. Earlier copy read "Share usage analytics / Anonymous
      // app-usage events only" — which a user would reasonably take as
      // covering everything. A consent control that reads broader than it acts
      // is a real harm in a mental-health app, and it is one careless copy
      // edit away from becoming untrue again. Hence pinned.
      await tester.pumpWidget(buildSettings());
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      await tester.scrollUntilVisible(
          find.text('Share extra usage data'), 100.0);
      expect(find.text('Share extra usage data'), findsOneWidget);

      final subtitle = tester
          .widgetList<Text>(find.byType(Text))
          .map((t) => t.data ?? '')
          .firstWhere((d) => d.contains('extra usage events'),
              orElse: () => '');
      expect(subtitle, isNotEmpty,
          reason: 'the analytics toggle needs a scope-bounded subtitle');
      expect(subtitle.contains('Anonymity mode'), isTrue,
          reason: 'copy must point at Anonymity mode as the total control, '
              'because this toggle does NOT stop Firebase/GA4 collection');
    });

  });
}
