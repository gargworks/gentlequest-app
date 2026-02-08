class FeatureFlags {
  // Gate streaming behind a flag. Toggle to enable/disable.
  static const bool enableStreaming = true;

  // Operation Leopard Seal: Enable the full "Leopard" Quest Engine.
  // FALSE = "Old Experiment" (Wellness Dashboard) is shown in the Quest Tab.
  // TRUE  = "New Experiment" (Leopard Gate -> Terminal -> Shell) is shown.
  static const bool enableLeopardMode = false;

  // Future: support other streaming transports (e.g., websockets)
  static const String streamingTransport = 'sse'; // 'sse'
}
