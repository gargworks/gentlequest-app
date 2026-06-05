package com.example.ai_buddy_web

import android.content.Context
import android.util.Log
import com.google.android.play.agesignals.AgeSignalsException
import com.google.android.play.agesignals.AgeSignalsManagerFactory
import com.google.android.play.agesignals.AgeSignalsRequest
import com.google.android.play.agesignals.AgeSignalsResult
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

/**
 * PlayAgeSignalsPlugin — Phase A2: real Play Age Signals SDK wiring.
 *
 * Bridges Flutter to the Play Age Signals API v0.0.3 (alpha). Exposes one
 * method: `getAgeSignals`, which accepts a required minimum age and returns
 * a status string the Dart layer maps onto `AgeSignalStatus`.
 *
 * Phase A2 swaps the deterministic Phase A stub for the real
 * `AgeSignalsManagerFactory.create(context).checkAgeSignals(request)` call.
 * The Dart-side string contract (`verifiedOver` / `verifiedUnder` /
 * `unverified` / `unavailable`) is unchanged so the Phase A unit tests and
 * the eventual Phase B/C integration layers continue to work.
 *
 * Channel registration stays in `MainActivity.kt`; Phase B is responsible
 * for wiring this service into `compliance_service.dart`.
 *
 * Spec: docs/integration/PLAY_AGE_SIGNALS_v0_0_3.md
 * Channel: com.gentlequest.www/play_age_signals
 *
 * --- Real SDK shape (verified against age-signals-0.0.3.aar, 2026-06-04) ---
 *  AgeSignalsManagerFactory.create(Context): AgeSignalsManager
 *  AgeSignalsManager.checkAgeSignals(AgeSignalsRequest): Task<AgeSignalsResult>
 *  AgeSignalsRequest.builder().build()           // no setRequiredAge() — request body is empty
 *  AgeSignalsResult.ageLower(): Integer?         // verified minimum age, or null if unknown
 *  AgeSignalsResult.ageUpper(): Integer?         // verified maximum age, or null if unknown
 *  AgeSignalsResult.userStatus(): Integer?       // AgeSignalsVerificationStatus int code
 *  AgeSignalsResult.installId(): String?
 *  AgeSignalsResult.mostRecentApprovalDate(): Date?
 *
 *  The required-age threshold is enforced client-side because the API only
 *  reports the verified age band; the spec pseudocode's `setRequiredAge` +
 *  `VERIFIED_OVER_THRESHOLD` enum does not exist in the published SDK.
 */
class PlayAgeSignalsPlugin(
    private val context: Context,
) : MethodChannel.MethodCallHandler {

    companion object {
        const val CHANNEL_NAME = "com.gentlequest.www/play_age_signals"
        private const val TAG = "PlayAgeSignalsPlugin"

        // Status string contract with Dart layer. MUST stay in sync with
        // AgeSignalStatus enum in lib/services/play_age_signals_service.dart.
        const val STATUS_VERIFIED_OVER = "verifiedOver"
        const val STATUS_VERIFIED_UNDER = "verifiedUnder"
        const val STATUS_UNVERIFIED = "unverified"
        const val STATUS_UNAVAILABLE = "unavailable"

        // Error codes surfaced back to Dart. Dart treats any non-null
        // errorCode as a signal to fall back to `unavailable` for the
        // overall status; the code is included for telemetry.
        // Non-SDK codes start at 1; SDK-originated codes come straight from
        // `AgeSignalsException.errorCode` and live in the
        // `com.google.android.play.agesignals.model.AgeSignalsErrorCode`
        // namespace (NO_ERROR, API_NOT_AVAILABLE, PLAY_STORE_NOT_FOUND,
        // NETWORK_ERROR, PLAY_SERVICES_NOT_FOUND, etc.).
        const val ERROR_INVALID_REQUIRED_AGE = 2
        const val ERROR_UNKNOWN = 99
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "getAgeSignals" -> handleGetAgeSignals(call, result)
            else -> result.notImplemented()
        }
    }

    private fun handleGetAgeSignals(call: MethodCall, result: MethodChannel.Result) {
        val requiredAge = call.argument<Int>("requiredAge") ?: 18
        if (requiredAge <= 0 || requiredAge > 120) {
            result.success(
                mapOf(
                    "status" to STATUS_UNAVAILABLE,
                    "errorCode" to ERROR_INVALID_REQUIRED_AGE,
                ),
            )
            return
        }

        try {
            val manager = AgeSignalsManagerFactory.create(context)
            val request = AgeSignalsRequest.builder().build()
            manager
                .checkAgeSignals(request)
                .addOnSuccessListener { ageResult ->
                    val status = classifyStatus(ageResult, requiredAge)
                    Log.d(
                        TAG,
                        "checkAgeSignals success: requiredAge=$requiredAge, " +
                            "ageLower=${ageResult.ageLower()}, ageUpper=${ageResult.ageUpper()}, " +
                            "userStatus=${ageResult.userStatus()}, mapped=$status",
                    )
                    result.success(mapOf("status" to status))
                }
                .addOnFailureListener { e ->
                    val errorCode = (e as? AgeSignalsException)?.errorCode ?: ERROR_UNKNOWN
                    Log.w(TAG, "checkAgeSignals failure: errorCode=$errorCode", e)
                    result.success(
                        mapOf(
                            "status" to STATUS_UNAVAILABLE,
                            "errorCode" to errorCode,
                        ),
                    )
                }
        } catch (t: Throwable) {
            // Factory or Task creation failed synchronously — typically when
            // the AAR is present at compile time but Play Services is missing
            // at runtime. Fall back to `unavailable` so the Dart layer can use
            // self-attestation.
            Log.w(TAG, "checkAgeSignals threw synchronously", t)
            result.success(
                mapOf(
                    "status" to STATUS_UNAVAILABLE,
                    "errorCode" to ERROR_UNKNOWN,
                ),
            )
        }
    }

    /**
     * Maps the SDK's age-band result onto the Dart-side string contract.
     *
     *  - `verifiedOver`  → SDK reported `ageLower >= requiredAge` (confidently above).
     *  - `verifiedUnder` → SDK reported `ageUpper < requiredAge` (confidently below).
     *  - `unverified`    → SDK responded but the band straddles `requiredAge`,
     *                      or the band is unknown. Callers fall back to
     *                      self-attestation.
     *
     * The classification deliberately treats null bands as `unverified`
     * rather than `unavailable` — `unavailable` is reserved for paths where
     * the SDK itself cannot be reached (failure listener / synchronous
     * throw / non-Android caller).
     */
    private fun classifyStatus(result: AgeSignalsResult, requiredAge: Int): String {
        val lower: Int? = result.ageLower()
        val upper: Int? = result.ageUpper()
        return when {
            lower != null && lower >= requiredAge -> STATUS_VERIFIED_OVER
            upper != null && upper < requiredAge -> STATUS_VERIFIED_UNDER
            else -> STATUS_UNVERIFIED
        }
    }
}
