import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/compliance_guard_screen.dart';
import 'package:ai_buddy_web/services/compliance_service.dart';
import 'test_helpers.dart';

void main() {
  // Age-gate copy is policy-driven (v1.3.0: 18+ everywhere). Derive the
  // expected strings from the same source the screen uses so the test
  // tracks policy changes instead of pinning a stale number.
  final minAge = ComplianceService.minAgeForRegion(null);
  final olderLabel = 'I am $minAge or older';
  final underLabel = 'I am under $minAge';

  group('J03: Compliance guard screen', () {
    setUp(setUpFreshInstall);

    testWidgets('ComplianceGuardScreen renders without crash', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.byType(ComplianceGuardScreen), findsOneWidget);
    });

    testWidgets('age gate "$olderLabel" button is present', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.text(olderLabel), findsOneWidget);
    });

    testWidgets('age gate "$underLabel" button is present', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.text(underLabel), findsOneWidget);
    });

    testWidgets('"$olderLabel" tap does not crash', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text(olderLabel));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"$underLabel" tap does not crash', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text(underLabel));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });
  });
}
