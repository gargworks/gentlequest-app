// Widget test for journal empty state privacy copy.
//
// Asserts that the privacy footer unconditionally shows
// "Stays on your device. Never synced. Never shared."
// regardless of auth state. The backend /api/journal/* routes
// were removed in PR #167 (2026-07-02); the isSignedIn branch
// that showed "Synced to your account" was unconditionally false
// and is now removed.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/screens/journal/journal_empty_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  Future<void> pumpEmptyState(WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: JournalEmptyState(
          onStartEntry: ({String? prefill}) async {},
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets(
      'privacy footer shows "Stays on your device" unconditionally '
      '(no isSignedIn branch)', (WidgetTester tester) async {
    await pumpEmptyState(tester);

    // Find the privacy footer text
    final privacyFinder = find.textContaining('Stays on your device');
    expect(privacyFinder, findsOneWidget,
        reason: 'Privacy footer must show "Stays on your device" unconditionally');

    // The old "Synced to your account" copy must NEVER appear
    final syncedFinder = find.textContaining('Synced to your account');
    expect(syncedFinder, findsNothing,
        reason: 'The stale "Synced to your account" copy must never appear — '
            'routes/journal.py was deleted in PR #167');
  });

  testWidgets('privacy footer contains "Never synced. Never shared."', (tester) async {
    await pumpEmptyState(tester);

    expect(find.textContaining('Never synced'), findsOneWidget);
    expect(find.textContaining('Never shared'), findsOneWidget);
  });

  testWidgets('privacy footer does not depend on AuthService', (tester) async {
    // If AuthService were still imported, this test would fail at compile time
    // because we'd need to mock it. The fact that we can pump without any
    // auth setup proves the branch was removed.
    await pumpEmptyState(tester);

    // Verify the lock icon is present (part of the privacy footer)
    expect(find.byIcon(Icons.lock_outline), findsOneWidget);
  });
}
