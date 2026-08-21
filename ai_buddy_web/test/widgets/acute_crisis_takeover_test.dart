import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/screens/profile/profile_prefs_keys.dart';
import 'package:ai_buddy_web/widgets/crisis_resources.dart';

// WO-6.3: AcuteCrisisTakeover rewrite — nav lock removed (Part A), a real
// exit button (Part B), updated copy (C1-C3), and a static visual treatment
// with a dangerInk CTA fill (Part D). These tests cover the acceptance
// list: back-gesture exit, exit-button exit, both reachable safety-plan
// states, and the tel: failure banner.
//
// Not tested here: "no re-fire on the same message" — the .crisis →
// full-screen routing itself is deliberately unwired pending the operator
// gate (WO-6.3 Part E), so there is no live call site yet to exercise that
// behavior against. Also not tested: SafetyPlanState.partial — confirmed
// dead, _loadSafetyPlanState() only ever returns .filled or .empty.
void main() {
  group('AcuteCrisisTakeover', () {
    Future<void> pushTakeover(WidgetTester tester, {VoidCallback? onStepBack}) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: Center(
                child: ElevatedButton(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => AcuteCrisisTakeover(onStepBack: onStepBack),
                    ),
                  ),
                  child: const Text('trigger'),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('trigger'));
      await tester.pump();
      // Let the async _loadPlanState() SharedPreferences read resolve.
      await tester.pump(const Duration(milliseconds: 150));
    }

    testWidgets('renders the C1/C2 headline and the 988 CTA', (tester) async {
      SharedPreferences.setMockInitialValues({});
      await pushTakeover(tester);

      expect(find.text("We're here, right now."), findsOneWidget);
      expect(
        find.text(
          'This sounds heavier than we can hold together. 988 is free, 24/7, and they answer.',
        ),
        findsOneWidget,
      );
      expect(find.text('Call 988'), findsWidgets);
      expect(find.text('Suicide & Crisis Lifeline · free, 24/7'), findsOneWidget);
    });

    testWidgets('has no nav lock — the route can be popped', (tester) async {
      SharedPreferences.setMockInitialValues({});
      await pushTakeover(tester);
      expect(find.byType(AcuteCrisisTakeover), findsOneWidget);
      expect(find.byType(PopScope), findsNothing);

      final takeoverContext = tester.element(find.byType(AcuteCrisisTakeover));
      final popped = await Navigator.of(takeoverContext).maybePop();
      await tester.pumpAndSettle();

      expect(popped, isTrue);
      expect(find.byType(AcuteCrisisTakeover), findsNothing);
      expect(find.text('trigger'), findsOneWidget);
    });

    testWidgets('exit button invokes onStepBack', (tester) async {
      SharedPreferences.setMockInitialValues({});
      var stepBackCalled = false;
      await pushTakeover(tester, onStepBack: () => stepBackCalled = true);

      await tester.ensureVisible(find.text("I'm okay for now"));
      await tester.tap(find.text("I'm okay for now"));
      await tester.pump();

      expect(stepBackCalled, isTrue);
    });

    testWidgets('exit button falls back to a plain pop with no onStepBack',
        (tester) async {
      SharedPreferences.setMockInitialValues({});
      await pushTakeover(tester);

      await tester.ensureVisible(find.text("I'm okay for now"));
      await tester.tap(find.text("I'm okay for now"));
      await tester.pumpAndSettle();

      expect(find.byType(AcuteCrisisTakeover), findsNothing);
      expect(find.text('trigger'), findsOneWidget);
    });

    testWidgets('shows the no-plan-yet banner when no safety plan exists',
        (tester) async {
      SharedPreferences.setMockInitialValues({});
      await pushTakeover(tester);

      expect(find.textContaining("You haven't written a plan yet"),
          findsOneWidget);
      expect(find.text('I have a safety plan I want to use'), findsNothing);
    });

    testWidgets('shows the safety-plan row when a plan is filled',
        (tester) async {
      // WO-6.4: .filled now requires content too, not just the flag —
      // _loadSafetyPlanState() derives it from both together.
      SharedPreferences.setMockInitialValues({
        kSafetyPlanFilled: true,
        kSafetyPlanFieldKeys.first: 'a warning sign',
      });
      await pushTakeover(tester);

      expect(find.text('I have a safety plan I want to use'), findsOneWidget);
      expect(find.textContaining("You haven't written a plan yet"),
          findsNothing);
    });

    testWidgets('shows the safety-plan row for a partial plan too (no flag)',
        (tester) async {
      // WO-6.4: a partial plan (content, no completion flag) must be
      // reachable here too, not just in the SafetyPlanCard — this was the
      // whole point of fixing the derivation.
      SharedPreferences.setMockInitialValues({
        kSafetyPlanFieldKeys.first: 'a warning sign',
      });
      await pushTakeover(tester);

      expect(find.text('I have a safety plan I want to use'), findsOneWidget);
      expect(find.textContaining("You haven't written a plan yet"),
          findsNothing);
    });

    testWidgets('shows a failure banner when the dialer cannot be reached',
        (tester) async {
      // Same mock-channel pattern as
      // age_verification_blocked_screen_test.dart's url_launcher coverage —
      // an unmocked channel call hangs rather than throwing, so the failure
      // path needs an explicit false response to be exercised. The
      // clipboard fallback that follows needs its own seam
      // (debugClipboardSetDataOverride) for the same reason — a real
      // device always has a working Clipboard, so _launchUri has no
      // existing test coverage of that path to follow.
      final messenger =
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
      const urlLauncherChannel = MethodChannel('plugins.flutter.io/url_launcher');
      messenger.setMockMethodCallHandler(
        urlLauncherChannel,
        (call) async => false,
      );
      addTearDown(() => messenger.setMockMethodCallHandler(urlLauncherChannel, null));
      debugClipboardSetDataOverride = (data) async {};
      addTearDown(() => debugClipboardSetDataOverride = null);

      SharedPreferences.setMockInitialValues({});
      await pushTakeover(tester);

      await tester.tap(find.text('Call 988').first);
      await tester.pumpAndSettle();

      expect(
        find.text("We couldn't open your phone app. The number is 988."),
        findsOneWidget,
      );
    });
  });
}
