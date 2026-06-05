// Widget tests for AgeVerificationBlockedScreen — v1.4.0 Phase C.
//
// Coverage:
//   1. Renders headline + body copy + CTA + support link.
//   2. CTA is present and tappable (we do NOT actually invoke
//      SystemNavigator/exit — those are platform-side and would tear down
//      the test binding).
//   3. Support-link tap invokes url_launcher with the expected
//      `mailto:support@gentlequest.app` URI.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_buddy_web/screens/age_verification_blocked_screen.dart';

void main() {
  group('AgeVerificationBlockedScreen', () {
    testWidgets('renders headline, body, CTA, and support link',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: AgeVerificationBlockedScreen()),
      );

      // Headline.
      expect(find.text('Sorry — GentleQuest is for adults'), findsOneWidget);

      // Body copy — match a stable substring (full string contains the
      // support email, which we assert separately via the address constant).
      expect(
        find.textContaining(
          "This app requires verification that you're 18 or older",
        ),
        findsOneWidget,
      );
      expect(
        find.textContaining(AgeVerificationBlockedScreen.supportEmail),
        findsOneWidget,
      );

      // Primary CTA + support link.
      expect(find.text('Close app'), findsOneWidget);
      expect(find.text('Contact support'), findsOneWidget);
      expect(find.byKey(const Key('age_blocked_close_button')), findsOneWidget);
      expect(
        find.byKey(const Key('age_blocked_support_link')),
        findsOneWidget,
      );
    });

    testWidgets('Close-app CTA is present and tappable',
        (WidgetTester tester) async {
      // Install a no-op override so tapping doesn't terminate the test
      // process via exit(0) on the host binding (macOS/Linux/CI).
      int closeInvocations = 0;
      AgeVerificationBlockedScreen.debugCloseAppOverride = () {
        closeInvocations += 1;
      };
      addTearDown(() {
        AgeVerificationBlockedScreen.debugCloseAppOverride = null;
      });

      await tester.pumpWidget(
        const MaterialApp(home: AgeVerificationBlockedScreen()),
      );

      final button = find.byKey(const Key('age_blocked_close_button'));
      expect(button, findsOneWidget);

      // Confirm the underlying widget is an ElevatedButton with a non-null
      // onPressed callback — i.e. it is enabled and tappable.
      final ElevatedButton elevated = tester.widget<ElevatedButton>(button);
      expect(elevated.onPressed, isNotNull);

      // Tap routes to the override (NOT SystemNavigator/exit).
      await tester.tap(button);
      await tester.pump();
      expect(closeInvocations, 1);
    });

    testWidgets('Contact-support link launches mailto URI',
        (WidgetTester tester) async {
      // url_launcher uses the `plugins.flutter.io/url_launcher` channel.
      // Capture the call args so we can assert on the URI.
      final messenger =
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
      final List<MethodCall> calls = <MethodCall>[];
      const MethodChannel urlLauncherChannel =
          MethodChannel('plugins.flutter.io/url_launcher');

      messenger.setMockMethodCallHandler(
        urlLauncherChannel,
        (MethodCall call) async {
          calls.add(call);
          // url_launcher's `launch` / `canLaunch` both expect bool return.
          if (call.method == 'canLaunch') return true;
          if (call.method == 'launch') return true;
          return null;
        },
      );

      addTearDown(() {
        messenger.setMockMethodCallHandler(urlLauncherChannel, null);
      });

      await tester.pumpWidget(
        const MaterialApp(home: AgeVerificationBlockedScreen()),
      );

      await tester.tap(find.byKey(const Key('age_blocked_support_link')));
      await tester.pumpAndSettle();

      // Expect at least one channel call mentioning the support address.
      // url_launcher_platform_interface dispatches via the channel; payload
      // shape varies by version, so we assert on a stable substring of the
      // serialized arguments.
      expect(calls, isNotEmpty,
          reason: 'Expected url_launcher channel to be invoked');
      final bool sawMailto = calls.any((MethodCall c) {
        final String argsStr = c.arguments.toString();
        return argsStr.contains('mailto:') &&
            argsStr.contains(AgeVerificationBlockedScreen.supportEmail);
      });
      expect(
        sawMailto,
        isTrue,
        reason:
            'Expected a url_launcher call carrying mailto:${AgeVerificationBlockedScreen.supportEmail}, '
            'got: $calls',
      );
    });
  });
}
