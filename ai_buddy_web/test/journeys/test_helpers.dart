import 'package:shared_preferences/shared_preferences.dart';

/// Sets SharedPreferences to bypass welcome + compliance gates.
/// Use in setUp() for tests that start from HomeShell.
Future<void> setUpBypassedPrefs() async {
  SharedPreferences.setMockInitialValues({
    'has_seen_welcome_v1': true,
    'compliance_age_verified_18_plus': true,
    'compliance_location_verified': true,
    'compliance_verified_region': 'CA',
    'compliance_verification_timestamp': DateTime.now().millisecondsSinceEpoch,
    'legal_ack_v1': true,
  });
}

/// Sets SharedPreferences to simulate a fresh install (no prefs set).
Future<void> setUpFreshInstall() async {
  SharedPreferences.setMockInitialValues({});
}
