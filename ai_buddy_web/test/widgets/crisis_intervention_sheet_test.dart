import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/screens/profile/profile_prefs_keys.dart';
import 'package:ai_buddy_web/widgets/crisis_resources.dart';

// WO-6.2: CrisisInterventionSheet gains a secondary "Your safety plan" row
// below the 988 CTA when the user has one — the live crisis surface had no
// safety-plan recall at all before this.
void main() {
  group('CrisisInterventionSheet — safety plan row', () {
    Future<void> openSheet(WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) => ElevatedButton(
              onPressed: () => showCrisisInterventionSheet(context),
              child: const Text('open'),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pump();
      // Let the FutureBuilder's SharedPreferences read resolve.
      await tester.pump(const Duration(milliseconds: 100));
    }

    testWidgets('does not render when no plan exists', (tester) async {
      SharedPreferences.setMockInitialValues({});
      await openSheet(tester);

      expect(find.text('Your safety plan'), findsNothing);
      // 988 stays present regardless.
      expect(find.text('Talk to someone now'), findsOneWidget);
    });

    testWidgets('renders below 988 when a plan is filled', (tester) async {
      SharedPreferences.setMockInitialValues({kSafetyPlanFilled: true});
      await openSheet(tester);

      expect(find.text('Your safety plan'), findsOneWidget);
      expect(find.text('The words you wrote for a moment like this.'),
          findsOneWidget);

      // Ordering: 988 stays the first/primary option, ahead of the plan row.
      final callY = tester.getTopLeft(find.text('Talk to someone now')).dy;
      final planY = tester.getTopLeft(find.text('Your safety plan')).dy;
      expect(callY, lessThan(planY));
    });

    testWidgets('tapping the row opens the safety plan recall sheet',
        (tester) async {
      SharedPreferences.setMockInitialValues({kSafetyPlanFilled: true});
      await openSheet(tester);

      await tester.tap(find.text('Your safety plan'));
      await tester.pumpAndSettle();

      // The crisis sheet's own content is still present underneath — the
      // recall sheet stacks above it rather than replacing it.
      expect(find.text('Talk to someone now'), findsOneWidget);
    });
  });
}
