// Phase A unit tests for the Play Age Signals platform-channel wrapper.
//
// Covers the four code paths defined in the Phase A directive:
//   1. Non-Android platforms short-circuit to `unavailable`.
//   2. Android + `verifiedOver` response → `AgeSignalStatus.verifiedOver`.
//   3. Android + `verifiedUnder` response → `AgeSignalStatus.verifiedUnder`.
//   4. Android + channel exception → `AgeSignalStatus.unavailable`.
//
// Spec: docs/integration/PLAY_AGE_SIGNALS_v0_0_3.md

import 'package:ai_buddy_web/services/play_age_signals_service.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  final TestDefaultBinaryMessenger messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;

  tearDown(() {
    // Reset the platform override and clear any mock handlers so test
    // order does not affect results.
    PlayAgeSignalsService.debugIsAndroidOverride = null;
    messenger.setMockMethodCallHandler(PlayAgeSignalsService.channel, null);
  });

  group('PlayAgeSignalsService.fetchAgeSignal', () {
    test('returns unavailable on non-Android platforms without touching channel',
        () async {
      PlayAgeSignalsService.debugIsAndroidOverride = false;

      var handlerInvoked = false;
      messenger.setMockMethodCallHandler(
        PlayAgeSignalsService.channel,
        (MethodCall _) async {
          handlerInvoked = true;
          return <String, dynamic>{'status': 'verifiedOver'};
        },
      );

      final AgeSignalStatus status =
          await PlayAgeSignalsService.fetchAgeSignal();

      expect(status, AgeSignalStatus.unavailable);
      expect(handlerInvoked, isFalse,
          reason:
              'Non-Android platforms must short-circuit without invoking the channel.');
    });

    test('parses verifiedOver response on Android', () async {
      PlayAgeSignalsService.debugIsAndroidOverride = true;
      messenger.setMockMethodCallHandler(
        PlayAgeSignalsService.channel,
        (MethodCall call) async {
          expect(call.method, 'getAgeSignals');
          expect(call.arguments, <String, dynamic>{'requiredAge': 18});
          return <String, dynamic>{'status': 'verifiedOver'};
        },
      );

      final AgeSignalStatus status =
          await PlayAgeSignalsService.fetchAgeSignal();

      expect(status, AgeSignalStatus.verifiedOver);
    });

    test('parses verifiedUnder response on Android', () async {
      PlayAgeSignalsService.debugIsAndroidOverride = true;
      messenger.setMockMethodCallHandler(
        PlayAgeSignalsService.channel,
        (MethodCall call) async {
          expect(call.method, 'getAgeSignals');
          return <String, dynamic>{
            'status': 'verifiedUnder',
            'errorCode': null,
          };
        },
      );

      final AgeSignalStatus status =
          await PlayAgeSignalsService.fetchAgeSignal(requiredAge: 18);

      expect(status, AgeSignalStatus.verifiedUnder);
    });

    test('returns unavailable when the channel throws PlatformException',
        () async {
      PlayAgeSignalsService.debugIsAndroidOverride = true;
      messenger.setMockMethodCallHandler(
        PlayAgeSignalsService.channel,
        (MethodCall _) async {
          throw PlatformException(
            code: 'TEST_ERROR',
            message: 'simulated SDK failure',
          );
        },
      );

      final AgeSignalStatus status =
          await PlayAgeSignalsService.fetchAgeSignal();

      expect(status, AgeSignalStatus.unavailable);
    });
  });
}
