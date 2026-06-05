# Play Age Signals API v0.0.3 + Texas SB 2420 — Integration Spec

> **Status:** SPEC (not implemented). v1.4.0 candidate.
> **Source:** https://developer.android.com/google/play/age-signals (fetched 2026-06-04).
> **Memory reference:** `project_texas_sb2420_play_age_signals.md`.

---

## Why this exists

Texas SB 2420 (App Store Accountability Act) is in effect after the Dec 2025 injunction was stayed. Google rolling out enforcement "in the coming weeks" per their 2026-06-03 email. Enforcement window: mid-Jun → mid-Jul 2026.

For GentleQuest:
- App is 18+ globally (existing `_kAgeVerifiedKey` self-attestation in `compliance_service.dart:46`).
- Texas users specifically will need **verified** age signals via Play, not just self-attestation, once Google's enforcement starts.
- v1.3.x ship is **not blocked** — existing self-attestation suffices until Google flips the enforcement switch.

---

## API surface (per Google docs)

### Dependency
```gradle
// ai_buddy_web/android/app/build.gradle
implementation 'com.google.android.play:age-signals:0.0.3'  // latest published 2026-06-04 (alpha)
```

> ⚠️ **Spec correction (2026-06-04 Phase A2 verification)**: actual Google Maven artifact is `com.google.android.play:age-signals`, NOT `play-services-age-signals`. Verified via `https://maven.google.com/com/google/android/play/age-signals/group-index.xml`; published versions: `0.0.1-beta01`, `0.0.1-beta02`, `0.0.1`, `0.0.2`, `0.0.3`. The earlier doc used the wrong artifact id.

### Core call (Kotlin/Java)
```kotlin
val manager = AgeSignalsManagerFactory.create(context)
val request = AgeSignalsRequest.Builder()
    // No setRequiredAge() in the real builder — the call returns a verified
    // age band, NOT a yes/no over-threshold answer. The 18+ check happens
    // in the caller via band comparison.
    .build()
manager.checkAgeSignals(request)
    .addOnSuccessListener { result: AgeSignalsResult ->
        // result.ageLower (Int?) and result.ageUpper (Int?) form the verified band.
        // Treat null/null as "no signal available" → unverified.
        val lower = result.ageLower
        val upper = result.ageUpper
        when {
            lower == null && upper == null -> fallbackToSelfAttestation() // unverified
            lower != null && lower >= 18 -> allowAccess()                  // verifiedOver
            upper != null && upper < 18 -> denyAccess()                    // verifiedUnder
            else -> fallbackToSelfAttestation()                            // ambiguous band
        }
    }
    .addOnFailureListener { e: AgeSignalsException ->
        // Default-deny conservatively per Google's guidance
        fallbackToSelfAttestation()
    }
```

> ⚠️ **Spec correction**: method is `checkAgeSignals(request)` (not `getAgeSignals`). Result is an age-band (`ageLower`, `ageUpper`) not a `verificationStatus` enum. The earlier doc followed Google's higher-level guidance pseudocode; the real SDK differs. The Kotlin platform plugin in PR #142 already translates the age-band into the Dart-side `AgeSignalStatus` enum (`verifiedOver` / `verifiedUnder` / `unverified` / `unavailable`) — so the Dart layer surface stays clean.

### Constraints from Google
- **No client-side data collection** — Google handles the verification, app only receives status.
- **Use only for age-appropriate content compliance** — not advertising, marketing, profiling, analytics. Violation = API access termination + app suspension.
- **Testing**: `com.google.android.play.agesignals.testing.FakeAgeSignalsManager` mocks for unit tests.

---

## Integration points in `compliance_service.dart`

Current flow (`ai_buddy_web/lib/services/compliance_service.dart`):
```dart
static const String _kAgeVerifiedKey = 'compliance_age_verified_18_plus';
// prefs.getBool(_kAgeVerifiedKey) ?? false   ← self-attestation today
```

New flow (Android Texas users only):
1. **At startup** in `compliance_service.dart` `initialize()`:
   - Read existing local geocode (line ~335 — reverse-geocode region detection).
   - If region == Texas (or other state with active age-verification law) AND `Platform.isAndroid`:
     - Invoke `AgeSignalsManager.getAgeSignals()` via a platform channel.
     - Cache result + expiry timestamp in SharedPreferences.
2. **At gated entry points** (chat, journal, settings access):
   - If region requires verified signal:
     - If cached signal is VERIFIED_OVER_THRESHOLD → allow.
     - If VERIFIED_UNDER_THRESHOLD → show "must be 18+" terminal screen.
     - If UNVERIFIED / unavailable → fall back to self-attestation modal (existing path).
3. **iOS users**: no Play Age Signals equivalent. Keep self-attestation; rely on App Store Connect age rating + privacy disclosure.

---

## New code surface

### Platform channel (Dart → Kotlin)
- `lib/services/play_age_signals_service.dart` (~80 LOC)
  - `Future<AgeSignalStatus> fetchAgeSignal()` method
  - `enum AgeSignalStatus { verifiedOver, verifiedUnder, unverified, unavailable }`
- `android/app/src/main/kotlin/.../PlayAgeSignalsPlugin.kt` (~120 LOC)
  - Implements platform channel method handler
  - Wraps `AgeSignalsManagerFactory` + `AgeSignalsRequest`
- `ios/.../IOSAgeSignalsStub.swift` (~30 LOC) — returns `unavailable` always

### compliance_service.dart changes
- ~40 LOC: hook the new service into the existing geocode-based region detection.
- Conditional: if region in `_kRegionsRequiringVerification` set (`['Texas']` initially, extensible).
- Cache + expiry logic.

### UI: terminal "must be 18+" screen
- ~50 LOC, leverages existing `BlockedRegionScreen` pattern.

### Tests
- `test/play_age_signals_test.dart` (~80 LOC) using `FakeAgeSignalsManager`.

**Total estimate: ~400 LOC** + 1 new gradle dependency + 1 SharedPreferences key + 1 region allowlist constant.

---

## Implementation phases (recommended)

1. **Phase A — Platform channel + Android plugin** (~3-4h):
   - Wire `play-services-age-signals` gradle dep.
   - Implement Kotlin plugin.
   - Implement Dart service.
   - Test with `FakeAgeSignalsManager`.
2. **Phase B — compliance_service.dart integration** (~2h):
   - Region detection wire-up.
   - Cache + expiry logic.
   - Fallback to self-attestation.
3. **Phase C — UI gating** (~1h):
   - Terminal screen for VERIFIED_UNDER_THRESHOLD.
4. **Phase D — Play Console disclosure** (operator-action, ~30min):
   - Declare age-verification compliance in app listing.
   - Complete Age Signals API + User Data policy.
   - Update Data safety section.

---

## Open questions for operator

1. **Region allowlist**: Texas-only at launch, or also include Utah, Louisiana, other states with active age-verification bills? Google's docs reference "Utah, Louisiana, and other US states follow per age verification bills" — we may want a single feature flag to expand the set without code changes.
2. **Default-deny vs fall-back**: When `AgeSignalsResult.UNVERIFIED` for a Texas user, do we (a) block until they verify in Play, or (b) fall back to existing self-attestation? Google's guidance says default-deny, but our existing self-attestation UX is gentler.
3. **iOS counterpart**: Is there a parallel App Store mechanism we should target, or is iOS exempt from Texas SB 2420?

---

## Ship gate

v1.4.0 is non-blocking right now. Enforcement window mid-Jun → mid-Jul 2026. The trigger to begin Phase A is operator-strategic — recommend starting before mid-June to leave headroom for Apple/Google review cycles + a TestFlight beta with the new gating.

## Carry-forward

- Update `project_texas_sb2420_play_age_signals.md` memory with Phase status as work progresses.
- After ship, add a §X in `MANUAL_RELEASE_PLAYBOOK.md` describing the age-verification gate as a release-readiness checklist item.
