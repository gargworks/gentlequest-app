import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/main.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    SharedPreferences.setMockInitialValues({
      'compliance_age_verified_18_plus': true,
      'compliance_location_verified': true,
      'compliance_verified_region': 'CA',
      'compliance_verification_timestamp': DateTime.now().millisecondsSinceEpoch,
    });
  });

  group('App Store Screenshots', () {
    testWidgets('1. Chat Interface', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle(const Duration(seconds: 5));
      
      if (find.text('Talk').evaluate().isNotEmpty) {
        await tester.tap(find.text('Talk'));
        await tester.pumpAndSettle();
      }
      
      await binding.takeScreenshot('chat_interface');
    });

    testWidgets('2. Mood Tracker', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle(const Duration(seconds: 5));
      
      await tester.tap(find.text('Mood'));
      await tester.pumpAndSettle(const Duration(seconds: 2));
      
      await binding.takeScreenshot('mood_tracker');
    });

    testWidgets('3. Community', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle(const Duration(seconds: 5));
      
      await tester.tap(find.text('Community'));
      await tester.pumpAndSettle(const Duration(seconds: 2));
      
      await binding.takeScreenshot('community_support');
    });
  });
}
