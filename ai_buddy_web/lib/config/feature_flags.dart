class FeatureFlags {
  // Gate streaming behind a flag. Toggle to enable/disable.
  static const bool enableStreaming = true;

  // Operation Leopard Seal: gates the "Leopard" Quest Engine experiment.
  // Both experiments it toggles between (the dhiwise Wellness Dashboard and
  // the Leopard Gate -> Terminal -> Shell) were archived in the Phase 3
  // dead-code sweep — see archive/code/ai_buddy_web/lib/features/leopard/
  // and archive/code/ai_buddy_web/lib/dhiwise/. Left in place (rather than
  // deleted) since it's a harmless standalone constant with no live reader.
  static const bool enableLeopardMode = false;

  // WO-6.3 Part E: route a server-classified RiskLevel.crisis to the
  // full-screen AcuteCrisisTakeover instead of the inline banner.
  //
  // DEFAULT OFF, and turning it on is an operator decision, not a code one.
  // The gate is not "is the takeover built" (it is) but "how liberally does
  // the backend return crisis rather than high" — because this is the only
  // remaining input that can seize the whole screen. Keyword-sourced .crisis
  // can never reach it (see interactive_chat_screen.dart), so the deny-list
  // false-positive class is already closed by construction; what is left is
  // the model's own calibration, answerable from server logs.
  //
  // NOTE: compile-time. Flipping this needs an app release — there is no
  // RemoteConfig or runtime kill-switch anywhere in this codebase. Do not
  // read this flag as something that can be pulled back remotely if the
  // rate turns out wrong.
  static const bool enableCrisisTakeover = false;

  // Future: support other streaming transports (e.g., websockets)
  static const String streamingTransport = 'sse'; // 'sse'
}
