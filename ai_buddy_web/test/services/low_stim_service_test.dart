import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/services/low_stim_service.dart';

/// Low-stim "quiet mode" service tests (v1.5.0 ADHD update, ADR-006).
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    // Fresh mock prefs + reset the static notifier before every test so
    // tests don't leak state through the shared static across the suite.
    SharedPreferences.setMockInitialValues({});
    LowStimService.lowStimNotifier.value = false;
  });

  group('LowStimService', () {
    test('defaults to disabled before hydrate()', () {
      expect(LowStimService.enabled, isFalse);
    });

    test('hydrate() reads a persisted true value into the notifier',
        () async {
      SharedPreferences.setMockInitialValues({
        LowStimService.kLowStimModeKey: true,
      });

      await LowStimService.hydrate();

      expect(LowStimService.enabled, isTrue);
    });

    test('hydrate() leaves default (false) when no pref is set', () async {
      await LowStimService.hydrate();

      expect(LowStimService.enabled, isFalse);
    });

    test('setEnabled(true) updates the notifier immediately', () async {
      final result = LowStimService.setEnabled(true);

      // Notifier updates synchronously, before the persistence await resolves.
      expect(LowStimService.enabled, isTrue);
      expect(await result, isTrue);
    });

    test('setEnabled persists across a fresh hydrate() (round-trip)',
        () async {
      await LowStimService.setEnabled(true);

      // Simulate a cold app relaunch: reset the in-memory notifier, then
      // hydrate from the (now-persisted) SharedPreferences state.
      LowStimService.lowStimNotifier.value = false;
      await LowStimService.hydrate();

      expect(LowStimService.enabled, isTrue);
    });

    test('setEnabled(false) after true round-trips correctly', () async {
      await LowStimService.setEnabled(true);
      await LowStimService.setEnabled(false);

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool(LowStimService.kLowStimModeKey), isFalse);
      expect(LowStimService.enabled, isFalse);
    });
  });
}
