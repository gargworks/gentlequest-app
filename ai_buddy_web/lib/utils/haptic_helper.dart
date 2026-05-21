import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/services.dart';

/// Cross-platform HapticFeedback wrapper.
///
/// On web HapticFeedback.* throws MissingPluginException — every call site
/// has to guard with kIsWeb. Import [Haptic] instead. Mass-replace of
/// existing HapticFeedback.* call sites is a follow-up; this just makes the
/// safe helper available so new code can adopt it immediately.
abstract final class Haptic {
  static void light() {
    if (kIsWeb) return;
    HapticFeedback.lightImpact();
  }

  static void medium() {
    if (kIsWeb) return;
    HapticFeedback.mediumImpact();
  }

  static void heavy() {
    if (kIsWeb) return;
    HapticFeedback.heavyImpact();
  }

  static void selection() {
    if (kIsWeb) return;
    HapticFeedback.selectionClick();
  }
}
