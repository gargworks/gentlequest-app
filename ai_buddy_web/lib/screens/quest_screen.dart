// R1D13 — Quests · GentleQuest_Quests.html
// Three views: A (list) · B (preview) · C (in-progress)
// Principles: P2 skip anywhere · P3 one clear next action · no streak-shame
// NO Level numbers · NO streak counts · coral-not-red · .withValues() API

import 'package:flutter/material.dart';
import 'dart:math' as math;

import '../theme/gq_tokens.dart';

// ─── Data models (UI-layer only, no backend) ─────────────────────────────────

enum QuestFilter { all, mornings, sleep, anxiousDays, heavyStretches }

class _QuestStep {
  final int day;
  final String title;
  final bool isBold;

  const _QuestStep({
    required this.day,
    required this.title,
    this.isBold = false,
  });
}

class _QuestData {
  final String id;
  final String title;
  final String subtitle; // e.g. "7 days · gentle"
  final String description;
  final String emoji;
  final QuestFilter filter;
  final List<_QuestStep> steps;

  const _QuestData({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.description,
    required this.emoji,
    required this.filter,
    required this.steps,
  });
}

// ─── Sample quest data (3 Good Things — verbatim from HTML) ──────────────────

const _kInProgressTitle = '7-day morning anchor';
const _kInProgressSubtitle = 'Day 4 of 7 · breakfast + 5 min outside';
const _kInProgressProgress = '4/7';
const _kInProgressCurrent = 4;
const _kInProgressTotal = 7;

const _kSampleQuests = <_QuestData>[
  _QuestData(
    id: '3goodthings',
    title: '3 Good Things',
    subtitle: '7 days · gentle',
    description:
        'When you write three good things, your brain practices noticing. '
        'Over 7 days, that practice compounds — even small moments stick.',
    emoji: '✨',
    filter: QuestFilter.mornings,
    steps: [
      _QuestStep(day: 1, title: 'Write any 3 good things · warm-up', isBold: true),
      _QuestStep(day: 2, title: '3 things + a tiny note about each', isBold: true),
      _QuestStep(day: 3, title: 'Same — small notes still count'),
      _QuestStep(day: 4, title: '3 things you noticed in others', isBold: true),
      _QuestStep(day: 5, title: 'Same — notice quietly'),
      _QuestStep(day: 6, title: '3 things about yourself', isBold: true),
      _QuestStep(day: 7, title: 'Free-form — what stuck?', isBold: true),
    ],
  ),
  _QuestData(
    id: 'phonedown',
    title: 'Phone down',
    subtitle: '5 days · gentle',
    description: 'A few minutes less on the phone. No tracking, no guilt.',
    emoji: '📵',
    filter: QuestFilter.mornings,
    steps: [],
  ),
  _QuestData(
    id: 'walkmeeting',
    title: 'Walking meeting (1 a day)',
    subtitle: '5 days · easy',
    description: 'Take one meeting or call outside each day.',
    emoji: '🚶',
    filter: QuestFilter.heavyStretches,
    steps: [],
  ),
  _QuestData(
    id: 'sleepwinddown',
    title: 'Sleep wind-down',
    subtitle: '7 days · gentle',
    description: 'A small ritual before bed to signal the end of the day.',
    emoji: '🌙',
    filter: QuestFilter.sleep,
    steps: [],
  ),
  _QuestData(
    id: 'breathingbreak',
    title: 'Breathing break',
    subtitle: '3 days · light',
    description: 'One slow breath when you notice you\'re holding tension.',
    emoji: '🫧',
    filter: QuestFilter.anxiousDays,
    steps: [],
  ),
  _QuestData(
    id: 'morningwater',
    title: 'Morning water',
    subtitle: '7 days · gentle',
    description: 'Glass of water before coffee. Simple.',
    emoji: '💧',
    filter: QuestFilter.mornings,
    steps: [],
  ),
];

// ─── Screen ───────────────────────────────────────────────────────────────────

/// Three-view Quests screen.
/// [_QuestView.list]        → View A (quest list + filter chips)
/// [_QuestView.preview]     → View B (quest preview before starting)
/// [_QuestView.inProgress]  → View C (active quest step view)
enum _QuestView { list, preview, inProgress }

class QuestScreen extends StatefulWidget {
  const QuestScreen({super.key});

  @override
  State<QuestScreen> createState() => _QuestScreenState();
}

class _QuestScreenState extends State<QuestScreen> {
  _QuestView _view = _QuestView.list;
  QuestFilter _activeFilter = QuestFilter.all;
  _QuestData? _selectedQuest;

  // In-progress state (UI-only; no backend)
  final List<String> _fields = ['', '', ''];
  bool _todayDone = false;

  void _goToPreview(_QuestData quest) {
    setState(() {
      _selectedQuest = quest;
      _view = _QuestView.preview;
    });
  }

  void _goToInProgress() {
    setState(() {
      _view = _QuestView.inProgress;
      _fields[0] = '';
      _fields[1] = '';
      _fields[2] = '';
      _todayDone = false;
    });
  }

  void _goToList() {
    setState(() {
      _view = _QuestView.list;
      _selectedQuest = null;
    });
  }

  void _skipToday() {
    // P2: skip is graceful, never shamed. Simply return to list.
    _goToList();
  }

  void _markTodayDone() {
    setState(() => _todayDone = true);
    // Show a "Quest done!" toast immediately so the completion moment is
    // unambiguous — synth-QA UC-Q3: the in-progress entry fields resembled a
    // journal screen and the 600 ms confirmation window was too brief to
    // distinguish. Extended to 1 500 ms + snackbar = clear completion signal.
    final messenger = ScaffoldMessenger.maybeOf(context);
    messenger?.showSnackBar(
      SnackBar(
        content: const Row(
          children: [
            Icon(Icons.check_circle_rounded, color: Colors.white, size: 18),
            SizedBox(width: 8),
            Text(
              'Quest done! Nice work.',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
          ],
        ),
        backgroundColor: GQColors.primary,
        behavior: SnackBarBehavior.floating,
        duration: const Duration(milliseconds: 1400),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GQRadii.card),
        ),
      ),
    );
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) _goToList();
    });
  }

  void _tellAlex(BuildContext ctx) {
    // Escape hatch: deep-link to chat. No navigation yet — show snack.
    ScaffoldMessenger.of(ctx).showSnackBar(
      SnackBar(
        content: const Text('Opening Alex…'),
        backgroundColor: GQColors.primary,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GQRadii.card),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return switch (_view) {
      _QuestView.list => _QuestListView(
          activeFilter: _activeFilter,
          onFilterChanged: (f) => setState(() => _activeFilter = f),
          onQuestTap: _goToPreview,
          onInProgressTap: _goToInProgress,
          onTellAlex: () => _tellAlex(context),
        ),
      _QuestView.preview => _QuestPreviewView(
          quest: _selectedQuest ?? _kSampleQuests.first,
          onStart: _goToInProgress,
          onBack: _goToList,
          onTellAlex: () => _tellAlex(context),
        ),
      _QuestView.inProgress => _QuestInProgressView(
          fields: _fields,
          onFieldChanged: (i, v) => setState(() => _fields[i] = v),
          onMarkDone: _markTodayDone,
          onSkip: _skipToday,
          onBack: _goToList,
          todayDone: _todayDone,
        ),
    };
  }
}

// ─── View A — Quest list ──────────────────────────────────────────────────────

class _QuestListView extends StatelessWidget {
  final QuestFilter activeFilter;
  final ValueChanged<QuestFilter> onFilterChanged;
  final ValueChanged<_QuestData> onQuestTap;
  final VoidCallback onInProgressTap;
  final VoidCallback onTellAlex;

  const _QuestListView({
    required this.activeFilter,
    required this.onFilterChanged,
    required this.onQuestTap,
    required this.onInProgressTap,
    required this.onTellAlex,
  });

  List<_QuestData> get _filtered {
    if (activeFilter == QuestFilter.all) return _kSampleQuests;
    return _kSampleQuests.where((q) => q.filter == activeFilter).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            // ── Header ────────────────────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Quests',
                      style: TextStyle(
                        fontFamily: GQTypography.displayFamily,
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink,
                        letterSpacing: -0.6,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'YOUR CALL · SKIP ANYTIME',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink3,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Gentle structure for harder days.',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: GQColors.ink2,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ── In-progress card ──────────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'CONTINUE WHAT YOU STARTED',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink3,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _InProgressCard(onTap: onInProgressTap),
                  ],
                ),
              ),
            ),

            // ── Filter chips ──────────────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 0, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'QUESTS FOR…',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink3,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 10),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.only(right: 20),
                      child: Row(
                        children: [
                          _FilterChip(
                            label: 'Mornings',
                            active: activeFilter == QuestFilter.mornings,
                            onTap: () => onFilterChanged(
                              activeFilter == QuestFilter.mornings
                                  ? QuestFilter.all
                                  : QuestFilter.mornings,
                            ),
                          ),
                          const SizedBox(width: 8),
                          _FilterChip(
                            label: 'Sleep',
                            active: activeFilter == QuestFilter.sleep,
                            onTap: () => onFilterChanged(
                              activeFilter == QuestFilter.sleep
                                  ? QuestFilter.all
                                  : QuestFilter.sleep,
                            ),
                          ),
                          const SizedBox(width: 8),
                          _FilterChip(
                            label: 'Anxious days',
                            active: activeFilter == QuestFilter.anxiousDays,
                            onTap: () => onFilterChanged(
                              activeFilter == QuestFilter.anxiousDays
                                  ? QuestFilter.all
                                  : QuestFilter.anxiousDays,
                            ),
                          ),
                          const SizedBox(width: 8),
                          _FilterChip(
                            label: 'Heavy stretches',
                            active: activeFilter == QuestFilter.heavyStretches,
                            onTap: () => onFilterChanged(
                              activeFilter == QuestFilter.heavyStretches
                                  ? QuestFilter.all
                                  : QuestFilter.heavyStretches,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ── 2-col browse grid ─────────────────────────────────────────
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              sliver: _QuestGrid(
                quests: _filtered,
                onTap: onQuestTap,
              ),
            ),

            // ── Tell Alex escape hatch ────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
                child: Center(
                  child: GestureDetector(
                    onTap: onTellAlex,
                    child: Text.rich(
                      TextSpan(
                        text: "Don't see what you need? ",
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 13,
                          color: GQColors.ink3,
                        ),
                        children: [
                          TextSpan(
                            text: 'Tell Alex',
                            style: TextStyle(
                              color: GQColors.primary,
                              fontWeight: FontWeight.w700,
                              decoration: TextDecoration.underline,
                              decorationColor: GQColors.primary,
                            ),
                          ),
                        ],
                      ),
                    ),
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

// ─── In-progress card ─────────────────────────────────────────────────────────

class _InProgressCard extends StatelessWidget {
  final VoidCallback onTap;
  const _InProgressCard({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(GQRadii.card),
          boxShadow: [
            BoxShadow(
              color: GQColors.ink.withValues(alpha: 0.06),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            // Progress ring
            _ProgressRing(
              current: _kInProgressCurrent,
              total: _kInProgressTotal,
              label: _kInProgressProgress,
              size: 48,
            ),
            const SizedBox(width: 14),
            // Title + subtitle
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _kInProgressTitle,
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 14.5,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink,
                      letterSpacing: -0.3,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    _kInProgressSubtitle,
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      color: GQColors.ink2,
                    ),
                  ),
                ],
              ),
            ),
            // Chevron
            Icon(Icons.chevron_right_rounded, color: GQColors.ink3, size: 20),
          ],
        ),
      ),
    );
  }
}

// ─── Filter chip ──────────────────────────────────────────────────────────────

class _FilterChip extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: GQDurations.fade,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: active ? GQColors.primary : Colors.white,
          borderRadius: BorderRadius.circular(GQRadii.button),
          border: Border.all(
            color: active ? GQColors.primary : GQColors.hair,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: active ? Colors.white : GQColors.ink2,
          ),
        ),
      ),
    );
  }
}

// ─── Quest grid ───────────────────────────────────────────────────────────────

class _QuestGrid extends StatelessWidget {
  final List<_QuestData> quests;
  final ValueChanged<_QuestData> onTap;

  const _QuestGrid({required this.quests, required this.onTap});

  @override
  Widget build(BuildContext context) {
    // Build sliver grid manually to avoid nesting scroll
    final rows = (quests.length / 2).ceil();
    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, rowIndex) {
          final left = rowIndex * 2;
          final right = left + 1;
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: _QuestGridCard(
                    quest: quests[left],
                    onTap: () => onTap(quests[left]),
                  ),
                ),
                const SizedBox(width: 12),
                if (right < quests.length)
                  Expanded(
                    child: _QuestGridCard(
                      quest: quests[right],
                      onTap: () => onTap(quests[right]),
                    ),
                  )
                else
                  const Expanded(child: SizedBox()),
              ],
            ),
          );
        },
        childCount: rows,
      ),
    );
  }
}

class _QuestGridCard extends StatelessWidget {
  final _QuestData quest;
  final VoidCallback onTap;

  const _QuestGridCard({required this.quest, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(GQRadii.card),
          boxShadow: [
            BoxShadow(
              color: GQColors.ink.withValues(alpha: 0.05),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Emoji icon
            Container(
              width: 36,
              height: 36,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: GQColors.primarySoft,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(quest.emoji, style: const TextStyle(fontSize: 18)),
            ),
            const SizedBox(height: 8),
            Text(
              quest.title,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13.5,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                letterSpacing: -0.2,
                height: 1.25,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              quest.subtitle,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 10.5,
                fontWeight: FontWeight.w700,
                color: GQColors.ink3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── View B — Quest preview ───────────────────────────────────────────────────

class _QuestPreviewView extends StatelessWidget {
  final _QuestData quest;
  final VoidCallback onStart;
  final VoidCallback onBack;
  final VoidCallback onTellAlex;

  const _QuestPreviewView({
    required this.quest,
    required this.onStart,
    required this.onBack,
    required this.onTellAlex,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: Column(
          children: [
            // Back nav row
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 12, 20, 0),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_ios_new_rounded),
                    color: GQColors.ink2,
                    onPressed: onBack,
                  ),
                  const Spacer(),
                ],
              ),
            ),
            // Scrollable body
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Title
                    Text(
                      quest.title,
                      style: TextStyle(
                        fontFamily: GQTypography.displayFamily,
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink,
                        letterSpacing: -0.5,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${quest.subtitle} · gratitude',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink2,
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Description
                    Text(
                      quest.description,
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 14.5,
                        color: GQColors.ink2,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 20),
                    // Skip note
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: GQColors.primarySoft,
                        borderRadius: BorderRadius.circular(GQRadii.card),
                      ),
                      child: Text(
                        "Skipping a day won't end the quest — life happens.",
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 12.5,
                          fontWeight: FontWeight.w600,
                          color: GQColors.primary,
                          height: 1.4,
                        ),
                      ),
                    ),
                    // Day-by-day timeline
                    if (quest.steps.isNotEmpty) ...[
                      const SizedBox(height: 20),
                      _DayByDayTimeline(steps: quest.steps),
                    ],
                    const SizedBox(height: 24),
                    // Start CTA
                    SizedBox(
                      width: double.infinity,
                      child: _PrimaryButton(
                        label: 'Start quest',
                        onTap: onStart,
                      ),
                    ),
                    const SizedBox(height: 12),
                    // Tell Alex instead
                    Center(
                      child: GestureDetector(
                        onTap: onTellAlex,
                        child: Text(
                          'Tell Alex instead',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: GQColors.ink2,
                            decoration: TextDecoration.underline,
                            decorationColor: GQColors.ink2,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Day-by-day timeline ──────────────────────────────────────────────────────

class _DayByDayTimeline extends StatelessWidget {
  final List<_QuestStep> steps;
  const _DayByDayTimeline({required this.steps});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: steps.asMap().entries.map((entry) {
        final isLast = entry.key == steps.length - 1;
        final step = entry.value;
        return IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Day number + line
              SizedBox(
                width: 32,
                child: Column(
                  children: [
                    Container(
                      width: 24,
                      height: 24,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: GQColors.primarySoft,
                        shape: BoxShape.circle,
                      ),
                      child: Text(
                        '${step.day}',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          color: GQColors.primary,
                        ),
                      ),
                    ),
                    if (!isLast)
                      Expanded(
                        child: Container(
                          width: 2,
                          margin: const EdgeInsets.symmetric(vertical: 2),
                          color: GQColors.hair,
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              // Step text
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: Text(
                    step.title,
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 13.5,
                      fontWeight: step.isBold ? FontWeight.w700 : FontWeight.w500,
                      color: step.isBold ? GQColors.ink : GQColors.ink2,
                      height: 1.35,
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

// ─── View C — In-progress ─────────────────────────────────────────────────────

class _QuestInProgressView extends StatelessWidget {
  final List<String> fields;
  final void Function(int, String) onFieldChanged;
  final VoidCallback onMarkDone;
  final VoidCallback onSkip;
  final VoidCallback onBack;
  final bool todayDone;

  const _QuestInProgressView({
    required this.fields,
    required this.onFieldChanged,
    required this.onMarkDone,
    required this.onSkip,
    required this.onBack,
    required this.todayDone,
  });

  bool get _canMarkDone => fields.any((f) => f.trim().isNotEmpty);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        child: Column(
          children: [
            // Nav row
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 12, 20, 0),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_ios_new_rounded),
                    color: GQColors.ink2,
                    onPressed: onBack,
                  ),
                  const Spacer(),
                ],
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header row: title + large progress ring
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '3 Good Things',
                                style: TextStyle(
                                  fontFamily: GQTypography.displayFamily,
                                  fontSize: 15,
                                  fontWeight: FontWeight.w800,
                                  color: GQColors.ink,
                                  letterSpacing: -0.3,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Day 3 of 7',
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: GQColors.ink2,
                                ),
                              ),
                            ],
                          ),
                        ),
                        _ProgressRing(
                          current: 3,
                          total: 7,
                          label: '3/7',
                          size: 60,
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    // Step view
                    Text(
                      '3 things + a tiny note about each',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink,
                        letterSpacing: -0.3,
                        height: 1.3,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '3 things you\'re grateful for, plus a tiny note about each.',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13.5,
                        color: GQColors.ink2,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 18),
                    // Numbered fields
                    _NumberedField(
                      index: 1,
                      value: fields[0],
                      onChanged: (v) => onFieldChanged(0, v),
                    ),
                    const SizedBox(height: 10),
                    _NumberedField(
                      index: 2,
                      value: fields[1],
                      onChanged: (v) => onFieldChanged(1, v),
                    ),
                    const SizedBox(height: 10),
                    _NumberedField(
                      index: 3,
                      value: fields[2],
                      onChanged: (v) => onFieldChanged(2, v),
                    ),
                    const SizedBox(height: 24),
                    // Mark today done CTA
                    if (!todayDone) ...[
                      SizedBox(
                        width: double.infinity,
                        child: _PrimaryButton(
                          label: 'Mark today done',
                          onTap: _canMarkDone ? onMarkDone : null,
                        ),
                      ),
                      const SizedBox(height: 14),
                      // Skip — always reachable (P2)
                      Center(
                        child: GestureDetector(
                          onTap: onSkip,
                          child: Text(
                            'Skip today (no judgment)',
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 12,
                              fontWeight: FontWeight.w800,
                              color: GQColors.ink2,
                              decoration: TextDecoration.underline,
                              decorationColor: GQColors.ink2,
                            ),
                          ),
                        ),
                      ),
                    ] else ...[
                      // Confirmation micro-state
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: GQColors.primarySoft,
                          borderRadius: BorderRadius.circular(GQRadii.card),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.check_circle_rounded,
                              color: GQColors.primary,
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Nice. See you tomorrow.',
                              style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: GQColors.primary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Numbered field ───────────────────────────────────────────────────────────

class _NumberedField extends StatelessWidget {
  final int index;
  final String value;
  final ValueChanged<String> onChanged;

  const _NumberedField({
    required this.index,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: GQColors.hair),
        boxShadow: [
          BoxShadow(
            color: GQColors.ink.withValues(alpha: 0.04),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // Number badge
          Container(
            width: 44,
            height: 52,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: GQColors.primarySoft,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(GQRadii.card),
                bottomLeft: Radius.circular(GQRadii.card),
              ),
            ),
            child: Text(
              '$index',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 15,
                fontWeight: FontWeight.w800,
                color: GQColors.primary,
              ),
            ),
          ),
          // Text input
          Expanded(
            child: TextField(
              onChanged: onChanged,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 14,
                color: GQColors.ink,
              ),
              decoration: InputDecoration(
                hintText: '_____ because…',
                hintStyle: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontStyle: FontStyle.italic,
                  color: GQColors.ink3,
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 14,
                ),
                border: InputBorder.none,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Progress ring ────────────────────────────────────────────────────────────

class _ProgressRing extends StatelessWidget {
  final int current;
  final int total;
  final String label;
  final double size;

  const _ProgressRing({
    required this.current,
    required this.total,
    required this.label,
    required this.size,
  });

  @override
  Widget build(BuildContext context) {
    final fraction = total > 0 ? current / total : 0.0;
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _RingPainter(fraction: fraction),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: size * 0.22,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
            ),
          ),
        ),
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  final double fraction;
  const _RingPainter({required this.fraction});

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final radius = (size.width - 6) / 2;
    const startAngle = -math.pi / 2;

    final trackPaint = Paint()
      ..color = GQColors.primarySoft
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round;

    final progressPaint = Paint()
      ..color = GQColors.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(Offset(cx, cy), radius, trackPaint);
    canvas.drawArc(
      Rect.fromCircle(center: Offset(cx, cy), radius: radius),
      startAngle,
      2 * math.pi * fraction,
      false,
      progressPaint,
    );
  }

  @override
  bool shouldRepaint(_RingPainter old) => old.fraction != fraction;
}

// ─── Primary button ───────────────────────────────────────────────────────────

class _PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;

  const _PrimaryButton({required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 15),
        decoration: BoxDecoration(
          color: enabled ? GQColors.primary : GQColors.primarySoft,
          borderRadius: BorderRadius.circular(GQRadii.button),
          boxShadow: enabled
              ? [
                  BoxShadow(
                    color: GQColors.primary.withValues(alpha: 0.35),
                    blurRadius: 20,
                    offset: const Offset(0, 8),
                  ),
                ]
              : null,
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 14.5,
            fontWeight: FontWeight.w800,
            color: enabled ? Colors.white : GQColors.ink3,
            letterSpacing: -0.2,
          ),
        ),
      ),
    );
  }
}
