// crisis_reentry_surface.dart — Crisis Re-Entry Surface
//
// What the user sees when they return to the app after a crisis was detected:
//   • Chat history intact at 82% opacity (aged like paper)
//   • Plain 'LAST NIGHT' datestamp above the old messages (11px, w700, ink3,
//     between hairlines)
//   • No banner saying "you were in crisis"
//   • No "How are you feeling?" — that's tone-deaf
//   • The companion is there, breathing normally
//   • Alex is silent — last night's "I'll be here in the morning" already
//     said it
//   • The input bar is focusable in the same tap-count as any other night
//
// After the user sends their first message post-crisis, the parent screen
// transitions back to normal opacity (300ms fade). This widget does NOT own
// that transition — it reports the first-send via [onFirstMessageSent] and
// the parent swaps it out.

import 'package:flutter/material.dart';

import '../models/companion.dart';
import '../theme/gq_tokens.dart';
import 'companion_painter.dart';

/// The crisis re-entry surface. Wraps the normal chat content (passed as
/// [child]) with aged opacity + a 'LAST NIGHT' datestamp + a breathing
/// companion. Alex is silent (no greeting bubble).
///
/// [crisisTimestamp] is when the crisis was detected. Used to render the
/// 'LAST NIGHT' label (if the crisis was yesterday) or the date otherwise.
/// [onFirstMessageSent] fires once when the user sends their first message
/// post-crisis; the parent uses it to fade back to normal opacity.
class CrisisReentrySurface extends StatefulWidget {
  const CrisisReentrySurface({
    super.key,
    required this.child,
    required this.crisisTimestamp,
    this.onFirstMessageSent,
    this.companionStage = GrowthStage.sapling,
  });

  /// The normal chat content (message list + input bar) to display at aged
  /// opacity.
  final Widget child;

  /// When the crisis was detected (epoch ms).
  final DateTime crisisTimestamp;

  /// Fires once when the user sends their first message post-crisis.
  final VoidCallback? onFirstMessageSent;

  /// Companion growth stage to render. Defaults to sapling.
  final GrowthStage companionStage;

  @override
  State<CrisisReentrySurface> createState() => CrisisReentrySurfaceState();
}

class CrisisReentrySurfaceState extends State<CrisisReentrySurface>
    with SingleTickerProviderStateMixin {
  bool _firstSent = false;
  late final AnimationController _breatheController;
  late final Animation<double> _breatheAnimation;

  @override
  void initState() {
    super.initState();
    _breatheController = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    );
    _breatheAnimation = Tween<double>(begin: 1.0, end: 1.035).animate(
      CurvedAnimation(parent: _breatheController, curve: Curves.easeInOut),
    );
    // Start mid-cycle so breathing appears to have been running.
    _breatheController.value = 0.5;
    _breatheController.repeat(reverse: true);
  }

  @override
  void dispose() {
    _breatheController.dispose();
    super.dispose();
  }

  /// Called by the parent (or wired to the input bar) when the user sends
  /// their first message post-crisis. Triggers [onFirstMessageSent] once.
  void markFirstMessageSent() {
    if (_firstSent) return;
    _firstSent = true;
    widget.onFirstMessageSent?.call();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Aged chat content — 82% opacity, like paper.
        Opacity(
          opacity: 0.82,
          child: widget.child,
        ),
        // 'LAST NIGHT' datestamp above the old messages, between hairlines.
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: _LastNightStamp(timestamp: widget.crisisTimestamp),
        ),
        // Companion — breathing normally, bottom-left. Silent (no greeting).
        // Renders a CompanionPainter directly (not via SilentWitness, which
        // returns its own Positioned and can't be nested here).
        Positioned(
          left: 18,
          bottom: 80,
          child: ScaleTransition(
            scale: _breatheAnimation,
            alignment: Alignment.bottomCenter,
            child: CustomPaint(
              size: const Size.square(30),
              painter: CompanionPainter(
                stage: widget.companionStage,
                simplified: true,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ─── 'LAST NIGHT' datestamp ──────────────────────────────────────────────────

class _LastNightStamp extends StatelessWidget {
  const _LastNightStamp({required this.timestamp});
  final DateTime timestamp;

  String _label() {
    final now = DateTime.now();
    final diff = DateTime(now.year, now.month, now.day)
        .difference(DateTime(timestamp.year, timestamp.month, timestamp.day));
    if (diff.inDays == 1) return 'LAST NIGHT';
    // Otherwise show the day name.
    const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
    return days[timestamp.weekday - 1];
  }

  @override
  Widget build(BuildContext context) {
    // 11px, w700, ink3, between hairlines. No banner styling — just a
    // quiet datestamp.
    return Container(
      color: Colors.transparent,
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
      child: Column(
        children: [
          Container(
            height: 1,
            color: GQColors.hair,
          ),
          const SizedBox(height: 8),
          Text(
            _label(),
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: GQColors.ink3,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            height: 1,
            color: GQColors.hair,
          ),
        ],
      ),
    );
  }
}

// ─── Crisis timestamp persistence (SharedPreferences) ─────────────────────────

/// SharedPreferences key for the last crisis timestamp (epoch ms).
const String kLastCrisisTimestampKey = 'last_crisis_timestamp_v1';

/// Returns true if the user is within 72h of the last recorded crisis.
/// Used by the chat screen to decide whether to show the re-entry surface
/// and whether to use the softer keyword threshold.
bool isWithinCrisisWindow(DateTime lastCrisis, {DateTime? now}) {
  final ref = now ?? DateTime.now();
  return ref.difference(lastCrisis).inHours < 72;
}
