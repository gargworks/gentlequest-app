// mdm_detection_service.dart — R1D11 Compliance Extensions
// Design source: docs/design/refs/htmls/GentleQuest_Compliance_Extensions.html §B
// Principle: P6 — Crisis never blocks.
//
// MDM Detection Service — UI stub only.
//
// ⚠️  BACKEND FOLLOW-UP REQUIRED (flagged for Lokesh review)
// Real MDM detection requires platform-channel calls:
//   • iOS:     UIDevice.current.isSupervised (requires entitlement + private API)
//   • Android: DevicePolicyManager.isDeviceOwnerApp / isProfileOwnerApp
//   • Samsung Knox: Knox SDK container API check
//
// Until the platform channels are wired, this stub returns `false` so the
// ManagedDeviceBlock UI (State B) is never shown in production.
// Flip `_stubReturnsMdm` to `true` in debug builds for manual UI testing.
//
// ADR reference: Backend follow-up to wire real MDM signals (post R1D11).

import 'package:flutter/foundation.dart';

class MdmDetectionService {
  MdmDetectionService._();

  // ── Stub control ────────────────────────────────────────────────────────────
  // Set to true in local debug builds to preview State B (ManagedDeviceBlock).
  // NEVER ship with this set to true.
  static const bool _stubReturnsMdm =
      bool.fromEnvironment('DEV_STUB_MDM', defaultValue: false);

  // ── Public API ───────────────────────────────────────────────────────────────

  /// Returns `true` if the device is managed by an MDM profile.
  ///
  /// **Stub:** always returns `false` in production.
  /// Activate the stub via: `flutter run --dart-define=DEV_STUB_MDM=true`
  ///
  /// Real implementation requires native platform channels — see file header.
  static Future<bool> isManagedDevice() async {
    if (kDebugMode && _stubReturnsMdm) {
      debugPrint('MdmDetectionService: DEV_STUB_MDM active — returning true.');
      return true;
    }
    // TODO(backend): wire iOS supervised / Android device-owner / Knox checks
    // via MethodChannel before enabling MDM detection in production.
    return false;
  }
}
