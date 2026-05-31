import 'package:shared_preferences/shared_preferences.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import 'package:flutter/foundation.dart';
import 'package:ai_buddy_web/services/firebase_service.dart';
import 'package:ai_buddy_web/services/api_service.dart';

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
  // Legacy key — kept as-is so existing 18+ verifications stay valid.
  // Naming is a misnomer now (post-2026-05-21 the threshold is 13+ for
  // most regions, see minAgeForRegion); the *bool value* just means
  // "user attested to be of acceptable age for their region".
  static const String _kAgeVerifiedKey = 'compliance_age_verified_18_plus';
  static const String _kLocationVerifiedKey = 'compliance_location_verified';
  static const String _kVerifiedRegionKey = 'compliance_verified_region';
  static const String _kVerificationTimestampKey = 'compliance_verification_timestamp';

  // ============================================
  // AGE-GATE THRESHOLDS BY REGION
  // ============================================
  // Lowered from blanket 18+ on 2026-05-21 — original app objective was
  // high-school students. The new floor is 13 (US COPPA / UK ICO digital
  // age of consent) wherever local law allows, stepping up to 16 or 18
  // for jurisdictions that mandate it. Default for unknown regions is the
  // GLOBAL universal threshold (currently 13) — review with counsel
  // before shipping to a market not already covered here.
  //
  // ⚠ LEGAL-REVIEW-NEEDED before public scale:
  //   - India (DPDP 2023): article 9 effectively requires 18+ for
  //     digital service consent unless verifiable parental consent flow
  //     is built. We mark India 18+ below but parental-consent flow is
  //     out of scope for Phase 1.
  //   - EU member states that chose >13 under GDPR-K (DE/FR/IT/NL/IE/
  //     LU/HU/LT/PL/RO/SK/CY/HR/EL): 16+.
  //   - Australia: no specific minimum but eSafety Commissioner
  //     guidance suggests 13+; treated as 13 here.
  // v1.3.0: operator decision — 18+ everywhere to match privacy policy and
  // avoid COPPA / GDPR-K / minor-data regulatory complexity.
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

  /// Check if age is already verified (18+)
  Future<bool> isAgeVerified() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kAgeVerifiedKey) ?? false;
  }

  /// Set age verification status
  Future<void> setAgeVerified(bool verified) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kAgeVerifiedKey, verified);
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
