import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/models/companion.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/screens/yours_screen.dart';
import 'package:ai_buddy_web/screens/settings_screen.dart';
import 'package:ai_buddy_web/widgets/companion_widget.dart';

// WO-6.1: the You tab now inlines ProfileScreen's content (About You / How
// Alex Talks / Safety Plan) plus Check-in and Settings rows, rather than
// linking out to Weekly Review / Journal / Resources — those three moved to
// the Journal tab (Weekly Review, Journal) and Home's quick lanes (Library).

void main() {
  group('YoursScreen', () {
    Future<void> buildScreen(WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({
        'gq.companion.v1': Companion.fresh().encode(),
      });
      // The inlined ProfileScreen content (About You / How Alex Talks /
      // Safety Plan) plus the two new rows is taller than the default
      // 800x600 test surface — the ListView virtualizes (SliverList), so
      // rows past the viewport's cache extent don't exist in the tree at
      // all, not just off-screen. Give the surface enough height that
      // nothing needs to scroll (same fix as WO-5.3's low-stim toggle test).
      await tester.binding.setSurfaceSize(const Size(800, 2000));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider(
            create: (_) => CompanionProvider(),
            child: const YoursScreen(),
          ),
        ),
      );
      // Let the provider's async _load() and ProfileHomeBody's prefs load
      // complete, and the widget rebuild.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));
    }

    testWidgets('renders the "Yours" title', (tester) async {
      await buildScreen(tester);
      expect(find.text('Yours'), findsOneWidget);
    });

    testWidgets(
        'renders About You, How Alex Talks, and Safety Plan sections',
        (tester) async {
      await buildScreen(tester);
      expect(find.text('ABOUT YOU'), findsOneWidget);
      expect(find.text('HOW ALEX TALKS TO YOU'), findsOneWidget);
      expect(find.text('YOUR SAFETY PLAN'), findsOneWidget);
    });

    testWidgets('renders Check in and Settings rows', (tester) async {
      await buildScreen(tester);
      expect(find.text('Check in'), findsOneWidget);
      expect(find.text('Settings'), findsOneWidget);
    });

    testWidgets('Settings row tap opens SettingsScreen', (tester) async {
      await buildScreen(tester);
      await tester.tap(find.text('Settings'));
      await tester.pumpAndSettle();
      expect(find.byType(SettingsScreen), findsOneWidget);
    });

    testWidgets('renders the companion in the header', (tester) async {
      await buildScreen(tester);
      expect(find.byType(CompanionWidget), findsOneWidget);
    });
  });
}
