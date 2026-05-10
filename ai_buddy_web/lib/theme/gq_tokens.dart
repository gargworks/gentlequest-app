import 'package:flutter/material.dart';

// GentleQuest design-system tokens — consolidated from 21-design audit.
// Source of truth: docs/design/refs/REVIEW.md § Cross-cutting design tokens.
//
// Usage rules:
//   • Reference these constants everywhere instead of raw Color literals.
//   • "coral-not-red" is principle #1: GQColors.coral replaces any red accent.
//   • Full ThemeData / ColorScheme migration is a downstream task (Tier 1.2+).
//   • Do NOT add widget-specific overrides here; keep this file token-only.

// ─── Colors ──────────────────────────────────────────────────────────────────

class GQColors {
  GQColors._();

  /// Primary accent — used for CTAs, active states, and interactive highlights.
  static const primary = Color(0xFF667EEA);

  /// Coral accent — warmth layer; replaces "red" everywhere (principle #1).
  static const coral = Color(0xFFFF6B6B);

  /// Soft lavender-tinted off-white — default screen/scaffold background.
  static const softBg = Color(0xFFF8F7FF);

  // Mood palette — ordered low-energy (index 0) → high-energy (index 4).
  static const moodSlateLavender = Color(0xFFC9CCEB); // index 0 — calm/low
  static const moodMutedPlum     = Color(0xFFB6A3D9); // index 1
  static const moodPeri          = Color(0xFFA9B5F4); // index 2 — mid
  static const moodPeach         = Color(0xFFFFB59B); // index 3
  static const moodCoralPeach    = Color(0xFFFF8E7A); // index 4 — warm/high

  /// Ordered list for programmatic mood-scale rendering (e.g. sliders, charts).
  static const moodPalette = [
    moodSlateLavender,
    moodMutedPlum,
    moodPeri,
    moodPeach,
    moodCoralPeach,
  ];
}

// ─── Radii ───────────────────────────────────────────────────────────────────

class GQRadii {
  GQRadii._();

  /// Standard card corner radius.
  static const card = 16.0;

  /// Bottom / modal sheet top-corner radius.
  static const sheet = 24.0;

  /// Stadium (fully-rounded) buttons — use with StadiumBorder or BorderRadius.circular(button).
  static const button = 999.0;
}

// ─── Durations ───────────────────────────────────────────────────────────────

class GQDurations {
  GQDurations._();

  /// Standard element fade-in / fade-out.
  static const fade = Duration(milliseconds: 300);

  /// Auto-advance interval (e.g. onboarding card carousel).
  static const autoAdvance = Duration(milliseconds: 800);

  /// Typewriter effect — delay between each text chunk in chat.
  static const typewriter = Duration(milliseconds: 200);

  /// Celebration / confetti animation total duration.
  static const celebrate = Duration(milliseconds: 1000);
}

// ─── Typography ──────────────────────────────────────────────────────────────

class GQTypography {
  GQTypography._();

  /// Body and UI text family — cross-platform (requires Inter in pubspec).
  static const bodyFamily = 'Inter';

  /// Display / friendly-headline family.
  ///
  /// SF Pro Rounded is iOS-system-only and unavailable as a Flutter asset font.
  /// Inter at heavier weight (FontWeight.w700+) is the cross-platform proxy
  /// until a portable rounded typeface (e.g. Nunito, Poppins) is evaluated.
  static const displayFamily = 'Inter';
}
