import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/screens/resource_library_screen.dart';
import 'test_helpers.dart';

void main() {
  group('J12: ResourceLibraryScreen', () {
    setUp(setUpBypassedPrefs);

    Widget buildLibrary() {
      return MaterialApp(
        routes: {
          '/interactive-chat': (_) => const Scaffold(body: Text('Chat')),
        },
        home: const Scaffold(body: ResourceLibraryScreen()),
      );
    }

    testWidgets('ResourceLibraryScreen renders without crash', (tester) async {
      await tester.pumpWidget(buildLibrary());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.byType(ResourceLibraryScreen), findsOneWidget);
    });

    testWidgets('no layout error on initial render', (tester) async {
      await tester.pumpWidget(buildLibrary());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Breathing" filter chip is present', (tester) async {
      await tester.pumpWidget(buildLibrary());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.text('Breathing'), findsWidgets);
    });

    testWidgets('"Grounding" filter chip is present', (tester) async {
      await tester.pumpWidget(buildLibrary());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.text('Grounding'), findsWidgets);
    });

    testWidgets('"Sleep" filter chip is present', (tester) async {
      await tester.pumpWidget(buildLibrary());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      expect(find.text('Sleep'), findsWidgets);
    });

    testWidgets('"Breathing" filter chip tap does not crash', (tester) async {
      await tester.pumpWidget(buildLibrary());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text('Breathing').first, warnIfMissed: false);
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('"Grounding" filter chip tap does not crash', (tester) async {
      await tester.pumpWidget(buildLibrary());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text('Grounding').first, warnIfMissed: false);
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });

    testWidgets('Quick wins exposes and opens Loop reset', (tester) async {
      await tester.pumpWidget(buildLibrary());
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump();

      await tester.tap(find.text('Quick wins'));
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('Loop reset'), findsOneWidget);
      final loopResetCard = find.byKey(const ValueKey('rumination_reset_card'));
      await tester.ensureVisible(loopResetCard);
      await tester.pump(const Duration(milliseconds: 500));
      await tester.tap(loopResetCard);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 500));

      expect(find.text('Your mind is looping.'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  });
}
