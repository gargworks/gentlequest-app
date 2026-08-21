import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/screens/profile/profile_prefs_keys.dart';
import 'package:ai_buddy_web/screens/profile/safety_plan_card.dart';
import 'package:ai_buddy_web/widgets/crisis_resources.dart' show deriveSafetyPlanState;

// WO-6.4: SafetyPlanCard's new .partial state, and the content-first
// derivation that makes it reachable. Before this, kSafetyPlanFilled was
// the only signal checked — a plan with real content but no completion
// flag silently reported .empty (a lost-work bug, not just a dead enum
// value).
void main() {
  group('deriveSafetyPlanState', () {
    Future<SafetyPlanState> derive(Map<String, Object> values) async {
      SharedPreferences.setMockInitialValues(values);
      final prefs = await SharedPreferences.getInstance();
      return deriveSafetyPlanState(prefs);
    }

    test('no content, no flag → empty', () async {
      expect(await derive({}), SafetyPlanState.empty);
    });

    test('content but no flag → partial (the WO-6.4 fix)', () async {
      expect(
        await derive({kSafetyPlanFieldKeys.first: 'a warning sign'}),
        SafetyPlanState.partial,
      );
    });

    test('content and flag → filled', () async {
      expect(
        await derive({
          kSafetyPlanFieldKeys.first: 'a warning sign',
          kSafetyPlanFilled: true,
        }),
        SafetyPlanState.filled,
      );
    });

    test('flag true but every field blank → empty, not filled', () async {
      // A wiped plan shouldn't leave a crisis row pointing at nothing.
      expect(
        await derive({kSafetyPlanFilled: true}),
        SafetyPlanState.empty,
      );
    });

    test('whitespace-only content counts as blank', () async {
      expect(
        await derive({kSafetyPlanFieldKeys.first: '   '}),
        SafetyPlanState.empty,
      );
    });
  });

  group('SafetyPlanCard', () {
    Widget wrap(SafetyPlanState state, {VoidCallback? onEdit}) {
      return MaterialApp(
        home: Scaffold(
          body: SafetyPlanCard(
            state: state,
            onBuild: () {},
            onEdit: onEdit ?? () {},
          ),
        ),
      );
    }

    testWidgets('empty renders the build-plan invitation', (tester) async {
      await tester.pumpWidget(wrap(SafetyPlanState.empty));
      expect(find.text('A plan for the heavy days'), findsOneWidget);
      expect(find.text('Build my safety plan'), findsOneWidget);
    });

    testWidgets('partial renders its own copy, not empty or filled copy',
        (tester) async {
      await tester.pumpWidget(wrap(SafetyPlanState.partial));
      expect(find.text('Your safety plan'), findsOneWidget);
      expect(find.text('Started — pick it up whenever.'), findsOneWidget);
      expect(find.text('Keep going'), findsOneWidget);
      // No completion fraction or progress indicator per WO-6.4.
      expect(find.textContaining('of 5'), findsNothing);
      expect(find.byType(LinearProgressIndicator), findsNothing);
      // Not the other two states' copy.
      expect(find.text('A plan for the heavy days'), findsNothing);
      expect(find.text('When the heavy hits, your plan is here.'), findsNothing);
    });

    testWidgets('partial "Keep going" invokes onEdit', (tester) async {
      var tapped = false;
      await tester.pumpWidget(
        wrap(SafetyPlanState.partial, onEdit: () => tapped = true),
      );
      await tester.tap(find.text('Keep going'));
      await tester.pump();
      expect(tapped, isTrue);
    });

    testWidgets('filled renders the plan-is-here copy', (tester) async {
      await tester.pumpWidget(wrap(SafetyPlanState.filled));
      expect(
        find.text('When the heavy hits, your plan is here.'),
        findsOneWidget,
      );
    });
  });
}
