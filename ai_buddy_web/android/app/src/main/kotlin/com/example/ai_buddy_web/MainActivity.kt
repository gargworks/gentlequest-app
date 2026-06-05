package com.example.ai_buddy_web

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Play Age Signals API v0.0.3 — Phase A scaffold (channel registered;
        // not yet wired into compliance_service.dart). See
        // docs/integration/PLAY_AGE_SIGNALS_v0_0_3.md.
        val ageSignalsPlugin = PlayAgeSignalsPlugin(applicationContext)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            PlayAgeSignalsPlugin.CHANNEL_NAME,
        ).setMethodCallHandler(ageSignalsPlugin)
    }
}
