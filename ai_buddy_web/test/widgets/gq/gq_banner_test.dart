import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/gq/gq_banner.dart';

void main() {
  Widget host(Widget child) => MaterialApp(home: Scaffold(body: child));

  testWidgets('inline GQBanner renders message for every category', (tester) async {
    for (final category in GQBannerCategory.values) {
      await tester.pumpWidget(host(GQBanner(message: 'msg-${category.name}', category: category)));
      await tester.pump();
      expect(find.text('msg-${category.name}'), findsOneWidget);
    }
  });

  testWidgets('onDismiss renders a close control that fires the callback', (tester) async {
    var dismissed = false;
    await tester.pumpWidget(host(GQBanner(message: 'Dismissible', onDismiss: () => dismissed = true)));
    await tester.tap(find.byIcon(Icons.close_rounded));
    await tester.pumpAndSettle();
    expect(dismissed, isTrue);
  });

  testWidgets('null onDismiss renders no close control', (tester) async {
    await tester.pumpWidget(host(const GQBanner(message: 'Sticky')));
    expect(find.byIcon(Icons.close_rounded), findsNothing);
  });

  testWidgets('GQBanner.show inserts an overlay banner and auto-dismisses after duration', (tester) async {
    await tester.pumpWidget(host(Builder(
      builder: (context) => ElevatedButton(
        onPressed: () => GQBanner.show(
          context,
          message: 'Overlay message',
          duration: const Duration(milliseconds: 500),
        ),
        child: const Text('fire'),
      ),
    )));

    await tester.tap(find.text('fire'));
    await tester.pump(); // build the OverlayEntry
    await tester.pump(); // post-frame callback flips _visible
    await tester.pump(const Duration(milliseconds: 350)); // mid slide-in
    expect(find.text('Overlay message'), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 600)); // past the 500ms auto-dismiss timer
    await tester.pumpAndSettle();
    expect(find.text('Overlay message'), findsNothing);
  });

  testWidgets('eyebrow and icon override render, and child slot renders below message', (tester) async {
    await tester.pumpWidget(host(const GQBanner(
      message: 'Body text',
      eyebrow: "we're here",
      icon: Icons.favorite_border,
      child: Text('embedded widget'),
    )));
    expect(find.text("WE'RE HERE"), findsOneWidget);
    expect(find.text('Body text'), findsOneWidget);
    expect(find.text('embedded widget'), findsOneWidget);
    expect(find.byIcon(Icons.favorite_border), findsOneWidget);
  });

  testWidgets('no child renders no extra content below message', (tester) async {
    await tester.pumpWidget(host(const GQBanner(message: 'Just a message')));
    expect(find.text('Just a message'), findsOneWidget);
  });
}
