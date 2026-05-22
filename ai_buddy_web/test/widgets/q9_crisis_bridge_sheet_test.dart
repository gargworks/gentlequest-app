import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/widgets/q9_crisis_bridge_sheet.dart';

void main() {
  group('Q9CrisisBridgeSheet', () {
    testWidgets('renders the three branches + 988 pill', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (ctx) => ElevatedButton(
                onPressed: () => Q9CrisisBridgeSheet.show(ctx),
                child: const Text('open'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      expect(find.textContaining("I'm safe"), findsOneWidget);
      expect(find.textContaining('talk to someone now'), findsOneWidget);
      expect(find.textContaining('heavy moment'), findsOneWidget);
      expect(find.textContaining('Call 988'), findsOneWidget);
    });

    testWidgets('keepGoing returns Q9BridgeAction.keepGoing', (tester) async {
      Q9BridgeAction? result;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (ctx) => ElevatedButton(
                onPressed: () async =>
                    result = await Q9CrisisBridgeSheet.show(ctx),
                child: const Text('open'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      await tester.tap(find.textContaining("I'm safe"));
      await tester.pumpAndSettle();
      expect(result, Q9BridgeAction.keepGoing);
    });

    testWidgets('talkNow returns Q9BridgeAction.talkNow', (tester) async {
      Q9BridgeAction? result;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (ctx) => ElevatedButton(
                onPressed: () async =>
                    result = await Q9CrisisBridgeSheet.show(ctx),
                child: const Text('open'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      await tester.tap(find.textContaining('talk to someone now'));
      await tester.pumpAndSettle();
      expect(result, Q9BridgeAction.talkNow);
    });

    testWidgets('heavyMoment returns Q9BridgeAction.heavyMoment',
        (tester) async {
      Q9BridgeAction? result;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (ctx) => ElevatedButton(
                onPressed: () async =>
                    result = await Q9CrisisBridgeSheet.show(ctx),
                child: const Text('open'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      await tester.tap(find.textContaining('heavy moment'));
      await tester.pumpAndSettle();
      expect(result, Q9BridgeAction.heavyMoment);
    });

    testWidgets('not dismissible by tap-outside', (tester) async {
      Q9BridgeAction? result = Q9BridgeAction.keepGoing; // start non-null
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (ctx) => ElevatedButton(
                onPressed: () async =>
                    result = await Q9CrisisBridgeSheet.show(ctx),
                child: const Text('open'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      // Tap above the sheet (should not dismiss)
      await tester.tapAt(const Offset(20, 20));
      await tester.pumpAndSettle();
      // Sheet still up — bridge headline still visible
      expect(find.textContaining('A QUIET PAUSE'), findsOneWidget);
      expect(result, Q9BridgeAction.keepGoing); // unchanged
    });
  });
}
