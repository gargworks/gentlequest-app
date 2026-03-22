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
  conversionRequired, // v3.1: Web users must use Mobile App
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
  static const String _kAgeVerifiedKey = 'compliance_age_verified_18_plus';
  static const String _kLocationVerifiedKey = 'compliance_location_verified';
  static const String _kVerifiedRegionKey = 'compliance_verified_region';
  static const String _kVerificationTimestampKey = 'compliance_verification_timestamp';

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
  // v3.1 Hardening: Reduced from 365 days to 24 HOURS
  static const int _reVerificationHours = 24;

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

  Future<ComplianceStatus> checkCompliance() async {
    await FirebaseService().logEvent('compliance_check_started');

    // 1. Age Check (must be 18+)
    final ageVerified = await isAgeVerified();
    if (!ageVerified) {
      await _logBlockEvent('age_verification_required', null);
      return ComplianceStatus.ageVerificationRequired;
    }

    // 2. Web platform - BLOCKED (v3.1 Hardening: Close browser loophole)
    // Web cannot reliably verify GPS without backend GeoIP.
    // Force users to Mobile App for geofence compliance.
    if (kIsWeb) {
      await _logBlockEvent('web_platform_conversion', null);
      return ComplianceStatus.conversionRequired;
    }

    // 3. Check if location already verified (ONE-TIME check)
    if (await _isLocationAlreadyVerified()) {
      // Check stored region against blocklists
      return await _checkStoredRegion();
    }

    // 4. First-time location verification required
    return await _verifyAndStoreLocation();
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
      if (position.isMocked) {
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
      // Log GPS failure to backend for funnel analytics
      final errorType = e.toString().contains('timeout') ? 'gps_timeout' : 'gps_error';
      try {
        await ApiService().post('/api/compliance/log', data: {
          'event_type': errorType,
          'metadata': {'error': e.toString().substring(0, 100)},
        });
      } catch (_) {} // Analytics should never block
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
