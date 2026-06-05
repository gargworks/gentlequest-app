package com.example.ai_buddy_web

import android.content.Context
import android.util.Log
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

/**
 * PlayAgeSignalsPlugin — Phase A scaffold for Texas SB 2420 compliance.
 *
 * Bridges Flutter to the Play Age Signals API v0.0.3 (alpha). Exposes one
 * method: `getAgeSignals`, which accepts a required minimum age and returns
 * a status string the Dart layer maps onto `AgeSignalStatus`.
 *
 * Phase A intentionally ships the channel + handler WITHOUT wiring into
 * compliance_service.dart. Phase B handles region detection + caching;
 * Phase C handles UI gating.
 *
 * Spec: docs/integration/PLAY_AGE_SIGNALS_v0_0_3.md
 * Channel: com.gentlequest.www/play_age_signals
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
        const val ERROR_API_UNAVAILABLE = 1
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

        // Phase A: SDK invocation is deferred until the alpha is GA-pinned and
        // FakeAgeSignalsManager is wired into the test harness. The handler
        // surfaces `unavailable` deterministically so the Dart layer can be
        // exercised end-to-end without taking a hard dependency on the
        // play-services-age-signals runtime.
        //
        // Phase A2 / Phase B will replace the body below with the real
        // AgeSignalsManagerFactory + AgeSignalsRequest call documented in
        // docs/integration/PLAY_AGE_SIGNALS_v0_0_3.md.
        try {
            Log.d(
                TAG,
                "getAgeSignals(requiredAge=$requiredAge) — Phase A stub returning unavailable",
            )
            result.success(
                mapOf(
                    "status" to STATUS_UNAVAILABLE,
                    "errorCode" to ERROR_API_UNAVAILABLE,
                ),
            )
        } catch (t: Throwable) {
            Log.w(TAG, "getAgeSignals failed", t)
            result.success(
                mapOf(
                    "status" to STATUS_UNAVAILABLE,
                    "errorCode" to ERROR_UNKNOWN,
                ),
            )
        }
    }
}
