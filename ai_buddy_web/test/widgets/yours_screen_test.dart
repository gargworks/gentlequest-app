import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/models/companion.dart';
import 'package:ai_buddy_web/providers/companion_provider.dart';
import 'package:ai_buddy_web/screens/yours_screen.dart';
import 'package:ai_buddy_web/widgets/companion_widget.dart';

void main() {
  group('YoursScreen', () {
    Future<void> buildScreen(WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({
        'gq.companion.v1': Companion.fresh().encode(),
      });
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider(
            create: (_) => CompanionProvider(),
            child: const YoursScreen(),
          ),
        ),
      );
      // Let the provider's async _load() complete and the widget rebuild.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
    }

    testWidgets('renders the "Yours" title', (tester) async {
      await buildScreen(tester);
      expect(find.text('Yours'), findsOneWidget);
    });

    testWidgets('renders all three cards: Weekly Review, Journal, Resources',
        (tester) async {
      await buildScreen(tester);
      expect(find.text('Weekly Review'), findsOneWidget);
      expect(find.text('Journal'), findsOneWidget);
      expect(find.text('Resources'), findsOneWidget);
    });

    testWidgets('renders the companion in the header', (tester) async {
      await buildScreen(tester);
      expect(find.byType(CompanionWidget), findsOneWidget);
    });
  });
}
