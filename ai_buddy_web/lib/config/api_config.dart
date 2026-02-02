import 'package:flutter/foundation.dart';

class ApiConfig {
  // Development - use local backend for testing
  static const String localUrl = 'http://localhost:8080';

  // Production (Cloud Run)
  static const String productionUrl =
      'https://gentlequest-backend-999376128638.us-central1.run.app';

  // Get the appropriate URL based on environment
  static String get baseUrl {
    // Mobile/native -> production URL
    if (!kIsWeb) {
      if (kDebugMode) {
        debugPrint('🔧 DEBUG: Mobile/native detected, using production URL');
      }
      return productionUrl;
    }

    // Web debug -> local backend
    if (kDebugMode) {
      debugPrint('🔧 DEBUG: Web debug detected, using local URL');
      return localUrl;
    }

    // Web release -> same-origin (served by Nginx), avoids CORS
    final origin = Uri.base.origin;
    return origin;
  }
}
