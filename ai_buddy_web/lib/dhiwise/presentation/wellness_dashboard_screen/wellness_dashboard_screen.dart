import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:async';
import 'package:confetti/confetti.dart';

import '../../core/app_export.dart';
import '../../../providers/mood_provider.dart';
import './widgets/recommendation_card_widget.dart';
import '../../../theme/text_style_helper.dart' as CoreTextStyles;
import '../../../widgets/assessment_splash.dart';

import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:provider/provider.dart';
import '../../../providers/quest_provider.dart';
import '../../../providers/progress_provider.dart';
import '../../../models/quest.dart' as model;
import 'package:shared_preferences/shared_preferences.dart';
import '../../../navigation/home_tab_deeplink.dart';
import '../../../navigation/route_observer.dart';
import '../../../screens/journal_screen.dart' show JournalScreen;
import '../../../screens/resource_library_screen.dart' show ResourceLibraryScreen;
import '../../../screens/exercise_scaffold_screen.dart' show ExerciseScaffoldScreen;
import '../../../widgets/exercise_card_scaffold.dart' show ExerciseType;
import '../../../widgets/keyboard_dismissible_scaffold.dart';
import '../../../widgets/app_bottom_nav.dart';
import '../../../widgets/app_back_button.dart';
import '../../../screens/quest_screen/widgets/quest_card_widget.dart';
import '../../../services/analytics_service.dart';
import '../../../services/notification_service.dart';
import '../../../widgets/feedback_dialog.dart';
import '../../../widgets/profile_nav_sheet.dart';
import '../../../theme/gq_tokens.dart';

// ── R1D2+R1D3: Dashboard state machine ───────────────────────────────────────
/// Enum for GentleQuest dashboard hero variants.
/// Priority (highest wins): longAbsence > notLogged/feelingGreat > weekend modifier.
enum DashboardState { notLogged, feelingGreat, longAbsence, weekend }

// DEBUG ONLY: toggle to reset quest state on each app launch
const bool _debugResetQuestsOnLaunch = false;
// DEBUG ONLY: toggle verbose XP chip position logs
const bool _debugXpLogs = false;
// DEBUG ONLY: run selector determinism/variety checks on init
const bool _debugSelectorTest = false;
// DEBUG ONLY: auto-run reminder microinteraction self-test after init
// Turned off after verification to avoid noise
const bool _debugAutoTestReminder = false;

// Animation tuning constants (microinteractions)
const Duration kRippleDuration = Duration(milliseconds: 380);
const double kRippleEndRadius = 84.0;
const Curve kRippleCurve = Curves.easeOutCubic;

const Duration kRingDuration = Duration(milliseconds: 520);
const Curve kRingCurve = Curves.easeOutCubic;

class WellnessDashboardScreen extends StatefulWidget {
  final bool showBottomNav;
  final ValueNotifier<int>? reselect;
  WellnessDashboardScreen({Key? key, this.showBottomNav = true, this.reselect})
      : super(key: key);

  @override
  State<WellnessDashboardScreen> createState() =>
      _WellnessDashboardScreenState();
}

// Painter for progress ring
class _RingPainter extends CustomPainter {
  final Offset center;
  final double progress; // 0..1
  final Color color;

  _RingPainter(
      {required this.center, required this.progress, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final radius = 46.0;
    final rect = Rect.fromCircle(center: center, radius: radius);
    final bg = Paint()
      ..color = color.withValues(alpha: 0.12)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0
      ..strokeCap = StrokeCap.round;
    final fg = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0
      ..strokeCap = StrokeCap.round;

    // background circle
    canvas.drawArc(rect, 0, 2 * 3.1415926535, false, bg);
    // progress arc from top (-pi/2)
    final sweep = (2 * 3.1415926535) * progress.clamp(0.0, 1.0);
    canvas.drawArc(rect, -3.1415926535 / 2, sweep, false, fg);
  }

  @override
  bool shouldRepaint(covariant _RingPainter oldDelegate) {
    return oldDelegate.center != center ||
        oldDelegate.progress != progress ||
        oldDelegate.color != color;
  }
}

// Painter for subtle expanding ripple
class _RipplePainter extends CustomPainter {
  final Offset center;
  final double radius;
  final double opacity; // 0..1
  final Color color;

  _RipplePainter({
    required this.center,
    required this.radius,
    required this.opacity,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final effectiveOpacity = opacity.clamp(0.0, 1.0);
    final fill = Paint()
      ..color = color.withValues(alpha: 0.10 * (1.0 - effectiveOpacity))
      ..style = PaintingStyle.fill;
    final stroke = Paint()
      ..color = color.withValues(alpha: 0.35 * (1.0 - effectiveOpacity))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    canvas.drawCircle(center, radius, fill);
    canvas.drawCircle(center, radius, stroke);
  }

  @override
  bool shouldRepaint(covariant _RipplePainter oldDelegate) {
    return oldDelegate.center != center ||
        oldDelegate.radius != radius ||
        oldDelegate.opacity != opacity ||
        oldDelegate.color != color;
  }
}

class _WellnessDashboardScreenState extends State<WellnessDashboardScreen>
    with TickerProviderStateMixin, RouteAware, WidgetsBindingObserver {
  // Quests state handled by QuestProvider
  Set<String> _exploreCompletedToday = {};

  bool _reminderOn = true; // UI-only reminder toggle (default ON)
  TimeOfDay _reminderTime = const TimeOfDay(hour: 19, minute: 0);

  // Reminder UI anchors (safe even if not attached)
  final GlobalKey _reminderToggleKey = GlobalKey();
  final GlobalKey _reminderTimeKey = GlobalKey();

  // Reminder scheduler
  Timer? _reminderTimer;

  // DEBUG QA hooks removed post-verification

  // Debug log throttling for reminder prints
  DateTime _lastReminderLogAt = DateTime.fromMillisecondsSinceEpoch(0);
  bool? _lastReminderNear;

  // Optional microinteraction flags (must be explicitly enabled)
  bool _enableSoftXpPop = true; // enabled per user approval
  // Reminder microinteraction anchors
  // (duplicates removed; declared once above)

  // Confetti controller for celebrations
  late ConfettiController _confettiController;
  // Celebration variation state
  bool _isStarConfetti = false;

  void _randomizeConfetti() {
    setState(() {
      _isStarConfetti = (DateTime.now().millisecondsSinceEpoch % 2) == 0;
    });
  }

  Path drawStar(Size size) {
    Path path = Path();
    path.moveTo(size.width * 0.5, 0);
    path.quadraticBezierTo(
        size.width * 0.6, size.height * 0.4, size.width, size.height * 0.5);
    path.quadraticBezierTo(
        size.width * 0.6, size.height * 0.6, size.width * 0.5, size.height);
    path.quadraticBezierTo(
        size.width * 0.4, size.height * 0.6, 0, size.height * 0.5);
    path.quadraticBezierTo(
        size.width * 0.4, size.height * 0.4, size.width * 0.5, 0);
    path.close();
    return path;
  }

  // Timer pill overlay state
  OverlayEntry? _timerPillEntry;
  Timer? _timerPillTicker;
  DateTime? _timerPillEndAt;
  String? _timerPillQuestId;
  AnimationController? _timerPillAnim;
  // Auto-complete timer for the active quest (cancelable replacement for Future.delayed)
  Timer? _autoCompleteTimer;

  // Main scroll controller (for re-tap scroll-to-top)
  final ScrollController _scrollController = ScrollController();

  // Segmented tabs: 0 = Today, 1 = Discover
  int _tabIndex = 0;
  // Explore filter state
  String _exploreFilter = 'All';
  List<String> _exploreCats = [
    'Mindfulness',
    'Task',
    'Resource',
    'Tip',
    'Activity',
    'Learning',
  ]; // Curated categories aligned with Quest types
  // Track which Explore quests we've logged an impression for (to avoid duplicates)
  final Set<String> _impressedExplore = <String>{};

  // Quick check-in daily flag (separate from mood logging)
  bool _hasCompletedQuickCheckinToday = false;

  // ── R1D2+R1D3: dashboard state ─────────────────────────────────────────────
  static const _prefsLastSeenDate = 'gq.last_seen_date_v1';
  DateTime? _lastSeenDate; // null = first open or data unavailable

  Future<void> _loadLastSeenDate() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final s = prefs.getString(_prefsLastSeenDate);
      if (s != null) {
        _lastSeenDate = DateTime.tryParse(s);
      }
    } catch (_) {}
  }

  Future<void> _saveLastSeenDate() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
          _prefsLastSeenDate, DateTime.now().toUtc().toIso8601String());
    } catch (_) {}
  }

  /// Compute the hero state to display.
  /// Priority: longAbsence (≥7 days) > feelingGreat/notLogged > weekend modifier.
  DashboardState _computeDashboardState(MoodProvider moodProvider) {
    final now = DateTime.now();

    // 1. Long absence check — highest priority
    if (_lastSeenDate != null) {
      final daysAway = now.toUtc().difference(_lastSeenDate!.toUtc()).inDays;
      if (daysAway >= 7) return DashboardState.longAbsence;
    } else if (moodProvider.moodEntries.isNotEmpty) {
      // Use last mood entry as proxy for last seen
      final sorted = [...moodProvider.moodEntries]
        ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
      final daysAway =
          now.toUtc().difference(sorted.first.timestamp.toUtc()).inDays;
      if (daysAway >= 7) return DashboardState.longAbsence;
    }

    // 2. Mood-based state (notLogged or feelingGreat)
    final loggedToday = _hasLoggedMoodToday(moodProvider);
    if (loggedToday) {
      // "Feeling great" = mood level 4 or 5 today
      final todayEntries = moodProvider.moodEntries.where((e) {
        final t = e.timestamp.toUtc();
        final n = now.toUtc();
        return t.year == n.year && t.month == n.month && t.day == n.day;
      });
      if (todayEntries.isNotEmpty &&
          todayEntries.any((e) => e.moodLevel >= 4)) {
        // Weekend modifier composes with feelingGreat — but feelingGreat wins hero
        return DashboardState.feelingGreat;
      }
      // Logged but not great: use weekend modifier if applicable
      final dayOfWeek = now.weekday; // 6=Sat, 7=Sun
      if (dayOfWeek == DateTime.saturday || dayOfWeek == DateTime.sunday) {
        return DashboardState.weekend;
      }
      // Logged + not great + weekday → notLogged (show checkin prompt is already done)
      // Re-use feelingGreat as "already logged" default
      return DashboardState.feelingGreat;
    }

    // 3. Weekend modifier (not logged + weekend)
    final dayOfWeek = now.weekday;
    if (dayOfWeek == DateTime.saturday || dayOfWeek == DateTime.sunday) {
      return DashboardState.weekend;
    }

    // 4. Default: not logged
    return DashboardState.notLogged;
  }

  /// Descriptive days-away count for State C copy (NOT punitive).
  int _daysAwayCount(MoodProvider moodProvider) {
    final now = DateTime.now().toUtc();
    if (_lastSeenDate != null) {
      return now.difference(_lastSeenDate!.toUtc()).inDays;
    }
    if (moodProvider.moodEntries.isNotEmpty) {
      final sorted = [...moodProvider.moodEntries]
        ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
      return now.difference(sorted.first.timestamp.toUtc()).inDays;
    }
    return 0;
  }

  // Telemetry helpers
  String _slug(String s) => s
      .toLowerCase()
      .replaceAll(RegExp(r'[^a-z0-9]+'), '-')
      .replaceAll(RegExp(r'^-+|-+$'), '');

  // Quick check-in flag key helper (UTC date)
  String _quickCheckinFlagKey(DateTime d) =>
      'daily_quick_checkin_${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}_utc';

  Future<void> _loadQuickCheckinFlag() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final now = DateTime.now().toUtc();
      final k = _quickCheckinFlagKey(now);
      final done = prefs.getBool(k) ?? false;
      if (mounted) {
        setState(() {
          _hasCompletedQuickCheckinToday = done;
        });
      }
    } catch (_) {}
  }

  Future<void> _markQuickCheckinCompletedToday() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final now = DateTime.now().toUtc();
      final k = _quickCheckinFlagKey(now);
      await prefs.setBool(k, true);
      if (mounted) {
        setState(() {
          _hasCompletedQuickCheckinToday = true;
        });
      }
    } catch (_) {}
  }

  // Handle completion of the Quick Check-in flow (explicit submission)
  Future<void> _onQuickCheckinSubmitted() async {
    final questProvider = context.read<QuestProvider>();

    // Determine the quick check-in quest id for today from Provider
    model.Quest? checkinQuest;
    try {
      // Prefer explicit check_in type
      checkinQuest = questProvider.quests.firstWhere(
        (q) => q.type == 'check_in',
        orElse: () => questProvider.quests.firstWhere(
          (q) => q.type == 'progress',
          orElse: () => questProvider.quests.first,
        ),
      );
    } catch (_) {}

    if (checkinQuest == null) return;
    final int questId = checkinQuest.id;
    final bool alreadyDone = checkinQuest.isCompleted;

    if (kDebugMode) {
      debugPrint('[QuickCheckin][Submitted] questId=$questId');
    }

    HapticFeedback.heavyImpact();

    // Mark as completed in backend via provider
    if (!alreadyDone) {
      await questProvider.updateQuestProgress(questId, 100);
    }

    // Refresh local flags
    // Determine if XP was newly awarded now (award occurs only if not already done today)
    bool awarded = !alreadyDone;
    if (!mounted) return;
    setState(() {});

    try {
      if (_enableSoftXpPop && awarded) {
        _showXpChipPop(_startBtnKey, amount: 10);
      }
      _showCheckRipple(_startBtnKey);
      // Trigger celebration
      if (mounted) {
        _randomizeConfetti();
        _confettiController.play();
      }

      // Celebration message
      _showCompletionSnackBar(
          questId, 'Done! Every small step builds something bigger. ✨');
    } catch (_) {}

    // Telemetry: track quest completion and daily check-in for retention
    try {
      if (awarded) {
        // Calculate day number for retention tracking
        int dayNumber = 1;
        try {
          final prefs = await SharedPreferences.getInstance();
          final firstCheckinKey = 'first_checkin_date_utc';
          final now = DateTime.now().toUtc();
          final firstCheckinStr = prefs.getString(firstCheckinKey);

          if (firstCheckinStr != null) {
            final firstCheckin = DateTime.parse(firstCheckinStr);
            dayNumber = now.difference(firstCheckin).inDays + 1;
          } else {
            // First time check-in - store the date
            await prefs.setString(firstCheckinKey, now.toIso8601String());
          }
        } catch (_) {}

        // Log quest completion
        logAnalyticsEvent('quest_complete', metadata: {
          'quest_id': questId,
          'surface': 'wellness_dashboard',
          'variant': 'today',
          'tag': 'xp_awarded',
          'ts': DateTime.now().millisecondsSinceEpoch,
          'success': true,
          'progress': 1.0,
          'ui': 'quick_checkin',
        });

        // Log daily check-in for retention tracking
        logAnalyticsEvent('daily_checkin_completed', metadata: {
          'day_number': dayNumber,
          'date_utc': DateTime.now().toUtc().toIso8601String(),
          'has_mood_data': true, // Always true since check-in includes mood
          'completion_time_seconds': 2, // Approximate
        });
      }
    } catch (_) {}

    // Sync providers: lifetime XP + today progress
    try {
      final lifetimeXp = questProvider.totalXP;
      if (mounted)
        context.read<ProgressProvider>().updateLifetimeXp(lifetimeXp);
    } catch (_) {}
    await _refreshToday();
    // Also refresh Explore to sync Discover tab cards and categories immediately
    await _refreshExplore();
    // Force a lightweight rebuild so Explore list reflects "Done" state right away
    if (mounted) setState(() {});

    // Mark daily quick check-in flag
    await _markQuickCheckinCompletedToday();

    // Track check-in count for feedback prompt
    try {
      final prefs = await SharedPreferences.getInstance();
      final checkinCount = prefs.getInt('checkin_count') ?? 0;
      await prefs.setInt('checkin_count', checkinCount + 1);

      // Check if we should show feedback dialog
      await checkAndShowFeedback(context);
    } catch (_) {}
  }

  // Compute global center of a widget by key
  Offset? _globalCenterOf(GlobalKey key) {
    final ctx = key.currentContext;
    if (ctx == null) return null;
    final box = ctx.findRenderObject() as RenderBox?;
    if (box == null || !box.attached) return null;
    final topLeft = box.localToGlobal(Offset.zero);
    final center = topLeft + Offset(box.size.width / 2, box.size.height / 2);
    return center;
  }

  // Look up duration_min for a quest using QuestProvider
  int? _durationFor(String? questId) {
    if (questId == null) return null;
    final q = context.read<QuestProvider>().getQuestById(questId);
    return q
        ?.target; // In our model, target is used for duration if it's a timed task
  }

  String? _titleFor(String? questId) {
    if (questId == null) return null;
    final q = context.read<QuestProvider>().getQuestById(questId);
    return q?.title;
  }

  String? _subtitleFor(String? questId) {
    if (questId == null) return null;
    final q = context.read<QuestProvider>().getQuestById(questId);
    return q?.description;
  }

  /// Map a quest (by title/subtitle text) to a launchable [ExerciseType].
  /// Returns null for quests without an interactive scaffold (calm music,
  /// articles, generic tips). For matched quests, RESOURCE/TIP card tap
  /// launches the actual exercise widget instead of being a self-report
  /// toggle — fixes v1.3.0 bug where "5-4-3-2-1 Grounding" card only
  /// flipped a checkbox.
  ExerciseType? _exerciseTypeForQuest(String? questId) {
    if (questId == null) return null;
    final q = context.read<QuestProvider>().getQuestById(questId);
    if (q == null) return null;
    final blob = '${q.title} ${q.description}'.toLowerCase();
    if (blob.contains('5-4-3-2-1') ||
        blob.contains('54321') ||
        blob.contains('grounding')) {
      return ExerciseType.grounding;
    }
    if (blob.contains('4-7-8') ||
        blob.contains('478') ||
        blob.contains('box breathing') ||
        blob.contains('breathing')) {
      return ExerciseType.breathing;
    }
    if (blob.contains('body scan') ||
        blob.contains('body_scan') ||
        blob.contains('progressive relax') ||
        blob.contains('prog_relax')) {
      return ExerciseType.bodyScan;
    }
    return null;
  }

  // Keys to compute positions for XP chip animation
  final GlobalKey _task1CardKey = GlobalKey();
  final GlobalKey _task2CardKey = GlobalKey();
  final GlobalKey _resCardKey = GlobalKey();
  final GlobalKey _tipCardKey = GlobalKey();
  final GlobalKey _xpCardKey = GlobalKey();
  // Start button key for microinteraction pill
  final GlobalKey _startBtnKey = GlobalKey();

  // Guard to ensure chip pop occurs only once per task per session
  // (Removed) _task1Popped was used for a local chip-pop guard; no longer needed.

  // Habit formation microcopy (rotates while active)
  final List<String> _microcopy = const [
    "You've got this!",
    "Stay on track!",
    "Future you is proud",
    "Small steps, big wins",
    "Consistency is power"
  ];
  int _microIndex = 0;
  Timer? _microTimer;
  Timer? _midnightTimer;

  // Gentle pulse for near-time attention
  late AnimationController _pulseController;

  // RouteObserver subscription guard
  bool _routeSubscribed = false;
  // IDs for the 4 displayed cards (derived from backend quests)
  String? _qTask1Id; // preferred: Focus reset variant
  String? _qTask2Id; // preferred: Study sprint variant
  String? _qResId; // a RESOURCE item
  String? _qTipId; // a TIP item

  // Persist reminder prefs
  static const _prefsReminderOn = 'wellness.reminder_on_v1';
  static const _prefsReminderMinutes = 'wellness.reminder_minutes_v1';
  // Daily first-use keys
  static const _prefsTipPopDate = 'xp_pop_tip_date_v1';
  static const _prefsResPopDate = 'xp_pop_res_date_v1';

  Future<void> _loadReminderPrefs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final on = prefs.getBool(_prefsReminderOn);
      final mins = prefs.getInt(_prefsReminderMinutes);
      if (on != null || mins != null) {
        if (mounted) {
          setState(() {
            if (on != null) _reminderOn = on;
            if (mins != null) {
              final h = (mins ~/ 60).clamp(0, 23);
              final m = (mins % 60).clamp(0, 59);
              _reminderTime = TimeOfDay(hour: h, minute: m);
            }
          });
        }
      }
    } catch (e) {
      // swallow
    }
  }

  // Subtle check ripple behind a card center
  void _showCheckRipple(GlobalKey sourceKey) {
    // Respect reduce-motion: skip decorative animation
    final reduceMotion =
        MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduceMotion) return;
    final startGlobal = _globalCenterOf(sourceKey);
    // Use screen-scoped overlay to avoid leaking into other tabs/screens
    final overlayState = Overlay.of(context);
    if (startGlobal == null) return;
    final overlayBox = overlayState.context.findRenderObject() as RenderBox?;
    if (overlayBox == null || !overlayBox.attached) return;
    final start = overlayBox.globalToLocal(startGlobal);
    final size = overlayBox.size;
    final controller =
        AnimationController(vsync: this, duration: kRippleDuration);
    final fade = CurvedAnimation(parent: controller, curve: kRippleCurve);
    final radius = Tween<double>(begin: 0, end: kRippleEndRadius)
        .animate(CurvedAnimation(parent: controller, curve: Curves.easeOut));

    late OverlayEntry entry;
    entry = OverlayEntry(builder: (_) {
      final r = radius.value;
      return Positioned.fill(
        child: IgnorePointer(
          ignoring: true,
          child: CustomPaint(
            painter: _RipplePainter(
              center: Offset(
                start.dx.clamp(0.0, size.width),
                start.dy.clamp(0.0, size.height),
              ),
              radius: r,
              opacity: (1.0 - fade.value).clamp(0.0, 1.0),
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
        ),
      );
    });
    overlayState.insert(entry);
    controller.addListener(() {
      entry.markNeedsBuild();
    });
    controller.addStatusListener((s) {
      if (s == AnimationStatus.completed) {
        entry.remove();
        controller.dispose();
      }
    });
    controller.forward();
  }

  Future<void> _saveReminderPrefs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_prefsReminderOn, _reminderOn);
      final mins = _reminderTime.hour * 60 + _reminderTime.minute;
      await prefs.setInt(_prefsReminderMinutes, mins);
    } catch (e) {
      // swallow
    }
  }

  // --- Daily first-use (Tip/Resource) helpers ---
  String _todayStr() {
    final now = DateTime.now();
    final mm = now.month.toString().padLeft(2, '0');
    final dd = now.day.toString().padLeft(2, '0');
    return '${now.year}-$mm-$dd';
  }

  Future<bool> _isFirstUseToday(String key) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final last = prefs.getString(key);
      return last != _todayStr();
    } catch (_) {
      return true;
    }
  }

  Future<void> _markUsedToday(String key) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(key, _todayStr());
    } catch (_) {}
  }

  Future<void> _initQuests() async {
    if (!mounted) return;
    final questProvider = context.read<QuestProvider>();
    await questProvider.loadQuests();
    if (!mounted) return;

    setState(() {
      _computeDisplayedQuestIds();
    });
  }

  Future<void> _refreshToday() async {
    await _initQuests();
  }

  // Refresh Explore: reload catalog via QuestProvider
  Future<void> _refreshExplore() async {
    await context.read<QuestProvider>().loadQuests();
    if (!mounted) return;
    setState(() {});
  }

  /// Unified completion feedback SnackBar with Undo action
  void _showCompletionSnackBar(int questId, String message) {
    if (!mounted) return;
    final questProvider = context.read<QuestProvider>();
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        duration: const Duration(seconds: 5),
        content: Text(message),
        action: SnackBarAction(
          label: 'Undo',
          onPressed: () async {
            await questProvider.updateQuestProgress(questId, 0);
            await _refreshToday();
            await _refreshExplore();
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Reverted.')),
              );
            }
          },
        ),
      ),
    );
  }

  // Choose IDs from today's items to back the 4 static cards.
  // Choose IDs from backend quests to back the 4 static cards.
  //
  // v1.3.3 fix: dedup-aware. Previous logic fell back to quests[2] for both
  // RESOURCE and TIP slots when the backend returned only 3 quests, which
  // surfaced the same exercise twice on the My Quest tab (operator caught
  // "5-4-3-2-1 Grounding" rendered as both RESOURCE + TIP on iOS v1.3.0
  // prod dogfood 2026-06-03). Now each slot pulls a UNIQUE quest_id —
  // when the pool is exhausted, the slot stays null and the per-slot
  // fallback title ("Calm music" / "One tiny step") shows instead.
  void _computeDisplayedQuestIds() {
    final quests = context.read<QuestProvider>().quests;
    if (quests.isEmpty) return;

    final used = <String>{};
    String? pick(int preferredIdx) {
      // Prefer the indexed slot if available + unused.
      if (preferredIdx < quests.length) {
        final candidate = quests[preferredIdx].id.toString();
        if (!used.contains(candidate)) {
          used.add(candidate);
          return candidate;
        }
      }
      // Otherwise scan for any unused quest.
      for (final q in quests) {
        final id = q.id.toString();
        if (!used.contains(id)) {
          used.add(id);
          return id;
        }
      }
      // Pool exhausted — leave null so per-slot fallback title shows.
      return null;
    }

    _qTask1Id = pick(0);
    _qTask2Id = pick(1);
    _qResId = pick(2);
    _qTipId = pick(3);
    assert(
      [_qTask1Id, _qTask2Id, _qResId, _qTipId]
              .where((id) => id != null)
              .toSet()
              .length ==
          [_qTask1Id, _qTask2Id, _qResId, _qTipId].where((id) => id != null).length,
      'Dashboard quest slots must hold distinct quest_ids',
    );
  }
// } removed extra brace

  void _scheduleMidnightRefresh() {
    _midnightTimer?.cancel();
    final now = DateTime.now();
    final nextMidnight =
        DateTime(now.year, now.month, now.day).add(const Duration(days: 1));
    final ms = nextMidnight.difference(now).inMilliseconds;
    _midnightTimer =
        Timer(Duration(milliseconds: ms.clamp(1000, 86400000)), () async {
      await _refreshToday();
      _rescheduleReminder('midnight');
      _scheduleMidnightRefresh();
    });
  }

  @override
  void dispose() {
    // Dispose confetti controller
    _confettiController.dispose();
    // Unsubscribe from route observer
    try {
      final route = ModalRoute.of(context);
      if (route is PageRoute) {
        routeObserver.unsubscribe(this);
        _routeSubscribed = false;
      }
    } catch (_) {}
    _removeTimerPill();
    _microTimer?.cancel();
    _midnightTimer?.cancel();
    _reminderTimer?.cancel();
    // Remove lifecycle observer
    try {
      WidgetsBinding.instance.removeObserver(this);
    } catch (_) {}
    widget.reselect?.removeListener(_onReselect);
    _scrollController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  void deactivate() {
    // Clean up floating UI when navigating away/tab switching
    _removeTimerPill();
    super.deactivate();
  }

  String _formatReminderTime(TimeOfDay t) {
    final hour12 = (t.hourOfPeriod == 0 ? 12 : t.hourOfPeriod).toString();
    final minute = t.minute.toString().padLeft(2, '0');
    final period = t.period == DayPeriod.am ? 'AM' : 'PM';
    return '$hour12:$minute $period';
  }

  bool _isTomorrowLabel(TimeOfDay t) {
    final now = DateTime.now();
    final todayTarget =
        DateTime(now.year, now.month, now.day, t.hour, t.minute);
    return todayTarget
        .isBefore(now); // if passed today, it's effectively tomorrow
  }

  bool _isReminderNear() {
    final now = DateTime.now();
    var target = DateTime(
        now.year, now.month, now.day, _reminderTime.hour, _reminderTime.minute);
    if (target.isBefore(now)) {
      target = target.add(const Duration(days: 1));
    }
    final minutes = target.difference(now).inMinutes;
    return minutes >= 0 && minutes < 10; // within next 10 minutes
  }

  // Reminder scheduler helpers
  void _cancelReminderTimer({String from = 'unspecified'}) {
    if (_reminderTimer != null) {
      if (kDebugMode) {
        try {
          debugPrint('[Reminder][cancel] from=$from');
        } catch (_) {}
      }
    }
    _reminderTimer?.cancel();
    _reminderTimer = null;
    // Only cancel native OS notification when user has reminders turned OFF.
    // Do NOT cancel during lifecycle pauses or reschedules, to avoid losing the scheduled alert.
    try {
      if (!_reminderOn) {
        NotificationService.cancelReminder();
      }
    } catch (_) {}
  }

  void _scheduleNextReminder({String from = 'unspecified'}) {
    // Only schedule when toggle is ON
    if (!_reminderOn) {
      _cancelReminderTimer(from: from);
      return;
    }
    _cancelReminderTimer(from: from);
    final now = DateTime.now();
    DateTime target = DateTime(
        now.year, now.month, now.day, _reminderTime.hour, _reminderTime.minute);
    if (!target.isAfter(now)) {
      target = target.add(const Duration(days: 1));
    }
    final delay = target.difference(now);
    // Clamp delay to reasonable bounds (>=1s, <= 2 days)
    final Duration clamped =
        Duration(milliseconds: delay.inMilliseconds.clamp(1000, 172800000));
    if (kDebugMode) {
      try {
        debugPrint(
            '[Reminder][schedule] from=$from target=${target.toIso8601String()} delay=${clamped.inSeconds}s');
      } catch (_) {}
    }
    _reminderTimer = Timer(clamped, _onReminderFired);
    // Also schedule a native OS notification so the user is nudged even if the app is backgrounded.
    // The service defensively cancels any previous pending reminder to avoid duplicates.
    try {
      NotificationService.scheduleOneShot(
        target: target,
        title: 'Daily check‑in',
        body:
            'Time for your quick check‑in. Take 2 minutes to reflect and log your mood.',
        debugTag: 'daily_reminder',
      );
    } catch (_) {}
  }

  void _rescheduleReminder(String from) {
    if (!_reminderOn) {
      _cancelReminderTimer(from: from);
      return;
    }
    _scheduleNextReminder(from: from);
  }

  void _onReminderFired() {
    // If widget disposed, skip
    if (!mounted) return;
    final now = DateTime.now();
    // Haptic + sound feedback
    HapticFeedback.mediumImpact();
    try {
      SystemSound.play(SystemSoundType.alert);
    } catch (_) {
      SystemSound.play(SystemSoundType.click);
    }
    // Microinteractions to draw attention
    _showCheckRipple(_reminderToggleKey);
    _showTimerRing(_reminderTimeKey);
    // In-app notification
    try {
      final msg = 'It\'s time for your daily reminder';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 4),
          action: SnackBarAction(
            label: 'Open',
            onPressed: () {
              // Bring user focus to Today tab if not already
              if (_tabIndex != 0) {
                setState(() {
                  _tabIndex = 0;
                });
              }
            },
          ),
        ),
      );
    } catch (_) {}
    // Telemetry
    try {
      final qid = _qTask1Id ?? _qTask2Id;
      logAnalyticsEvent('quest_reminder_fired', metadata: {
        if (qid != null) 'quest_id': qid,
        'surface': 'wellness_dashboard',
        'variant': 'today',
        'tag': 'fired',
        'ts': now.millisecondsSinceEpoch,
        'ui': 'in_app',
      });
    } catch (_) {}
    // Schedule next occurrence (tomorrow)
    _scheduleNextReminder(from: 'post_fire');
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    if (kDebugMode) {
      try {
        debugPrint('[Lifecycle] state=$state');
      } catch (_) {}
    }
    if (state == AppLifecycleState.resumed) {
      // If we missed the target while backgrounded, fire immediately within grace window
      final now = DateTime.now();
      DateTime target = DateTime(now.year, now.month, now.day,
          _reminderTime.hour, _reminderTime.minute);
      if (!target.isAfter(now)) {
        // Today target has passed
        final diff = now.difference(target).inMinutes;
        // Fire if within 15 minutes of target, else just schedule next
        if (_reminderOn && diff >= 0 && diff <= 15) {
          // Avoid double-fire if timer also triggers; cancel then fire
          _cancelReminderTimer(from: 'resume_fire');
          _onReminderFired();
          return;
        }
      }
      _rescheduleReminder('resume');
    } else if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      // Cancel active timer to avoid stale callback while backgrounded
      _cancelReminderTimer(from: 'pause');
    }
  }

  void _startMicrocopyRotation() {
    _microTimer?.cancel();
    if (_reminderOn) {
      _microTimer = Timer.periodic(const Duration(seconds: 6), (_) {
        setState(() {
          _microIndex = (_microIndex + 1) % _microcopy.length;
        });
      });
    }
  }

  // DEBUG ONLY: programmatically exercise reminder microinteractions once
  Future<void> _debugRunReminderSelfTestOnce() async {
    if (!kDebugMode || !_debugAutoTestReminder) return;
    // Only run once per day to avoid annoyance on hot restarts
    const key = 'debug.reminder_test_run_today_v1';
    final first = await _isFirstUseToday(key);
    if (!first) return;
    await _markUsedToday(key);
    await Future<void>.delayed(const Duration(milliseconds: 300));
    if (!mounted) return;
    if (kDebugMode) debugPrint('[Reminder][selftest] start');
    // 1) Toggle ripple: flip OFF then ON with ripple
    setState(() {
      _reminderOn = !_reminderOn;
    });
    if (kDebugMode)
      debugPrint(
          '[Reminder][selftest] toggle -> ${_reminderOn ? 'ON' : 'OFF'}');
    HapticFeedback.lightImpact();
    SystemSound.play(SystemSoundType.click);
    _showCheckRipple(_reminderToggleKey);
    await Future<void>.delayed(const Duration(milliseconds: 420));
    if (!mounted) return;
    setState(() {
      _reminderOn = true;
    });
    if (kDebugMode) debugPrint('[Reminder][selftest] toggle -> ON');
    HapticFeedback.lightImpact();
    SystemSound.play(SystemSoundType.click);
    _showCheckRipple(_reminderToggleKey);
    await _saveReminderPrefs();
    if (!mounted) return;
    // 2) Time change ring: move time by +1 min and show ring
    final nextMinute = (TimeOfDay(
      hour: _reminderTime.hour,
      minute: (_reminderTime.minute + 1) % 60,
    ));
    setState(() {
      _reminderTime = nextMinute;
    });
    if (kDebugMode)
      debugPrint(
          '[Reminder][selftest] time -> ${_reminderTime.format(context)}');
    HapticFeedback.selectionClick();
    SystemSound.play(SystemSoundType.click);
    _showTimerRing(_reminderTimeKey);
    await _saveReminderPrefs();
    if (kDebugMode) debugPrint('[Reminder][selftest] done');
  }

  @override
  void initState() {
    super.initState();
    _loadQuickCheckinFlag();
    // Initialize confetti controller - refined duration for premium feel
    _confettiController =
        ConfettiController(duration: const Duration(seconds: 2));
    // Observe app lifecycle for reminder scheduling
    WidgetsBinding.instance.addObserver(this);
    // When embedded inside HomeShell (no bottom nav), start on Today tab by default
    if (!widget.showBottomNav) {
      _tabIndex = 0; // Default to Today (0) when embedded; 1 = Explore
    }
    _pulseController = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1200))
      ..repeat(reverse: true);
    _startMicrocopyRotation();
    // Initialize asynchronously: reminder prefs, quests data, and midnight refresh
    Future.microtask(() async {
      await _loadReminderPrefs();
      await _loadLastSeenDate(); // R1D3: for longAbsence detection
      _rescheduleReminder('init');
      // DEBUG ONLY: reset quests state on each launch to test persistence/awards
      // NOTE: Quests state is now managed via QuestProvider
      await _initQuests();
      await _saveLastSeenDate(); // R1D3: record today as last-seen
      _scheduleMidnightRefresh();
      // DEBUG ONLY: run reminder microinteraction self-test once per day,
      // after first frame so keys are mounted
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _debugRunReminderSelfTestOnce();
      });
    });
    // Listen for bottom-tab re-tap events
    widget.reselect?.addListener(_onReselect);
  }

  @override
  void didUpdateWidget(WellnessDashboardScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.reselect != widget.reselect) {
      oldWidget.reselect?.removeListener(_onReselect);
      widget.reselect?.addListener(_onReselect);
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Subscribe to route changes so we can clean up overlay when covered
    final route = ModalRoute.of(context);
    if (route is PageRoute) {
      try {
        // Avoid duplicate subscriptions across dependency changes
        if (_routeSubscribed) {
          routeObserver.unsubscribe(this);
          _routeSubscribed = false;
        }
        routeObserver.subscribe(this, route);
        _routeSubscribed = true;
      } catch (_) {}
    }
  }

  @override
  void didPushNext() {
    // Another route pushed on top (e.g., switching tabs or opening sheet)
    if (kDebugMode) {
      try {
        debugPrint('[Pill][ROUTE] didPushNext -> remove pill');
      } catch (_) {}
    }
    _removeTimerPill();
  }

  @override
  void didPopNext() {
    // A subsequent route popped, revealing this one
    if (kDebugMode) {
      try {
        debugPrint('[Pill][ROUTE] didPopNext');
      } catch (_) {}
    }
    // No-op: pill is only created explicitly while on this screen
  }

  // Handle bottom tab reselect: scroll to top if scrolled, otherwise refresh
  void _onReselect() {
    if (!mounted) return;
    final reduceMotion =
        MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (_scrollController.hasClients) {
      final offset = _scrollController.offset;
      const threshold = 64.0;
      if (offset > threshold) {
        if (reduceMotion) {
          _scrollController.jumpTo(0);
        } else {
          _scrollController.animateTo(0,
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOut);
        }
        return;
      }
    }
    // Near top: trigger a lightweight refresh of active tab
    if (_tabIndex == 0) {
      _refreshToday();
    } else {
      _refreshExplore();
    }
  }

  @override
  void didPop() {
    // This route popped: ensure complete cleanup
    if (kDebugMode) {
      try {
        debugPrint('[Pill][ROUTE] didPop -> remove pill');
      } catch (_) {}
    }
    _removeTimerPill();
  }

  // Start a floating timer pill anchored near the given card.
  void _startTimerPill(
      {required GlobalKey cardKey,
      required String questId,
      required Duration total}) {
    _removeTimerPill();
    // Only show pill when this screen is visible.
    // If used standalone (showBottomNav=true), require route '/wellness-dashboard' and current.
    // If used inside HomeShell (showBottomNav=false), we are on '/home'; allow when current.
    final route = ModalRoute.of(context);
    final routeName = route?.settings.name;
    final isCurrent = route?.isCurrent ?? true;
    // Consider visible when current; do not strictly require a named route (can be null under builders)
    final bool allow = isCurrent &&
        (!widget.showBottomNav ||
            routeName == '/wellness-dashboard' ||
            routeName == null);
    // Also require we're on the Today tab to avoid showing on Explore/programmatic switches
    if (!allow || _tabIndex != 0) {
      _removeTimerPill(forQuestId: questId);
      return;
    }
    if (kDebugMode) {
      try {
        debugPrint(
            '[Pill][START] questId=$questId total=${total.inMinutes}m route=${routeName ?? 'null'} isCurrent=$isCurrent');
      } catch (_) {}
    }
    final reduceMotion =
        MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    // Use screen-scoped overlay so the pill is owned by this screen
    final overlay = Overlay.of(context);
    final overlayBox = overlay.context.findRenderObject() as RenderBox?;
    final centerGlobal = _globalCenterOf(cardKey);
    if (overlayBox == null || !overlayBox.attached || centerGlobal == null)
      return;
    final centerLocal = overlayBox.globalToLocal(centerGlobal);
    _timerPillQuestId = questId;
    _timerPillEndAt = DateTime.now().add(total);
    // Prepare animation controller and scale tween
    _timerPillAnim?.dispose();
    _timerPillAnim = null;
    if (!reduceMotion) {
      _timerPillAnim = AnimationController(
          vsync: this, duration: const Duration(milliseconds: 1400))
        ..repeat(reverse: true);
    }
    final Animation<double> scaleAnim = _timerPillAnim == null
        ? const AlwaysStoppedAnimation<double>(1.0)
        : Tween<double>(begin: 0.98, end: 1.02).animate(
            CurvedAnimation(parent: _timerPillAnim!, curve: Curves.easeInOut));

    String _fmt(Duration d) {
      final s = d.inSeconds.clamp(0, 24 * 3600);
      final mm = (s ~/ 60).toString().padLeft(2, '0');
      final ss = (s % 60).toString().padLeft(2, '0');
      return '$mm:$ss';
    }

    _timerPillEntry = OverlayEntry(builder: (_) {
      final now = DateTime.now();
      final remaining = _timerPillEndAt != null
          ? _timerPillEndAt!.difference(now)
          : Duration.zero;
      final txt = _fmt(remaining);
      // Position slightly to the right of the card center
      final left = (centerLocal.dx + 64)
          .clamp(8.0, (overlayBox.size.width - 140).toDouble());
      final top = (centerLocal.dy - 16)
          .clamp(8.0, (overlayBox.size.height - 40).toDouble());
      return Positioned(
        left: left,
        top: top,
        child: IgnorePointer(
          ignoring: true,
          child: AnimatedBuilder(
            animation: scaleAnim,
            builder: (context, child) =>
                Transform.scale(scale: scaleAnim.value, child: child),
            child: Builder(builder: (ctx) {
              final scheme = Theme.of(ctx).colorScheme;
              final scaffoldBg = Theme.of(ctx).scaffoldBackgroundColor;
              Color bg = scheme.primary;
              // If primary is too close to scaffold background, fall back
              bool similar(Color a, Color b) {
                double dr = (a.r - b.r).abs();
                double dg = (a.g - b.g).abs();
                double db = (a.b - b.b).abs();
                return (dr + dg + db) <
                    0.12; // ~30/255 threshold for normalized channels
              }

              if (similar(bg, scaffoldBg)) {
                bg = scheme.primaryContainer;
                if (similar(bg, scaffoldBg)) {
                  bg = scheme.secondary;
                }
              }
              final fg =
                  ThemeData.estimateBrightnessForColor(bg) == Brightness.dark
                      ? Colors.white
                      : Colors.black87;
              return Material(
                color: bg,
                shape: const StadiumBorder(),
                elevation: 3,
                shadowColor: Colors.black.withValues(alpha: 0.2),
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  child: Text(
                    txt,
                    style: TextStyleHelper.instance.titleMediumInter
                        .copyWith(color: fg, fontWeight: FontWeight.w700),
                  ),
                ),
              );
            }),
          ),
        ),
      );
    });
    overlay.insert(_timerPillEntry!);
    _timerPillTicker = Timer.periodic(const Duration(seconds: 1), (_) {
      // If screen no longer visible, remove immediately
      final route = ModalRoute.of(context);
      final currentName = route?.settings.name;
      final isCurrent = route?.isCurrent ?? true;
      final bool stillVisible =
          isCurrent; // route name can be null when built via builder
      final bool onToday = _tabIndex == 0;
      if (!stillVisible || !onToday) {
        if (kDebugMode) {
          try {
            debugPrint(
                '[Pill][CLEANUP] route_or_tab_changed current=${currentName ?? 'null'} isCurrent=$isCurrent tab=$_tabIndex questId=$questId');
          } catch (_) {}
        }
        _removeTimerPill(forQuestId: questId);
        return;
      }
      if (_timerPillEndAt == null) return;
      if (DateTime.now().isAfter(_timerPillEndAt!)) {
        _removeTimerPill(forQuestId: questId);
      } else {
        _timerPillEntry?.markNeedsBuild();
      }
    });
    _timerPillAnim?.addStatusListener((_) {});
  }

  void _removeTimerPill({String? forQuestId}) {
    if (forQuestId != null &&
        _timerPillQuestId != null &&
        _timerPillQuestId != forQuestId) return;
    if (kDebugMode) {
      try {
        debugPrint(
            '[Pill][REMOVE] questId=${forQuestId ?? _timerPillQuestId ?? 'null'} hadTicker=${(_timerPillTicker != null)} hadEntry=${(_timerPillEntry != null)}');
      } catch (_) {}
    }
    // Cancel any scheduled auto-complete to avoid firing after navigation/cancel
    if (_autoCompleteTimer != null) {
      try {
        if (kDebugMode)
          debugPrint(
              '[Pill][AUTO] cancel questId=${forQuestId ?? _timerPillQuestId ?? 'null'}');
      } catch (_) {}
    }
    _autoCompleteTimer?.cancel();
    _autoCompleteTimer = null;
    // Clear timer-related state
    _timerPillTicker?.cancel();
    _timerPillTicker = null;
    _timerPillEndAt = null;
    _timerPillQuestId = null;
    _timerPillAnim?.dispose();
    _timerPillAnim = null;
    _timerPillEntry?.remove();
    _timerPillEntry = null;
  }

  Future<void> _openTimerSheet({
    required String questId,
    required GlobalKey cardKey,
    required String title,
    required int durationMin,
  }) async {
    if (!mounted) return;
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: TextStyleHelper.instance.headline21Inter),
              const SizedBox(height: 8),
              Text('Estimated ${durationMin} min',
                  style: TextStyleHelper.instance.titleMediumInter
                      .copyWith(color: const Color(0xFF6B7280))),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () async {
                    Navigator.of(ctx).pop();
                    // In-memory start for UI
                    HapticFeedback.lightImpact();
                    SystemSound.play(SystemSoundType.click);
                    _showTimerRing(cardKey);
                    _startTimerPill(
                        cardKey: cardKey,
                        questId: questId,
                        total: Duration(minutes: durationMin));
                    // Telemetry: quest_progress at timer start
                    try {
                      logAnalyticsEvent('quest_progress', metadata: {
                        'quest_id': questId,
                        'surface': 'wellness_dashboard',
                        'variant': 'today',
                        'tag': 'timer_start',
                        'ts': DateTime.now().millisecondsSinceEpoch,
                        'progress': 0.0,
                        'duration_ms': durationMin * 60000,
                        'ui': 'timer_sheet',
                      });
                    } catch (_) {}
                    // Auto-complete disabled: require explicit user action to complete
                    try {
                      if (kDebugMode)
                        debugPrint(
                            '[Pill][AUTO] disabled (require explicit completion) questId=$questId');
                    } catch (_) {}
                    _autoCompleteTimer?.cancel();
                    _autoCompleteTimer = null;
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                            content:
                                Text('Timer started for $durationMin min')),
                      );
                    }
                  },
                  child: Text('Start ${durationMin} min'),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () async {
                    Navigator.of(ctx).pop();
                    final qId = int.tryParse(questId);
                    if (qId != null) {
                      await context
                          .read<QuestProvider>()
                          .updateQuestProgress(qId, 100);

                      try {
                        final lifetimeXp =
                            context.read<QuestProvider>().totalXP;
                        if (mounted) {
                          context
                              .read<ProgressProvider>()
                              .updateLifetimeXp(lifetimeXp);
                        }
                      } catch (_) {}
                    }
                    _showCheckRipple(cardKey);
                    // Telemetry: quest_complete for instant completion
                    try {
                      logAnalyticsEvent('quest_complete', metadata: {
                        'quest_id': questId,
                        'surface': 'wellness_dashboard',
                        'variant': 'today',
                        'tag': 'complete_now',
                        'ts': DateTime.now().millisecondsSinceEpoch,
                        'success': true,
                        'progress': 1.0,
                        'ui': 'timer_sheet',
                      });
                    } catch (_) {}
                    await _refreshToday();
                    await _refreshExplore();

                    _showCompletionSnackBar(
                        qId!, 'Done! You showed up for yourself today 💪');
                  },
                  child: const Text('Complete now'),
                ),
              ),
              const SizedBox(height: 8),
              Center(
                child: TextButton(
                  onPressed: () => Navigator.of(ctx).pop(),
                  child: const Text('Cancel'),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _showCompleteConfirmation({
    required String questId,
    required String title,
    required String telemetryTag,
    required String ui,
    required GlobalKey cardKey,
  }) async {
    if (!mounted) return;
    final questProvider = context.read<QuestProvider>();
    final q = questProvider.getQuestById(int.tryParse(questId) ?? -1);
    if (q == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Quest not found')),
        );
      }
      return;
    }

    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: TextStyleHelper.instance.headline21Inter),
              const SizedBox(height: 8),
              Text('Mark complete for today?',
                  style: TextStyleHelper.instance.titleMediumInter
                      .copyWith(color: const Color(0xFF6B7280))),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () async {
                        Navigator.of(ctx).pop();
                        HapticFeedback.heavyImpact();
                        SystemSound.play(SystemSoundType.click);

                        try {
                          await questProvider.updateQuestProgress(q.id, 100);

                          // Visual feedback
                          try {
                            _showCheckRipple(cardKey);
                          } catch (_) {}

                          // Telemetry
                          try {
                            logAnalyticsEvent('quest_complete', metadata: {
                              'quest_id': questId,
                              'surface': 'wellness_dashboard',
                              'variant': 'today',
                              'tag': 'xp_awarded',
                              'ts': DateTime.now().millisecondsSinceEpoch,
                              'success': true,
                              'progress': 1.0,
                              'ui': ui,
                              'source': telemetryTag,
                            });
                          } catch (_) {}

                          await _refreshToday();
                          await _refreshExplore();

                          _showCompletionSnackBar(q.id,
                              'Done! You showed up for yourself today 💪');
                        } catch (e) {
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                  content: Text('Failed to update progress')),
                            );
                          }
                        }
                      },
                      child: const Text('Mark complete'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        Navigator.of(ctx).pop();
                      },
                      child: const Text('Cancel'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  // Short timer ring microinteraction centered on a card
  void _showTimerRing(GlobalKey sourceKey) {
    // Respect reduce-motion: skip decorative animation
    final reduceMotion =
        MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduceMotion) return;
    final startGlobal = _globalCenterOf(sourceKey);
    // Use screen-scoped overlay so ring belongs to this screen
    final overlayState = Overlay.of(context);
    if (startGlobal == null) return;
    final overlayBox = overlayState.context.findRenderObject() as RenderBox?;
    if (overlayBox == null || !overlayBox.attached) return;
    final start = overlayBox.globalToLocal(startGlobal);
    final size = overlayBox.size;

    final controller = AnimationController(
      vsync: this,
      duration: kRingDuration,
    );
    final anim = CurvedAnimation(parent: controller, curve: kRingCurve);

    late OverlayEntry entry;
    entry = OverlayEntry(builder: (_) {
      return Positioned.fill(
        child: IgnorePointer(
          ignoring: true,
          child: CustomPaint(
            painter: _RingPainter(
              center: Offset(
                start.dx.clamp(0.0, size.width),
                start.dy.clamp(0.0, size.height),
              ),
              progress: anim.value, // 0..1
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
        ),
      );
    });
    overlayState.insert(entry);
    controller.addListener(() {
      entry.markNeedsBuild();
    });
    controller.forward().whenComplete(() {
      entry.remove();
      controller.dispose();
    });
  }

  // Optional +XP chip pop animation from a source card to XP card
  void _showXpChipPop(GlobalKey sourceKey, {required int amount}) {
    final startGlobal = _globalCenterOf(sourceKey);
    final endGlobal = _globalCenterOf(_xpCardKey);
    if (startGlobal == null || endGlobal == null) return;

    final overlayState = Navigator.of(context).overlay ?? Overlay.of(context);

    final overlayBox = overlayState.context.findRenderObject() as RenderBox?;
    if (overlayBox == null || !overlayBox.attached) return;

    // Convert to overlay-local coordinates
    Offset start = overlayBox.globalToLocal(startGlobal);
    Offset end = overlayBox.globalToLocal(endGlobal);

    // Clamp and fallback for small screens or offscreen targets
    final size = overlayBox.size;
    bool endOff = end.dx.isNaN ||
        end.dy.isNaN ||
        end.dx < 0 ||
        end.dy < 0 ||
        end.dx > size.width ||
        end.dy > size.height;
    if (endOff) {
      // simple upward pop if XP card is not visible
      end = start.translate(0, -80);
    }
    if (kDebugMode && _debugXpLogs) {
      // optional position logs removed
    }

    // Respect reduce-motion: show a lightweight toast instead of animated chip
    final reduceMotion =
        MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduceMotion) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('+$amount XP'),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(milliseconds: 900),
        ),
      );
      return;
    }

    // Animation polish: snappier ease + minor timing tweak
    final controller = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 380));
    final position = Tween<Offset>(begin: start, end: end)
        .chain(CurveTween(curve: Curves.easeOutCubic))
        .animate(controller);
    final fade = CurvedAnimation(
        parent: controller,
        curve: const Interval(0.0, 0.8, curve: Curves.easeOut));
    final scale = Tween<double>(begin: 0.92, end: 1.06)
        .chain(CurveTween(curve: Curves.fastOutSlowIn))
        .animate(controller);

    late OverlayEntry entry;
    entry = OverlayEntry(builder: (ctx) {
      final pos = position.value;
      final primary = Theme.of(context).colorScheme.primary;
      double left = pos.dx - 26;
      double top = pos.dy - 14;
      // Bound the chip within overlay to avoid rendering offscreen
      left = left.clamp(4.0, size.width - 52.0);
      top = top.clamp(4.0, size.height - 32.0);
      return Positioned(
        left: left,
        top: top,
        child: IgnorePointer(
          ignoring: true,
          child: Opacity(
            opacity: fade.value.clamp(0.0, 1.0),
            child: Transform.scale(
              scale: scale.value,
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                decoration: BoxDecoration(
                  color: primary,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.white, width: 1.5),
                  boxShadow: [
                    BoxShadow(
                      color: primary.withValues(alpha: 0.22),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.star_rounded,
                        color: Colors.white, size: 16),
                    const SizedBox(width: 6),
                    Text(
                      '+$amount XP',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    });

    overlayState.insert(entry);
    controller.addListener(() => entry.markNeedsBuild());
    controller.forward().whenComplete(() async {
      // Slightly faster fade-out tail (-80ms)
      await Future<void>.delayed(const Duration(milliseconds: 40));
      entry.remove();
      controller.dispose();
    });
  }

  @override
  Widget build(BuildContext context) {
    // Build
    return Sizer(builder: (context, orientation, deviceType) {
      return KeyboardDismissibleScaffold(
        safeTop: false,
        safeBottom: false,
        bottomNavigationBar: widget.showBottomNav
            ? const AppBottomNav(current: AppTab.quest)
            : null,
        body: Stack(
          children: [
            Column(
              children: [
                // Sticky header outside the scroll view (matches Mood Tracker)
                _buildHeader(),
                // Scrollable content below header
                Expanded(
                  child: Stack(
                    children: [
                      // Plain themed background (no image)
                      Container(
                        height: MediaQuery.of(context).size.height,
                        width: MediaQuery.of(context).size.width,
                        color: Theme.of(context).scaffoldBackgroundColor,
                      ),
                      SingleChildScrollView(
                        controller: _scrollController,
                        padding: EdgeInsets.only(
                            bottom: MediaQuery.of(context).viewPadding.bottom),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Segmented tabs at top of scrollable content
                            _buildTabsSection(),
                            // Sections (conditional by tab)
                            if (_tabIndex == 0) ...[
                              // R1D2+R1D3: state-branched hero replaces gamification cards
                              _buildHeroSection(),
                              _buildWeekShapeSection(),
                              _buildQuickLanesSection(),
                              _buildNudgeZoneSection(),
                              _buildRecommendationsSection(),
                            ] else ...[
                              _buildExploreSection(),
                            ],
                            SizedBox(height: 24.h),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            // Confetti celebration overlay
            Align(
              alignment: Alignment.topCenter,
              child: ConfettiWidget(
                confettiController: _confettiController,
                blastDirectionality: BlastDirectionality.explosive,
                shouldLoop: false,
                colors: _isStarConfetti
                    ? const [Colors.amber, Colors.orange, Colors.purpleAccent]
                    : const [
                        Color(0xFF667EEA), // Primary purple
                        Color(0xFFFF6B6B), // Coral
                        Color(0xFF4ECDC4), // Teal
                        Color(0xFFFFE66D), // Yellow
                        Color(0xFF95E1D3), // Mint
                      ],
                createParticlePath: _isStarConfetti ? drawStar : null,
                numberOfParticles: 30,
                gravity: 0.2,
              ),
            ),
          ],
        ),
      );
    });
  }

  // Legacy mood gating (still used elsewhere if needed)
  bool _hasLoggedMoodToday(MoodProvider moodProvider) {
    final now = DateTime.now().toUtc();
    for (final e in moodProvider.moodEntries) {
      final t = e.timestamp.toUtc();
      if (t.year == now.year && t.month == now.month && t.day == now.day) {
        return true;
      }
    }
    return false;
  }

  // Sticky header above the segmented control
  Widget _buildHeader() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          color: appTheme.whiteCustom,
          padding: EdgeInsets.symmetric(horizontal: 16.h, vertical: 16.h),
          child: SafeArea(
            top: true,
            bottom: false,
            child: Row(
              children: [
                Builder(
                  builder: (ctx) {
                    final canPop = Navigator.of(ctx).canPop();
                    final route = ModalRoute.of(ctx);
                    final isModal =
                        route is PageRoute && route.fullscreenDialog == true;
                    if (canPop) {
                      return AppBackButton(isModal: isModal);
                    }
                    return SizedBox(width: 44.h);
                  },
                ),
                Expanded(
                  child: GestureDetector(
                    onLongPress: () async {
                      if (!kDebugMode) return;
                      try {
                        HapticFeedback.selectionClick();
                      } catch (_) {}
                      if (kDebugMode) {
                        try {
                          debugPrint(
                              '[Debug][Quests] Reset via header long-press');
                        } catch (_) {}
                      }
                      try {
                        await context.read<QuestProvider>().loadQuests();
                      } catch (_) {}
                      try {
                        await _refreshToday();
                        await _refreshExplore();
                      } catch (_) {}
                      if (mounted) {
                        try {
                          ScaffoldMessenger.of(context).hideCurrentSnackBar();
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text('Quests reset (debug)')),
                          );
                        } catch (_) {}
                      }
                    },
                    child: Text(
                      'My Quest',
                      textAlign: TextAlign.center,
                      style: TextStyleHelper.instance.headline24Bold,
                    ),
                  ),
                ),
                // R1D2: Profile avatar button — opens profile nav sheet (Tier 2.1)
                GestureDetector(
                  onTap: () => showProfileNavSheet(context),
                  child: Container(
                    width: 44.h,
                    height: 44.h,
                    alignment: Alignment.center,
                    child: Container(
                      width: 36.h,
                      height: 36.h,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [GQColors.primary, GQColors.coral],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Color(0x26667EEA),
                            blurRadius: 14,
                            offset: Offset(0, 6),
                          ),
                        ],
                      ),
                      child: const Icon(Icons.person,
                          color: Colors.white, size: 16),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        Container(
          height: 8.h,
          color: appTheme.colorFFF3F4,
        ),
      ],
    );
  }

  // ── R1D2+R1D3: Hero section — state-branched dashboard hero card ─────────────

  /// Greeting text for State A/B/D per HTML spec.
  String _greetingLine1(DashboardState state, String dayName) {
    switch (state) {
      case DashboardState.longAbsence:
        return 'Welcome back, friend.';
      case DashboardState.weekend:
        return 'Good morning, friend.';
      case DashboardState.feelingGreat:
        return 'Evening, friend.';
      case DashboardState.notLogged:
        return 'Good evening, friend.';
    }
  }

  String _greetingLine2(DashboardState state, String dayName) {
    switch (state) {
      case DashboardState.longAbsence:
        return "It's been a bit.";
      case DashboardState.weekend:
        return '$dayName — slower today.';
      case DashboardState.feelingGreat:
        return 'Glowing today 🌱';
      case DashboardState.notLogged:
        return 'Quick check-in?';
    }
  }

  Widget _buildHeroSection() {
    final moodProvider = context.watch<MoodProvider>();
    final now = DateTime.now();
    final dayNames = [
      'Monday', 'Tuesday', 'Wednesday', 'Thursday',
      'Friday', 'Saturday', 'Sunday'
    ];
    final dayName = dayNames[now.weekday - 1];
    final state = _computeDashboardState(moodProvider);
    final daysAway = _daysAwayCount(moodProvider);

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 600),
        padding: EdgeInsets.fromLTRB(16.h, 20.h, 16.h, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Greeting strip ─────────────────────────────────────────────
            Text(
              _greetingLine1(state, dayName),
              style: TextStyleHelper.instance.headline28BoldInter.copyWith(
                fontFamily: CoreTextStyles
                    .TextStyleHelper.instance.headline24Bold.fontFamily,
                color: GQColors.ink,
                letterSpacing: -0.4,
                height: 1.15,
              ),
            ),
            SizedBox(height: 2.h),
            Text(
              _greetingLine2(state, dayName),
              style: TextStyleHelper.instance.titleMediumInter.copyWith(
                fontFamily: CoreTextStyles
                    .TextStyleHelper.instance.headline24Bold.fontFamily,
                color: GQColors.ink2,
                fontWeight: FontWeight.w600,
              ),
            ),
            SizedBox(height: 16.h),
            // ── Hero card (state-branched) ──────────────────────────────────
            _buildHeroCard(state, daysAway),
          ],
        ),
      ),
    );
  }

  Widget _buildHeroCard(DashboardState state, int daysAway) {
    switch (state) {
      case DashboardState.notLogged:
        return _buildNotLoggedCard();
      case DashboardState.feelingGreat:
        return _buildFeelingGreatCard();
      case DashboardState.longAbsence:
        return _buildLongAbsenceCard(daysAway);
      case DashboardState.weekend:
        return _buildWeekendCard();
    }
  }

  // State A — notLogged: mood check-in prompt (existing pattern, modernised)
  Widget _buildNotLoggedCard() {
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFEEF0FE), Color(0xFFFBF1F4), Color(0xFFFFE8E8)],
        ),
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        border: Border.all(color: const Color(0x2D667EEA)),
      ),
      padding: EdgeInsets.all(20.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'TODAY, JUST ONE THING',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: GQColors.primaryDk,
              letterSpacing: 0.5,
            ),
          ),
          SizedBox(height: 6.h),
          Text(
            "Log how you're feeling — 15 seconds.",
            style: TextStyleHelper.instance.headline21Inter.copyWith(
              fontFamily: CoreTextStyles
                  .TextStyleHelper.instance.headline24Bold.fontFamily,
              color: GQColors.ink,
              fontWeight: FontWeight.w800,
              fontSize: 18,
              height: 1.3,
              letterSpacing: -0.3,
            ),
          ),
          SizedBox(height: 12.h),
          // Mood teaser strip
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: const [
              Text('😔', style: TextStyle(fontSize: 22)),
              SizedBox(width: 10),
              Text('😐', style: TextStyle(fontSize: 22)),
              SizedBox(width: 10),
              Text('🙂', style: TextStyle(fontSize: 22)),
              SizedBox(width: 10),
              Text('😊', style: TextStyle(fontSize: 22)),
              SizedBox(width: 10),
              Text('😄', style: TextStyle(fontSize: 22)),
            ],
          ),
          SizedBox(height: 14.h),
          Builder(builder: (context) {
            final isDone = _hasCompletedQuickCheckinToday ||
                (context.watch<QuestProvider>().quests.any(
                    (q) => q.type == 'check_in' && q.isCompleted));
            return SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                key: _startBtnKey,
                onPressed: isDone
                    ? null
                    : () async {
                        HapticFeedback.selectionClick();
                        await Future<void>.delayed(
                            const Duration(milliseconds: 220));
                        if (!mounted) return;
                        showDialog(
                          context: context,
                          barrierDismissible: false,
                          builder: (ctx) => AssessmentSplash(
                            onSubmitted: _onQuickCheckinSubmitted,
                          ),
                        );
                      },
                style: ElevatedButton.styleFrom(
                  backgroundColor:
                      isDone ? const Color(0xFFE6EAF0) : GQColors.primary,
                  foregroundColor: isDone ? GQColors.ink3 : Colors.white,
                  shape: const StadiumBorder(),
                  padding:
                      EdgeInsets.symmetric(horizontal: 24.h, vertical: 14.h),
                  elevation: isDone ? 0 : 4,
                  shadowColor: GQColors.primary.withValues(alpha: 0.35),
                ),
                child: Text(
                  isDone ? 'Logged today ✓' : 'Quick check-in',
                  style: const TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w800),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  // State B — feelingGreat: capture wisdom card
  Widget _buildFeelingGreatCard() {
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFF1E5), Color(0xFFFFE8E8)],
        ),
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        border: Border.all(color: const Color(0x40FF8A6E)),
      ),
      padding: EdgeInsets.all(20.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'TODAY, JUST ONE THING',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: const Color(0xFFB5562F),
              letterSpacing: 0.5,
            ),
          ),
          SizedBox(height: 6.h),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('✨', style: TextStyle(fontSize: 24)),
              SizedBox(width: 10.h),
              Expanded(
                child: Text(
                  "Nice. Want to capture what's working?",
                  style: TextStyleHelper.instance.headline21Inter.copyWith(
                    fontFamily: CoreTextStyles
                        .TextStyleHelper.instance.headline24Bold.fontFamily,
                    color: GQColors.ink,
                    fontWeight: FontWeight.w800,
                    fontSize: 18,
                    height: 1.3,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 14.h),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                HapticFeedback.selectionClick();
                Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const JournalScreen()));
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: GQColors.coral,
                foregroundColor: Colors.white,
                shape: const StadiumBorder(),
                padding:
                    EdgeInsets.symmetric(horizontal: 24.h, vertical: 14.h),
                elevation: 4,
                shadowColor: GQColors.coral.withValues(alpha: 0.5),
              ),
              child: const Text(
                'Add a journal note',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800),
              ),
            ),
          ),
          SizedBox(height: 8.h),
          Center(
            child: GestureDetector(
              onTap: () {
                HapticFeedback.selectionClick();
                Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const JournalScreen()));
              },
              child: const Text(
                "Tomorrow's me will thank you →",
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF9A6049),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // State C — longAbsence: ReturningRecoveryCard — gentle, not punitive
  Widget _buildLongAbsenceCard(int daysAway) {
    final streakDays = context.read<QuestProvider>().streak;
    return Column(
      children: [
        // Main recovery card
        Container(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFFEEF0FE),
                Color(0xFFF8F7FF),
                Color(0xFFFFE8E8)
              ],
            ),
            borderRadius: BorderRadius.circular(GQRadii.cardLg),
            border: Border.all(color: const Color(0x2D667EEA)),
          ),
          padding: EdgeInsets.all(20.h),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'PICK UP, OR START FRESH',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: GQColors.primaryDk,
                  letterSpacing: 0.5,
                ),
              ),
              SizedBox(height: 6.h),
              Text(
                'Your data is right where you left it.',
                style: TextStyleHelper.instance.headline21Inter.copyWith(
                  fontFamily: CoreTextStyles
                      .TextStyleHelper.instance.headline24Bold.fontFamily,
                  color: GQColors.ink,
                  fontWeight: FontWeight.w800,
                  fontSize: 18,
                  height: 1.3,
                  letterSpacing: -0.3,
                ),
              ),
              // Streak pause pill — descriptive, not punitive
              if (streakDays > 0) ...[
                SizedBox(height: 12.h),
                Container(
                  padding: EdgeInsets.symmetric(
                      horizontal: 12.h, vertical: 9.h),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: GQColors.hair),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('🌱', style: TextStyle(fontSize: 13)),
                      SizedBox(width: 6.h),
                      Flexible(
                        child: RichText(
                          text: TextSpan(
                            style: const TextStyle(
                              fontSize: 11.5,
                              fontWeight: FontWeight.w700,
                              color: GQColors.ink2,
                            ),
                            children: [
                              const TextSpan(text: 'Your '),
                              TextSpan(
                                text: '$streakDays active days',
                                style: const TextStyle(
                                    color: GQColors.ink,
                                    fontWeight: FontWeight.w800),
                              ),
                              const TextSpan(
                                  text:
                                      ' — no rush, no pressure.'),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              SizedBox(height: 14.h),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () {
                        HapticFeedback.selectionClick();
                        showDialog(
                          context: context,
                          barrierDismissible: false,
                          builder: (ctx) => AssessmentSplash(
                            onSubmitted: _onQuickCheckinSubmitted,
                          ),
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: GQColors.primary,
                        foregroundColor: Colors.white,
                        shape: const StadiumBorder(),
                        padding: EdgeInsets.symmetric(vertical: 12.h),
                        elevation: 3,
                        shadowColor:
                            GQColors.primary.withValues(alpha: 0.4),
                      ),
                      child: const Text(
                        'Start fresh',
                        style: TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w800),
                      ),
                    ),
                  ),
                  SizedBox(width: 8.h),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        HapticFeedback.selectionClick();
                        showDialog(
                          context: context,
                          barrierDismissible: false,
                          builder: (ctx) => AssessmentSplash(
                            onSubmitted: _onQuickCheckinSubmitted,
                          ),
                        );
                      },
                      style: OutlinedButton.styleFrom(
                        foregroundColor: GQColors.ink,
                        side: const BorderSide(color: GQColors.hair),
                        shape: const StadiumBorder(),
                        padding: EdgeInsets.symmetric(vertical: 12.h),
                      ),
                      child: Text(
                        streakDays > 0
                            ? 'Keep going — $streakDays active days'
                            : 'Continue',
                        style: const TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w800),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        // Compact one-thing prompt below recovery card
        SizedBox(height: 10.h),
        Container(
          padding: EdgeInsets.symmetric(horizontal: 14.h, vertical: 11.h),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(color: GQColors.hair),
          ),
          child: Row(
            children: [
              Container(
                width: 36.h,
                height: 36.h,
                decoration: BoxDecoration(
                  color: GQColors.primarySoft,
                  borderRadius: BorderRadius.circular(12.h),
                ),
                child:
                    const Center(child: Text('📋', style: TextStyle(fontSize: 16))),
              ),
              SizedBox(width: 10.h),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'Today, just one thing',
                      style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: GQColors.ink),
                    ),
                    SizedBox(height: 1),
                    Text(
                      'A 15-second mood log to start.',
                      style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: GQColors.ink3),
                    ),
                  ],
                ),
              ),
              ElevatedButton(
                onPressed: () {
                  HapticFeedback.selectionClick();
                  showDialog(
                    context: context,
                    barrierDismissible: false,
                    builder: (ctx) => AssessmentSplash(
                      onSubmitted: _onQuickCheckinSubmitted,
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: GQColors.primary,
                  foregroundColor: Colors.white,
                  shape: const StadiumBorder(),
                  padding:
                      EdgeInsets.symmetric(horizontal: 14.h, vertical: 7.h),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  elevation: 2,
                ),
                child: const Text('Log',
                    style:
                        TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800)),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // State D — weekend: LIGHT DAY PLAN card
  Widget _buildWeekendCard() {
    final now = DateTime.now();
    final isDone = _hasCompletedQuickCheckinToday ||
        context.read<QuestProvider>().quests.any(
            (q) => q.type == 'check_in' && q.isCompleted);
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFEEF0FE), Color(0xFFF8F7FF)],
        ),
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        border: Border.all(color: const Color(0x2D667EEA)),
      ),
      padding: EdgeInsets.all(20.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'LIGHT DAY PLAN',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: GQColors.primaryDk,
              letterSpacing: 0.5,
            ),
          ),
          SizedBox(height: 6.h),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('🌤️', style: TextStyle(fontSize: 24)),
              SizedBox(width: 10.h),
              Expanded(
                child: Text(
                  'Log mood, breathe, that\'s it.',
                  style: TextStyleHelper.instance.headline21Inter.copyWith(
                    fontFamily: CoreTextStyles
                        .TextStyleHelper.instance.headline24Bold.fontFamily,
                    color: GQColors.ink,
                    fontWeight: FontWeight.w800,
                    fontSize: 18,
                    height: 1.3,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 14.h),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              key: _startBtnKey,
              onPressed: isDone
                  ? null
                  : () async {
                      HapticFeedback.selectionClick();
                      await Future<void>.delayed(
                          const Duration(milliseconds: 220));
                      if (!mounted) return;
                      showDialog(
                        context: context,
                        barrierDismissible: false,
                        builder: (ctx) => AssessmentSplash(
                          onSubmitted: _onQuickCheckinSubmitted,
                        ),
                      );
                    },
              style: ElevatedButton.styleFrom(
                backgroundColor:
                    isDone ? const Color(0xFFE6EAF0) : GQColors.primary,
                foregroundColor: isDone ? GQColors.ink3 : Colors.white,
                shape: const StadiumBorder(),
                padding:
                    EdgeInsets.symmetric(horizontal: 24.h, vertical: 14.h),
                elevation: isDone ? 0 : 4,
                shadowColor: GQColors.primary.withValues(alpha: 0.35),
              ),
              child: Text(
                isDone ? 'Logged today ✓' : 'Easy check-in',
                style:
                    const TextStyle(fontSize: 14, fontWeight: FontWeight.w800),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── R1D2+R1D3: WeekShape — 7-bar mood chart ──────────────────────────────
  Widget _buildWeekShapeSection() {
    final moodProvider = context.watch<MoodProvider>();
    final now = DateTime.now();
    final state = _computeDashboardState(moodProvider);
    final isWeekend = now.weekday == DateTime.saturday ||
        now.weekday == DateTime.sunday;
    // Build 7-bar data: Mon → Sun (or Mon → Sat/Sun for weekend state)
    // For .allEmpty (longAbsence): all bars dashed gray, today dashed primary
    final bool allEmpty = state == DashboardState.longAbsence;

    // Determine bar colors from mood entries per day
    final moodByDay = <int, int?>{}; // weekday (1-7) → moodLevel or null
    for (final e in moodProvider.moodEntries) {
      final dayDiff = now.toUtc().difference(e.timestamp.toUtc()).inDays;
      if (dayDiff >= 0 && dayDiff < 7) {
        final wd = e.timestamp.weekday;
        if (moodByDay[wd] == null ||
            (moodByDay[wd]! < e.moodLevel)) {
          moodByDay[wd] = e.moodLevel;
        }
      }
    }

    Color moodColor(int? level) {
      if (level == null) return Colors.transparent;
      return GQColors.moodPalette[
          (level - 1).clamp(0, GQColors.moodPalette.length - 1)];
    }

    // Bar height proportions
    double barHeightFrac(int? level) {
      if (level == null) return 0.55;
      return 0.4 + (level / 5.0) * 0.55;
    }

    final weekDayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

    // Weekend variant: starts Mon, Sat halo'd
    Widget buildBar(int weekdayIndex) {
      final wd = weekdayIndex + 1; // 1=Mon ... 7=Sun
      final isToday = wd == now.weekday;
      final level = moodByDay[wd];
      final hasData = level != null;
      final hFrac = barHeightFrac(level);

      if (allEmpty) {
        // State C: all dashed gray; today dashed primary
        return Expanded(
          child: FractionallySizedBox(
            heightFactor: 0.55,
            alignment: Alignment.bottomCenter,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.transparent,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(
                  color: isToday
                      ? GQColors.primary.withValues(alpha: 0.45)
                      : GQColors.ink3.withValues(alpha: 0.4),
                  width: 1.5,
                ),
              ),
            ),
          ),
        );
      }

      if (!hasData) {
        // No data: dashed outline
        final highlight = isToday && state == DashboardState.weekend;
        return Expanded(
          child: FractionallySizedBox(
            heightFactor: 0.55,
            alignment: Alignment.bottomCenter,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.transparent,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(
                  color: GQColors.primary.withValues(
                      alpha: highlight ? 0.6 : 0.45),
                  width: highlight ? 2.0 : 1.5,
                ),
                boxShadow: highlight
                    ? [
                        BoxShadow(
                          color: GQColors.primary.withValues(alpha: 0.06),
                          spreadRadius: 3,
                        )
                      ]
                    : null,
              ),
            ),
          ),
        );
      }

      // Has data: solid bar
      final isBestToday = state == DashboardState.feelingGreat && isToday;
      return Expanded(
        child: FractionallySizedBox(
          heightFactor: hFrac,
          alignment: Alignment.bottomCenter,
          child: Container(
            decoration: BoxDecoration(
              color: moodColor(level),
              borderRadius: BorderRadius.circular(6),
              boxShadow: isBestToday
                  ? [
                      BoxShadow(
                          color: Colors.white,
                          spreadRadius: 2,
                          blurRadius: 0),
                      BoxShadow(
                          color: moodColor(level).withValues(alpha: 0.8),
                          spreadRadius: 4,
                          blurRadius: 0),
                    ]
                  : null,
            ),
          ),
        ),
      );
    }

    String weekStatusText() {
      if (allEmpty) return 'No logs yet';
      final count = moodByDay.length;
      if (state == DashboardState.feelingGreat) return '$count logs · trending up';
      return '$count day${count == 1 ? '' : 's'} logged this week';
    }

    String weekSubText() {
      if (allEmpty) return 'Catch up when you\'re ready. No pressure.';
      if (state == DashboardState.feelingGreat) return 'Best day this week. Three good days in a row.';
      if (isWeekend) return 'Weekends count too — same softness.';
      final loggedToday = moodByDay[now.weekday] != null;
      return loggedToday
          ? '${moodByDay.length} days logged this week. Great momentum.'
          : '${moodByDay.length} days logged this week. Your call on today.';
    }

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 600),
        padding: EdgeInsets.fromLTRB(16.h, 16.h, 16.h, 0),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(color: GQColors.hair),
          ),
          padding: EdgeInsets.all(16.h),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'THIS WEEK',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.5,
                          color: GQColors.ink3,
                        ),
                      ),
                      SizedBox(height: 1.h),
                      Text(
                        weekStatusText(),
                        style: const TextStyle(
                          fontSize: 13.5,
                          fontWeight: FontWeight.w800,
                          color: GQColors.ink,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    padding: EdgeInsets.symmetric(
                        horizontal: 7.h, vertical: 3.h),
                    decoration: BoxDecoration(
                      color: allEmpty
                          ? GQColors.primarySoft
                          : (state == DashboardState.feelingGreat
                              ? const Color(0xFFFFF1E5)
                              : (isWeekend
                                  ? GQColors.primarySoft
                                  : GQColors.primarySoft)),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      allEmpty
                          ? 'CATCHING UP'
                          : (state == DashboardState.feelingGreat
                              ? 'BEST DAY'
                              : (isWeekend ? 'WEEKEND' : 'PENDING')),
                      style: TextStyle(
                        fontSize: 9.5,
                        fontWeight: FontWeight.w800,
                        color: allEmpty
                            ? GQColors.ink3
                            : (state == DashboardState.feelingGreat
                                ? const Color(0xFFB5562F)
                                : GQColors.primaryDk),
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 12.h),
              SizedBox(
                height: 42.h,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    for (int i = 0; i < 7; i++) ...[
                      buildBar(i),
                      if (i < 6) SizedBox(width: 4.h),
                    ],
                  ],
                ),
              ),
              SizedBox(height: 6.h),
              Row(
                children: [
                  for (int i = 0; i < 7; i++) ...[
                    Expanded(
                      child: Center(
                        child: Text(
                          weekDayLabels[i],
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: (i + 1 == now.weekday)
                                ? FontWeight.w800
                                : FontWeight.w600,
                            color: (i + 1 == now.weekday)
                                ? (state == DashboardState.feelingGreat
                                    ? const Color(0xFFB5562F)
                                    : GQColors.primaryDk)
                                : GQColors.ink3,
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              SizedBox(height: 8.h),
              Text(
                weekSubText(),
                style: const TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w600,
                  color: GQColors.ink2,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── R1D2+R1D3: QuickLanes — 3-button navigation row ──────────────────────
  Widget _buildQuickLanesSection() {
    final moodProvider = context.read<MoodProvider>();
    final state = _computeDashboardState(moodProvider);
    final isWeekend = state == DashboardState.weekend;

    // Weekend order: [Exercises, Log mood, Talk to Alex]
    // Default order: [Talk to Alex, Log mood, Exercises]
    final lanes = isWeekend
        ? [
            _QuickLane(
              icon: Icons.self_improvement_outlined,
              iconBg: const Color(0xFFFFF1E5),
              iconColor: const Color(0xFFC2522F),
              label: 'Browse exercises',
              onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const ResourceLibraryScreen())),
            ),
            _QuickLane(
              icon: Icons.favorite_border,
              iconBg: GQColors.accentSoft,
              iconColor: GQColors.coral,
              label: 'Log mood',
              onTap: () => homeTabDeepLink.request(AppTab.mood),
            ),
            _QuickLane(
              icon: Icons.chat_bubble_outline,
              iconBg: GQColors.primarySoft,
              iconColor: GQColors.primary,
              label: 'Talk to Alex',
              onTap: () => homeTabDeepLink.request(AppTab.talk),
            ),
          ]
        : [
            _QuickLane(
              icon: Icons.chat_bubble_outline,
              iconBg: GQColors.primarySoft,
              iconColor: GQColors.primary,
              label: 'Talk to Alex',
              onTap: () => homeTabDeepLink.request(AppTab.talk),
            ),
            _QuickLane(
              icon: Icons.favorite_border,
              iconBg: GQColors.accentSoft,
              iconColor: GQColors.coral,
              label: 'Log mood',
              onTap: () => homeTabDeepLink.request(AppTab.mood),
            ),
            _QuickLane(
              icon: Icons.self_improvement_outlined,
              iconBg: const Color(0xFFFFF1E5),
              iconColor: const Color(0xFFC2522F),
              label: 'Exercises',
              onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const ResourceLibraryScreen())),
            ),
          ];

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 600),
        padding: EdgeInsets.fromLTRB(16.h, 16.h, 16.h, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isWeekend ? 'QUICK LANES · WEEKEND' : 'QUICK LANES',
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.5,
                color: GQColors.ink3,
              ),
            ),
            SizedBox(height: 8.h),
            Row(
              children: lanes
                  .map((lane) => Expanded(
                        child: GestureDetector(
                          onTap: () {
                            HapticFeedback.selectionClick();
                            lane.onTap();
                          },
                          child: Container(
                            margin: EdgeInsets.symmetric(horizontal: 4.h),
                            padding: EdgeInsets.symmetric(vertical: 12.h),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius:
                                  BorderRadius.circular(GQRadii.card),
                              border: Border.all(color: GQColors.hair),
                            ),
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Container(
                                  width: 44.h,
                                  height: 44.h,
                                  decoration: BoxDecoration(
                                    color: lane.iconBg,
                                    borderRadius:
                                        BorderRadius.circular(12.h),
                                  ),
                                  child: Icon(lane.icon,
                                      color: lane.iconColor, size: 20),
                                ),
                                SizedBox(height: 6.h),
                                Text(
                                  lane.label,
                                  textAlign: TextAlign.center,
                                  style: const TextStyle(
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.w800,
                                    color: GQColors.ink,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ))
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }

  // ── R1D2+R1D3: NudgeZone — contextual soft nudge ─────────────────────────
  Widget _buildNudgeZoneSection() {
    final moodProvider = context.read<MoodProvider>();
    final state = _computeDashboardState(moodProvider);

    // State B (feelingGreat): nudge is hidden — user already engaged
    if (state == DashboardState.feelingGreat) return SizedBox(height: 16.h);

    String nudgeText() {
      switch (state) {
        case DashboardState.longAbsence:
          return 'No rush. One small log is enough for today.';
        case DashboardState.weekend:
          return 'Slower pace, same care. There\'s no homework here.';
        case DashboardState.notLogged:
        default:
          return 'A 15-second log is the smallest brick in a long wall.';
      }
    }

    String nudgeEmoji() {
      switch (state) {
        case DashboardState.longAbsence:
          return '🌿';
        case DashboardState.weekend:
          return '🌿';
        default:
          return '💭';
      }
    }

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 600),
        padding: EdgeInsets.fromLTRB(16.h, 16.h, 16.h, 0),
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 14.h, vertical: 11.h),
          decoration: BoxDecoration(
            color: GQColors.primary.withValues(alpha: 0.06),
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(
                color: GQColors.primary.withValues(alpha: 0.25),
                width: 1,
                style: BorderStyle.solid),
          ),
          child: Row(
            children: [
              Text(nudgeEmoji(), style: const TextStyle(fontSize: 14)),
              SizedBox(width: 10.h),
              Expanded(
                child: Text(
                  nudgeText(),
                  style: const TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink2,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Legacy _buildMoodCheckInSection — REPLACED by _buildHeroSection ───────
  // Kept as dead stub to avoid merge conflicts; body removed per R1D2 Tier 4.1.
  // ignore: unused_element
  Widget _buildMoodCheckInSection_legacy_removed() => const SizedBox.shrink();

  // ── REMOVED: _buildProgressSection (gamification — Tier 4.1 no streak/level) ─

  // Large Quick check-in prompt section (title, subtitle, and Start button)
  // R1D2+R1D3: _buildMoodCheckInSection superseded by _buildHeroSection.
  // _buildProgressSection removed — gamification (streak/level) per Tier 4.1.
  Widget _buildRecommendationsSection() {
    final questProvider = context.read<QuestProvider>();
    final bool task1Done = _qTask1Id != null &&
        questProvider.quests
            .any((q) => q.id.toString() == _qTask1Id && q.isCompleted);
    final bool task2Done = _qTask2Id != null &&
        questProvider.quests
            .any((q) => q.id.toString() == _qTask2Id && q.isCompleted);
    final bool resDone = _qResId != null &&
        questProvider.quests
            .any((q) => q.id.toString() == _qResId && q.isCompleted);
    final bool tipDone = _qTipId != null &&
        questProvider.quests
            .any((q) => q.id.toString() == _qTipId && q.isCompleted);

    // Pull durations for tasks from today's selection for accurate display
    final int? _task1Dur = _durationFor(_qTask1Id);
    final int? _task2Dur = _durationFor(_qTask2Id);
    return Center(
        child: Container(
            constraints: const BoxConstraints(maxWidth: 600),
            padding:
                EdgeInsets.symmetric(horizontal: 16.h).copyWith(bottom: 32.h),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Today\'s Recommendations',
                  style: TextStyleHelper.instance.display32BoldInter.copyWith(
                      fontFamily: CoreTextStyles
                          .TextStyleHelper.instance.headline24Bold.fontFamily,
                      color: Color(0xFF4A5261))),
              SizedBox(height: 8.h),
              Text(
                'Estimated time: 10 min',
                style: TextStyleHelper.instance.headline21Inter.copyWith(
                    fontFamily: CoreTextStyles
                        .TextStyleHelper.instance.headline24Bold.fontFamily,
                    color: Color(0xFF8C9CAA)),
              ),
              SizedBox(height: 20.h),
              RecommendationCardWidget(
                  containerKey: _task1CardKey,
                  category: 'TASK',
                  title: _task1Dur != null
                      ? 'Focus reset (${_task1Dur} min)'
                      : 'Focus reset',
                  subtitle: (task1Done && task2Done)
                      ? 'All steps complete 🎉'
                      : 'Quick breathing + desk tidy',
                  imagePath: 'assets/images/quests/task_focus.svg',
                  doneImagePath: 'assets/images/quests/task_focus_done.svg',
                  completed: task1Done,
                  onTap: () async {
                    final questId = _qTask1Id;
                    if (questId == null) return;

                    // Toggle undo if already done
                    if (task1Done) {
                      final qId = int.tryParse(questId);
                      if (qId != null) {
                        await questProvider.updateQuestProgress(qId, 0);
                        await _refreshToday();
                        await _refreshExplore();
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Marked undone')),
                          );
                        }
                      }
                      return;
                    }

                    final dur = _durationFor(questId);
                    if (dur != null && dur > 0) {
                      await _openTimerSheet(
                          questId: questId,
                          cardKey: _task1CardKey,
                          title: _titleFor(questId) ?? 'Focus reset',
                          durationMin: dur);
                      return;
                    }
                  }),
              SizedBox(height: 24.h),
              // Card 2 (TASK)
              if (_qTask2Id != null)
                RecommendationCardWidget(
                    containerKey: _task2CardKey,
                    category: 'TASK',
                    title: _task2Dur != null
                        ? 'Study sprint (${_task2Dur} min)'
                        : 'Study sprint',
                    subtitle: 'Timer + no-phone rule',
                    imagePath: 'assets/images/quests/task_study.svg',
                    doneImagePath: 'assets/images/quests/task_study_done.svg',
                    completed: task2Done,
                    onTap: () async {
                      final questId = _qTask2Id;
                      if (questId == null) return;

                      // Toggle undo if already done
                      if (task2Done) {
                        final qId = int.tryParse(questId);
                        if (qId != null) {
                          await questProvider.updateQuestProgress(qId, 0);
                          await _refreshToday();
                          await _refreshExplore();
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Marked undone')),
                            );
                          }
                        }
                        return;
                      }

                      final dur = _durationFor(questId);
                      if (dur != null && dur > 0) {
                        await _openTimerSheet(
                            questId: questId,
                            cardKey: _task2CardKey,
                            title: _titleFor(questId) ?? 'Study sprint',
                            durationMin: dur);
                        return;
                      }
                    }),
              SizedBox(height: 24.h),
              // Card 3 (RESOURCE)
              RecommendationCardWidget(
                  containerKey: _resCardKey,
                  category: 'RESOURCE',
                  title: _titleFor(_qResId) ?? 'Calm music',
                  subtitle: _subtitleFor(_qResId) ?? 'Lo‑fi playlist',
                  imagePath:
                      'assets/images/quests/resource_headphone_match_v8.svg',
                  doneImagePath:
                      'assets/images/quests/resource_headphone_match_v8_done.svg',
                  completed: resDone,
                  onTap: () async {
                    HapticFeedback.lightImpact();
                    SystemSound.play(SystemSoundType.click);

                    final questIdStr = _qResId;
                    if (questIdStr == null) return;

                    final qId = int.tryParse(questIdStr);
                    if (qId == null) return;

                    // v1.3.2: if this quest is an interactive exercise
                    // (grounding / breathing / body scan), launch the
                    // exercise widget instead of just toggling done.
                    final exType = _exerciseTypeForQuest(questIdStr);
                    if (exType != null && !resDone) {
                      await ExerciseScaffoldScreen.show(context, exType);
                      if (!mounted) return;
                      try {
                        await questProvider.updateQuestProgress(qId, 100);
                        if (mounted) {
                          _showCheckRipple(_resCardKey);
                          _randomizeConfetti();
                          _confettiController.play();
                          await _refreshToday();
                          await _refreshExplore();
                          _showCompletionSnackBar(
                              qId, 'Done! You showed up for yourself today 💪');
                        }
                      } catch (_) {}
                      return;
                    }

                    if (!resDone) {
                      // Mark as completed (optimistic 100% progress)
                      try {
                        await questProvider.updateQuestProgress(qId, 100);
                        if (mounted) {
                          _showCheckRipple(_resCardKey);
                          _randomizeConfetti();
                          _confettiController.play();

                          await _refreshToday();
                          await _refreshExplore();

                          _showCompletionSnackBar(
                              qId, 'Done! You showed up for yourself today 💪');
                        }
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text('Failed to update progress')),
                          );
                        }
                      }
                    } else {
                      // Toggle back to 0 (Undo via direct tap)
                      try {
                        await questProvider.updateQuestProgress(qId, 0);
                        await _refreshToday();
                        await _refreshExplore();
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Marked undone')),
                          );
                        }
                      } catch (_) {}
                    }
                  }),
              SizedBox(height: 24.h),
              // Card 4 (TIP)
              RecommendationCardWidget(
                  containerKey: _tipCardKey,
                  category: 'TIP',
                  title: _titleFor(_qTipId) ?? 'One tiny step',
                  subtitle:
                      _subtitleFor(_qTipId) ?? 'Pick the easiest task first',
                  imagePath: 'assets/images/quests/tip_generic.svg',
                  doneImagePath: 'assets/images/quests/tip_generic_done.svg',
                  completed: tipDone,
                  onTap: () async {
                    HapticFeedback.lightImpact();
                    SystemSound.play(SystemSoundType.click);

                    final questIdStr = _qTipId;
                    if (questIdStr == null) return;

                    final qId = int.tryParse(questIdStr);
                    if (qId == null) return;

                    // v1.3.2: launch exercise widget if this tip maps to one
                    final exType = _exerciseTypeForQuest(questIdStr);
                    if (exType != null && !tipDone) {
                      await ExerciseScaffoldScreen.show(context, exType);
                      if (!mounted) return;
                      try {
                        await questProvider.updateQuestProgress(qId, 100);
                        if (mounted) {
                          _showCheckRipple(_tipCardKey);
                          _randomizeConfetti();
                          _confettiController.play();
                          await _refreshToday();
                          await _refreshExplore();
                          _showCompletionSnackBar(
                              qId, 'Done! You showed up for yourself today 💪');
                        }
                      } catch (_) {}
                      return;
                    }

                    if (!tipDone) {
                      try {
                        await questProvider.updateQuestProgress(qId, 100);
                        _showCheckRipple(_tipCardKey);
                        _randomizeConfetti();
                        _confettiController.play();

                        await _refreshToday();
                        await _refreshExplore();

                        _showCompletionSnackBar(
                            qId, 'Done! You showed up for yourself today 💪');
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text('Failed to update progress')),
                          );
                        }
                      }
                    } else {
                      try {
                        await questProvider.updateQuestProgress(qId, 0);
                        await _refreshToday();
                        await _refreshExplore();
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Marked undone')),
                          );
                        }
                      } catch (_) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text('Failed to update progress')),
                          );
                        }
                      }
                    }
                  }),
              SizedBox(height: 24.h),
              // Card 5 (REMINDER) - themed toggle + change time
              Builder(
                builder: (context) {
                  final near = _isReminderNear();
                  final now = DateTime.now();
                  // Fire telemetry on transition into near state (release + debug)
                  final becameNear = near && (_lastReminderNear != true);
                  if (becameNear) {
                    final qid = _qTask1Id ?? _qTask2Id;
                    try {
                      logAnalyticsEvent('quest_reminder_fired', metadata: {
                        if (qid != null) 'quest_id': qid,
                        'surface': 'wellness_dashboard',
                        'variant': 'today',
                        'tag': 'fired',
                        'ts': now.millisecondsSinceEpoch,
                        'ui': 'reminder_near',
                      });
                    } catch (_) {}
                  }
                  // Update last-seen state always
                  _lastReminderNear = near;
                  // Keep debug prints throttled
                  if (kDebugMode) {
                    final shouldLog = (_lastReminderLogAt ==
                            DateTime.fromMillisecondsSinceEpoch(0)) ||
                        (now.difference(_lastReminderLogAt).inSeconds >= 60) ||
                        becameNear;
                    if (shouldLog) {
                      debugPrint(
                          '[Reminder][near] now=$near on=$_reminderOn time=${_reminderTime.format(context)}');
                      _lastReminderLogAt = now;
                    }
                  }
                  if (near && !_pulseController.isAnimating) {
                    _pulseController.repeat(reverse: true);
                  } else if (!near && _pulseController.isAnimating) {
                    _pulseController.stop();
                  }
                  final primary = Theme.of(context).colorScheme.primary;
                  final borderBase = const Color(0xFFF4F5F7);
                  final borderColor = near
                      ? Color.lerp(borderBase, primary,
                          0.6 + 0.4 * _pulseController.value)!
                      : borderBase;
                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 220),
                    curve: Curves.easeInOut,
                    decoration: BoxDecoration(
                      color: _reminderOn
                          ? const Color(0xFFF4F1FF)
                          : const Color(0xFFFEFEFE),
                      border: Border.all(color: borderColor),
                      borderRadius: BorderRadius.circular(29.h),
                      boxShadow: _reminderOn
                          ? [
                              BoxShadow(
                                color: primary.withValues(alpha: 0.12),
                                blurRadius: 18,
                                offset: const Offset(0, 8),
                              ),
                            ]
                          : [],
                    ),
                    padding: EdgeInsets.all(28.h),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                crossAxisAlignment: CrossAxisAlignment.center,
                                children: [
                                  Text(
                                    'REMINDER',
                                    style: TextStyleHelper
                                        .instance.title19BoldInter
                                        .copyWith(
                                      fontFamily: CoreTextStyles.TextStyleHelper
                                          .instance.headline24Bold.fontFamily,
                                      color: const Color(0xFF8E98A7),
                                    ),
                                  ),
                                  GestureDetector(
                                    onTap: () {
                                      setState(() {
                                        _reminderOn = !_reminderOn;
                                        _startMicrocopyRotation();
                                      });
                                      _saveReminderPrefs();
                                      // Apply scheduling change immediately
                                      _rescheduleReminder('toggle');
                                      if (kDebugMode) {
                                        debugPrint(
                                            '[Reminder][toggle] on=$_reminderOn');
                                      }
                                      // Microinteraction: subtle ripple on toggle change
                                      HapticFeedback.lightImpact();
                                      SystemSound.play(SystemSoundType.click);
                                      _showCheckRipple(_reminderToggleKey);
                                      // Telemetry: quest_reminder_toggle
                                      final qid = _qTask1Id ?? _qTask2Id;
                                      try {
                                        logAnalyticsEvent(
                                            'quest_reminder_toggle',
                                            metadata: {
                                              if (qid != null) 'quest_id': qid,
                                              'surface': 'wellness_dashboard',
                                              'variant': 'today',
                                              'tag': _reminderOn
                                                  ? 'toggle_on'
                                                  : 'toggle_off',
                                              'ts': DateTime.now()
                                                  .millisecondsSinceEpoch,
                                              'ui': 'reminder_toggle',
                                            });
                                      } catch (_) {}
                                    },
                                    child: Container(
                                      key: _reminderToggleKey,
                                      child: AnimatedContainer(
                                        duration:
                                            const Duration(milliseconds: 220),
                                        curve: Curves.easeOutCubic,
                                        width: 56.h,
                                        height: 30.h,
                                        padding: EdgeInsets.symmetric(
                                            horizontal: 4.h, vertical: 4.h),
                                        decoration: BoxDecoration(
                                          color: _reminderOn
                                              ? Theme.of(context)
                                                  .colorScheme
                                                  .primary
                                              : const Color(0xFFE6EAF0),
                                          borderRadius:
                                              BorderRadius.circular(20.h),
                                          boxShadow: _reminderOn
                                              ? [
                                                  BoxShadow(
                                                    color: Theme.of(context)
                                                        .colorScheme
                                                        .primary
                                                        .withValues(
                                                            alpha: 0.35),
                                                    blurRadius: 14,
                                                    spreadRadius: 1,
                                                    offset: const Offset(0, 3),
                                                  )
                                                ]
                                              : [],
                                        ),
                                        child: AnimatedAlign(
                                          duration:
                                              const Duration(milliseconds: 220),
                                          curve: Curves.easeOutCubic,
                                          alignment: _reminderOn
                                              ? Alignment.centerRight
                                              : Alignment.centerLeft,
                                          child: AnimatedScale(
                                            duration: const Duration(
                                                milliseconds: 160),
                                            curve: Curves.easeOutBack,
                                            scale: _reminderOn ? 1.0 : 0.96,
                                            child: Container(
                                              width: 22.h,
                                              height: 22.h,
                                              decoration: const BoxDecoration(
                                                  color: Colors.white,
                                                  shape: BoxShape.circle),
                                              child: _reminderOn
                                                  ? Icon(Icons.check,
                                                      size: 16.h,
                                                      color: Theme.of(context)
                                                          .colorScheme
                                                          .primary)
                                                  : null,
                                            ),
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              SizedBox(height: 8.h),
                              Row(
                                children: [
                                  Expanded(
                                    child: Row(
                                      children: [
                                        Flexible(
                                          child: Text(
                                            _formatReminderTime(_reminderTime),
                                            overflow: TextOverflow.ellipsis,
                                            style: TextStyleHelper
                                                .instance.headline26BoldInter
                                                .copyWith(
                                              fontFamily: CoreTextStyles
                                                  .TextStyleHelper
                                                  .instance
                                                  .headline24Bold
                                                  .fontFamily,
                                              color: _reminderOn
                                                  ? const Color(0xFF4C5664)
                                                  : const Color(0xFFB8C0CC),
                                            ),
                                          ),
                                        ),
                                        SizedBox(
                                            width:
                                                _isTomorrowLabel(_reminderTime)
                                                    ? 8.h
                                                    : 0),
                                        _isTomorrowLabel(_reminderTime)
                                            ? Text(
                                                'tomorrow',
                                                style: TextStyleHelper
                                                    .instance.headline21Inter
                                                    .copyWith(
                                                  fontFamily: CoreTextStyles
                                                      .TextStyleHelper
                                                      .instance
                                                      .headline24Bold
                                                      .fontFamily,
                                                  color:
                                                      const Color(0xFF8E98A7),
                                                ),
                                              )
                                            : const SizedBox.shrink(),
                                      ],
                                    ),
                                  ),
                                  SizedBox(width: 8.h),
                                  OutlinedButton.icon(
                                    key: _reminderTimeKey,
                                    onPressed: _reminderOn
                                        ? () async {
                                            final picked = await showTimePicker(
                                              context: context,
                                              initialTime: _reminderTime,
                                              builder: (context, child) {
                                                return Theme(
                                                    data: Theme.of(context),
                                                    child: child!);
                                              },
                                            );
                                            if (!mounted) return;
                                            if (picked != null) {
                                              setState(() {
                                                _reminderTime = picked;
                                                _reminderOn = true;
                                              });
                                              _saveReminderPrefs();
                                              // Reschedule to new time immediately
                                              _rescheduleReminder(
                                                  'time_changed');
                                              if (kDebugMode) {
                                                debugPrint(
                                                    '[Reminder][timeChanged] to=${_formatReminderTime(_reminderTime)}');
                                              }
                                              // Microinteraction: confirmation ring + haptics
                                              HapticFeedback.selectionClick();
                                              SystemSound.play(
                                                  SystemSoundType.click);
                                              _showTimerRing(_reminderTimeKey);
                                              // Telemetry: quest_reminder_toggle (time changed)
                                              final qid =
                                                  _qTask1Id ?? _qTask2Id;
                                              try {
                                                logAnalyticsEvent(
                                                    'quest_reminder_toggle',
                                                    metadata: {
                                                      if (qid != null)
                                                        'quest_id': qid,
                                                      'surface':
                                                          'wellness_dashboard',
                                                      'variant': 'today',
                                                      'tag': 'time_changed',
                                                      'ts': DateTime.now()
                                                          .millisecondsSinceEpoch,
                                                      'ui': 'reminder_time',
                                                    });
                                              } catch (_) {}
                                            }
                                          }
                                        : null,
                                    style: OutlinedButton.styleFrom(
                                      padding: EdgeInsets.symmetric(
                                          horizontal: 12.h, vertical: 0),
                                      minimumSize:
                                          Size(0, 30.h), // match toggle height
                                      side: BorderSide(
                                        color: _reminderOn
                                            ? Theme.of(context)
                                                .colorScheme
                                                .primary
                                            : const Color(0xFFB8C0CC),
                                      ),
                                      foregroundColor: _reminderOn
                                          ? Theme.of(context)
                                              .colorScheme
                                              .primary
                                          : const Color(0xFFB8C0CC),
                                      shape: const StadiumBorder(),
                                    ),
                                    icon: Icon(Icons.edit, size: 18.h),
                                    label: Text(
                                      'Change',
                                      style: TextStyleHelper
                                          .instance.headline21Inter
                                          .copyWith(
                                        fontFamily: CoreTextStyles
                                            .TextStyleHelper
                                            .instance
                                            .headline24Bold
                                            .fontFamily,
                                        fontSize: 12.h,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              SizedBox(height: 12.h),
                              AnimatedSwitcher(
                                duration: const Duration(milliseconds: 300),
                                child: Text(
                                  _reminderOn
                                      ? _microcopy[_microIndex]
                                      : 'Nudge me to finish the quest',
                                  key: ValueKey(_microIndex.toString() +
                                      _reminderOn.toString()),
                                  style: TextStyleHelper
                                      .instance.headline21Inter
                                      .copyWith(
                                    fontFamily: CoreTextStyles.TextStyleHelper
                                        .instance.headline24Bold.fontFamily,
                                    color: const Color(0xFFA8B1BF),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        // Removed right-side image to give space for time + tomorrow label
                      ],
                    ),
                  );
                },
              ),
            ])));
  }

  // Utility: title-case a string for category display
  String _titleCase(String input) {
    if (input.isEmpty) return input;
    final normalized = input.replaceAll('_', ' ').replaceAll('-', ' ');
    final parts =
        normalized.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).toList();
    return parts
        .map((w) =>
            w.substring(0, 1).toUpperCase() +
            (w.length > 1 ? w.substring(1).toLowerCase() : ''))
        .join(' ');
  }

  // Explore: minimal gating helper for awarding XP
  Future<void> _handleExploreComplete(String questId) async {
    HapticFeedback.lightImpact();
    SystemSound.play(SystemSoundType.click);

    final qId = int.tryParse(questId);
    if (qId == null) return;

    final questProvider = context.read<QuestProvider>();
    final q = questProvider.getQuestById(questId);
    if (q == null) return;

    // Interaction Rationalization:
    // If it's a 'progress' quest (Assessment), we navigate the user to the tool.
    // We only complete IF they actually finish it (return true).
    if (q.type == 'progress') {
      final result = await Navigator.pushNamed(context, '/clinical-assessment');
      if (result != true) {
        return; // User didn't complete it
      }
    }

    try {
      await questProvider.updateQuestProgress(qId, 100);

      if (mounted) {
        setState(() {
          _exploreCompletedToday.add(questId);
        });

        // Celebration logic: Rationalized
        // Only confetti for high-impact achievements (>40 XP)
        if (q.xpReward >= 40) {
          HapticFeedback.heavyImpact();
          try {
            _confettiController.play();
          } catch (_) {}
        }
      }
    } catch (_) {}
  }

  Widget _buildTab(int index, String label, {bool selected = false}) {
    final primary = Theme.of(context).colorScheme.primary;
    return InkWell(
      onTap: () {
        if (_tabIndex == index) return;
        HapticFeedback.selectionClick();
        SystemSound.play(SystemSoundType.click);
        if (kDebugMode) {
          try {
            debugPrint('[Tabs] switch to index=$index -> clearing pill');
          } catch (_) {}
        }
        _removeTimerPill();
        setState(() {
          _tabIndex = index;
        });
        // Telemetry: log Explore tab view
        if (index == 1) {
          try {
            logAnalyticsEvent('quest_view', metadata: {
              'surface': 'wellness_dashboard',
              'variant': 'explore',
              'tag': 'explore_tab',
              'ts': DateTime.now().millisecondsSinceEpoch,
              'ui': 'tab_switch',
            });
          } catch (_) {}
        }
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
        padding: EdgeInsets.symmetric(horizontal: 16.h, vertical: 12.h),
        decoration: BoxDecoration(
          color: selected ? primary : Colors.white,
          borderRadius: BorderRadius.circular(22.h),
          border: Border.all(color: const Color(0xFFE0E6EE)),
          boxShadow: selected
              ? [
                  BoxShadow(
                    color: primary.withValues(alpha: 0.18),
                    blurRadius: 12,
                    offset: const Offset(0, 6),
                  )
                ]
              : [],
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyleHelper.instance.headline21Inter.copyWith(
              fontFamily: CoreTextStyles
                  .TextStyleHelper.instance.headline24Bold.fontFamily,
              color: selected ? Colors.white : const Color(0xFF47505E),
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTabsSection() {
    Widget segButton(String label, int index) {
      bool selected = _tabIndex == index;
      return _buildTab(index, label, selected: selected);
    }

    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 16.h),
      child: Row(
        children: [
          Expanded(child: segButton('Today', 0)),
          SizedBox(width: 12.h),
          Expanded(child: segButton('Discover', 1)),
        ],
      ),
    );
  }

  // Explore tab content (header + category filters + placeholder grid)
  Widget _buildExploreSection() {
    final qp = context.watch<QuestProvider>();

    // Filter categories to only those with available quests
    final activeCats = _exploreCats.where((cat) {
      if (cat == 'All') return true;
      // Case-insensitive match between display category and quest type
      return qp.quests.any((q) => q.type.toUpperCase() == cat.toUpperCase());
    }).toList();

    final List<String> cats = <String>{'All', ...activeCats}.toList();
    final List<String> visible = _exploreFilter == 'All'
        ? activeCats
        : activeCats.where((c) => c == _exploreFilter).toList();
    // Keep XP display consistent with Today tab
    final int xpToday = qp.quests
        .where((q) => q.isCompleted)
        .fold(0, (sum, q) => sum + q.xpReward); // Derive from completed quests
    final int lifetimeXp = qp.totalXP;
    // Streak values for header (No-Guilt)
    final int streakDays = qp.streak;
    final int recordStreak = 0; // Unused in header
    // Responsive tweaks
    final double _w = MediaQuery.of(context).size.width;
    final bool _narrow = _w < 420;
    final String _dayWord = streakDays == 1 ? 'day' : 'days';
    final String _recordLabel = _narrow ? 'rec' : 'record';
    final double _whiteBlur = _narrow ? 8 : 10;
    final double _whiteAlpha = _narrow ? 0.05 : 0.06;
    final double _xpBlur = _narrow ? 10 : 12;
    final double _xpAlpha = _narrow ? 0.14 : 0.18;

    // Responsive horizontal padding: tighter on narrow screens
    final double hp = _w >= 900 ? 70.h : 16.h;

    return Padding(
      padding: EdgeInsets.symmetric(horizontal: hp)
          .copyWith(top: 48.h, bottom: 32.h),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        // Category chips + compact metrics on the same row
        Builder(builder: (context) {
          final int energyLeft = 3; // Derive from qp if backend supports energy
          const int energyLimit = 3;
          final bool energyEmpty = energyLeft <= 0;
          final Color energyFg = energyEmpty
              ? const Color(0xFF8C9CAA)
              : Theme.of(context).colorScheme.primary;
          // Tighten spacing for very narrow widths
          final double chipHPad = _narrow ? 8.h : 10.h;
          final double chipVPad = _narrow ? 4.h : 6.h;
          final double iconSize = _narrow ? 14 : 16;
          final double iconGap = _narrow ? 4.h : 6.h;
          final double wrapSpacing = _narrow ? 6.h : 8.h;
          final double groupGap = _narrow ? 6.h : 8.h;
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Left: category chips (wrap)
              Expanded(
                child: Wrap(
                  spacing: wrapSpacing,
                  runSpacing: wrapSpacing,
                  children: cats.map((cat) {
                    final bool selected = _exploreFilter == cat;
                    return ChoiceChip(
                      label: Text(cat),
                      selected: selected,
                      onSelected: (_) {
                        setState(() {
                          _exploreFilter = cat;
                        });
                      },
                      labelStyle:
                          TextStyleHelper.instance.headline21Inter.copyWith(
                        fontFamily: CoreTextStyles
                            .TextStyleHelper.instance.headline24Bold.fontFamily,
                        color:
                            selected ? Colors.white : const Color(0xFF47505E),
                      ),
                      selectedColor: Theme.of(context).colorScheme.primary,
                      backgroundColor: Colors.white,
                      shape: const StadiumBorder(
                          side: BorderSide(color: Color(0xFFE0E6EE))),
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      padding: EdgeInsets.symmetric(
                          horizontal: chipHPad, vertical: chipVPad),
                    );
                  }).toList(),
                ),
              ),
              SizedBox(width: groupGap),
              // Right: compact metrics (Energy, Streak, +XP)
              Flexible(
                child: Align(
                  alignment: Alignment.topRight,
                  child: Wrap(
                    spacing: wrapSpacing,
                    runSpacing: wrapSpacing,
                    alignment: WrapAlignment.end,
                    children: [
                      // Standardize chip height to avoid mismatched sizes across metrics
                      // and ensure internal text never wraps.
                      // Keep this in sync with chip padding and font sizes.
                      // Narrow: slightly smaller height.

                      // Energy: flash + 3/3
                      Container(
                        padding: EdgeInsets.symmetric(
                            horizontal: chipHPad, vertical: chipVPad),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(18.h),
                          border: Border.all(color: const Color(0xFFE0E6EE)),
                          boxShadow: [
                            BoxShadow(
                              color:
                                  Colors.black.withValues(alpha: _whiteAlpha),
                              blurRadius: _whiteBlur,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        constraints:
                            BoxConstraints(minHeight: _narrow ? 30.h : 34.h),
                        child: Row(mainAxisSize: MainAxisSize.min, children: [
                          Icon(Icons.flash_on_outlined,
                              size: iconSize, color: energyFg),
                          SizedBox(width: iconGap),
                          Flexible(
                            child: Text(
                              '$energyLeft/$energyLimit',
                              maxLines: 1,
                              softWrap: false,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyleHelper.instance.titleMediumInter
                                  .copyWith(
                                      color: energyFg,
                                      fontWeight: FontWeight.w700),
                            ),
                          ),
                        ]),
                      ),
                      // Streak: flame + 2d
                      Container(
                        padding: EdgeInsets.symmetric(
                            horizontal: chipHPad, vertical: chipVPad),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(18.h),
                          border: Border.all(color: const Color(0xFFE0E6EE)),
                          boxShadow: [
                            BoxShadow(
                              color:
                                  Colors.black.withValues(alpha: _whiteAlpha),
                              blurRadius: _whiteBlur,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        constraints: BoxConstraints(
                          minHeight: _narrow ? 30.h : 34.h,
                        ),
                        child: Row(mainAxisSize: MainAxisSize.min, children: [
                          Icon(Icons.spa_outlined, // Seedling for growth
                              size: iconSize,
                              color: Theme.of(context).colorScheme.primary),
                          SizedBox(width: iconGap),
                          Flexible(
                            child: Text(
                              '${streakDays}d',
                              maxLines: 1,
                              softWrap: false,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyleHelper.instance.titleMediumInter
                                  .copyWith(
                                      color: const Color(0xFF47505E),
                                      fontWeight: FontWeight.w700),
                            ),
                          ),
                        ]),
                      ),
                      // XP: star + "+today" (chip flexes to content; wraps with others when needed)
                      Container(
                        key: _xpCardKey,
                        padding: EdgeInsets.symmetric(
                            horizontal: chipHPad, vertical: chipVPad),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primary,
                          borderRadius: BorderRadius.circular(18.h),
                          boxShadow: [
                            BoxShadow(
                              color: Theme.of(context)
                                  .colorScheme
                                  .primary
                                  .withValues(alpha: _xpAlpha),
                              blurRadius: _xpBlur,
                              offset: const Offset(0, 6),
                            ),
                          ],
                        ),
                        constraints: BoxConstraints(
                          minHeight: _narrow ? 30.h : 34.h,
                        ),
                        child: Row(mainAxisSize: MainAxisSize.min, children: [
                          Icon(Icons.star_rounded,
                              color: Colors.white, size: iconSize),
                          SizedBox(width: iconGap),
                          Flexible(
                            child: Text(
                              '+$xpToday',
                              maxLines: 1,
                              softWrap: false,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyleHelper.instance.titleMediumInter
                                  .copyWith(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w700),
                            ),
                          ),
                        ]),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        }),
        SizedBox(height: _narrow ? 16.h : 20.h),

        // Dynamic Explore quest cards from catalog filtered by category
        Builder(builder: (context) {
          final questProvider = context.watch<QuestProvider>();
          final items = (_exploreFilter == 'All')
              ? questProvider.quests
              : questProvider.quests
                  .where((q) =>
                      (q.type ?? '').toLowerCase() ==
                      _exploreFilter.toLowerCase())
                  .toList();

          if (questProvider.quests.isEmpty) {
            return Container(
              padding: EdgeInsets.symmetric(horizontal: 20.h, vertical: 18.h),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20.h),
                border: Border.all(color: const Color(0xFFE0E6EE)),
              ),
              child: Text(
                'Loading quests…',
                textAlign: TextAlign.center,
                style: TextStyleHelper.instance.headline21Inter.copyWith(
                  fontFamily: CoreTextStyles
                      .TextStyleHelper.instance.headline24Bold.fontFamily,
                  color: const Color(0xFF8C9CAA),
                ),
              ),
            );
          }

          // Best-effort: mark impressions (if needed in analytics)
          WidgetsBinding.instance.addPostFrameCallback((_) {
            for (final q in items) {
              if (_impressedExplore.add(q.id.toString())) {
                try {
                  logAnalyticsEvent('quest_view', metadata: {
                    'quest_id': q.id,
                    'type': q.type,
                    'surface': 'wellness_dashboard',
                    'variant': 'explore',
                    'ts': DateTime.now().millisecondsSinceEpoch,
                    'ui': 'explore',
                  });
                } catch (_) {}
              }
            }
          });

          if (items.isEmpty) {
            return Container(
              padding: EdgeInsets.symmetric(horizontal: 20.h, vertical: 18.h),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20.h),
                border: Border.all(color: const Color(0xFFE0E6EE)),
              ),
              child: Text(
                'No quests available',
                textAlign: TextAlign.center,
                style: TextStyleHelper.instance.headline21Inter.copyWith(
                  fontFamily: CoreTextStyles
                      .TextStyleHelper.instance.headline24Bold.fontFamily,
                  color: const Color(0xFF8C9CAA),
                ),
              ),
            );
          }

          IconData iconFor(model.Quest q) {
            final type = (q.type ?? '').toLowerCase();
            switch (type) {
              case 'mindfulness':
                return Icons.self_improvement_outlined;
              case 'activity':
                return Icons.directions_walk;
              case 'social':
                return Icons.forum_outlined;
              case 'learning':
                return Icons.school_outlined;
              case 'challenge':
                return Icons.flag_outlined;
              case 'task':
                return Icons.check_circle_outline;
              case 'tip':
                return Icons.lightbulb_outline;
              case 'resource':
                return Icons.menu_book_outlined;
              case 'reminder':
                return Icons.alarm_outlined;
              case 'check_in':
                return Icons.favorite_border;
              case 'progress':
                return Icons.trending_up_outlined;
            }
            return Icons.help_outline;
          }

          Color colorFor(model.Quest q) {
            final type = (q.type ?? '').toLowerCase();
            switch (type) {
              case 'mindfulness':
                return Colors.teal;
              case 'activity':
                return Colors.green;
              case 'social':
                return Colors.indigo;
              case 'learning':
                return Colors.deepPurple;
              case 'challenge':
                return Colors.redAccent;
              case 'task':
                return Theme.of(context).colorScheme.primary;
              case 'tip':
                return Colors.orange;
              case 'resource':
                return Colors.blue;
              case 'reminder':
                return Colors.pink;
              case 'check_in':
                return Colors.cyan;
              case 'progress':
                return Colors.amber;
            }
            return Colors.grey;
          }

          return ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: items.length,
            separatorBuilder: (_, __) => SizedBox(height: 12.h),
            itemBuilder: (context, index) {
              final q = items[index];
              final bool doneToday = q.isCompleted;
              final double? progress = doneToday ? 1.0 : null;

              return QuestCardWidget(
                title: q.title,
                subtitle: q.description.isNotEmpty ? q.description : null,
                icon: iconFor(q),
                color: colorFor(q),
                progress: progress,
                xp: q.xpReward,
                // v1.3.2: Quest cards now route to the exercise scaffold
                // when the quest title/subtitle maps to an interactive
                // exercise (grounding / breathing / body scan). For
                // non-exercise quests (calm music, articles, generic
                // tips), tap remains a self-report toggle. Label is
                // "Start" for exercises, "I did this" for self-report —
                // the affordance matches the behavior. Replaces the
                // v1.3.0 design where every Explore card was a silent
                // self-report toggle that visually mimicked a launcher.
                actionLabel: _exerciseTypeForQuest(q.id.toString()) != null
                    ? 'Start'
                    : 'I did this',
                onTap: () async {
                  try {
                    logAnalyticsEvent('quest_start', metadata: {
                      'quest_id': q.id,
                      'type': q.type,
                      'surface': 'wellness_dashboard',
                      'variant': 'explore',
                      'ts': DateTime.now().millisecondsSinceEpoch,
                      'ui': 'explore',
                    });
                  } catch (_) {}

                  // v1.3.2: launch the exercise widget on tap if mapped
                  final exType = _exerciseTypeForQuest(q.id.toString());
                  if (exType != null && !q.isCompleted) {
                    await ExerciseScaffoldScreen.show(context, exType);
                    if (mounted) _handleExploreComplete(q.id.toString());
                    return;
                  }

                  // Toggle logic for non-exercise Explore cards
                  if (q.isCompleted) {
                    // Undo
                    final qId = q.id;
                    try {
                      context.read<QuestProvider>().updateQuestProgress(qId, 0);
                      if (mounted) {
                        setState(() {
                          _exploreCompletedToday.remove(qId.toString());
                        });
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Marked undone')),
                        );
                      }
                    } catch (_) {}
                  } else {
                    // Complete (self-report)
                    _handleExploreComplete(q.id.toString());
                  }
                },
              );
            },
          );
        }),
      ]),
    );
  }
}


// ── R1D2+R1D3 helpers ────────────────────────────────────────────────────────

/// Data class for a single Quick Lane tile.
class _QuickLane {
  final IconData icon;
  final Color iconBg;
  final Color iconColor;
  final String label;
  final VoidCallback onTap;

  const _QuickLane({
    required this.icon,
    required this.iconBg,
    required this.iconColor,
    required this.label,
    required this.onTap,
  });
}
