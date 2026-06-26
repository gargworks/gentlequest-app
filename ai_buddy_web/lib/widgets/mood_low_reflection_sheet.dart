import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/gq_tokens.dart';
import '../models/interactive_exercise.dart';
import '../navigation/home_tab_deeplink.dart';
import '../services/notification_service.dart';
import '../widgets/app_bottom_nav.dart';
import 'exercises/breathing_exercise_widget.dart';

/// R2D4 — post-submit reflection sheet for low-mood entries (moodLevel 1–2 on
/// a 1-5 scale).
///
/// Design reference: DOGFOOD_LOG.md § S11 / R2D4:
///   "Logged. Heavy day, hm? / Want to do one tiny thing together?"
///
/// Principles applied:
///   • coral-not-red (#1)    → accent = GQColors.coral
///   • no-streak-shame (#11) → no metrics shown
///   • optional>required     → all CTAs are optional, skip always present
///   • save-exit-always      → "Skip for now" always visible
///
/// [latestMoodLevel] (1–2 range expected) is forwarded to
/// [NotificationService.scheduleWorriedCheckin] when the sheet completes,
/// so the user receives a follow-up "worried check-in" notification.
/// Default is `null`, in which case the check-in is skipped — useful for
/// tests and any caller that doesn't have the level handy.
///
/// TODO(wiring): callers in `mood_tracker.dart` should pass
/// `latestMoodLevel: moodLevel` when invoking this. As of 2026-05-21 the
/// existing call site at `mood_tracker.dart:746` does not pass it; without
/// the parameter the worried check-in won't schedule. Update that call to
/// `showMoodLowReflectionSheet(context, latestMoodLevel: moodLevel);` once
/// the mood_tracker.dart owner approves.
Future<void> showMoodLowReflectionSheet(
  BuildContext context, {
  int? latestMoodLevel,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    // useRootNavigator so it floats above the mood dialog that was just popped
    useRootNavigator: true,
    builder: (_) => _ReflectionSheet(latestMoodLevel: latestMoodLevel),
  );
}

// ─── Box-breathing preset ─────────────────────────────────────────────────────

BreathingExercise _buildBoxBreathing() => BreathingExercise(
      name: 'Box Breathing',
      description: 'A simple 4-4-4-4 pattern to settle your nervous system.',
      steps: [
        BreathingStep(
          action: 'breathe_in',
          duration: 4,
          instruction: 'Breathe in slowly',
        ),
        BreathingStep(
          action: 'hold',
          duration: 4,
          instruction: 'Hold',
        ),
        BreathingStep(
          action: 'breathe_out',
          duration: 4,
          instruction: 'Breathe out slowly',
        ),
        BreathingStep(
          action: 'hold',
          duration: 4,
          instruction: 'Rest',
        ),
      ],
      cycles: 3,
      totalTimeSeconds: 48,
    );

// ─── Sheet widget ─────────────────────────────────────────────────────────────

class _ReflectionSheet extends StatefulWidget {
  const _ReflectionSheet({this.latestMoodLevel});

  /// Mood level that triggered this sheet (1–2 expected). Forwarded to the
  /// notification service when the sheet completes so we can schedule a
  /// follow-up worried check-in. `null` skips scheduling.
  final int? latestMoodLevel;

  @override
  State<_ReflectionSheet> createState() => _ReflectionSheetState();
}

class _ReflectionSheetState extends State<_ReflectionSheet>
    with SingleTickerProviderStateMixin {
  late final AnimationController _fadeCtrl;
  late final Animation<double> _fadeAnim;
  late final DateTime _entryTime;

  // State: null = showing CTAs, 'breathing' = showing inline breathing widget
  String? _activeView;

  // "Just breathe a moment" auto-dismiss timer
  Timer? _autoTimer;
  bool _fadingOut = false;

  // Schedule-on-complete guard so the worried check-in fires exactly once
  // even if multiple dismiss paths race (e.g. autoTimer + manual pop).
  bool _scheduledWorriedCheckin = false;

  @override
  void initState() {
    super.initState();
    _entryTime = DateTime.now();
    _fadeCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.fade,
    );
    _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeIn);
    _fadeCtrl.forward();
  }

  @override
  void dispose() {
    _autoTimer?.cancel();
    _fadeCtrl.dispose();
    super.dispose();
  }

  /// Schedule a worried check-in notification on sheet completion.
  /// Idempotent — guards against duplicate fires on racing dismiss paths.
  /// No-op when [latestMoodLevel] wasn't supplied (e.g. tests, legacy
  /// callers — see TODO in [showMoodLowReflectionSheet]).
  Future<void> _maybeScheduleWorriedCheckin() async {
    if (_scheduledWorriedCheckin) return;
    final level = widget.latestMoodLevel;
    if (level == null) return;
    _scheduledWorriedCheckin = true;
    try {
      await NotificationService.scheduleWorriedCheckin(
        latestMoodLevel: level,
        entryTime: _entryTime,
      );
    } catch (e) {
      // Non-fatal — sheet completes regardless. Notification service
      // failures (permission denied, plugin missing on web, etc.) shouldn't
      // bubble up. Surface for dev visibility.
      debugPrint('[mood_low_sheet] scheduleWorriedCheckin failed: $e');
    }
  }

  void _dismiss() {
    if (!mounted) return;
    // Fire-and-forget — don't block the pop on async scheduling.
    _maybeScheduleWorriedCheckin();
    Navigator.of(context).pop();
  }

  void _goToChat() {
    _dismiss();
    // Deep-link to Talk tab. Uses .request() (not .value=) because the bus
    // is a custom ChangeNotifier that always fires — required when the user
    // happens to already be on Talk per the bus state, since a plain
    // ValueNotifier suppresses same-value writes and the listener never ran.
    homeTabDeepLink.request(AppTab.talk);
  }

  void _startBreathing() {
    setState(() => _activeView = 'breathing');
  }

  void _justBreathe() {
    setState(() {
      _activeView = 'fade';
      _fadingOut = false;
    });
    // After 3 s start fade-out, then dismiss
    _autoTimer = Timer(const Duration(seconds: 3), () {
      if (!mounted) return;
      setState(() => _fadingOut = true);
      // Wait for the fade-out animation to finish, then pop
      Future.delayed(GQDurations.fade, _dismiss);
    });
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnim,
      child: Container(
        decoration: const BoxDecoration(
          color: GQColors.softBg,
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(GQRadii.sheet),
          ),
        ),
        padding: EdgeInsets.fromLTRB(
          24,
          20,
          24,
          // Add bottom safe-area padding
          MediaQuery.of(context).padding.bottom + 24,
        ),
        child: AnimatedSwitcher(
          duration: GQDurations.fade,
          child: _buildBody(),
        ),
      ),
    );
  }

  Widget _buildBody() {
    switch (_activeView) {
      case 'breathing':
        return _BreathingView(onDone: _dismiss);
      case 'fade':
        return _JustBreatheView(fadingOut: _fadingOut);
      default:
        return _CtaView(
          onChat: _goToChat,
          onBreathing: _startBreathing,
          onJustBreathe: _justBreathe,
          onSkip: _dismiss,
        );
    }
  }
}

// ─── CTA view ────────────────────────────────────────────────────────────────

class _CtaView extends StatelessWidget {
  final VoidCallback onChat;
  final VoidCallback onBreathing;
  final VoidCallback onJustBreathe;
  final VoidCallback onSkip;

  const _CtaView({
    required this.onChat,
    required this.onBreathing,
    required this.onJustBreathe,
    required this.onSkip,
  });

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Column(
      key: const ValueKey('cta'),
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Drag handle
        Center(
          child: Container(
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.black12,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Headline
        Text(
          'Thanks for sharing.',
          style: textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w700,
            fontFamily: 'Inter',
            color: Colors.black87,
          ),
        ),
        const SizedBox(height: 8),

        // Sub-copy (R2D4 tone — observational, not clinical)
        Text(
          'Low days are part of it. Want to do something gentle?',
          style: textTheme.bodyMedium?.copyWith(
            fontFamily: 'Inter',
            color: Colors.black54,
            height: 1.4,
          ),
        ),
        const SizedBox(height: 24),

        // CTA 1 — Chat with Alex
        _CtaButton(
          icon: Icons.chat_bubble_outline_rounded,
          label: 'Chat with Alex',
          onTap: onChat,
        ),
        const SizedBox(height: 12),

        // CTA 2 — Breathing exercise
        _CtaButton(
          icon: Icons.air_rounded,
          label: 'Breathing exercise',
          onTap: onBreathing,
        ),
        const SizedBox(height: 12),

        // CTA 3 — Just breathe a moment (soft, auto-dismiss)
        _CtaButton(
          icon: Icons.self_improvement_rounded,
          label: 'Just breathe a moment',
          onTap: onJustBreathe,
        ),
        const SizedBox(height: 20),

        // Skip link — always present (save-exit-always, optional>required)
        Center(
          child: TextButton(
            onPressed: onSkip,
            style: TextButton.styleFrom(
              foregroundColor: Colors.black45,
            ),
            child: const Text(
              'Skip for now',
              style: TextStyle(
                fontFamily: 'Inter',
                fontSize: 14,
                decoration: TextDecoration.underline,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ─── Shared CTA button ────────────────────────────────────────────────────────

class _CtaButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _CtaButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(GQRadii.card),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(GQRadii.card),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Icon(icon, color: GQColors.coral, size: 22),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(
                    fontFamily: 'Inter',
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                    color: Colors.black87,
                  ),
                ),
              ),
              const Icon(Icons.chevron_right_rounded,
                  color: Colors.black26, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Breathing view (inline) ──────────────────────────────────────────────────

class _BreathingView extends StatelessWidget {
  final VoidCallback onDone;
  const _BreathingView({required this.onDone});

  @override
  Widget build(BuildContext context) {
    return Column(
      key: const ValueKey('breathing'),
      mainAxisSize: MainAxisSize.min,
      children: [
        // Back / close row
        Row(
          children: [
            IconButton(
              icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
              onPressed: onDone,
              color: Colors.black54,
            ),
            const Expanded(
              child: Text(
                'Box Breathing',
                style: TextStyle(
                  fontFamily: 'Inter',
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                  color: Colors.black87,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        BreathingExerciseWidget(
          exercise: _buildBoxBreathing(),
          onComplete: onDone,
        ),
        const SizedBox(height: 8),
      ],
    );
  }
}

// ─── "Just breathe" fade view ─────────────────────────────────────────────────

class _JustBreatheView extends StatelessWidget {
  final bool fadingOut;
  const _JustBreatheView({required this.fadingOut});

  @override
  Widget build(BuildContext context) {
    return AnimatedOpacity(
      key: const ValueKey('justbreathe'),
      opacity: fadingOut ? 0.0 : 1.0,
      duration: GQDurations.fade,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.favorite_border_rounded,
              color: GQColors.coral,
              size: 40,
            ),
            const SizedBox(height: 16),
            const Text(
              'Take a slow breath.\nYou don\'t have to do anything right now.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Inter',
                fontSize: 16,
                color: Colors.black54,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
