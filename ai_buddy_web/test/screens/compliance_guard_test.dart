import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/compliance_guard_screen.dart';

void main() {
  group('ComplianceGuardScreen', () {
    testWidgets('renders without crashing', (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({});

      await tester.pumpWidget(
        const MaterialApp(home: ComplianceGuardScreen()),
      );

      // Should show loading or initial state
      await tester.pump();
      expect(find.byType(ComplianceGuardScreen), findsOneWidget);
    });
  });
}
