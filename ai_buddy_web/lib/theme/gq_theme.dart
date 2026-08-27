import 'package:flutter/material.dart';

import 'gq_tokens.dart';

/// WO-8 Part A — the mode-aware layer over [GQColors].
///
/// ## Why a ThemeExtension and not Material's ColorScheme
///
/// `ColorScheme` has no slot for `amber`, `leafInk`, `dangerSoft`, or the mood
/// scale. Mapping them onto `primary`/`secondary`/`tertiary` would discard the
/// semantic names WO-3 spent an entire work order protecting, and re-open the
/// exact drift that reconciliation closed. So the GQ layer keeps its own names
/// and rides alongside the ColorScheme rather than inside it.
///
/// ## What is deliberately NOT in here
///
/// **CTA fills that carry white text are absent by design, not by omission.**
/// [GQColors.primaryDk] (5.30:1 with white) and [GQColors.dangerInk] (4.75:1)
/// must be byte-identical in light and dark, because a fill that shifts by mode
/// can silently lose contrast when the OS flips — and the one button that must
/// never be hard to read is the 988 CTA.
///
/// The enforcement is structural rather than documentary: because those two
/// colours have no slot here, there is nowhere to put a dark variant. A future
/// author cannot darken them through this class without first adding a field,
/// which is a visible act in review. Contrast that with including them as equal
/// values in both factories, where a one-character edit would go unnoticed.
/// Keep reading them from [GQColors] directly at call sites.
///
/// **[GQColors.coralDk] was briefly on this exception list (ruling of
/// 2026-08-27, morning) and was REVERSED the same day on evidence.** The
/// original ruling assumed it was fill-family like [GQColors.dangerInk]; a
/// grep showed all six call sites are INK/foreground (crisis heart icons,
/// tag text, assessment accent) on theme-shifting surfaces — a static ink
/// fails contrast on dark. It is now the [coralDk] slot: light keeps
/// #E0494C, dark uses [GQDarkColors.coral] per D3. The reversal is recorded
/// here deliberately — the wrong ruling and the evidence that undid it are
/// both part of the record.
///
/// **Mood colours are absent for the same reason.** A mood being a different
/// colour at night breaks recognition, and [GQMoodScale] already carries
/// shape + dotCount as its accessibility channels (D2), so hue does not need
/// to do that work in either mode.
///
/// **Illustration tokens are absent too** — they get a single [illustrationOpacity]
/// knob rather than seventeen invented dark hexes. Real dark art direction for
/// the companion creature is its own work order; inventing hexes here would be
/// exactly the kind of unratified colour invention standing rule 7 forbids.
@immutable
class GQTheme extends ThemeExtension<GQTheme> {
  const GQTheme({
    required this.bg,
    required this.surface,
    required this.surface2,
    required this.ink,
    required this.ink2,
    required this.ink3,
    required this.hair,
    required this.primary,
    required this.primarySoft,
    required this.coral,
    required this.coralDk,
    required this.accentSoft,
    required this.inkOnCoral,
    required this.amber,
    required this.amberSoft,
    required this.inkOnAmber,
    required this.successInk,
    required this.successSoft,
    required this.dangerSoft,
    required this.warmSoft,
    required this.illustrationOpacity,
  });

  // ── Surfaces ──────────────────────────────────────────────────────────────
  final Color bg;
  final Color surface;
  final Color surface2;

  // ── Text ──────────────────────────────────────────────────────────────────
  final Color ink;
  final Color ink2;

  /// Light mode: decorative / >=14px only (D3). Dark mode: text-legal at
  /// ~5.4:1. The constraint genuinely differs by mode, which is precisely
  /// why it is a theme slot instead of a constant.
  final Color ink3;

  final Color hair;

  // ── Accent (text/icon use — NOT fills) ────────────────────────────────────
  /// Lifted on dark for legibility. CTA fills do NOT use this — see the class
  /// doc on why fills are absent from this extension.
  final Color primary;
  final Color primarySoft;

  final Color coral;

  /// Coral-family INK accent (icons, tag text). Slotted 2026-08-27 by
  /// operator re-ruling: every call site is foreground on a theme-shifting
  /// surface, so a static value fails contrast on dark — unlike the
  /// primaryDk/dangerInk FILLS, whose white-text contrast travels with them.
  /// Light: GQColors.coralDk (#E0494C). Dark: GQDarkColors.coral (#FF6B6B,
  /// the D3-ruled on-dark coral ink) — no new hex invented.
  final Color coralDk;
  final Color accentSoft;

  /// Foreground for text/icons sitting on [accentSoft]. Must track its
  /// background across modes — a dark-red ink over a dark-mode tint would be
  /// unreadable, so this is a slot rather than a constant.
  final Color inkOnCoral;

  // ── Semantic states ───────────────────────────────────────────────────────
  final Color amber;
  final Color amberSoft;
  final Color inkOnAmber;
  final Color successInk;
  final Color successSoft;
  final Color dangerSoft;
  final Color warmSoft;

  // ── Illustration ──────────────────────────────────────────────────────────
  /// Single multiplier applied to illustration/gradient surfaces in dark mode.
  /// 1.0 in light, damped in dark so light-mode artwork does not glare against
  /// a deep ink-violet ground.
  final double illustrationOpacity;

  /// Light mode — every value is the existing [GQColors] constant, unchanged.
  /// Landing dark mode must not alter light mode; if any of these drift from
  /// GQColors, that is a bug, not a redesign.
  static const GQTheme light = GQTheme(
    bg: GQColors.softBg,
    surface: GQColors.surface,
    surface2: GQColors.surface2,
    ink: GQColors.ink,
    ink2: GQColors.ink2,
    ink3: GQColors.ink3,
    hair: GQColors.hair,
    primary: GQColors.primary,
    primarySoft: GQColors.primarySoft,
    coral: GQColors.coral,
    coralDk: GQColors.coralDk,
    accentSoft: GQColors.accentSoft,
    inkOnCoral: GQColors.inkOnCoral,
    amber: GQColors.amber,
    amberSoft: GQColors.amberSoft,
    inkOnAmber: GQColors.inkOnAmber,
    successInk: GQColors.successInk,
    successSoft: GQColors.successSoft,
    dangerSoft: GQColors.dangerSoft,
    warmSoft: GQColors.warmSoft,
    illustrationOpacity: 1.0,
  );

  /// Dark mode — Token Sheet v2 dark set.
  ///
  /// Soft tints are NOT the light-mode pastels reused: those are opaque and
  /// near-white, and would read as blown-out panels on a dark ground. They are
  /// alpha washes of the parent hue instead, per [GQDarkColors.softTint].
  /// Foregrounds that sit on those washes ([inkOnCoral], [inkOnAmber]) move to
  /// the light ink so they stay legible over a dark backing.
  static final GQTheme dark = GQTheme(
    bg: GQDarkColors.bg,
    surface: GQDarkColors.surface,
    surface2: GQDarkColors.surface,
    ink: GQDarkColors.ink,
    ink2: GQDarkColors.ink2,
    ink3: GQDarkColors.ink3,
    hair: GQDarkColors.ink.withValues(alpha: 0.12),
    primary: GQDarkColors.primary,
    primarySoft: GQDarkColors.softTint(GQDarkColors.primary),
    coral: GQDarkColors.coral,
    coralDk: GQDarkColors.coral,
    accentSoft: GQDarkColors.softTint(GQDarkColors.coral),
    inkOnCoral: GQDarkColors.ink,
    amber: GQColors.amber,
    amberSoft: GQDarkColors.softTint(GQColors.amber),
    inkOnAmber: GQDarkColors.ink,
    successInk: GQColors.successInk,
    successSoft: GQDarkColors.softTint(GQColors.successInk),
    dangerSoft: GQDarkColors.softTint(GQColors.dangerInk),
    warmSoft: GQDarkColors.softTint(GQColors.warmSoft),
    illustrationOpacity: 0.72,
  );

  /// Convenience accessor. Falls back to [light] rather than throwing, so a
  /// widget rendered outside a themed subtree (a bare test pump, a detached
  /// overlay) degrades to today's appearance instead of crashing.
  static GQTheme of(BuildContext context) =>
      Theme.of(context).extension<GQTheme>() ?? light;

  @override
  GQTheme copyWith({
    Color? bg,
    Color? surface,
    Color? surface2,
    Color? ink,
    Color? ink2,
    Color? ink3,
    Color? hair,
    Color? primary,
    Color? primarySoft,
    Color? coral,
    Color? coralDk,
    Color? accentSoft,
    Color? inkOnCoral,
    Color? amber,
    Color? amberSoft,
    Color? inkOnAmber,
    Color? successInk,
    Color? successSoft,
    Color? dangerSoft,
    Color? warmSoft,
    double? illustrationOpacity,
  }) {
    return GQTheme(
      bg: bg ?? this.bg,
      surface: surface ?? this.surface,
      surface2: surface2 ?? this.surface2,
      ink: ink ?? this.ink,
      ink2: ink2 ?? this.ink2,
      ink3: ink3 ?? this.ink3,
      hair: hair ?? this.hair,
      primary: primary ?? this.primary,
      primarySoft: primarySoft ?? this.primarySoft,
      coral: coral ?? this.coral,
      coralDk: coralDk ?? this.coralDk,
      accentSoft: accentSoft ?? this.accentSoft,
      inkOnCoral: inkOnCoral ?? this.inkOnCoral,
      amber: amber ?? this.amber,
      amberSoft: amberSoft ?? this.amberSoft,
      inkOnAmber: inkOnAmber ?? this.inkOnAmber,
      successInk: successInk ?? this.successInk,
      successSoft: successSoft ?? this.successSoft,
      dangerSoft: dangerSoft ?? this.dangerSoft,
      warmSoft: warmSoft ?? this.warmSoft,
      illustrationOpacity: illustrationOpacity ?? this.illustrationOpacity,
    );
  }

  @override
  GQTheme lerp(ThemeExtension<GQTheme>? other, double t) {
    if (other is! GQTheme) return this;
    return GQTheme(
      bg: Color.lerp(bg, other.bg, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surface2: Color.lerp(surface2, other.surface2, t)!,
      ink: Color.lerp(ink, other.ink, t)!,
      ink2: Color.lerp(ink2, other.ink2, t)!,
      ink3: Color.lerp(ink3, other.ink3, t)!,
      hair: Color.lerp(hair, other.hair, t)!,
      primary: Color.lerp(primary, other.primary, t)!,
      primarySoft: Color.lerp(primarySoft, other.primarySoft, t)!,
      coral: Color.lerp(coral, other.coral, t)!,
      coralDk: Color.lerp(coralDk, other.coralDk, t)!,
      accentSoft: Color.lerp(accentSoft, other.accentSoft, t)!,
      inkOnCoral: Color.lerp(inkOnCoral, other.inkOnCoral, t)!,
      amber: Color.lerp(amber, other.amber, t)!,
      amberSoft: Color.lerp(amberSoft, other.amberSoft, t)!,
      inkOnAmber: Color.lerp(inkOnAmber, other.inkOnAmber, t)!,
      successInk: Color.lerp(successInk, other.successInk, t)!,
      successSoft: Color.lerp(successSoft, other.successSoft, t)!,
      dangerSoft: Color.lerp(dangerSoft, other.dangerSoft, t)!,
      warmSoft: Color.lerp(warmSoft, other.warmSoft, t)!,
      illustrationOpacity:
          illustrationOpacity + (other.illustrationOpacity - illustrationOpacity) * t,
    );
  }
}
