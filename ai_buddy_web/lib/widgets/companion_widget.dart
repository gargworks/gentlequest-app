/// GentleQuest companion creature — visual widget.
///
/// Renders the companion as an emoji-based creature that changes with
/// growth stage, shows its name, level, and growth progress to the next
/// stage, and displays total active days (NOT a streak — anti-streak
/// design). Tapping the companion shows a small encouraging message.
/// A gentle animation fires on level-up.
///
/// Design principles (from the billion-dollar roadmap):
///   • The companion GROWS with gentle check-ins.
///   • It NEVER punishes absence — no streaks that break, no decay, no shame.
///   • Uses total active days, not consecutive days.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/companion.dart';
import '../providers/companion_provider.dart';
import '../theme/gq_tokens.dart';
import 'companion_painter.dart';

/// Short label for each growth stage, shown under the name.
const Map<GrowthStage, String> _kStageLabel = {
  GrowthStage.seed: 'Seed',
  GrowthStage.sprout: 'Sprout',
  GrowthStage.sapling: 'Sapling',
  GrowthStage.young: 'Young one',
  GrowthStage.mature: 'Mature',
};

/// Encouraging messages shown when the companion is tapped. Picked by
/// mood so the creature's voice matches its state. Absence is never
/// shamed — even [CompanionMood.content] (the floor) is warm.
const Map<CompanionMood, List<String>> _kTapMessages = {
  CompanionMood.content: [
    "I'm always glad to see you. No rush.",
    'You showed up. That counts.',
    'We go at your pace.',
  ],
  CompanionMood.happy: [
    'You\'re here! That makes me happy.',
    'Look at us, growing together.',
    'Good to see you again.',
  ],
  CompanionMood.sleepy: [
    'I was resting. Glad you\'re back.',
    'No pressure — I\'ll be here.',
    'Quiet days are okay too.',
  ],
  CompanionMood.excited: [
    'You came back twice! I love it.',
    'We\'re on a roll — gently.',
    'This is fun. Thank you.',
  ],
  CompanionMood.peaceful: [
    'Nice and easy. That\'s the way.',
    'Steady is just as good as fast.',
    'I feel calm when you\'re here.',
  ],
};

/// The companion creature widget. Stateless itself; reads state from
/// [CompanionProvider] and rebuilds on notify.
class CompanionWidget extends StatefulWidget {
  const CompanionWidget({super.key});

  @override
  State<CompanionWidget> createState() => _CompanionWidgetState();
}

class _CompanionWidgetState extends State<CompanionWidget>
    with TickerProviderStateMixin {
  late final AnimationController _bounceController;
  late final AnimationController _breatheController;
  late final Animation<double> _breatheAnimation;
  bool _celebrating = false;

  @override
  void initState() {
    super.initState();
    _bounceController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _breatheController = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    );
    _breatheAnimation = Tween<double>(begin: 1.0, end: 1.035).animate(
      CurvedAnimation(
        parent: _breatheController,
        curve: Curves.easeInOut,
      ),
    );
    // Return-after-absence: start mid-cycle (phase -2.8s = half-breath) so
    // the breathing appears to have been running before the user arrived,
    // not beginning fresh at phase 0.
    _breatheController.value = 0.5;
    _breatheController.repeat(reverse: true);
  }

  @override
  void dispose() {
    _bounceController.dispose();
    _breatheController.dispose();
    super.dispose();
  }

  void _maybeFireCelebration(bool leveledUp) {
    if (!leveledUp || !mounted) return;
    setState(() => _celebrating = true);
    _bounceController.forward(from: 0.0).whenCompleteOrCancel(() {
      if (mounted) setState(() => _celebrating = false);
    });
  }

  String _pickTapMessage(CompanionMood mood) {
    final list = _kTapMessages[mood] ?? _kTapMessages[CompanionMood.content]!;
    return list[(mood.hashCode).abs() % list.length];
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CompanionProvider>(
      builder: (context, provider, _) {
        final companion = provider.companion;
        // Fire the celebration once when a level-up is flagged, then clear.
        if (provider.leveledUpThisCycle && !_celebrating) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _maybeFireCelebration(provider.leveledUpThisCycle);
            provider.clearLevelUpFlag();
          });
        }
        return _buildCard(context, companion);
      },
    );
  }

  Widget _buildCard(BuildContext context, Companion companion) {
    final stageLabel = _kStageLabel[companion.growthStage] ?? 'Seed';

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Material(
        color: GQColors.softBg,
        borderRadius: BorderRadius.circular(GQRadii.card),
        child: InkWell(
          onTap: () => _showEncouragement(context, companion),
          borderRadius: BorderRadius.circular(GQRadii.card),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
            child: Row(
              children: [
                // Creature illustration with a gentle bounce on level-up.
                ScaleTransition(
                  scale: Tween<double>(begin: 1.0, end: 1.25).animate(
                    CurvedAnimation(
                      parent: _bounceController,
                      curve: Curves.elasticOut,
                    ),
                  ),
                  child: AnimatedSwitcher(
                    duration: GQDurations.companionStageChange,
                    transitionBuilder: (child, anim) =>
                        FadeTransition(opacity: anim, child: child),
                    child: ScaleTransition(
                      scale: _breatheAnimation,
                      key: ValueKey(companion.growthStage),
                      child: CustomPaint(
                        size: const Size.square(36),
                        painter: CompanionPainter(
                          stage: companion.growthStage,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Name only — Lv badge and XP bar removed from the
                      // companion card. Level chip and XP bar stay on Quest
                      // surfaces only.
                      Text(
                        companion.name,
                        style: const TextStyle(
                          fontFamily: GQTypography.displayFamily,
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: GQColors.ink,
                          letterSpacing: -0.2,
                        ),
                      ),
                      const SizedBox(height: 4),
                      // Stage label + active days only (no level, no XP bar).
                      Text(
                        '$stageLabel · ${companion.totalActiveDays} active '
                        '${companion.totalActiveDays == 1 ? 'day' : 'days'}',
                        style: const TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: GQColors.ink3,
                        ),
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

  void _showEncouragement(BuildContext context, Companion companion) {
    final message = _pickTapMessage(companion.mood);
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            CustomPaint(
              size: const Size.square(20),
              painter: CompanionPainter(
                stage: companion.growthStage,
                simplified: true,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
        behavior: SnackBarBehavior.floating,
        backgroundColor: GQColors.ink,
        duration: const Duration(seconds: 2),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GQRadii.card),
        ),
      ),
    );
  }
}
