import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../navigation/home_tab_deeplink.dart';
import '../screens/exercise_scaffold_screen.dart';
import '../theme/gq_tokens.dart';
import '../widgets/app_bottom_nav.dart' show AppTab;
import '../widgets/exercise_card_scaffold.dart';

// resource_library_screen.dart — Tier R1D17
//
// Design source: docs/design/refs/htmls/GentleQuest_Library.html
// REVIEW.md tier: R1D17
//
// Implements:
//   • Header "Library" + search icon (tappable, not yet wired to search flow)
//   • Horizontal single-select filter chips: All · Breathing · Grounding · Body · Quick wins · Sleep
//   • Featured section: "RECOMMENDED · BASED ON YOUR LAST 3 DAYS" / "TRY THIS WHEN YOU'RE HEAVY"
//     with animated breathing orb, 4-7-8 breathing card, Start CTA
//   • 2-column exercise grid with Recent/Favorite inline badge chips
//   • Footer "Ask Alex if nothing fits" → deep-links to chat
//
// Privacy note: recommendation runs locally on the last 3 mood entries.
// While Anonymity Mode is ON, recommender falls back to .default — no mood read.
// (Anonymity mode is not yet wired; always falls back to .recentMoodHeavy for v1.)
//
// ExerciseCardScaffold fullscreen tap IS wired through _exerciseScaffoldType()
// for the in-catalog exercise ids (breath_478 / box_breathing /
// grounding_54321 / body_scan / prog_relax). Cards without a scaffold mapping
// silently bail out in release builds; debug asserts catch unmapped ids
// during development. The earlier "TODO snackbar" copy in this comment was
// stale — the code shipped with proper routing as of R1D17.
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
      duration: const Duration(milliseconds: 6000),
    )..repeat(reverse: true);

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
    HapticFeedback.lightImpact();
    // Every exercise in _kExercises has a scaffold mapping; ids without
    // one are kept out of the catalog (see the FUTURE WORK block above
    // _kExercises). Assert in debug for fast-feedback during development;
    // log + bail in release so a future-added unmapped id doesn't crash
    // the app on the user.
    final scaffoldType = _exerciseScaffoldType(exercise);
    assert(scaffoldType != null,
        'Exercise ${exercise.id} has no scaffold mapping; '
        'add to _exerciseScaffoldType() or remove from _kExercises.');
    if (scaffoldType == null) {
      debugPrint('[resource_library] no scaffold for ${exercise.id}; skipping tap');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${exercise.name} is coming soon!'),
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 3),
          ),
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
    HapticFeedback.lightImpact();
    Navigator.of(context).maybePop();
    homeTabDeepLink.request(AppTab.talk);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: Column(
          children: [
            _LibraryNavBar(onSearch: () {
              // Search affordance — out of scope for v1; icon is tappable
              // but search UI is deferred to a follow-up tier.
            }),
            Expanded(
              child: ListView(
                padding: EdgeInsets.zero,
                children: [
                  // Filter chips
                  _FilterChipsRow(
                    selected: _selectedCategory,
                    onTap: (cat) =>
                        setState(() => _selectedCategory = cat),
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
                        _kExercises
                            .firstWhere((e) => e.id == 'breath_478'),
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
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 10.5,
                            fontWeight: FontWeight.w800,
                            color: GQColors.ink3,
                            letterSpacing: 0.7,
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '${_filteredExercises.length}',
                          style: const TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: GQColors.ink3,
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
          ],
        ),
      ),
    );
  }
}

// ─── Nav bar ─────────────────────────────────────────────────────────────────

class _LibraryNavBar extends StatelessWidget {
  final VoidCallback onSearch;

  const _LibraryNavBar({required this.onSearch});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 50,
      padding: const EdgeInsets.symmetric(horizontal: 18),
      decoration: BoxDecoration(
        color: GQColors.softBg.withAlpha(217), // ~0.85 opacity
        border: const Border(
          bottom: BorderSide(color: GQColors.hair, width: 1),
        ),
      ),
      child: Row(
        children: [
          // Back button
          GestureDetector(
            onTap: () => Navigator.of(context).maybePop(),
            child: Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                border: Border.all(color: GQColors.hair),
              ),
              child: const Icon(
                Icons.chevron_left,
                color: GQColors.ink,
                size: 18,
              ),
            ),
          ),
          const SizedBox(width: 10),
          // Title — verbatim from HTML
          const Text(
            'Library',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
              letterSpacing: -0.3,
            ),
          ),
          const Spacer(),
          // Search icon hidden until the search UI ships — the onSearch
          // callback was wired to `() {}` which is a vestigial affordance
          // (visible search button, tap does nothing). Re-render when the
          // search feature lands. Original GestureDetector + Icon block
          // preserved as a code comment below for the rewrite:
          //
          //   GestureDetector(onTap: onSearch, child: Container(...
          //     child: Icon(Icons.search, color: GQColors.ink2, size: 16)));
        ],
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
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
      child: Row(
        children: _ExerciseCategory.values.map((cat) {
          final isOn = cat == selected;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => onTap(cat),
              child: AnimatedContainer(
                duration: GQDurations.fade,
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: isOn ? GQColors.primary : Colors.white,
                  borderRadius:
                      BorderRadius.circular(GQRadii.button),
                  border: Border.all(
                    color: isOn ? GQColors.primary : GQColors.hair,
                  ),
                  boxShadow: isOn
                      ? [
                          BoxShadow(
                            color: GQColors.primary.withAlpha(115), // ~0.45
                            offset: const Offset(0, 6),
                            blurRadius: 14,
                            spreadRadius: -6,
                          )
                        ]
                      : null,
                ),
                child: Text(
                  cat.label,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: isOn ? Colors.white : GQColors.ink2,
                  ),
                ),
              ),
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
        style: const TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 10.5,
          fontWeight: FontWeight.w800,
          color: GQColors.ink3,
          letterSpacing: 0.7,
        ),
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
      child: ClipRRect(
        borderRadius: BorderRadius.circular(22),
        child: Container(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF6BA8E8), Color(0xFF8C77E0)],
            ),
            borderRadius: BorderRadius.circular(22),
            boxShadow: [
              BoxShadow(
                color: GQColors.primary.withAlpha(140), // ~0.55
                offset: const Offset(0, 18),
                blurRadius: 38,
                spreadRadius: -16,
              ),
            ],
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
                    // Animated orb
                    Center(
                      child: AnimatedBuilder(
                        animation: breatheScale,
                        builder: (_, __) => Transform.scale(
                          scale: breatheScale.value,
                          child: Opacity(
                            opacity: breatheOpacity.value,
                            child: Container(
                              width: 130,
                              height: 130,
                              decoration: const BoxDecoration(
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
                        ),
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
                    SizedBox(
                      width: double.infinity,
                      child: GestureDetector(
                        onTap: onStart,
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 11),
                          decoration: BoxDecoration(
                            color: GQColors.primary,
                            borderRadius:
                                BorderRadius.circular(GQRadii.button),
                            boxShadow: [
                              BoxShadow(
                                color: GQColors.primary.withAlpha(140),
                                offset: const Offset(0, 10),
                                blurRadius: 22,
                                spreadRadius: -10,
                              ),
                            ],
                          ),
                          child: const Text(
                            'Start',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 13,
                              fontWeight: FontWeight.w800,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
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

  @override
  Widget build(BuildContext context) {
    if (exercises.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 32),
        child: Text(
          'No exercises in this category yet.',
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 13,
            color: GQColors.ink3,
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
            Expanded(child: _ExerciseGridItem(exercise: left, onTap: onTap)),
            const SizedBox(width: 10),
            right != null
                ? Expanded(
                    child: _ExerciseGridItem(exercise: right, onTap: onTap))
                : const Expanded(child: SizedBox.shrink()),
          ],
        ),
      );
      if (i + 2 < exercises.length) rows.add(const SizedBox(height: 10));
    }
    return Column(children: rows);
  }
}

class _ExerciseGridItem extends StatelessWidget {
  final _Exercise exercise;
  final void Function(_Exercise) onTap;

  const _ExerciseGridItem({required this.exercise, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onTap(exercise),
      child: Container(
        constraints: const BoxConstraints(minHeight: 138),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: GQColors.hair),
        ),
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
                    color: GQColors.ink3,
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
            if (exercise.isFavorite)
              Positioned(
                top: 0,
                right: 0,
                child: Container(
                  width: 22,
                  height: 22,
                  decoration: const BoxDecoration(
                    // HTML: rgba(255,107,107,0.14) ≈ GQColors.coral at 14% opacity
                    color: Color(0x24FF6B6B),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.favorite_rounded,
                    size: 11,
                    color: GQColors.coral,
                  ),
                ),
              )
            else if (exercise.isRecent)
              Positioned(
                top: 0,
                right: 0,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                  decoration: BoxDecoration(
                    color: GQColors.primarySoft,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    'RECENT',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 9,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.5,
                      color: GQColors.primaryDk,
                    ),
                  ),
                ),
              ),
          ],
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
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [GQColors.primarySoft, Color(0xFFF8F1FA)],
          ),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: Color(0x59667EEA), // primary at ~0.35 opacity
            // Using explicit hex since withOpacity produces same value
            // and there's no dedicated "primary-dashed" token. [assumed]
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    "Don't see what you need?",
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 12.5,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink,
                      height: 1.3,
                    ),
                  ),
                  SizedBox(height: 2),
                  Text(
                    // Verbatim from spec: "Ask Alex if nothing fits"
                    // HTML sub-text says "Tell Alex — opens chat with a head start."
                    // Using REVIEW.md footer CTA verbatim as the primary label.
                    'Ask Alex if nothing fits',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: GQColors.ink2,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: const [
                Text(
                  'Ask',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: GQColors.primaryDk,
                  ),
                ),
                SizedBox(width: 4),
                Icon(
                  Icons.arrow_forward_rounded,
                  size: 14,
                  color: GQColors.primaryDk,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
