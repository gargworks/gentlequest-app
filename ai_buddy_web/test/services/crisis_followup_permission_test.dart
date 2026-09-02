import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest_all.dart' as tz_data;

import 'package:ai_buddy_web/services/notification_service_impl.dart';

/// Opposed-pair test for the permission guard added to
/// `scheduleCrisisFollowup` on 2026-09-02.
///
/// This is the ONLY scheduled notification category not reached via a Settings
/// toggle, and the toggles were the only callers of `requestPermissions()`.
/// Before the fix, a fresh-install user could signal "check on me later" in the
/// Q9 crisis bridge and we would schedule a follow-up the OS then silently
/// discarded.  These two tests pin the guard:
///
///   1. PERMISSION GRANTED → `zonedSchedule` IS reached.
///   2. PERMISSION DENIED  → `zonedSchedule` is NEVER reached, and the call
///      returns normally without throwing.
///
/// The flutter_local_notifications plugin talks over a MethodChannel named
/// `'dexterous.com/flutter/local_notifications'` (verified in the plugin
/// source at `~/.pub-cache/.../flutter_local_notifications-17.2.4/lib/src/
/// platform_flutter_local_notifications.dart:33`).  We mock that channel,
/// record every invoked method name, and assert on the presence/absence of
/// `'zonedSchedule'` (the real scheduling method name, verified at line 207
/// of the same file).  The Android permission method is
/// `'requestNotificationsPermission'` (line 182), not `'requestPermissions'`
/// (that's the iOS variant at line 657/870).
void main() {
  const channel = MethodChannel('dexterous.com/flutter/local_notifications');

  setUp(() {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    // `data/latest_all.dart` embeds the timezone database as Dart constants —
    // no asset-bundle load needed, so this works in a pure unit test.
    tz_data.initializeTimeZones();
    // The permission branch in requestPermissions() is Android-specific
    // (line 325 of notification_service_impl.dart).
    debugDefaultTargetPlatformOverride = TargetPlatform.android;
  });

  tearDown(() {
    debugDefaultTargetPlatformOverride = null;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  /// Sets up a channel mock that records every MethodCall and returns
  /// [granted] for the Android permission request.
  List<MethodCall> installMock({required bool granted}) {
    final calls = <MethodCall>[];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call);
      // Android permission ask (real method name from plugin source line 182)
      if (call.method == 'requestNotificationsPermission') return granted;
      // Plugin init (line 143) — must return true so the plugin considers
      // itself initialized.
      if (call.method == 'initialize') return true;
      // Launch-details query (line 51) — null is a valid "no launch" answer.
      if (call.method == 'getNotificationAppLaunchDetails') return null;
      // createNotificationChannel, cancel, zonedSchedule, etc. → null is fine
      // for void-returning methods.
      return null;
    });
    return calls;
  }

  test(
      'scheduleCrisisFollowup: permission GRANTED → zonedSchedule IS called',
      () async {
    final calls = installMock(granted: true);

    await NotificationService.scheduleCrisisFollowup();

    expect(
      calls.any((c) => c.method == 'zonedSchedule'),
      isTrue,
      reason: 'Permission was granted; a crisis follow-up notification MUST be '
          'scheduled. Methods called: ${calls.map((c) => c.method).toList()}',
    );
  });

  test(
      'scheduleCrisisFollowup: permission DENIED → zonedSchedule is NOT '
      'called and the call returns normally', () async {
    final calls = installMock(granted: false);

    // Must not throw — the denied path should return gracefully.
    await NotificationService.scheduleCrisisFollowup();

    expect(
      calls.any((c) => c.method == 'zonedSchedule'),
      isFalse,
      reason: 'Permission was DENIED; nothing may be scheduled, because the OS '
          'would silently discard it and the user would believe a follow-up is '
          'coming. Methods called: ${calls.map((c) => c.method).toList()}',
    );

    // The permission MUST actually have been asked for — the whole point of
    // the fix. Without this, deleting the requestPermissions() call would
    // still leave the assertion above passing (nothing scheduled), so the
    // test would silently stop testing the thing it exists to test.
    expect(
      calls.any((c) => c.method == 'requestNotificationsPermission'),
      isTrue,
      reason: 'scheduleCrisisFollowup must REQUEST permission, not assume it. '
          'Methods called: ${calls.map((c) => c.method).toList()}',
    );
  });
}
