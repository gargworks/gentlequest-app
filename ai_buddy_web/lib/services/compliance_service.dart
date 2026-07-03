import 'package:shared_preferences/shared_preferences.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import 'package:flutter/foundation.dart';
import 'package:ai_buddy_web/services/firebase_service.dart';
import 'package:ai_buddy_web/services/api_service.dart';
import 'package:ai_buddy_web/services/play_age_signals_service.dart';

/// Compliance Status for the Pragmatic Defense v3.0 Strategy
/// 
/// Based on research-verified legal requirements as of Feb 2026:
/// - Illinois: HARD BAN (WOPR Act, $10K/violation)
/// - Utah, Washington: TEMP BLOCK (pending Phase 2 compliance features)
/// - Colorado, UK, all other states: ALLOWED
/// - EU/AUS/China: Store-level exclusion (no in-app code)
enum ComplianceStatus {
  allowed,
  loading,
  ageVerificationRequired,
  locationPermissionRequired,
  locationServicesDisabled,
  blockedRegion,
  blockedAge,
  error,
  // Retained for backwards compatibility with anything that switches on
  // this enum, but no compliance path returns it anymore (was the web →
  // mobile-only hard bounce, removed 2026-05-21). If we ever need a true
  // "your platform can't be served" terminal state again, re-wire here.
  conversionRequired,
}

/// Block reason for analytics and future unlock logic
enum BlockReason {
  hardBan,           // No legal path to operate (Illinois)
  pendingCompliance, // Can unlock when Phase 2 compliance is built (Utah, Washington)
  none,              // Allowed
}

class ComplianceService {
  // ============================================
  // PREFERENCE KEYS
  // ============================================
  // Key name says "18_plus" and that's accurate: v1.3.0 (operator decision)
  // enforces 18+ everywhere via _kMinAgeUniversal below. A 2026-05-21
  // proposal briefly lowered this to a 13+/region-aware floor; it was
  // reverted before shipping, and the universal 18+ policy below is what's
  // actually live. The *bool value* just means "user attested to be of
  // acceptable age for their region" (today, that's always 18) — the key
  // name is otherwise cosmetic. The one-tap attestation UI
  // (welcome_screen.dart) briefly drifted out of sync with the reversion —
  // shipped asking "I'm 13 or older" — fixed 2026-07-02 (PR #172).
  static const String _kAgeVerifiedKey = 'compliance_age_verified_18_plus';
  static const String _kLocationVerifiedKey = 'compliance_location_verified';
  static const String _kVerifiedRegionKey = 'compliance_verified_region';
  static const String _kVerificationTimestampKey = 'compliance_verification_timestamp';

  // ============================================
  // v1.4.0 — VERIFIED AGE-SIGNAL CACHE (Phase B)
  // ============================================
  // Regions that mandate a verified age signal (in addition to self-attestation).
  // Texas SB 2420 (signed 2026-06-02, enforcement window mid-Jun → mid-Jul 2026)
  // requires platforms to consult an age-signal API where available; the
  // self-attestation alone is no longer sufficient for users in these regions.
  // Add new regions here as legislation lands; keep this set ASCII region names
  // matching whatever `_kVerifiedRegionKey` stores (placemark.administrativeArea
  // from reverse-geocode → full name like "Texas"; IP-region check → backend
  // string).
  static const Set<String> _kRegionsRequiringVerifiedSignal = {
    'Texas',
    'TX',
  };

  // Cache keys for the most-recent Play Age Signals result. We re-query at
  // most once per 24h to avoid hammering the SDK on every cold start; the
  // signal itself is a high-latency network call on Android.
  static const String _kAgeSignalStatusKey = 'compliance_age_signal_status_v1';
  static const String _kAgeSignalCachedAtKey = 'compliance_age_signal_cached_at_v1';
  static const Duration _kAgeSignalCacheTtl = Duration(hours: 24);

  // ============================================
  // AGE-GATE THRESHOLD — universal 18+ (v1.3.0)
  // ============================================
  // Current, live behavior: 18+ everywhere, no regional differentiation.
  // This is an operator decision, not a per-region legal minimum — chosen
  // to match GentleQuest's store rating (17+/Mature), match the privacy
  // policy's stated 18+ floor, and sidestep COPPA / GDPR-K / minor-data
  // regulatory complexity entirely instead of building region-aware
  // handling for it.
  //
  // History (reverted, kept for context only): a 2026-05-21 proposal
  // explored lowering the floor to 13 (US COPPA / UK ICO digital age of
  // consent) with region-specific step-ups to 16 or 18 where mandated —
  // e.g. India (DPDP 2023, parental-consent flow required below 18),
  // GDPR-K EU member states (DE/FR/IT/NL/IE/LU/HU/LT/PL/RO/SK/CY/HR/EL:
  // 16+), Australia (eSafety Commissioner guidance suggests 13+). That
  // proposal was reverted before shipping in favor of the universal-18+
  // decision below; none of the region-specific thresholds it would have
  // required were ever built. The one-tap attestation UI
  // (welcome_screen.dart) briefly drifted out of sync with the reversion —
  // shipped asking "I'm 13 or older" — fixed 2026-07-02 (PR #172).
  //
  // If region-aware age gating is revisited, re-verify every citation
  // above against current law rather than trusting this comment — it's
  // already over a month old.
  static const int _kMinAgeUniversal = 18;

  /// Minimum age (years) before a user can use the app.
  /// v1.3.0 operator decision: 18+ everywhere — matches privacy policy,
  /// avoids COPPA / GDPR-K / minor-data regulatory complexity.
  /// Region-differentiation deferred to v1.4.0 pending legal review.
  static int minAgeForRegion(String? region) {
    return _kMinAgeUniversal; // 18 everywhere
  }

  // ============================================
  // 🔴 HARD BAN STATES (Permanent GPS Block)
  // No legal operating path without licensed partnerships.
  // ============================================
  // Illinois: WOPR Act (HB1806), effective Aug 1, 2025
  // - Bans AI therapy/emotion detection by unlicensed entities
  // - Penalty: $10,000 per violation
  // ============================================
  static const Set<String> _hardBanStates = {
    'IL', 'Illinois',
  };

  // ============================================
  // 🟡 TEMP BLOCK STATES (Pending Compliance)
  // Can be unlocked when Phase 2 compliance features are built.
  // ============================================
  // Utah: HB 452, effective May 7, 2025
  // - Requires: Safety policy filed with state, licensed therapist review
  // - Penalty: $2,500/violation
  // 
  // Washington: MHMDA, effective Mar 31, 2024
  // - Requires: Standalone health data privacy policy, opt-in consent
  // - Penalty: Private right of action
  // ============================================
  static const Set<String> _pendingComplianceStates = {
    'UT', 'Utah',
    'WA', 'Washington',
  };

  // ============================================
  // 🟢 ALLOWED JURISDICTIONS (no code needed)
  // ============================================
  // Colorado: AI Act delayed to June 30, 2026 - NOT APPLICABLE
  // UK: Online Safety Act - adults allowed with disclosure
  // California: CCPA applies, standard privacy compliance
  // All other US states: No specific AI MH legislation
  // 
  // 🔵 STORE-LEVEL EXCLUSIONS (handled by App Store/Play Console)
  // EU, Australia, China - no in-app code needed
  // ============================================

  // ============================================
  // ONE-TIME VERIFICATION CONFIG
  // ============================================
  // Phase 1+2 Redesign: Extended from 24h to 168h (7 days) to reduce GPS bounce rate
  static const int _reVerificationHours = 168;

  // GPS retry counter — after 2 failures, offer IP-based fallback
  int _gpsAttempts = 0;
  static const int _maxGpsAttemptsBeforeFallback = 2;

  // ============================================
  // PUBLIC API
  // ============================================

  /// Check if the user has cleared the age gate for their region.
  ///
  /// Returns true iff EITHER:
  ///   (a) The user is in a region that does NOT require a verified signal
  ///       AND the self-attestation flag (`_kAgeVerifiedKey`) is set, OR
  ///   (b) The user is in a region that DOES require a verified signal AND
  ///       the cached Play Age Signals result is `verifiedOver`, OR
  ///   (c) The user is in a region that DOES require a verified signal but
  ///       the signal is `unverified` / `unavailable` — we fall back to the
  ///       self-attestation flag so the app remains usable when the SDK is
  ///       not yet GA (Phase A scaffold returns `unavailable` deterministically).
  ///
  /// Returns false (blocks the user) when the cached signal is
  /// `verifiedUnder` — that case is the terminal-block path handled by
  /// `AgeVerificationBlockedScreen` (Phase C).
  Future<bool> isAgeVerified() async {
    final prefs = await SharedPreferences.getInstance();
    final selfAttested = prefs.getBool(_kAgeVerifiedKey) ?? false;

    if (!await requiresVerifiedSignal()) {
      return selfAttested;
    }

    final cached = _readCachedAgeSignal(prefs);
    switch (cached) {
      case AgeSignalStatus.verifiedOver:
        return true;
      case AgeSignalStatus.verifiedUnder:
        return false;
      case AgeSignalStatus.unverified:
      case AgeSignalStatus.unavailable:
      case null:
        // Signal is missing or inconclusive — fall back to self-attestation
        // so we don't block the entire Texas user-base while the Play Age
        // Signals SDK is still rolling out (per directive: "fall back to
        // self-attestation when unavailable").
        return selfAttested;
    }
  }

  /// Set age verification status (self-attestation flag).
  Future<void> setAgeVerified(bool verified) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kAgeVerifiedKey, verified);
  }

  /// True when the stored region mandates a verified age signal (e.g. Texas
  /// SB 2420). Returns false on non-Android platforms — the Play Age Signals
  /// API is Android-only, so iOS / Web users continue to rely on
  /// self-attestation regardless of region. Returns false when no region is
  /// stored yet (the compliance flow hasn't run).
  static Future<bool> requiresVerifiedSignal() async {
    if (!_isAndroidPlatform()) return false;
    final region = await _resolveRegionForSignalCheck();
    if (region == null || region.isEmpty) return false;
    return _kRegionsRequiringVerifiedSignal.contains(region) ||
        _kRegionsRequiringVerifiedSignal.contains(region.toUpperCase());
  }

  /// Returns the most-recent Play Age Signals verdict for the user, querying
  /// the platform channel at most once per [_kAgeSignalCacheTtl]. The result
  /// is persisted in SharedPreferences and reused on cold start.
  ///
  /// Callers MUST first check [requiresVerifiedSignal] — calling this on
  /// regions that don't require the signal still works (it will simply
  /// invoke and cache) but wastes a Play Services round-trip. On non-Android
  /// platforms `PlayAgeSignalsService.fetchAgeSignal` short-circuits to
  /// `unavailable` so this method is safe to call from any platform.
  static Future<AgeSignalStatus> fetchAndCacheAgeSignal({
    int requiredAge = 18,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final cachedAt = prefs.getInt(_kAgeSignalCachedAtKey) ?? 0;
    final ageMs = DateTime.now().millisecondsSinceEpoch - cachedAt;
    final cached = _readCachedAgeSignal(prefs);
    if (cached != null &&
        cachedAt > 0 &&
        ageMs < _kAgeSignalCacheTtl.inMilliseconds) {
      return cached;
    }

    final status =
        await PlayAgeSignalsService.fetchAgeSignal(requiredAge: requiredAge);
    await prefs.setString(_kAgeSignalStatusKey, status.name);
    await prefs.setInt(
      _kAgeSignalCachedAtKey,
      DateTime.now().millisecondsSinceEpoch,
    );
    return status;
  }

  // ── Phase B test seams ───────────────────────────────────────────────────
  // Tests inject a region without touching geocoding / SharedPreferences-
  // backed location flow; the production path resolves region via
  // `getStoredRegion()` below. Setting these to non-null in test code lets
  // unit tests drive `requiresVerifiedSignal()` deterministically.
  @visibleForTesting
  static String? debugRegionOverride;

  @visibleForTesting
  static bool? debugIsAndroidOverride;

  /// Wipe the verified-signal cache so the next call re-invokes the API.
  /// Test-only: production never needs to invalidate (24h TTL handles it).
  @visibleForTesting
  static Future<void> debugClearAgeSignalCache() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kAgeSignalStatusKey);
    await prefs.remove(_kAgeSignalCachedAtKey);
  }

  /// Test-only: forcibly seed the cache with a given status + timestamp.
  /// Real callers should use `fetchAndCacheAgeSignal` which manages both.
  @visibleForTesting
  static Future<void> debugSeedAgeSignalCache({
    required AgeSignalStatus status,
    DateTime? cachedAt,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kAgeSignalStatusKey, status.name);
    await prefs.setInt(
      _kAgeSignalCachedAtKey,
      (cachedAt ?? DateTime.now()).millisecondsSinceEpoch,
    );
  }

  // ── Region resolution ────────────────────────────────────────────────────
  // We deliberately reuse the existing `_kVerifiedRegionKey` written by the
  // GPS/IP compliance flow rather than introducing a NEW reverse-geocode call
  // site (per Phase B directive: "do NOT add a NEW geocode call site"). This
  // means `requiresVerifiedSignal` only fires AFTER the user has cleared the
  // location-verification step — which is consistent with the Phase C splash
  // gate ordering (welcome → compliance → age-signal gate runs late in boot).
  //
  // Trade-off documented in the PR body: on the very first cold-start, the
  // age-signal check is a no-op (no stored region yet) and the user proceeds
  // to the existing compliance flow normally. The verified-signal gate only
  // engages on the SECOND boot once region is cached.
  static Future<String?> _resolveRegionForSignalCheck() async {
    if (debugRegionOverride != null) return debugRegionOverride;
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kVerifiedRegionKey);
  }

  static bool _isAndroidPlatform() {
    if (debugIsAndroidOverride != null) return debugIsAndroidOverride!;
    if (kIsWeb) return false;
    return defaultTargetPlatform == TargetPlatform.android;
  }

  static AgeSignalStatus? _readCachedAgeSignal(SharedPreferences prefs) {
    final raw = prefs.getString(_kAgeSignalStatusKey);
    if (raw == null) return null;
    for (final status in AgeSignalStatus.values) {
      if (status.name == raw) return status;
    }
    return null;
  }

  // Debug-only bypass for dogfood/sim testing. kDebugMode-gated; cannot ship to prod.
  // Activate with: flutter run --dart-define=DEV_BYPASS_COMPLIANCE=true
  static const bool _kDevBypassCompliance =
      bool.fromEnvironment('DEV_BYPASS_COMPLIANCE', defaultValue: false);

  Future<ComplianceStatus> checkCompliance() async {
    if (kDebugMode && _kDevBypassCompliance) {
      debugPrint('Compliance: DEV_BYPASS_COMPLIANCE active — returning allowed.');
      return ComplianceStatus.allowed;
    }

    await FirebaseService().logEvent('compliance_check_started');

    // 1. Age Check (per-region minimum age; see minAgeForRegion())
    final ageVerified = await isAgeVerified();
    if (!ageVerified) {
      await _logBlockEvent('age_verification_required', null);
      return ComplianceStatus.ageVerificationRequired;
    }

    // 2. Check if location already verified (ONE-TIME check)
    if (await _isLocationAlreadyVerified()) {
      return await _checkStoredRegion();
    }

    // 3. Server-IP region check (PRIMARY).
    //
    // Web platform note: was previously hard-bounced here to a "use mobile
    // app" conversion screen on the assumption that browsers couldn't
    // verify region. That cost us the entire web acquisition surface for
    // no real safety win — the IP-region check below runs against our
    // own backend and is platform-agnostic, so it works fine on web.
    // The mobile-app upsell now happens as a non-blocking promo sheet on
    // the chat screen instead of as a compliance gate (see
    // WebMobilePromoSheet in widgets/web_mobile_promo_sheet.dart).
    final ipResult = await _verifyViaIpRegion();
    if (ipResult != null) return ipResult;

    // 4. GPS fallback (only if IP unreachable).
    //
    // On web the geolocator plugin uses the browser's navigator.geolocation
    // API, which prompts for permission and can resolve country/region with
    // varying accuracy. If both IP AND GPS fail on web, _verifyAndStoreLocation
    // returns ComplianceStatus.locationPermissionRequired or .error — the
    // user can retry. We no longer force a conversionRequired bounce.
    return await _verifyAndStoreLocation();
  }

  Future<ComplianceStatus?> _verifyViaIpRegion() async {
    try {
      final result = await ApiService().get('/api/compliance/ip-region-check');
      if (result == null || result is! Map) return null;
      final blocked = result['blocked'] == true;
      final region = (result['region'] ?? 'ip_verified').toString();
      await _storeLocationVerification(region);
      if (blocked) {
        await _logBlockEvent('blocked_region_ip', region);
        return ComplianceStatus.blockedRegion;
      }
      await FirebaseService().logEvent('compliance_result', {
        'status': 'allowed',
        'region': region,
        'method': 'ip_primary',
      });
      return ComplianceStatus.allowed;
    } catch (_) {
      return null; // signal "fall through to GPS"
    }
  }

  Future<void> _logBlockEvent(String reason, String? region) async {
    await FirebaseService().logEvent('compliance_blocked', {
      'reason': reason,
      'region': region ?? 'unknown',
    });
  }

  /// Request location permission (called by UI)
  Future<LocationPermission> requestLocationPermission() async {
    return await Geolocator.requestPermission();
  }

  /// Return the most-recently stored region string (e.g. "Illinois", "Utah").
  /// Returns null if no verification has been stored yet.
  Future<String?> getStoredRegion() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kVerifiedRegionKey);
  }

  /// Get the block reason for a region (for analytics/UI)
  BlockReason getBlockReason(String? region) {
    if (region == null) return BlockReason.none;
    
    if (_hardBanStates.contains(region) || 
        _hardBanStates.contains(region.toUpperCase())) {
      return BlockReason.hardBan;
    }
    
    if (_pendingComplianceStates.contains(region) || 
        _pendingComplianceStates.contains(region.toUpperCase())) {
      return BlockReason.pendingCompliance;
    }
    
    return BlockReason.none;
  }

  // ============================================
  // PRIVATE METHODS
  // ============================================

  /// Check if location was already verified within the re-verification window
  Future<bool> _isLocationAlreadyVerified() async {
    final prefs = await SharedPreferences.getInstance();
    final verified = prefs.getBool(_kLocationVerifiedKey) ?? false;
    
    if (!verified) return false;
    
    // v3.1 Hardening: Check if re-verification is needed (after 24 HOURS)
    final timestampMs = prefs.getInt(_kVerificationTimestampKey) ?? 0;
    if (timestampMs == 0) return false;
    
    final verifiedAt = DateTime.fromMillisecondsSinceEpoch(timestampMs);
    final hoursSinceVerification = DateTime.now().difference(verifiedAt).inHours;
    
    return hoursSinceVerification < _reVerificationHours;
  }

  /// Check stored region against blocklists
  Future<ComplianceStatus> _checkStoredRegion() async {
    final prefs = await SharedPreferences.getInstance();
    final storedRegion = prefs.getString(_kVerifiedRegionKey);
    
    if (storedRegion == null) {
      // Something went wrong, force re-verification
      return await _verifyAndStoreLocation();
    }
    
    // Check if region is blocked
    if (_isBlockedRegion(storedRegion)) {
      return ComplianceStatus.blockedRegion;
    }
    
    return ComplianceStatus.allowed;
  }

  /// Verify location via GPS and store result
  Future<ComplianceStatus> _verifyAndStoreLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    // Check if location services are enabled
    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      try { await ApiService().post('/api/compliance/log', data: {'event_type': 'gps_services_disabled'}); } catch (_) {}
      return ComplianceStatus.locationServicesDisabled;
    }

    // Check permission status
    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      try { await ApiService().post('/api/compliance/log', data: {'event_type': 'gps_permission_denied'}); } catch (_) {}
      return ComplianceStatus.locationPermissionRequired;
    }

    if (permission == LocationPermission.deniedForever) {
      try { await ApiService().post('/api/compliance/log', data: {'event_type': 'gps_permission_denied', 'metadata': {'forever': true}}); } catch (_) {}
      return ComplianceStatus.locationPermissionRequired;
    }

    // Get current position
    try {
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.low, // Coarse is sufficient for state-level
          timeLimit: Duration(seconds: 30), // 30s for cold GPS locks (was 15s)
        ),
      );

      // v3.1 Hardening: Reject Mock Locations (Android anti-spoofing)
      // On iOS, this property is always false (jailbreak detection is Phase 2)
      if (position.isMocked && !kDebugMode) {
        debugPrint('Security: Mock location detected and rejected.');
        await _logBlockEvent('mock_location', null);
        return ComplianceStatus.error;
      }

      // Reverse geocode to get region
      List<Placemark> placemarks = await placemarkFromCoordinates(
        position.latitude,
        position.longitude,
      );

      if (placemarks.isNotEmpty) {
        final place = placemarks.first;
        final region = place.administrativeArea ?? '';
        final country = place.isoCountryCode ?? '';
        
        debugPrint('Compliance: Location verified - Country=$country, State=$region');

        // Store the verification result (ONE-TIME)
        await _storeLocationVerification(region);

        // Check if this region is blocked
        if (_isBlockedRegion(region)) {
          await _logBlockEvent('blocked_region', region);
          return ComplianceStatus.blockedRegion;
        }
      }
      
      await FirebaseService().logEvent('compliance_result', {
        'status': 'allowed',
        'region': placemarks.isNotEmpty ? placemarks.first.administrativeArea : 'unknown',
      });
      return ComplianceStatus.allowed;

    } catch (e) {
      debugPrint('Compliance: Location verification error - $e');
      _gpsAttempts++;

      // Log GPS failure to backend for funnel analytics
      final errorType = e.toString().contains('timeout') ? 'gps_timeout' : 'gps_error';
      try {
        await ApiService().post('/api/compliance/log', data: {
          'event_type': errorType,
          'metadata': {'error': e.toString().substring(0, 100), 'attempt': _gpsAttempts},
        });
      } catch (_) {} // Analytics should never block

      // After 2 GPS failures, try IP-based region fallback
      if (_gpsAttempts >= _maxGpsAttemptsBeforeFallback) {
        try {
          final result = await ApiService().get('/api/compliance/ip-region-check');
          if (result != null && result is Map) {
            final blocked = result['blocked'] == true;
            final region = result['region'] ?? 'ip_verified';
            if (!blocked) {
              await _storeLocationVerification(region);
              await FirebaseService().logEvent('compliance_result', {
                'status': 'allowed',
                'region': region,
                'method': 'ip_fallback',
              });
              return ComplianceStatus.allowed;
            } else {
              await _logBlockEvent('blocked_region_ip', region);
              return ComplianceStatus.blockedRegion;
            }
          }
        } catch (_) {} // IP fallback failed too — show retry UI
      }

      // On error, we cannot verify -> treat as needing retry
      return ComplianceStatus.error;
    }
  }

  /// Store location verification in preferences (ONE-TIME)
  Future<void> _storeLocationVerification(String region) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kLocationVerifiedKey, true);
    await prefs.setString(_kVerifiedRegionKey, region);
    await prefs.setInt(_kVerificationTimestampKey, DateTime.now().millisecondsSinceEpoch);
  }

  /// Check if a region is blocked (hard ban OR pending compliance)
  bool _isBlockedRegion(String region) {
    // Check hard ban states (Illinois)
    if (_hardBanStates.contains(region) || 
        _hardBanStates.contains(region.toUpperCase())) {
      return true;
    }
    
    // Check pending compliance states (Utah, Washington)
    // These are blocked until Phase 2 compliance features are built
    if (_pendingComplianceStates.contains(region) || 
        _pendingComplianceStates.contains(region.toUpperCase())) {
      return true;
    }
    
    return false;
  }
}
