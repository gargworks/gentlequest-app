# Dark mode — open design rulings (Arc B)

Accumulated during the slice conversions (commits `2971aecb`…). Each needs an
operator or Claude Design ruling before `themeMode: ThemeMode.system` activates.
Rule, then move the entry to the Resolved section with the ruling + commit.

## Pending

1. **AvatarDot selection ring** — `lib/screens/profile/profile_widgets.dart`
   (slice 5, `bbc60737`). 1px `Colors.white` ring on an arbitrary user-chosen
   avatar gradient. Not a themed surface, not clearly fill-or-foreground.
   Left static with inline comment. Ruling needed: keep white in both modes,
   or slot it?

2. **Greeting-zone avatar badge gradient** — `lib/screens/home/wellness_home_screen.dart`
   (slice 6, `495a80cd`). Two-color `LinearGradient(t.primary, t.coral)` circle
   with a static `Colors.white` person icon. Tension: `gq_theme.dart` class doc
   marks `primary` as "accent (text/icon use — NOT fills)", yet here it is a
   fill; and dark-mode `primary`/`coral` are LIFTED (lighter) hues, so the
   white icon's contrast drops in dark. Options: (a) keep as converted,
   (b) revert gradient to static GQColors, (c) swap icon foreground to
   `t.inkOnCoral`-style slot. Converted + white icon left static, inline
   comment at site. Ruling needed.

3. **primaryDk used as INK** — `lib/screens/clinical_assessment_screen.dart`
   accentColor (flagged by Claude Design WO-9 review). primaryDk is the static
   CTA-fill exception, but at this site it is a foreground accent on a
   theme-shifting surface — same class of mistake the coralDk reversal fixed.
   Ruling needed: slot a dark variant for ink-position primaryDk sites, or
   accept reduced contrast.

4. **Companion-family files held from conversion** (WO-9 dark art direction
   owns them): `companion_*`, `silent_witness*`, `weekly_letter*`,
   `letter_fragment_picker.dart`, `crisis_reentry_surface*`, `branded_splash*`.
   Convert only after WO-9 v2 rulings are consumed.

## Resolved

- **coralDk** — 2026-08-27: static ruling REVERSED same day on grep evidence
  (all 6 sites are ink on shifting surfaces); slotted with dark variant
  `GQDarkColors.coral`. Commit `2971aecb`; record in `gq_theme.dart` class doc.
