// Play Age Signals API v0.0.3 — Phase A Dart wrapper.
//
// Bridges the Android platform channel implemented in
// `android/app/src/main/kotlin/com/example/ai_buddy_web/PlayAgeSignalsPlugin.kt`
// into a typed Dart surface. On iOS / Web the service short-circuits to
// `AgeSignalStatus.unavailable` — the spec calls for falling back to the
// existing self-attestation path on those platforms.
//
// Phase A is scaffold-only: this service is NOT yet referenced by
// `compliance_service.dart`. Phase B wires it into the region-gated flow.
//
// Spec: docs/integration/PLAY_AGE_SIGNALS_v0_0_3.md

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Verification outcome returned by the Play Age Signals API.
///
/// Mirrors the Kotlin status-string contract in `PlayAgeSignalsPlugin.kt`
/// (`STATUS_VERIFIED_OVER` / `STATUS_VERIFIED_UNDER` / `STATUS_UNVERIFIED` /
/// `STATUS_UNAVAILABLE`).
enum AgeSignalStatus {
  /// Google verified the signed-in user meets or exceeds `requiredAge`.
  verifiedOver,

  /// Google verified the signed-in user is below `requiredAge`.
  verifiedUnder,

  /// The user is signed into Play but no verified signal is available
  /// (e.g. account too new, region without signed Play credentials).
  /// Callers should fall back to self-attestation.
  unverified,

  /// Platform does not support Play Age Signals (iOS, Web), the SDK is
  /// missing at runtime, or the channel raised. Callers should fall back
  /// to self-attestation without surfacing an error to the user.
  unavailable,
}

/// Thin platform-channel wrapper around the Play Age Signals API.
///
/// All methods are `static` because there is no per-instance state; the
/// channel itself is stateless and callers do not need to manage a
/// lifecycle.
class PlayAgeSignalsService {
  PlayAgeSignalsService._();

  @visibleForTesting
  static const MethodChannel channel = MethodChannel(
    'com.gentlequest.www/play_age_signals',
  );

  /// Override the platform check in tests. When `null` (production) the
  /// service uses real `Platform.isAndroid` semantics via `defaultTargetPlatform`.
  @visibleForTesting
  static bool? debugIsAndroidOverride;

  /// Request an age-verification signal from Google Play.
  ///
  /// Returns [AgeSignalStatus.unavailable] on iOS / Web, on any
  /// PlatformException, on a malformed channel response, or when the
  /// underlying SDK is not yet GA (the Phase A scaffold returns
  /// `unavailable` deterministically).
  ///
  /// [requiredAge] defaults to 18 to match GentleQuest's global 18+ gate
  /// (`_kAgeVerifiedKey` in `compliance_service.dart`).
  static Future<AgeSignalStatus> fetchAgeSignal({int requiredAge = 18}) async {
    if (!_isAndroid()) {
      return AgeSignalStatus.unavailable;
    }

    try {
      final dynamic raw = await channel.invokeMethod<dynamic>(
        'getAgeSignals',
        <String, dynamic>{'requiredAge': requiredAge},
      );
      return _parseStatus(raw);
    } on PlatformException catch (e) {
      debugPrint(
        '[PlayAgeSignalsService] PlatformException: ${e.code} ${e.message}',
      );
      return AgeSignalStatus.unavailable;
    } on MissingPluginException catch (e) {
      debugPrint('[PlayAgeSignalsService] MissingPluginException: ${e.message}');
      return AgeSignalStatus.unavailable;
    } catch (e) {
      debugPrint('[PlayAgeSignalsService] Unexpected error: $e');
      return AgeSignalStatus.unavailable;
    }
  }

  static bool _isAndroid() {
    if (debugIsAndroidOverride != null) {
      return debugIsAndroidOverride!;
    }
    if (kIsWeb) {
      return false;
    }
    return defaultTargetPlatform == TargetPlatform.android;
  }

  static AgeSignalStatus _parseStatus(dynamic raw) {
    if (raw is! Map) {
      return AgeSignalStatus.unavailable;
    }
    final String? status = raw['status'] as String?;
    switch (status) {
      case 'verifiedOver':
        return AgeSignalStatus.verifiedOver;
      case 'verifiedUnder':
        return AgeSignalStatus.verifiedUnder;
      case 'unverified':
        return AgeSignalStatus.unverified;
      case 'unavailable':
        return AgeSignalStatus.unavailable;
      default:
        return AgeSignalStatus.unavailable;
    }
  }
}
