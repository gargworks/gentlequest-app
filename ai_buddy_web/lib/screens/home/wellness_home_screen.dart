import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/mood_entry.dart';
import '../../navigation/home_tab_deeplink.dart';
import '../../providers/companion_provider.dart';
import '../../providers/mood_provider.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/app_bottom_nav.dart';
import '../../widgets/exercise_card_scaffold.dart' show ExerciseType;
import '../../widgets/gq/gq.dart';
import '../exercise_scaffold_screen.dart';
import '../journal_screen.dart';
import '../mood_tracker_screen.dart';
import '../resource_library_screen.dart';
import '../settings/notification_detail_screen.dart';
import '../weekly_review_screen.dart';

/// Design Authority WO-6 — Home tab (D5's 4-tab IA: Home/Chat/Journal/You).
///
/// Built from `refs/Wellness Dashboard (Home).html` and
/// `refs/Dashboard States (Home).html`, translated through the GQ widget
/// layer rather than ported HTML/CSS. Five zones, in the mock's own budget:
/// greeting (12%) · today's one thing (25%) · week shape (25%) ·
/// quick lanes (13%) · gentle nudge (10%, cut entirely if not relevant).
///
/// Deliberately does NOT use a streak/fire-emoji pill or a breakable
/// "N-day streak" — [CompanionProvider]'s own doc is explicit that the
/// companion "NEVER punishes absence: no streaks that break, no decay, no
/// shame," and the design doc's own standing rules ban
/// scores-first/streak framing. The mock's decorative streak pill loses to
/// that already-ratified product principle; [totalActiveDays] (cumulative,
/// never resets) carries the "day X" copy instead.
class WellnessHomeScreen extends StatefulWidget {
  const WellnessHomeScreen({
    super.key,
    this.showBottomNav = true,
    this.reselect,
  });

  final bool showBottomNav;

  /// Bumped by the parent shell on tab-reselect; scrolls back to top.
  final ValueNotifier<int>? reselect;

  @override
  State<WellnessHomeScreen> createState() => _WellnessHomeScreenState();
}

class _WellnessHomeScreenState extends State<WellnessHomeScreen> {
  final _scrollController = ScrollController();

  static const _weekdayLetters = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
  static const _weekdayNames = [
    'MONDAY',
    'TUESDAY',
    'WEDNESDAY',
    'THURSDAY',
    'FRIDAY',
    'SATURDAY',
    'SUNDAY',
  ];
  static const _monthNames = [
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
    'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
  ];

  @override
  void initState() {
    super.initState();
    widget.reselect?.addListener(_onReselect);
  }

  @override
  void dispose() {
    widget.reselect?.removeListener(_onReselect);
    _scrollController.dispose();
    super.dispose();
  }

  void _onReselect() {
    if (!_scrollController.hasClients) return;
    _scrollController.animateTo(
      0,
      duration: GQDurations.pageFade,
      curve: GQMotion.standardCurve,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      bottomNavigationBar:
          widget.showBottomNav ? const AppBottomNav(current: AppTab.home) : null,
      body: SafeArea(
        child: Consumer2<MoodProvider, CompanionProvider>(
          builder: (context, moodProvider, companionProvider, _) {
            return ListView(
              controller: _scrollController,
              padding: const EdgeInsets.fromLTRB(
                GQSpacing.lg, GQSpacing.sm, GQSpacing.lg, GQSpacing.xxxl,
              ),
              children: [
                _GreetingZone(activeDays: companionProvider.companion.totalActiveDays),
                const SizedBox(height: GQSpacing.xs),
                _TodaysOneThingZone(moodProvider: moodProvider),
                const SizedBox(height: GQSpacing.md),
                _WeekShapeZone(moodProvider: moodProvider),
                const SizedBox(height: GQSpacing.md),
                const _QuickLanesZone(),
                const SizedBox(height: GQSpacing.md),
                const _DailyNudgeZone(),
              ],
            );
          },
        ),
      ),
    );
  }
}

// ── Zone 1 · Greeting ───────────────────────────────────────────────────

class _GreetingZone extends StatelessWidget {
  const _GreetingZone({required this.activeDays});
  final int activeDays;

  String _greeting(int hour) {
    if (hour < 12) return 'Good morning, friend';
    if (hour < 18) return 'Good afternoon, friend';
    return 'Good evening, friend';
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final weekday = _WellnessHomeScreenState._weekdayNames[now.weekday - 1];
    final month = _WellnessHomeScreenState._monthNames[now.month - 1];

    return Padding(
      padding: const EdgeInsets.only(top: GQSpacing.sm),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$weekday · $month ${now.day}',
                  // D3: ink3 never carries text below 14px; micro is 11px.
                  style: GQTypography.micro.copyWith(color: GQColors.ink2),
                ),
                const SizedBox(height: GQSpacing.xs),
                Text(_greeting(now.hour), style: GQTypography.titleSm.copyWith(color: GQColors.ink)),
                if (activeDays > 0) ...[
                  const SizedBox(height: 2),
                  Text(
                    activeDays == 1 ? 'Day 1 of checking in' : 'Day $activeDays of checking in',
                    style: GQTypography.caption.copyWith(color: GQColors.ink2),
                  ),
                ],
              ],
            ),
          ),
          GestureDetector(
            onTap: () => homeTabDeepLink.request(AppTab.yours),
            child: Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [GQColors.primary, GQColors.coral],
                ),
              ),
              child: const Icon(Icons.person_rounded, size: 18, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Zone 2 · Today's one thing ──────────────────────────────────────────

enum _OneThingState { notLogged, lowMood, steady, feelingGreat }

class _TodaysOneThingZone extends StatelessWidget {
  const _TodaysOneThingZone({required this.moodProvider});
  final MoodProvider moodProvider;

  _OneThingState _stateFor(List<MoodEntry> todayEntries) {
    if (todayEntries.isEmpty) return _OneThingState.notLogged;
    final level = todayEntries.last.moodLevel;
    if (level <= 2) return _OneThingState.lowMood;
    if (level >= 4) return _OneThingState.feelingGreat;
    return _OneThingState.steady;
  }

  @override
  Widget build(BuildContext context) {
    final today = moodProvider.getMoodEntriesForDate(DateTime.now());
    final state = _stateFor(today);

    final (eyebrow, headline, body, ctaLabel, onTap) = switch (state) {
      _OneThingState.notLogged => (
          'Today, just one thing',
          "Log how you're feeling — 15 seconds.",
          "A quick check-in helps me notice patterns with you, gently.",
          'Quick check-in',
          () => Navigator.of(context).push<void>(
              MaterialPageRoute(builder: (_) => const MoodTrackerScreen(showBottomNav: false))),
        ),
      _OneThingState.lowMood => (
          'Today, just one thing',
          'Maybe 3 minutes of breathing?',
          "You logged low today. I'll guide you — no pressure to talk.",
          'Try together',
          () => ExerciseScaffoldScreen.show(context, ExerciseType.breathing),
        ),
      _OneThingState.feelingGreat => (
          'Today, just one thing',
          'Nice. Want to capture what\'s working?',
          "Good days are worth remembering, in your own words.",
          'Add a journal note',
          () => Navigator.of(context).push<void>(
              MaterialPageRoute(builder: (_) => const JournalScreen())),
        ),
      _OneThingState.steady => (
          'Today, just one thing',
          'How\'s today going so far?',
          "Whenever you're ready — no pressure either way.",
          'Log how today\'s going',
          () => Navigator.of(context).push<void>(
              MaterialPageRoute(builder: (_) => const MoodTrackerScreen(showBottomNav: false))),
        ),
    };

    return GQCard(
      large: true,
      color: GQColors.primarySoft,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(GQRadii.chip),
                ),
                child: const Icon(Icons.spa_outlined, color: GQColors.primaryDk, size: 22),
              ),
              const SizedBox(width: GQSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      eyebrow.toUpperCase(),
                      style: GQTypography.micro.copyWith(color: GQColors.primaryDk),
                    ),
                    const SizedBox(height: GQSpacing.xs),
                    Text(headline, style: GQTypography.titleSm.copyWith(color: GQColors.ink)),
                    const SizedBox(height: GQSpacing.xs),
                    Text(body, style: GQTypography.caption.copyWith(color: GQColors.ink2, fontWeight: FontWeight.w500)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: GQSpacing.md),
          GQButton(label: ctaLabel, onPressed: onTap, fullWidth: false),
        ],
      ),
    );
  }
}

// ── Zone 3 · This week ──────────────────────────────────────────────────

class _WeekShapeZone extends StatelessWidget {
  const _WeekShapeZone({required this.moodProvider});
  final MoodProvider moodProvider;

  GQMoodScaleEntry? _scaleFor(int? level) {
    return switch (level) {
      1 => GQMoodScale.rough,
      2 => GQMoodScale.meh,
      3 => GQMoodScale.okay,
      4 => GQMoodScale.good,
      5 => GQMoodScale.great,
      _ => null,
    };
  }

  @override
  Widget build(BuildContext context) {
    final today = DateTime.now();
    final monday = today.subtract(Duration(days: today.weekday - 1));
    final days = List.generate(7, (i) => monday.add(Duration(days: i)));
    final anyLogged = days.any((d) => moodProvider.getMoodEntriesForDate(d).isNotEmpty);

    return GQCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('THIS WEEK', style: GQTypography.micro.copyWith(color: GQColors.ink2)),
              GestureDetector(
                onTap: () => Navigator.of(context).push<void>(
                    MaterialPageRoute(builder: (_) => WeeklyReviewScreen(data: WeeklyReviewData.stubFull()))),
                child: Row(
                  children: [
                    Text('TIMELINE', style: GQTypography.micro.copyWith(color: GQColors.primaryDk)),
                    const Icon(Icons.chevron_right_rounded, size: 16, color: GQColors.primaryDk),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: GQSpacing.md),
          if (!anyLogged)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: GQSpacing.md),
              child: Text(
                'No logs yet this week — the shape fills in as you check in.',
                style: GQTypography.caption.copyWith(color: GQColors.ink2),
              ),
            )
          else
            SizedBox(
              height: 90,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  for (var i = 0; i < 7; i++) ...[
                    if (i > 0) const SizedBox(width: GQSpacing.xs),
                    Expanded(child: _DayBar(
                      entries: moodProvider.getMoodEntriesForDate(days[i]),
                      letter: _WellnessHomeScreenState._weekdayLetters[i],
                      isToday: days[i].year == today.year && days[i].month == today.month && days[i].day == today.day,
                      scaleFor: _scaleFor,
                    )),
                  ],
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _DayBar extends StatelessWidget {
  const _DayBar({
    required this.entries,
    required this.letter,
    required this.isToday,
    required this.scaleFor,
  });

  final List<MoodEntry> entries;
  final String letter;
  final bool isToday;
  final GQMoodScaleEntry? Function(int?) scaleFor;

  @override
  Widget build(BuildContext context) {
    final scale = entries.isEmpty ? null : scaleFor(entries.last.moodLevel);
    final barHeight = scale == null ? 8.0 : 24.0 + (entries.last.moodLevel * 10.0);

    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        Container(
          height: barHeight,
          decoration: BoxDecoration(
            color: scale?.color ?? GQColors.hair,
            borderRadius: BorderRadius.circular(4),
            border: isToday ? Border.all(color: GQColors.primaryDk, width: 2) : null,
          ),
        ),
        const SizedBox(height: GQSpacing.xs),
        Text(
          isToday ? 'TODAY' : letter,
          style: GQTypography.micro.copyWith(
            color: isToday ? GQColors.primaryDk : GQColors.ink2,
            fontSize: isToday ? 9 : 10.5,
          ),
        ),
      ],
    );
  }
}

// ── Zone 4 · Quick lanes ────────────────────────────────────────────────

class _QuickLanesZone extends StatelessWidget {
  const _QuickLanesZone();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _QuickLane(
          icon: Icons.chat_bubble_outline_rounded,
          label: 'Talk to Alex',
          onTap: () => homeTabDeepLink.request(AppTab.talk),
        )),
        const SizedBox(width: GQSpacing.sm),
        Expanded(child: _QuickLane(
          icon: Icons.mood_rounded,
          label: 'Log mood',
          onTap: () => Navigator.of(context).push<void>(
              MaterialPageRoute(builder: (_) => const MoodTrackerScreen(showBottomNav: false))),
        )),
        const SizedBox(width: GQSpacing.sm),
        Expanded(child: _QuickLane(
          icon: Icons.self_improvement_rounded,
          label: 'Exercises',
          onTap: () => Navigator.of(context).push<void>(
              MaterialPageRoute(builder: (_) => const ResourceLibraryScreen())),
        )),
      ],
    );
  }
}

class _QuickLane extends StatelessWidget {
  const _QuickLane({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GQCard(
      onTap: onTap,
      padding: const EdgeInsets.symmetric(vertical: GQSpacing.md, horizontal: GQSpacing.xs),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: GQColors.primarySoft,
              borderRadius: BorderRadius.circular(GQRadii.chip),
            ),
            child: Icon(icon, color: GQColors.primaryDk, size: 20),
          ),
          const SizedBox(height: GQSpacing.xs),
          Text(
            label,
            textAlign: TextAlign.center,
            style: GQTypography.caption.copyWith(color: GQColors.ink, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}

// ── Zone 5 · Gentle nudge ───────────────────────────────────────────────

class _DailyNudgeZone extends StatelessWidget {
  const _DailyNudgeZone();

  @override
  Widget build(BuildContext context) {
    return GQCard(
      color: GQColors.surface,
      onTap: () => Navigator.of(context).push<void>(
          MaterialPageRoute(builder: (_) => const NotificationDetailScreen())),
      child: Row(
        children: [
          const Text('💌', style: TextStyle(fontSize: 18)),
          const SizedBox(width: GQSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('A gentle daily nudge?', style: GQTypography.caption.copyWith(color: GQColors.ink, fontWeight: FontWeight.w800)),
                const SizedBox(height: 2),
                Text('One soft reminder. Off whenever you want.', style: GQTypography.micro.copyWith(color: GQColors.ink2)),
              ],
            ),
          ),
          const Icon(Icons.chevron_right_rounded, color: GQColors.ink3),
        ],
      ),
    );
  }
}
