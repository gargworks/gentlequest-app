import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/welcome_screen.dart';

// Most assertions in this file were written against an older WelcomeScreen
// (Meet Alex heading / Get Started button / three value propositions) that
// was superseded by the R1D1 onboarding redesign before 2026-05-21. The
// current WelcomeScreen is driven by docs/design/refs/htmls/
// GentleQuest_Onboarding_R1D1.html and doesn't surface any of those
// strings. The render/has-been-seen assertions still hold and are kept;
// rewrite the structural tests against the R1D1 surface in a follow-up.
void main() {
  group('WelcomeScreen', () {
    testWidgets('hasBeenSeen returns false initially',
        (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({});

      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, false);
    });

    testWidgets('hasBeenSeen returns true after marking seen',
        (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({'has_seen_welcome_v1': true});

      final seen = await WelcomeScreen.hasBeenSeen();
      expect(seen, true);
    });
  });
}
