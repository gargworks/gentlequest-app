import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/providers/assessment_provider.dart';
import 'package:ai_buddy_web/screens/clinical_assessment/assessment_flow_screen.dart';
import 'package:ai_buddy_web/screens/clinical_assessment/assessment_models.dart';
import 'package:ai_buddy_web/widgets/crisis_reentry_surface.dart'
    show kLastCrisisTimestampKey, isWithinCrisisWindow;

/// The flow screen and the bridge sheet both run animations that
/// pumpAndSettle cannot outlast, so every wait here is a bounded pump.
Future<void> settle(WidgetTester tester) async {
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 200));
  }
}

/// Regression for the 2026-09-03 crisis-path audit finding.
///
/// Two comments in the codebase asserted that the in-app crisis re-entry
/// surface "remains the fallback" when a notification permission is denied.
/// That was FALSE for the assessment path: kLastCrisisTimestampKey had exactly
/// one writer (interactive_chat_screen._recordCrisisTimestamp), reachable only
/// from a crisis detected in CHAT. A user who disclosed via the Q9 assessment
/// bridge and denied the permission got neither the push nor the surface.
///
/// This pins the write. If it fails, that false assurance is back and the
/// highest-acuity path in the product has no fallback at all.
void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  Widget buildFlow() {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AssessmentProvider()),
      ],
      child: const MaterialApp(
        home: AssessmentFlowScreen(scale: AssessmentScale.phq9),
      ),
    );
  }

  /// Answers questions 1..8 with "Not at all", then answers Q9 with a
  /// non-zero option, which is what opens the crisis bridge sheet.
  Future<void> reachQ9Bridge(WidgetTester tester) async {
    await tester.pumpWidget(buildFlow());
    await tester.pump(const Duration(milliseconds: 400));

    for (var q = 0; q < 8; q++) {
      await tester.tap(find.text(kLikertLabels[0]).first);
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pump(const Duration(milliseconds: 400));
    }
    // Q9 with score >= 1 -> _q9Triggered -> bridge sheet.
    await tester.tap(find.text(kLikertLabels[1]).first);
    await tester.pump(const Duration(milliseconds: 400));
    await settle(tester);
  }

  testWidgets(
      'Q9 "heavy" arms the in-app crisis re-entry surface (not just the push)',
      (tester) async {
    await reachQ9Bridge(tester);
    expect(find.textContaining('heavy moment'), findsOneWidget,
        reason: 'The Q9 crisis bridge should be open at this point.');

    await tester.tap(find.textContaining('heavy moment'));
    await settle(tester);

    final prefs = await SharedPreferences.getInstance();
    final ms = prefs.getInt(kLastCrisisTimestampKey);

    expect(ms, isNotNull,
        reason: 'The assessment crisis path MUST write '
            'kLastCrisisTimestampKey. Without it the in-app re-entry surface '
            'never arms, and a user who denies the notification permission '
            'here gets no follow-up of any kind — while the code comments '
            'claim the surface covers them.');
    expect(
      isWithinCrisisWindow(DateTime.fromMillisecondsSinceEpoch(ms!)),
      isTrue,
      reason: 'The stamp must be now, so the 72h window is live.',
    );
  });

  testWidgets('the queued follow-up stamp is still written alongside it',
      (tester) async {
    await reachQ9Bridge(tester);
    await tester.tap(find.textContaining('heavy moment'));
    await settle(tester);

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getStringList('follow_up_24h_pending'), hasLength(1),
        reason: 'Adding the crisis stamp must not displace the existing '
            'follow-up queue stamp.');
  });

  testWidgets(
      'OPPOSED CONTROL: "I am safe" must NOT arm the crisis surface',
      (tester) async {
    await reachQ9Bridge(tester);
    await tester.tap(find.textContaining("I'm safe"));
    await settle(tester);

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getInt(kLastCrisisTimestampKey), isNull,
        reason: 'Only the "heavy" branch signals an active crisis. If this '
            'fails, the test above proves nothing — it would pass for any '
            'branch, including doing nothing at all.');
  });
}
