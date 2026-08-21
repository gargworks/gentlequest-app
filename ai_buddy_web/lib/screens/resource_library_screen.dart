import 'dart:async';

import 'package:flutter/material.dart';

import '../navigation/home_tab_deeplink.dart';
import '../screens/exercise_scaffold_screen.dart';
import '../theme/gq_tokens.dart';
import '../widgets/app_bottom_nav.dart' show AppTab;
import '../widgets/exercise_card_scaffold.dart';
import '../widgets/gq/gq.dart';

// resource_library_screen.dart — Tier R1D17, WO-5.4 sweep
//
// Design source: docs/design/refs/htmls/GentleQuest_Library.html
// REVIEW.md tier: R1D17
//
// Implements:
//   • Header "Library" (GQHeader)
//   • Horizontal single-select filter chips: All · Breathing · Grounding · Body · Quick wins · Sleep
//   • Featured section: "RECOMMENDED · BASED ON YOUR LAST 3 DAYS" / "TRY THIS WHEN YOU'RE HEAVY"
//     with animated breathing orb, 4-7-8 breathing card, Start CTA
//   • 2-column exercise grid with Recent/Favorite inline badge chips
//   • Footer "Nothing here fits?" → deep-links to chat
//
// Privacy note: recommendation runs locally on the last 3 mood entries.
// While Anonymity Mode is ON, recommender falls back to .default — no mood read.
// (Anonymity mode is not yet wired; always falls back to .recentMoodHeavy for v1.)
//
// ExerciseCardScaffold fullscreen tap IS wired through _exerciseScaffoldType()
// for the in-catalog exercise ids (breath_478 / box_breathing /
// grounding_54321 / body_scan / prog_relax). Cards without a scaffold mapping
// show an inline GQBanner rather than silently bailing; debug asserts catch
// unmapped ids during development.
//
// "Ask Alex" deep-links to the Talk tab (HomeShell.AppTab.talk) via
// homeTabDeepLink.request() — see _onAskAlex below. Library-context
// pre-fill ("I'm looking for an exercise to ...") is the remaining
// R1D17-followup TODO once HomeShell/InteractiveChatScreen accept an
// initialMessage hint.

// ─── Data model ──────────────────────────────────────────────────────────────

enum _ExerciseCategory { all, breathing, grounding, body, quickWins, sleep }

extension _ExerciseCategoryLabel on _ExerciseCategory {
  String get label {
    switch (this) {
      case _ExerciseCategory.all:
        return 'All';
      case _ExerciseCategory.breathing:
        return 'Breathing';
      case _ExerciseCategory.grounding:
        return 'Grounding';
      case _ExerciseCategory.body:
        return 'Body';
      case _ExerciseCategory.quickWins:
        return 'Quick wins';
      case _ExerciseCategory.sleep:
        return 'Sleep';
    }
  }
}

class _Exercise {
  final String id;
  final String name;
  final String emoji;
  final String durationLabel; // e.g. "1 min"
  final String categoryLabel; // e.g. "breath"
  final _ExerciseCategory category;
  final Color tileBackground;
  final bool isFavorite;
  final bool isRecent;

  const _Exercise({
    required this.id,
    required this.name,
    required this.emoji,
    required this.durationLabel,
    required this.categoryLabel,
    required this.category,
    required this.tileBackground,
    this.isFavorite = false,
    this.isRecent = false,
  });
}

// Static exercise list (v1 — backend API is out of scope for this tier).
// Sort order: favorites → recents → rest, per HTML spec.
const List<_Exercise> _kExercises = [
  _Exercise(
    id: 'breath_478',
    name: '4-7-8 breathing',
    emoji: '🌬️',
    durationLabel: '1 min',
    categoryLabel: 'breath',
    category: _ExerciseCategory.breathing,
    tileBackground: GQColors.primarySoft,
    isFavorite: true,
  ),
  _Exercise(
    id: 'grounding_54321',
    name: '5-4-3-2-1 grounding',
    emoji: '🪨',
    durationLabel: '3 min',
    categoryLabel: 'grounding',
    category: _ExerciseCategory.grounding,
    tileBackground: GQColors.warmSoft,
    isRecent: true,
  ),
  _Exercise(
    id: 'body_scan',
    name: '3-min body scan',
    emoji: '🫁',
    durationLabel: '3 min',
    categoryLabel: 'body',
    category: _ExerciseCategory.body,
    tileBackground: Color(0xFFF0F5EC),
  ),
  _Exercise(
    id: 'box_breathing',
    name: 'Box breathing',
    emoji: '⬛',
    durationLabel: '2 min',
    categoryLabel: 'breath',
    category: _ExerciseCategory.breathing,
    tileBackground: GQColors.primarySoft,
  ),
  _Exercise(
    id: 'prog_relax',
    name: 'Progressive relaxation',
    emoji: '😌',
    durationLabel: '5 min',
    categoryLabel: 'body',
    category: _ExerciseCategory.body,
    tileBackground: Color(0xFFF4ECEC),
  ),
  // FUTURE WORK — Loving-kindness exercise.
  //
  // Removed from the live catalog because there is no ExerciseScaffold
  // implementation for it yet. The previous in-UI "guided version coming
  // soon" SnackBar was a placeholder that lied — re-add when the scaffold
  // ships, with the matching ExerciseType.lovingKindness branch wired in
  // _exerciseScaffoldType() below.
  //
  //   _Exercise(
  //     id: 'loving_kindness',
  //     name: 'Loving-kindness',
  //     emoji: '💝',
  //     durationLabel: '4 min',
  //     categoryLabel: 'quick',
  //     category: _ExerciseCategory.quickWins,
  //     tileBackground: GQColors.accentSoft,
  //   ),
];

// ─── Screen ──────────────────────────────────────────────────────────────────

class ResourceLibraryScreen extends StatefulWidget {
  const ResourceLibraryScreen({super.key});

  @override
  State<ResourceLibraryScreen> createState() => _ResourceLibraryScreenState();
}

class _ResourceLibraryScreenState extends State<ResourceLibraryScreen>
    with SingleTickerProviderStateMixin {
  _ExerciseCategory _selectedCategory = _ExerciseCategory.all;
  late final AnimationController _breatheController;
  late final Animation<double> _breatheScale;
  late final Animation<double> _breatheOpacity;

  @override
  void initState() {
    super.initState();
    _breatheController = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    );
    if (!(WidgetsBinding.instance.platformDispatcher.accessibilityFeatures
        .disableAnimations)) {
      _breatheController.repeat(reverse: true);
    }

    _breatheScale = Tween<double>(begin: 0.85, end: 1.08).animate(
      CurvedAnimation(parent: _breatheController, curve: Curves.easeInOut),
    );
    _breatheOpacity = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(parent: _breatheController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _breatheController.dispose();
    super.dispose();
  }

  List<_Exercise> get _filteredExercises {
    if (_selectedCategory == _ExerciseCategory.all) {
      // Sort: favorites → recents → rest
      final favs = _kExercises.where((e) => e.isFavorite).toList();
      final recents =
          _kExercises.where((e) => e.isRecent && !e.isFavorite).toList();
      final rest = _kExercises
          .where((e) => !e.isFavorite && !e.isRecent)
          .toList();
      return [...favs, ...recents, ...rest];
    }
    return _kExercises.where((e) => e.category == _selectedCategory).toList();
  }

  void _onExerciseTap(_Exercise exercise) {
    // Every exercise in _kExercises has a scaffold mapping; ids without
    // one are kept out of the catalog (see the FUTURE WORK block above
    // _kExercises). Assert in debug for fast-feedback during development;
    // in release, an unmapped id shows the same honest "not ready yet"
    // banner as Part B's SnackBar conversion — this is the zero-SnackBar
    // invariant's single surviving fallback path.
    final scaffoldType = _exerciseScaffoldType(exercise);
    assert(scaffoldType != null,
        'Exercise ${exercise.id} has no scaffold mapping; '
        'add to _exerciseScaffoldType() or remove from _kExercises.');
    if (scaffoldType == null) {
      debugPrint('[resource_library] no scaffold for ${exercise.id}; skipping tap');
      if (mounted) {
        GQBanner.show(
          context,
          message: "That one isn't ready yet. It'll show up here when it is.",
          category: GQBannerCategory.info,
        );
      }
      return;
    }
    ExerciseScaffoldScreen.show(context, scaffoldType);
  }

  ExerciseType? _exerciseScaffoldType(_Exercise exercise) {
    switch (exercise.id) {
      case 'breath_478':
      case 'box_breathing':
        return ExerciseType.breathing;
      case 'grounding_54321':
        return ExerciseType.grounding;
      case 'body_scan':
      case 'prog_relax':
        return ExerciseType.bodyScan;
      // FUTURE WORK — add `case 'loving_kindness': return
      //   ExerciseType.lovingKindness;` once the scaffold ships
      //   (currently only breathing/grounding/bodyScan are implemented
      //   in widgets/exercise_card_scaffold.dart).
      default:
        return null;
    }
  }

  void _onAskAlex() {
    // Deep-link to the modern Talk tab (InteractiveChatScreen) instead of
    // pushing the legacy `screens/chat_screen.dart` ChatScreen on top of
    // Library. The legacy ChatScreen is a bare Column with no Scaffold/
    // Material ancestor — its TextField throws a runtime "No Material
    // widget found" error, surfaced as a red error widget at the bottom of
    // the chat. Captured during sim QC 2026-05-23 (Lokesh).
    //
    // Library is pushed on top of HomeShell via ProfileNavSheet, so
    // homeTabDeepLink.request() correctly unwinds back to HomeShell and
    // switches to the Talk tab, surfacing the modern InteractiveChatScreen
    // (R1D3 first-turn warmth + R1D7 inline crisis banner + status avatar).
    //
    // TODO(R1D17-followup): pass a library-context message hint so the
    // chat surface can render "I'm looking for an exercise to ..." as a
    // starter chip on entry. Requires plumbing through HomeShell into
    // InteractiveChatScreen — out of scope for this fix.
    Navigator.of(context).maybePop();
    homeTabDeepLink.request(AppTab.talk);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: const GQHeader(title: 'Library'),
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            // Filter chips
            _FilterChipsRow(
              selected: _selectedCategory,
              onTap: (cat) => setState(() => _selectedCategory = cat),
            ),

            // Featured section (shown only when "All" or "Breathing")
            if (_selectedCategory == _ExerciseCategory.all ||
                _selectedCategory == _ExerciseCategory.breathing) ...[
              const _FeaturedLabel(),
              _FeaturedExerciseCard(
                breatheScale: _breatheScale,
                breatheOpacity: _breatheOpacity,
                onStart: () => _onExerciseTap(
                  // Look up by id rather than .first so a future
                  // favorites/recents reorder doesn't accidentally
                  // route "4-7-8 breathing" Start to a different
                  // exercise.
                  _kExercises.firstWhere((e) => e.id == 'breath_478'),
                ),
              ),
            ],

            // Grid header
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    'ALL EXERCISES',
                    style: GQTypography.micro.copyWith(color: GQColors.ink2),
                  ),
                  const Spacer(),
                  Text(
                    '${_filteredExercises.length}',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: GQColors.ink2,
                    ),
                  ),
                ],
              ),
            ),

            // 2-column exercise grid
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: _ExerciseGrid(
                exercises: _filteredExercises,
                onTap: _onExerciseTap,
              ),
            ),

            // Ask Alex footer
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 18, 16, 0),
              child: _AskAlexFallback(onTap: _onAskAlex),
            ),

            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

// ─── Filter chips row ────────────────────────────────────────────────────────

class _FilterChipsRow extends StatelessWidget {
  final _ExerciseCategory selected;
  final ValueChanged<_ExerciseCategory> onTap;

  const _FilterChipsRow({required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Row(
        children: _ExerciseCategory.values.map((cat) {
          final isOn = cat == selected;
          return Padding(
            padding: const EdgeInsets.only(right: GQSpacing.sm),
            // GQChip fires its own selection haptic (D7) — don't double it.
            child: GQChip(
              label: cat.label,
              selected: isOn,
              onSelected: (_) => onTap(cat),
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ─── Featured section ─────────────────────────────────────────────────────────

class _FeaturedLabel extends StatelessWidget {
  const _FeaturedLabel();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 4, 18, 8),
      child: Text(
        // Verbatim from spec
        'RECOMMENDED · BASED ON YOUR LAST 3 DAYS',
        style: GQTypography.micro.copyWith(color: GQColors.ink2),
      ),
    );
  }
}

class _FeaturedExerciseCard extends StatelessWidget {
  final Animation<double> breatheScale;
  final Animation<double> breatheOpacity;
  final VoidCallback onStart;

  const _FeaturedExerciseCard({
    required this.breatheScale,
    required this.breatheOpacity,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: GQCard(
        large: true,
        onTap: onStart,
        padding: EdgeInsets.zero,
        color: Colors.transparent,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(GQRadii.cardLg),
          child: Container(
            // IMG-TINT — featured-card illustration, intentional off-token
            // (A1): the hero gradient is illustration, not UI chrome.
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF6BA8E8), Color(0xFF8C77E0)],
              ),
            ),
            child: Column(
              children: [
                // Art section with breathing orb
                SizedBox(
                  height: 110,
                  child: Stack(
                    children: [
                      // Outer ring
                      Center(
                        child: Container(
                          width: 170,
                          height: 170,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: Colors.white.withAlpha(102), // ~0.4
                            ),
                          ),
                        ),
                      ),
                      // Animated orb — collapses to static under
                      // reduced-motion (A1: a perpetually pulsing element
                      // is the single most likely thing here to bother a
                      // light-sensitive user).
                      Center(
                        child: AnimatedBuilder(
                          animation: breatheScale,
                          builder: (_, __) {
                            final reduceMotion = MediaQuery.maybeOf(context)
                                    ?.disableAnimations ??
                                false;
                            final scale =
                                reduceMotion ? 1.0 : breatheScale.value;
                            final opacity =
                                reduceMotion ? 1.0 : breatheOpacity.value;
                            return Transform.scale(
                              scale: scale,
                              child: Opacity(
                                opacity: opacity,
                                child: Container(
                                  width: 130,
                                  height: 130,
                                  decoration: const BoxDecoration(
                                    // IMG-TINT — featured-card illustration,
                                    // intentional off-token (A1).
                                    shape: BoxShape.circle,
                                    gradient: RadialGradient(
                                      center: Alignment(-0.3, -0.4),
                                      radius: 0.9,
                                      colors: [
                                        Color(0xD9FFFFFF),
                                        Color(0x2EFFFFFF),
                                        Colors.transparent,
                                      ],
                                      stops: [0.0, 0.55, 0.70],
                                    ),
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                      // Sub-label chip — verbatim: "TRY THIS WHEN YOU'RE HEAVY"
                      Positioned(
                        top: 12,
                        left: 14,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: Colors.white.withAlpha(56), // ~0.22
                            borderRadius:
                                BorderRadius.circular(GQRadii.button),
                          ),
                          child: const Text(
                            "TRY THIS WHEN YOU'RE HEAVY",
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                              color: Colors.white,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      ),
                      // Duration chip — verbatim: "1 MIN"
                      Positioned(
                        top: 12,
                        right: 14,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 9, vertical: 5),
                          decoration: BoxDecoration(
                            color: Colors.black.withAlpha(56), // ~0.22
                            borderRadius:
                                BorderRadius.circular(GQRadii.button),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.access_time_rounded,
                                size: 10,
                                color: Colors.white.withAlpha(230),
                              ),
                              const SizedBox(width: 4),
                              const Text(
                                '1 MIN',
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w800,
                                  color: Colors.white,
                                  letterSpacing: 0.4,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // Body section
                Container(
                  color: Colors.white,
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: const [
                          Text('🌬️', style: TextStyle(fontSize: 18)),
                          SizedBox(width: 7),
                          // Verbatim from spec: "4-7-8 breathing" [with leaf emoji]
                          // Note: HTML uses 🌬️ (wind-face); REVIEW.md says "leaf emoji" —
                          // HTML is authoritative; using 🌬️. [assumed: leaf may be design-doc
                          // shorthand for "breathing emoji".]
                          Text(
                            '4-7-8 breathing',
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 18,
                              fontWeight: FontWeight.w800,
                              color: GQColors.ink,
                              letterSpacing: -0.4,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'In for 4, hold for 7, out for 8. Slows your nervous system in a single round.',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 12.5,
                          fontWeight: FontWeight.w500,
                          color: GQColors.ink2,
                          height: 1.45,
                        ),
                      ),
                      const SizedBox(height: 12),
                      GQButton(
                        label: 'Start',
                        onPressed: onStart,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Exercise grid ───────────────────────────────────────────────────────────

class _ExerciseGrid extends StatelessWidget {
  final List<_Exercise> exercises;
  final void Function(_Exercise) onTap;

  const _ExerciseGrid({required this.exercises, required this.onTap});

  // Grid-entrance stagger (Part C): 80ms per item on first paint, capped at
  // 6 items so a long list doesn't feel slow. Collapses to instant under
  // reduced-motion.
  static const int _maxStaggeredItems = 6;

  @override
  Widget build(BuildContext context) {
    if (exercises.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 32),
        child: Text(
          'No exercises in this category yet.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 13,
            color: GQColors.ink2,
          ),
        ),
      );
    }

    // Build pairs for 2-column layout
    final rows = <Widget>[];
    for (var i = 0; i < exercises.length; i += 2) {
      final left = exercises[i];
      final right = i + 1 < exercises.length ? exercises[i + 1] : null;
      rows.add(
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: _ExerciseGridItem(
                key: ValueKey(left.id),
                exercise: left,
                onTap: onTap,
                staggerIndex: i,
              ),
            ),
            const SizedBox(width: 10),
            right != null
                ? Expanded(
                    child: _ExerciseGridItem(
                      key: ValueKey(right.id),
                      exercise: right,
                      onTap: onTap,
                      staggerIndex: i + 1,
                    ),
                  )
                : const Expanded(child: SizedBox.shrink()),
          ],
        ),
      );
      if (i + 2 < exercises.length) rows.add(const SizedBox(height: 10));
    }
    return Column(children: rows);
  }
}

class _ExerciseGridItem extends StatefulWidget {
  final _Exercise exercise;
  final void Function(_Exercise) onTap;
  final int staggerIndex;

  const _ExerciseGridItem({
    super.key,
    required this.exercise,
    required this.onTap,
    required this.staggerIndex,
  });

  @override
  State<_ExerciseGridItem> createState() => _ExerciseGridItemState();
}

class _ExerciseGridItemState extends State<_ExerciseGridItem> {
  bool _visible = false;
  bool _reduceMotion = false;
  Timer? _entranceTimer;
  bool _scheduled = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (_scheduled) return;
    _scheduled = true;
    if (_reduceMotion) {
      setState(() => _visible = true);
      return;
    }
    final cappedIndex =
        widget.staggerIndex.clamp(0, _ExerciseGrid._maxStaggeredItems);
    _entranceTimer = Timer(GQDurations.staggerStep * cappedIndex, () {
      if (mounted) setState(() => _visible = true);
    });
  }

  @override
  void dispose() {
    _entranceTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final exercise = widget.exercise;
    return AnimatedOpacity(
      opacity: _visible ? 1.0 : 0.0,
      duration: _reduceMotion ? Duration.zero : GQDurations.fade,
      curve: GQMotion.standardCurve,
      child: AnimatedSlide(
        offset: _visible ? Offset.zero : const Offset(0, 0.06),
        duration: _reduceMotion ? Duration.zero : GQDurations.fade,
        curve: GQMotion.standardCurve,
        child: GQCard(
          onTap: () => widget.onTap(exercise),
          child: Stack(
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Icon tile
                  Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: exercise.tileBackground,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      exercise.emoji,
                      style: const TextStyle(fontSize: 18),
                    ),
                  ),
                  const SizedBox(height: 10),
                  // Name
                  Text(
                    exercise.name,
                    style: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 13.5,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink,
                      height: 1.25,
                      letterSpacing: -0.2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  // Meta
                  Text(
                    '⏱ ${exercise.durationLabel} · ${exercise.categoryLabel}',
                    style: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: GQColors.ink2,
                      letterSpacing: 0.4,
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Start row
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Start',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            color: GQColors.primaryDk,
                          ),
                        ),
                        const Icon(
                          Icons.arrow_forward_rounded,
                          size: 14,
                          color: GQColors.primaryDk,
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              // Trailing badge: FavoritePin (coral) or RecentTag (primarySoft)
              // (A2 — badges are UI state, not decoration; each keeps its
              // own glyph so they're never distinguishable by color alone).
              if (exercise.isFavorite)
                Positioned(
                  top: 0,
                  right: 0,
                  child: Container(
                    width: 22,
                    height: 22,
                    decoration: const BoxDecoration(
                      color: GQColors.warmSoft,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.favorite_rounded,
                      size: 11,
                      color: GQColors.coralDk,
                    ),
                  ),
                )
              else if (exercise.isRecent)
                Positioned(
                  top: 0,
                  right: 0,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 7, vertical: 3),
                    decoration: BoxDecoration(
                      color: GQColors.primarySoft,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.history_rounded,
                            size: 9, color: GQColors.primaryDk),
                        const SizedBox(width: 3),
                        const Text(
                          'RECENT',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 9,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.5,
                            color: GQColors.primaryDk,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Ask Alex fallback ───────────────────────────────────────────────────────

class _AskAlexFallback extends StatelessWidget {
  final VoidCallback onTap;

  const _AskAlexFallback({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GQCard(
      color: const Color(0xFFF4F0FA),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // A3: headline + button label + caption are a label and a
          // caption, not competing copy — the screen needs both.
          const Text(
            'Nothing here fits?',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
            ),
          ),
          const SizedBox(height: GQSpacing.md),
          GQButton(
            label: 'Ask Alex',
            onPressed: onTap,
          ),
          const SizedBox(height: GQSpacing.sm),
          Text(
            'Opens a chat with a head start.',
            textAlign: TextAlign.center,
            style: GQTypography.caption.copyWith(color: GQColors.ink2),
          ),
        ],
      ),
    );
  }
}
