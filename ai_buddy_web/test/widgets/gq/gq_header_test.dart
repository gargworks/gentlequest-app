import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/widgets/gq/gq_header.dart';

void main() {
  testWidgets('renders title and a back button that pops the route', (tester) async {
    await tester.pumpWidget(MaterialApp(
      navigatorKey: GlobalKey<NavigatorState>(),
      home: Builder(
        builder: (context) => Scaffold(
          appBar: const GQHeader(title: 'Journal'),
          body: Center(
            child: ElevatedButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => Scaffold(appBar: const GQHeader(title: 'Detail'))),
              ),
              child: const Text('push'),
            ),
          ),
        ),
      ),
    ));

    expect(find.text('Journal'), findsOneWidget);

    await tester.tap(find.text('push'));
    await tester.pumpAndSettle();
    expect(find.text('Detail'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.arrow_back_ios_new_rounded));
    await tester.pumpAndSettle();
    expect(find.text('Journal'), findsOneWidget);
  });

  testWidgets('showBack: false hides the back button', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(appBar: GQHeader(title: 'Root', showBack: false)),
    ));
    expect(find.byIcon(Icons.arrow_back_ios_new_rounded), findsNothing);
  });

  testWidgets('preferredSize matches kToolbarHeight', (tester) async {
    const header = GQHeader(title: 'X');
    expect(header.preferredSize.height, kToolbarHeight);
  });
}
