import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest_all.dart' as tz_data;

import 'package:ai_buddy_web/services/notification_service_impl.dart';

/// Pins `NotificationService.hasPermission()`, added 2026-09-03.
///
/// Permission used to be checked ONLY at the instant a Settings toggle was
/// flipped on. If the user later revoked notifications in OS settings, the
/// stored pref still said "on" and Settings kept displaying "on" while the OS
/// dropped every scheduled notification — someone could believe a check-in was
/// coming when nothing was. Settings now reconciles against this query on
/// entry.
///
/// The three-way contract is the whole point, so all three are pinned:
///   granted -> true, revoked -> false, unknown -> null.
/// null must NOT collapse to false: the caller switches toggles OFF on false,
/// so a null-means-denied bug would silently kill reminders a user did grant.
void main() {
  const channel = MethodChannel('dexterous.com/flutter/local_notifications');

  setUp(() {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    tz_data.initializeTimeZones();
    debugDefaultTargetPlatformOverride = TargetPlatform.android;
  });

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
    debugDefaultTargetPlatformOverride = null;
  });

  /// Mocks the plugin channel, answering `areNotificationsEnabled` with
  /// [enabled] — or throwing if [throws] is set.
  void mockChannel({Object? enabled, bool throws = false}) {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      if (call.method == 'areNotificationsEnabled') {
        if (throws) throw PlatformException(code: 'boom');
        return enabled;
      }
      // The plugin only considers itself initialized if this returns true;
      // without it _ensureInited() fails and hasPermission() reports null,
      // which would make the "unknown" controls below pass for the wrong
      // reason.
      if (call.method == 'initialize') return true;
      if (call.method == 'getNotificationAppLaunchDetails') return null;
      return null;
    });
  }

  test('permission granted -> true', () async {
    mockChannel(enabled: true);
    expect(await NotificationService.hasPermission(), isTrue);
  });

  test('permission revoked in OS settings -> false', () async {
    mockChannel(enabled: false);
    expect(await NotificationService.hasPermission(), isFalse,
        reason: 'This false is what tells Settings to switch the reminder '
            'toggles off. Without it the UI keeps claiming a check-in is '
            'coming while the OS drops every notification.');
  });

  test('OPPOSED CONTROL: unknown answer -> null, NOT false', () async {
    mockChannel(enabled: null);
    expect(await NotificationService.hasPermission(), isNull,
        reason: 'null means "we do not know" and the caller must leave the '
            'user alone. If this ever returns false, every unknown answer '
            'silently switches OFF reminders the user actually granted — the '
            'same harm in the other direction.');
  });

  test('OPPOSED CONTROL: a channel throw -> null, NOT false', () async {
    mockChannel(throws: true);
    expect(await NotificationService.hasPermission(), isNull,
        reason: 'A platform error is not evidence of denial.');
  });
}
