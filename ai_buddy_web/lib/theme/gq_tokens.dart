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

  /// Pressed/hover state of primary.
  /// Source: R1D4 Mood_Entry + R1D1 Onboarding.
  static const primaryDk = Color(0xFF4F63C9);

  /// Primary tint — chip backgrounds, card backgrounds.
  /// Source: R1D4 GentleQuest_Mood_Entry.html --gq-primary-soft
  static const primarySoft = Color(0xFFEEF0FE);

  /// Coral accent — warmth layer; replaces "red" everywhere (principle #1).
  static const coral = Color(0xFFFF6B6B);

  /// Coral tint — light mood chips, Heavy/Low mood background, under-18 dignity path accents.
  /// Source: R1D4 GentleQuest_Mood_Entry.html --gq-accent-soft + R1D1 Onboarding.
  static const accentSoft = Color(0xFFFFE8E8);

  /// Soft lavender-tinted off-white — default screen/scaffold background.
  static const softBg = Color(0xFFF8F7FF);

  /// Near-black primary text — --gq-ink.
  /// Source: R1D4 GentleQuest_Mood_Entry.html + R1D1 Onboarding.
  static const ink = Color(0xFF1F1B3A);

  /// Mid purple-ink — secondary text — --gq-ink-2.
  /// Source: R1D4 GentleQuest_Mood_Entry.html + R1D1 Onboarding.
  static const ink2 = Color(0xFF4A4670);

  /// Light ink — metadata, labels — --gq-ink-3.
  /// Source: R1D4 GentleQuest_Mood_Entry.html + R1D1 Onboarding.
  static const ink3 = Color(0xFF8B86AB);

  /// Divider lines, subtle borders — --gq-hair (rgba(31,27,58,0.08)).
  /// Source: R1D4 GentleQuest_Mood_Entry.html + R1D1 Onboarding.
  static const hair = Color(0x141F1B3A);

  // ── Semantic mood colours (R1D4 — emoji pill row) ──────────────────────────
  // These match the token table in REVIEW.md § Cross-cutting design tokens.

  /// Semantic "Great" mood — green. --gq-great.
  /// Source: REVIEW.md cross-cutting tokens + R1D4 HTML
  static const moodGreat = Color(0xFF9CC487);

  /// Semantic "Good" mood — peach. --gq-good.
  /// Source: REVIEW.md cross-cutting tokens + R1D4 HTML
  static const moodGood = Color(0xFFFFB59B);

  /// Semantic "Okay" mood — lavender. --gq-okay.
  /// Source: REVIEW.md cross-cutting tokens + R1D4 HTML
  static const moodOkay = Color(0xFFC9B7F0);

  /// Semantic "Meh" mood — slate grey. --gq-meh.
  /// Source: GentleQuest_Journal.html (R1D14) + timeline widget map.
  static const moodMeh = Color(0xFFB8B5CC);

  /// Semantic "Rough" mood — muted purple. --gq-rough.
  /// Source: GentleQuest_Journal.html (R1D14) + timeline widget map.
  static const moodRough = Color(0xFFC49AD9);

  // Mood palette — ordered low-energy (index 0) → high-energy (index 4).
  static const moodSlateLavender = Color(0xFFC9CCEB); // index 0 — calm/low
  static const moodMutedPlum     = Color(0xFFB6A3D9); // index 1
  static const moodPeri          = Color(0xFFA9B5F4); // index 2 — mid
  static const moodPeach         = Color(0xFFFFB59B); // index 3
  static const moodCoralPeach    = Color(0xFFFF8E7A); // index 4 — warm/high

  /// Amber — offline state indicator, non-critical warnings.
  /// Source: REVIEW.md cross-cutting tokens + GentleQuest_Push_Notifications.html --gq-amber
  static const amber = Color(0xFFC8923D);

  /// Amber soft tint — background for offline banners and amber-state surfaces.
  /// Source: GentleQuest_Offline_States.html --gq-amber-soft: #FBF1DC (R1D12)
  static const amberSoft = Color(0xFFFBF1DC);

  /// Coral dark — pressed/dark coral, on-light text accent.
  /// Source: agent ruling 2026-05-22 (compliance_guard L360/L683/L1460 sweep).
  static const coralDk = Color(0xFFE0494C);

  /// Success soft tint — pale green background for "safe / passed" surfaces.
  /// Source: agent ruling 2026-05-22 (compliance_guard L695/L698 sweep).
  static const successSoft = Color(0xFFE8F4EE);

  /// Success ink — green foreground for success copy / icons.
  /// Source: agent ruling 2026-05-22 (compliance_guard L696/L699/L873 sweep).
  static const successInk = Color(0xFF3F8B6A);

  /// Leaf ink — olive green for nature/eco/illustration surfaces.
  /// Used across mood illustrations, quest visuals, safety/eco affordances,
  /// offline states. 7-site / 5-file recurrence promoted to token 2026-05-22.
  static const leafInk = Color(0xFF5C7A48);

  // ── Crisis / warmth gradient stops (R1D9 — Crisis Intervention) ───────────
  // Source: GentleQuest_Crisis_Intervention.html --gq-warm-1 / --gq-warm-2
  /// Warm peach tint — start of crisis gradient / icon halos.
  static const warm1 = Color(0xFFFFD8C4); // --gq-warm-1
  /// Warm salmon — mid-stop of crisis icon gradient.
  static const warm2 = Color(0xFFFFB89E); // --gq-warm-2

  // ── Safety plan card gradient (R1D19 — Profile) ───────────────────────────
  // Source: GentleQuest_Profile.html .safety-card gradient stops.
  /// Safety plan card — gradient start (deep indigo).
  static const safetyGradStart = Color(0xFF6F62D6);
  /// Safety plan card — gradient mid (medium purple).
  static const safetyGradMid = Color(0xFF8C77E0);
  /// Safety plan card — gradient end (soft lilac).
  static const safetyGradEnd = Color(0xFFB488DF);
  /// Safety plan card — contact-row call button text (crisis-line accent).
  static const safetyCallButtonInk = Color(0xFF5C49B6);

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

  /// Onboarding resource card radius.
  /// Source: GentleQuest_Onboarding.html (R1D1).
  static const cardLg = 20.0;

  /// Bottom / modal sheet top-corner radius.
  static const sheet = 24.0;

  /// Bottom sheet top-corner radius (onboarding age modal).
  /// Source: GentleQuest_Onboarding.html (R1D1).
  static const sheetLg = 32.0;

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

  /// Welcome hero illustration breathing loop.
  /// Source: GentleQuest_Onboarding.html (R1D1).
  static const breathe = Duration(milliseconds: 5600);

  /// Heart-pulse animation in crisis surfaces — slow, calming rhythm.
  /// Source: GentleQuest_Crisis_Intervention.html (R1D9) @keyframes gqHeartPulse 2400ms.
  static const heartPulse = Duration(milliseconds: 2400);

  /// Slide-up sheet animation for crisis State A.
  /// Source: GentleQuest_Crisis_Intervention.html (R1D9) 300ms cubic-bezier.
  static const crisisSheetSlide = Duration(milliseconds: 300);

  /// Stagger delay increment for sequenced fade-in-up children.
  /// Source: GentleQuest_Onboarding.html — 80ms between each child.
  static const staggerStep = Duration(milliseconds: 80);

  // ── R1D11 — Compliance Extensions ─────────────────────────────────────────

  /// Crossfade from standard compliance block to crisis-keyword override (State A).
  /// Source: GentleQuest_Compliance_Extensions.html — "200ms swap".
  static const complianceCrisisSwap = Duration(milliseconds: 200);

  /// Urgency ring pulse period for the 988 surface (State A).
  /// Source: GentleQuest_Compliance_Extensions.html — gqUrgentPulse 2200ms.
  static const urgencyRingPulse = Duration(milliseconds: 2200);

  /// Envelope single-pulse for notify-me confirmation (State C).
  /// Source: GentleQuest_Compliance_Extensions.html — gqEnvelopePulse 900ms.
  static const envelopePulse = Duration(milliseconds: 900);

  /// Crossfade from notify-me form to confirmation state (State C).
  /// Source: GentleQuest_Compliance_Extensions.html — "300ms ease-in crossfade".
  static const notifyConfirmCrossfade = Duration(milliseconds: 300);
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

  /// Reflective serif — R1D14 Journal entry bodies + reflective surfaces.
  /// Do NOT adopt globally; serif on input fields hurts legibility while typing.
  /// Scoped to: _JournalEntryView body, _JournalEntryCard preview, empty-state headline.
  /// Source: GentleQuest_Journal.html (R1D14) "warmth of notebook".
  static const journalSerif = 'Fraunces';

  /// Handwritten encouraging copy — R1D14 chip starters + scribble accents.
  /// Scoped to: _StarterChips labels, _NotebookScribble Text.
  /// Source: GentleQuest_Journal.html (R1D14) "Today, what worked was…" starters.
  static const handwritten = 'Caveat';
}
