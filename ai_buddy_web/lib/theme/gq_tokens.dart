import 'package:flutter/material.dart';

// GentleQuest design-system tokens — consolidated from 21-design audit.
// Source of truth: docs/design/refs/REVIEW.md § Cross-cutting design tokens,
// superseded where noted by Token Sheet v2 (GentleQuest Design Authority,
// WO-3, 2026-08-21 handoff).
//
// Usage rules:
//   • Reference these constants everywhere instead of raw Color literals.
//   • "coral-not-red" is principle #1: GQColors.coral replaces any red accent.
//   • Full ThemeData / ColorScheme migration is a downstream task (Tier 1.2+).
//   • Do NOT add widget-specific overrides here; keep this file token-only.
//
// WO-3 note: Token Sheet v2 names some existing tokens differently
// (accentSoft -> coralSoft, softBg -> bg). Values are unchanged; only the
// v2 name is added as an alias rather than renaming ~40 call sites blind.
// Renaming existing usages is WO-5 sweep scope, not WO-3 token-landing scope.

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

  /// Token Sheet v2 name for [accentSoft]. Same value.
  static const coralSoft = accentSoft;

  /// Soft lavender-tinted off-white — default screen/scaffold background.
  static const softBg = Color(0xFFF8F7FF);

  /// Token Sheet v2 name for [softBg] (page background). Same value.
  static const bg = softBg;

  /// Card surface — Token Sheet v2. White, distinct from [bg].
  static const surface = Color(0xFFFFFFFF);

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

  /// Ink on amber — dark warm foreground for text/icons on amberSoft surfaces.
  /// Source: Chat Error Implementation Spec (offline_banner, chat error bubble).
  static const inkOnAmber = Color(0xFF7A5A20);

  /// Ink on coral — dark warm foreground for text/icons on accentSoft surfaces.
  /// Source: Chat Error Implementation Spec (crisis row in offline safe list).
  static const inkOnCoral = Color(0xFF7A2424);

  /// Secondary surface — tinted lavender for muted companion backing, cards.
  /// Source: Chat Error Implementation Spec (muted avatar backing).
  static const surface2 = Color(0xFFF2F1FE);

  /// Coral dark — pressed/dark coral, on-light text accent.
  /// Source: agent ruling 2026-05-22 (compliance_guard L360/L683/L1460 sweep).
  static const coralDk = Color(0xFFE0494C);

  /// Coral dark deep — darker coral for crisis-line icon accents (#B33636).
  /// Distinct from [coralDk] (#E0494C); used in offline crisis-row phone icon.
  /// Source: offline_banner.dart _CrisisLineRow phone icon (R1D12).
  static const coralDkDeep = Color(0xFFB33636);

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

  /// Danger ink — destructive-action emphasis (delete account, privacy clear).
  /// Deliberately outside the coral palette: "coral never red" is a decorative
  /// principle; destructive copy is the one place deep red-adjacent is warranted.
  /// 5-site / 2-file recurrence promoted to token 2026-05-22.
  static const dangerInk = Color(0xFFC44A4A);

  /// Danger soft — pale red background paired with dangerInk for destructive cards.
  /// Source: rgba(196,74,74,0.08) approx (clinical_assessment L1924).
  static const dangerSoft = Color(0xFFFFEBEB);

  /// Warm soft — peach-cream tint for icon backgrounds and warm gradient stops.
  /// 12-site / 8-file recurrence (8 active surfaces + 4 legacy dhiwise) promoted
  /// to token 2026-05-22. Sibling of accentSoft/primarySoft/successSoft.
  static const warmSoft = Color(0xFFFFF1E5);

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

  // ── Shared Solitude (Fable #4) — dusk room palette ────────────────────────
  // Source: Fable #4 spec — Shared Solitude (body doubling as presence).
  /// Dusk gradient stop 1 — top.
  static const duskTop = Color(0xFFEFEEFB);
  /// Dusk gradient stop 2 — middle.
  static const duskMid = Color(0xFFE9E7F8);
  /// Dusk gradient stop 3 — bottom.
  static const duskBottom = Color(0xFFF5EFF2);
  /// Ambient glow — top-left field.
  static const glowTopLeft = Color(0xFFDDE2FB);
  /// Ambient glow — top-right field.
  static const glowTopRight = Color(0xFFFBE3DD);

  /// Ordered list for programmatic mood-scale rendering (e.g. sliders, charts).
  static const moodPalette = [
    moodSlateLavender,
    moodMutedPlum,
    moodPeri,
    moodPeach,
    moodCoralPeach,
  ];
}

/// Dark color set — Token Sheet v2, Design Authority D7.
///
/// Defined now so no future work invents its own dark palette; NOT wired
/// into ThemeData / MaterialApp yet — that integration is WO-8 (gated
/// behind the GQ widget layer landing in WO-4, so 7 components get themed
/// instead of ~40 screens individually). Deep ink-violet, not black.
class GQDarkColors {
  GQDarkColors._();

  static const bg = Color(0xFF14121F);
  static const surface = Color(0xFF1E1B2E);

  static const ink = Color(0xFFF2F0FA);
  static const ink2 = Color(0xFFC9C5DC);

  /// Unlike light-mode ink3 (decorative/≥14px only, D3), ink3 passes
  /// contrast on dark (~5.4:1) and is text-legal there.
  static const ink3 = Color(0xFF8B86AB);

  /// Lifted primary for dark backgrounds. CTA fills stay [GQColors.primaryDk]
  /// with white text even in dark mode — D3's contrast ruling doesn't relax.
  static const primary = Color(0xFF8B9CF2);

  /// Coral as text/icon on dark passes (~6.8:1); still never a white-text
  /// fill, on light or dark — see D3.
  static const coral = Color(0xFFFF6B6B);

  /// Soft-tint replacement rule for dark mode: don't reuse the light-mode
  /// fixed pastels (primarySoft, coralSoft, etc.) — use 12-16% alpha of the
  /// parent hue instead. Helper, not a fixed palette.
  static Color softTint(Color hue, {double alpha = 0.14}) =>
      hue.withValues(alpha: alpha);
}

// ─── Radii ───────────────────────────────────────────────────────────────────

class GQRadii {
  GQRadii._();

  /// Chip / pill-adjacent corner radius — Token Sheet v2.
  static const chip = 12.0;

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

// ─── Spacing ─────────────────────────────────────────────────────────────────
// Token Sheet v2 — 4-pt grid. Section rhythm: eyebrow -8-> title -14-> body
// -24-> next section. Did not exist before WO-3; screens previously used ad
// hoc values (8/12/13/14/16/20/24/28/32 with no shared rhythm — the design
// audit's "density chaos" finding).

class GQSpacing {
  GQSpacing._();

  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 24.0;
  static const xxl = 32.0;
  static const xxxl = 48.0;
  static const xxxxl = 64.0;
}

// ─── Accessibility ───────────────────────────────────────────────────────────

class GQA11y {
  GQA11y._();

  /// Minimum touch target — Token Sheet v2. Close buttons, toggles, and
  /// chips are included; no exceptions.
  static const minTouchTarget = 44.0;
}

// ─── Mood shape-channel (D2 — binding accessibility rule) ───────────────────
// "Mood is never encoded by hue alone." WCAG 1.4.1. Every mood visualization
// must pair color with a second channel: size/shape in charts, a label on
// pills, an icon in dots. This enum + map is that second channel, so a chart
// built against it can't accidentally regress to color-only.

enum GQMoodShape { largest, large, medium, small, smallest }

class GQMoodScaleEntry {
  const GQMoodScaleEntry({
    required this.color,
    required this.label,
    required this.shape,
    required this.dotCount,
  });

  final Color color;
  final String label;
  final GQMoodShape shape;

  /// Dot-count channel for compact indicators (e.g. a 5-dot strip).
  final int dotCount;
}

class GQMoodScale {
  GQMoodScale._();

  /// Canonical five moods, ordered high -> low energy, per D2. The prior
  /// 6-mood set (with an Angry entry) and the separate --mood-1..5 rose/blue
  /// scale used in the Weekly Review mock are retired by this decision.
  static const great = GQMoodScaleEntry(
    color: GQColors.moodGreat,
    label: 'Great',
    shape: GQMoodShape.largest,
    dotCount: 5,
  );
  static const good = GQMoodScaleEntry(
    color: GQColors.moodGood,
    label: 'Good',
    shape: GQMoodShape.large,
    dotCount: 4,
  );
  static const okay = GQMoodScaleEntry(
    color: GQColors.moodOkay,
    label: 'Okay',
    shape: GQMoodShape.medium,
    dotCount: 3,
  );
  static const meh = GQMoodScaleEntry(
    color: GQColors.moodMeh,
    label: 'Meh',
    shape: GQMoodShape.small,
    dotCount: 2,
  );
  static const rough = GQMoodScaleEntry(
    color: GQColors.moodRough,
    label: 'Rough',
    shape: GQMoodShape.smallest,
    dotCount: 1,
  );

  static const all = [great, good, okay, meh, rough];
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

  /// Companion creature stage change crossfade.
  /// Deliberately slower than [fade] — a stage change should feel deliberate,
  /// not snap. New stage scales 0.94 → 1.0 over this duration.
  static const companionStageChange = Duration(milliseconds: 600);

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

  // ── Fable #4 — Shared Solitude (body doubling as presence) ───────────────

  /// Entering a room isn't a UI event — app chrome fades, dusk + glows come up.
  static const roomEnter = Duration(milliseconds: 1800);

  /// Ambient glow field 1 breathing period (top-left).
  static const glowBreathe1 = Duration(milliseconds: 9000);

  /// Ambient glow field 2 breathing period (top-right) — desynced from field 1.
  static const glowBreathe2 = Duration(milliseconds: 12000);

  /// Someone leaves/arrives — glow opacity eases over this window.
  static const presenceDim = Duration(milliseconds: 4000);

  /// The return — no bell. Dusk gradient transitions to gq-bg over this window.
  static const roomReturn = Duration(milliseconds: 45000);

  // ── Token Sheet v2 (WO-3) — the GQ widget layer's baseline motion set ────
  // "Motion constants ship inside the [widget] layer — no screen re-declares
  // a duration." (D6). These are the only legal general-purpose timings for
  // new widget-layer components; existing feature-scoped durations above
  // (crisisSheetSlide, urgencyRingPulse, etc.) are untouched.

  /// Tap feedback — scale to .98. Pair with [GQMotion.standardCurve].
  static const tap = Duration(milliseconds: 200);

  /// Selection — spring to 1.04. The mood-select / chip-select affordance.
  static const select = Duration(milliseconds: 220);

  /// Generic sheet slide-in (GQSheet, D6). Distinct from the crisis-specific
  /// [crisisSheetSlide] (300ms) — do not merge; that one is intentionally
  /// tuned separately for the crisis surface.
  static const sheetSlide = Duration(milliseconds: 320);

  /// Full-page cross-fade on navigation.
  static const pageFade = Duration(milliseconds: 300);
}

/// Motion curve — Token Sheet v2. The one legal easing curve for widget-layer
/// motion; screens should not invent their own.
class GQMotion {
  GQMotion._();

  static const standardCurve = Cubic(0.22, 0.94, 0.32, 1.0);
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

  // ── Type scale (Token Sheet v2, WO-3) — "the only legal sizes" ───────────
  // Did not exist before WO-3: this class previously held font-FAMILY names
  // only, no sizes/weights, so every screen picked its own — the design
  // audit's "text style anarchy" finding (inline TextStyle(fontSize: 16),
  // TextStyleHelper legacy, GoogleFonts.interTextTheme, and this class, all
  // live at once). These styles are additive — they don't retrofit existing
  // screens (that's WO-5); they give new/swept work one place to read from.
  //
  // bodyLg deliberately uses [bodyFamily] (Inter), not [journalSerif]: the
  // existing journalSerif doc comment above is explicit that Fraunces is
  // scoped to journal surfaces only and must not be adopted globally. Journal
  // widgets that want the serif "lead" treatment should compose
  // TextStyle(fontFamily: GQTypography.journalSerif) on top of bodyLg's
  // size/weight/height rather than bodyLg itself defaulting to serif.

  static const display = TextStyle(
    fontFamily: displayFamily,
    fontSize: 34,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.8,
  );

  static const title = TextStyle(
    fontFamily: displayFamily,
    fontSize: 24,
    fontWeight: FontWeight.w800,
    letterSpacing: -0.5,
  );

  static const titleSm = TextStyle(
    fontFamily: displayFamily,
    fontSize: 20,
    fontWeight: FontWeight.w800,
    letterSpacing: -0.4,
  );

  static const bodyLg = TextStyle(
    fontFamily: bodyFamily,
    fontSize: 17,
    fontWeight: FontWeight.w500,
    height: 1.55,
  );

  static const body = TextStyle(
    fontFamily: bodyFamily,
    fontSize: 15,
    fontWeight: FontWeight.w500,
    height: 1.5,
  );

  /// Secondary rows, hints. Pair with [GQColors.ink2] per D3 (ink3 never
  /// sets text below 14px).
  static const caption = TextStyle(
    fontFamily: bodyFamily,
    fontSize: 13,
    fontWeight: FontWeight.w600,
  );

  /// Eyebrows, timestamps. Pair with [GQColors.ink2], not ink3 (D3) —
  /// despite the name, this is an 11px style and ink3 is barred below 14px.
  static const micro = TextStyle(
    fontFamily: bodyFamily,
    fontSize: 11,
    fontWeight: FontWeight.w700,
    letterSpacing: 1.2,
  );
}
