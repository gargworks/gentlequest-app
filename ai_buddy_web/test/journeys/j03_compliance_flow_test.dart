import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/compliance_guard_screen.dart';
import 'test_helpers.dart';

void main() {
  group('J03: Compliance guard screen', () {
    setUp(setUpFreshInstall);

    testWidgets('ComplianceGuardScreen renders without crash', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.byType(ComplianceGuardScreen), findsOneWidget);
    });

    testWidgets('age gate "I am 13 or older" button is present', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.text('I am 13 or older'), findsOneWidget);
    });

    testWidgets('age gate "I am under 13" button is present', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.text('I am under 13'), findsOneWidget);
    });

    testWidgets('"I am 13 or older" tap does not crash', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text('I am 13 or older'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"I am under 13" tap does not crash', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: ComplianceGuardScreen()));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text('I am under 13'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });
  });
}
