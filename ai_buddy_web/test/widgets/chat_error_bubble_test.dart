import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/chat_error_bubble.dart';

void main() {
  group('ChatErrorBubble — failed state', () {
    testWidgets('renders title, body, and retry button', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChatErrorBubble(
              state: ChatErrorState.failed,
              onRetry: () {},
            ),
          ),
        ),
      );

      expect(find.text('That didn\u2019t reach me'), findsOneWidget);
      expect(
        find.textContaining('Your message is saved'),
        findsOneWidget,
      );
      expect(find.text('Try again'), findsOneWidget);
    });

    testWidgets('retry button is at least 44px tall', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChatErrorBubble(
              state: ChatErrorState.failed,
              onRetry: () {},
            ),
          ),
        ),
      );

      // The primary button is an InkWell with a minHeight-44 constraint.
      // Find the InkWell and verify its rendered height.
      final InkWell button =
          tester.widget<InkWell>(find.byType(InkWell).first);
      expect(button.onTap, isNotNull);

      // Measure the button container height by finding the Container with
      // minHeight constraint inside the first InkWell.
      final containers = tester.widgetList<Container>(
        find.descendant(
          of: find.byType(InkWell).first,
          matching: find.byType(Container),
        ),
      );
      double? buttonHeight;
      for (final c in containers) {
        if (c.constraints is BoxConstraints) {
          final bc = c.constraints as BoxConstraints;
          if (bc.minHeight == 44) {
            buttonHeight = tester.getSize(find.byWidget(c)).height;
            break;
          }
        }
      }
      expect(buttonHeight, isNotNull, reason: 'Should find a 44-min-height container');
      expect(buttonHeight! >= 44, isTrue,
          reason: 'Retry button must be at least 44px tall');
    });

    testWidgets('secondary button is present', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChatErrorBubble(
              state: ChatErrorState.failed,
              onRetry: () {},
            ),
          ),
        ),
      );

      expect(find.text('Something else instead'), findsOneWidget);
    });
  });

  group('ChatErrorBubble — unreachable state', () {
    testWidgets('renders different copy from failed state', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChatErrorBubble(
              state: ChatErrorState.unreachable,
              onRetry: () {},
            ),
          ),
        ),
      );

      // Unreachable-specific title
      expect(find.text('Still not connecting'), findsOneWidget);
      // Unreachable-specific body
      expect(
        find.textContaining('This one is on our side'),
        findsOneWidget,
      );
      // Unreachable-specific primary button
      expect(find.text('Try once more'), findsOneWidget);
      // Unreachable-specific secondary button
      expect(find.text('Use the offline tools'), findsOneWidget);

      // Verify failed-state copy is NOT present
      expect(find.text('That didn\u2019t reach me'), findsNothing);
      expect(find.text('Try again'), findsNothing);
    });
  });

  group('ChatErrorBubble — action row visibility', () {
    testWidgets('hides action row when showActions is false', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChatErrorBubble(
              state: ChatErrorState.failed,
              onRetry: () {},
              showActions: false,
            ),
          ),
        ),
      );

      // Title and body still present
      expect(find.text('That didn\u2019t reach me'), findsOneWidget);
      // Action buttons absent
      expect(find.text('Try again'), findsNothing);
      expect(find.text('Something else instead'), findsNothing);
    });
  });

  group('ChatErrorBubble — tap callback', () {
    testWidgets('fires onRetry when primary button is tapped', (tester) async {
      bool retried = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChatErrorBubble(
              state: ChatErrorState.failed,
              onRetry: () => retried = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('Try again'));
      await tester.pump();
      expect(retried, isTrue);
    });
  });
}
