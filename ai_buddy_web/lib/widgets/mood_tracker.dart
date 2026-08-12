import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../providers/mood_provider.dart';
import '../providers/companion_provider.dart';
import '../models/mood_entry.dart';
import '../quests/quests_engine.dart';
import '../theme/gq_tokens.dart';
import 'mood_low_reflection_sheet.dart';
import 'mood_reflection_sheet.dart';
import '../screens/onboarding_extensions_screen.dart';
import '../services/notification_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum ViewMode { daily, all }

class MoodTrackerWidget extends StatefulWidget {
  const MoodTrackerWidget({super.key});

  @override
  State<MoodTrackerWidget> createState() => _MoodTrackerWidgetState();
}

class _MoodTrackerWidgetState extends State<MoodTrackerWidget> {
  ViewMode _mode = ViewMode.daily; // default to Daily trend (aggregated)
  static const bool _enableCheckinsExpand =
      false; // feature toggle (hidden for now)
  bool _showLatestDayDetails = false;

  @override
  Widget build(BuildContext context) {
    return Consumer<MoodProvider>(
      builder: (context, moodProvider, child) {
        final hasEntries = moodProvider.moodEntries.isNotEmpty;
        // Do not block UI on initial load; show input immediately

        return SingleChildScrollView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              // Show error banner only when there are no entries to display.
              if (moodProvider.error != null && !hasEntries) ...[
                _buildErrorBanner(context, moodProvider),
                const SizedBox(height: 12),
              ],
              _buildMoodInput(context, moodProvider),
              const SizedBox(height: 16),
              // Clinical Check-in card
              _buildClinicalCheckInCard(context),
              const SizedBox(height: 16),
              // Weekly Pulse hero (show when there are at least 3 entries)
              if (moodProvider.moodEntries.length >= 3) ...[
                _buildWeeklyPulseHero(context, moodProvider),
                const SizedBox(height: 16),
              ],
              // "You Are Not Alone" pulse card
              if (moodProvider.latestPulse != null) ...[
                _buildPulseCard(context, moodProvider),
                const SizedBox(height: 16),
              ],
              // Toggle between Daily (aggregated) and All check-ins
              if (hasEntries) ...[
                _buildViewToggle(context),
                const SizedBox(height: 8),
                _buildCheckinsInfo(context, moodProvider),
                const SizedBox(height: 8),
              ],
              if (moodProvider.moodEntries.isNotEmpty) ...[
                _buildMoodChart(context, moodProvider, _mode),
                if (_mode == ViewMode.daily) ...[
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Avg per day',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context)
                                .textTheme
                                .bodySmall
                                ?.color
                                ?.withValues(alpha: 0.7),
                            fontFamily: 'Inter',
                          ),
                    ),
                  ),
                  const SizedBox(height: 8),
                ],
                const SizedBox(height: 16),
                _buildMoodStats(context, moodProvider),
              ] else ...[
                _buildEmptyMoodPlaceholder(context),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildErrorBanner(BuildContext context, MoodProvider moodProvider) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.error.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
            color: Theme.of(context).colorScheme.error.withValues(alpha: 0.35)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Icon(Icons.warning_amber_outlined,
              color: Theme.of(context).colorScheme.error),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              moodProvider.error ?? 'Something went wrong',
              style: TextStyle(
                color: Theme.of(context).colorScheme.error,
                fontFamily: 'Inter',
              ),
            ),
          ),
          TextButton(
            onPressed: () => moodProvider.reload(),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildPulseCard(BuildContext context, MoodProvider moodProvider) {
    final pulse = moodProvider.latestPulse;
    final moodLevel = moodProvider.lastMoodLevel;
    if (pulse == null || moodLevel == null) return const SizedBox.shrink();

    final theme = Theme.of(context);
    final percentages = pulse['percentages'] as Map<String, dynamic>?;
    final messages = pulse['solidarity_messages'] as Map<String, dynamic>?;
    final total = pulse['total_checkins_today'] as int? ?? 0;

    final pct = percentages?['$moodLevel'] ?? 0;
    final message = messages?['$moodLevel'] ?? "You're not alone.";

    return Card(
      elevation: 2.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
      color: theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.people_outline, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    message,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                      fontFamily: 'Inter',
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 18),
                  onPressed: () => moodProvider.clearPulse(),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (total > 1)
              Text(
                '$pct% of $total check-ins today felt the same way',
                style: theme.textTheme.bodySmall?.copyWith(
                  color:
                      theme.textTheme.bodySmall?.color?.withValues(alpha: 0.7),
                  fontFamily: 'Inter',
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyMoodPlaceholder(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 2.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SizedBox(
          height: 200,
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.show_chart_outlined,
                  size: 40,
                  color: theme.colorScheme.primary.withValues(alpha: 0.4),
                ),
                const SizedBox(height: 8),
                Text(
                  'Your feelings matter',
                  style: theme.textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  "Start tracking to discover patterns over time 🌱",
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.textTheme.bodySmall?.color
                        ?.withValues(alpha: 0.7),
                    fontFamily: 'Inter',
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ── R1D4 — GentleQuest Mood Entry sheet trigger ────────────────────────────
  // Design: docs/design/refs/htmls/GentleQuest_Mood_Entry.html
  // Principles: P1 (warmth), P2 (skip anything), P7 (no auto-advance without cancel)
  Widget _buildMoodInput(BuildContext context, MoodProvider moodProvider) {
    final now = DateTime.now();
    final dayLabel =
        '${DateFormat('EEEE').format(now).toUpperCase()} · ${DateFormat('MMM d').format(now).toUpperCase()}';
    return GestureDetector(
      onTap: () {
        HapticFeedback.selectionClick();
        _showMoodEntrySheet(context, moodProvider);
      },
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: Border.all(color: GQColors.hair),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0A1F1B3A),
              blurRadius: 12,
              offset: Offset(0, 4),
            ),
          ],
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    dayLabel,
                    style: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: GQColors.ink3,
                      letterSpacing: 0.3,
                    ),
                  ),
                  const SizedBox(height: 4),
                  // Verbatim copy from R1D4 spec
                  const Text(
                    'How are you, right now?',
                    style: TextStyle(
                      fontFamily: GQTypography.displayFamily,
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink,
                      letterSpacing: -0.3,
                    ),
                  ),
                  const SizedBox(height: 2),
                  // Verbatim sub from R1D4 spec
                  const Text(
                    'Takes 5 seconds. Skip anything you want.',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: GQColors.ink3,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            // Labeled pill instead of bare '+' circle: recognition > recall
            // (synthetic UX QA UC-M1 H6 — Maya didn't know the '+' meant "log mood").
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
              decoration: BoxDecoration(
                color: GQColors.primarySoft,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.add_rounded,
                    color: GQColors.primary,
                    size: 18,
                  ),
                  SizedBox(width: 4),
                  Text(
                    'Log mood',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: GQColors.primary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildClinicalCheckInCard(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 2.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
      child: InkWell(
        onTap: () => Navigator.of(context, rootNavigator: true)
            .pushNamed('/clinical-assessment'),
        borderRadius: BorderRadius.circular(12.0),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color:
                      theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  Icons.assignment_outlined,
                  color: theme.colorScheme.primary,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      // Softened from "Clinical Check-in" — medical jargon
                      // at first-touch was scaring anxious target users.
                      'Mental wellness check-in',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      // PHQ-9/GAD-7 names still used internally; user-facing
                      // copy describes the experience, not the instrument.
                      'A brief, private check-in · ~2 min',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.textTheme.bodySmall?.color
                            ?.withValues(alpha: 0.7),
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.chevron_right,
                color: theme.colorScheme.primary,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildViewToggle(BuildContext context) {
    final isDaily = _mode == ViewMode.daily;
    return Align(
      alignment: Alignment.centerRight,
      child: ToggleButtons(
        isSelected: [isDaily, !isDaily],
        onPressed: (index) {
          setState(() {
            _mode = index == 0 ? ViewMode.daily : ViewMode.all;
          });
        },
        constraints: const BoxConstraints(minHeight: 36, minWidth: 56),
        borderRadius: BorderRadius.circular(8),
        selectedBorderColor: Theme.of(context).colorScheme.primary,
        selectedColor: Theme.of(context).colorScheme.primary,
        fillColor:
            Theme.of(context).colorScheme.primary.withValues(alpha: 0.12),
        children: const [
          Padding(
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: Text('Daily')),
          Padding(
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: Text('All')),
        ],
      ),
    );
  }

  Widget _buildCheckinsInfo(BuildContext context, MoodProvider moodProvider) {
    if (_mode != ViewMode.daily) return const SizedBox.shrink();
    final map = moodProvider.moodEntriesByDate;
    if (map.isEmpty) return const SizedBox.shrink();
    final days = map.keys.toList()..sort();
    final lastDay = days.last;
    final count = map[lastDay]?.length ?? 0;
    if (count <= 1) return const SizedBox.shrink();
    final locale = Localizations.localeOf(context);
    final dateLocale = (locale.countryCode?.toUpperCase() == 'IN')
        ? 'en_GB'
        : locale.toLanguageTag();
    final label =
        '$count check-ins on ${DateFormat.MMMd(dateLocale).format(lastDay)}';
    final dayEntries = List<MoodEntry>.from(map[lastDay] ?? const <MoodEntry>[])
      ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: Chip(label: Text(label)),
        ),
        if (_enableCheckinsExpand)
          TextButton(
            onPressed: () {
              setState(() {
                _showLatestDayDetails = !_showLatestDayDetails;
              });
            },
            child: Text(
                _showLatestDayDetails ? 'Hide check-ins' : 'View check-ins'),
          ),
        if (_enableCheckinsExpand && _showLatestDayDetails)
          Card(
            elevation: 1.0,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8.0)),
            child: Padding(
              padding:
                  const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
              child: Column(
                children: dayEntries.map((e) {
                  final t = e.timestamp.toLocal();
                  return ListTile(
                    dense: true,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 8.0),
                    leading:
                        Text(e.moodEmoji, style: const TextStyle(fontSize: 20)),
                    title: Text(DateFormat('HH:mm').format(t)),
                    subtitle: (e.note != null && e.note!.trim().isNotEmpty)
                        ? Text(e.note!.trim())
                        : null,
                  );
                }).toList(),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildMoodChart(
      BuildContext context, MoodProvider moodProvider, ViewMode mode) {
    // Prepare data and labels based on selected mode
    List<String> labels = <String>[];
    List<FlSpot> spots = <FlSpot>[];
    final locale = Localizations.localeOf(context);
    final dateLocale = (locale.countryCode?.toUpperCase() == 'IN')
        ? 'en_GB'
        : locale.toLanguageTag();

    if (mode == ViewMode.daily) {
      final map = moodProvider.moodEntriesByDate;
      if (map.isEmpty) return const SizedBox.shrink();
      final days = map.keys.toList()..sort();
      for (int i = 0; i < days.length; i++) {
        final d = days[i];
        final list = map[d] ?? const <MoodEntry>[];
        if (list.isEmpty) continue;
        final sum = list.fold<int>(0, (s, e) => s + e.moodLevel);
        final avg = sum / list.length;
        labels.add(DateFormat.MMMd(dateLocale).format(d));
        spots.add(FlSpot(i.toDouble(), avg.toDouble()));
      }
    } else {
      final entries = moodProvider.moodEntries;
      if (entries.isEmpty) return const SizedBox.shrink();
      // If all entries are the same day, show time-of-day for clarity; otherwise show date.
      final first = entries.first.timestamp.toLocal();
      final sameDay = entries.every((e) {
        final t = e.timestamp.toLocal();
        return t.year == first.year &&
            t.month == first.month &&
            t.day == first.day;
      });
      labels = entries
          .map((e) => sameDay
              ? DateFormat('HH:mm').format(e.timestamp.toLocal())
              : DateFormat.MMMd(dateLocale).format(e.timestamp.toLocal()))
          .toList();
      spots = entries
          .asMap()
          .entries
          .map((entry) =>
              FlSpot(entry.key.toDouble(), entry.value.moodLevel.toDouble()))
          .toList();
    }

    if (labels.isEmpty || spots.isEmpty) return const SizedBox.shrink();

    // Determine tick density for bottom axis to avoid clutter.
    final len = labels.length;
    final step = len <= 6 ? 1 : (len / 6).ceil();

    return Card(
      elevation: 2.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SizedBox(
          height: 200,
          child: LineChart(
            LineChartData(
              gridData: const FlGridData(show: false),
              titlesData: FlTitlesData(
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 1,
                    reservedSize: 40,
                    getTitlesWidget: (value, meta) {
                      if (value < 1 || value > 5) return const Text('');
                      return Text(
                          MoodEntry(moodLevel: value.toInt()).moodEmoji);
                    },
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 1,
                    getTitlesWidget: (value, meta) {
                      final i = value.toInt();
                      if (i < 0 || i >= labels.length) return const Text('');
                      // Only show a subset of labels to reduce clutter
                      if (i == 0 || i == labels.length - 1 || i % step == 0) {
                        return Text(labels[i]);
                      }
                      return const Text('');
                    },
                  ),
                ),
                rightTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                topTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
              ),
              borderData: FlBorderData(show: false),
              minX: 0,
              maxX: labels.length.toDouble() - 1,
              minY: 1,
              maxY: 5,
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: spots.length > 2,
                  color: Theme.of(context).colorScheme.primary,
                  barWidth: 3,
                  isStrokeCapRound: true,
                  dotData: const FlDotData(show: true),
                  belowBarData: BarAreaData(
                    show: spots.length > 1,
                    color: Theme.of(context)
                        .colorScheme
                        .primary
                        .withValues(alpha: 0.1),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMoodStats(BuildContext context, MoodProvider moodProvider) {
    final entries = moodProvider.moodEntries;
    if (entries.isEmpty) return const SizedBox.shrink();

    final averageMood = moodProvider.averageMood;
    final latestMood = entries.last;

    return Card(
      elevation: 2.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Mood Statistics',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatItem(
                  context,
                  'Current',
                  latestMood.moodEmoji,
                  latestMood.moodDescription,
                ),
                _buildStatItem(
                  context,
                  'Average',
                  MoodEntry(moodLevel: averageMood.round()).moodEmoji,
                  averageMood.toStringAsFixed(1),
                ),
                _buildStatItem(
                  context,
                  'Entries',
                  '📊',
                  entries.length.toString(),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(
    BuildContext context,
    String label,
    String emoji,
    String value,
  ) {
    return Column(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontFamily: 'Inter', // Match chat screen font family
              ),
        ),
        const SizedBox(height: 4),
        Text(
          emoji,
          style: const TextStyle(fontSize: 32),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontFamily: 'Inter', // Match chat screen font family
              ),
        ),
      ],
    );
  }

  // ── R1D4 — opens the GentleQuest Mood Entry bottom sheet ───────────────────
  Future<void> _showMoodEntrySheet(
    BuildContext context,
    MoodProvider moodProvider,
  ) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      useRootNavigator: true,
      builder: (sheetCtx) => _MoodEntrySheet(
        onSave: (int moodLevel, List<_MoodContext> contexts, String? note) async {
          HapticFeedback.mediumImpact();
          // Track if this is the user's first mood entry — used to show
          // the notification opt-in sheet after the reflection/toast.
          final bool isFirstEntry = moodProvider.moodEntries.isEmpty;
          // R1D5 streak-race fix: await the provider so the optimistic cache
          // update + first save have landed before we compute the streak for
          // the reflection sheet. `addMoodEntry` is `Future<void>` and only
          // returns once the local cache is updated; computing streakDays
          // afterwards prevents the badge from under-counting on first entry
          // of the day. We also resolve streakDays *here* (in the closure)
          // rather than inside `addPostFrameCallback`, so the value is bound
          // to the moment we know the entry is in.
          // Stage 1 — capture the companion provider ref before any await
          // so the post-await context use stays sync-safe.
          final companionProvider =
              Provider.of<CompanionProvider>(context, listen: false);
          final addFuture = moodProvider.addMoodEntry(
            moodLevel,
            note: note?.trim(),
            contextChips: contexts.map((context) => context.label).toList(),
          );
          // Pop the sheet immediately for snappy UX — the await runs in
          // parallel with the pop transition.
          Navigator.of(sheetCtx, rootNavigator: true).pop();
          await addFuture;
          // Sheet was popped; the parent (MoodTrackerWidget) may have rebuilt
          // or unmounted. Guard with `mounted` before any further UI.
          if (!mounted) return;
          // Stage 1 — feed the companion creature on every mood check-in.
          // The companion never punishes absence; it only grows. We derive
          // a 7-day cadence + today's count from the mood provider so the
          // creature's mood reflects recent presence, not streak breakage.
          try {
            final now = DateTime.now();
            final today = DateTime(now.year, now.month, now.day);
            int recentDays = 0;
            for (int i = 0; i < 7; i++) {
              final d = today.subtract(Duration(days: i));
              if ((moodProvider.moodEntriesByDate[d] ?? const []).isNotEmpty) {
                recentDays++;
              }
            }
            final checkInsToday =
                (moodProvider.moodEntriesByDate[today] ?? const []).length;
            await companionProvider.checkIn(
              recentCheckInDays: recentDays,
              checkInsToday: checkInsToday,
            );
          } catch (_) {
            // Companion feed is best-effort; never block the mood flow.
          }
          // Pre-compute streak now that the entry has propagated. Bind it
          // into the closure so the post-frame callback uses this value
          // rather than recomputing after another frame.
          final int? streakDays =
              moodLevel == 5 ? QuestsEngine().computeTotalActiveDays() : null;
          // R1D5 — Post-submit reflection: branch by mood level.
          //   moodLevel 1–2 → Low mood sheet (State A)
          //   moodLevel 5   → Great mood sheet (State B, celebrates + harvests insight)
          //   moodLevel 3–4 → Neutral auto-dismiss toast (State C)
          // Guard with `mounted` — the parent widget can unmount between
          // pop and post-frame (e.g. user backs out during the haptic)
          // and we'd hit "showModalBottomSheet on a defunct context".
          WidgetsBinding.instance.addPostFrameCallback((_) async {
            if (!mounted) return;
            // Show reflection sheet based on mood level
            if (moodLevel <= 2) {
              await showMoodLowReflectionSheet(context, latestMoodLevel: moodLevel);
            } else if (moodLevel == 5) {
              // streakDays already computed above with fresh provider state.
              await showMoodGreatReflectionSheet(context, streakDays: streakDays!);
            } else {
              // Neutral (3–4): lightweight logged toast, auto-dismisses ~3s.
              showMoodNeutralToast(context);
              await Future.delayed(const Duration(seconds: 3));
            }
            // After first mood entry, offer notification opt-in
            if (isFirstEntry && mounted) {
              await _maybeShowNotifOptIn(context);
            }
          });
        },
      ),
    );
  }

  /// Shows the notification opt-in sheet after the first mood check-in,
  /// if the user hasn't already enabled notifications or snoozed the prompt.
  Future<void> _maybeShowNotifOptIn(BuildContext context) async {
    // Check if user already snoozed the opt-in
    final canShow = await shouldShowNotifOptIn();
    if (!canShow || !mounted) return;

    // Check if daily check-in is already enabled in prefs
    final prefs = await SharedPreferences.getInstance();
    final dailyEnabled = prefs.getBool('daily_checkin_enabled') ?? false;
    if (dailyEnabled) return; // already opted in

    if (!mounted) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      useRootNavigator: true,
      builder: (_) => NotificationOptInSheet(
        onEnable: (selections) async {
          if (selections[NotifKind.dailyCheckIn] == true) {
            final granted = await NotificationService.requestPermissions();
            if (granted) {
              await NotificationService.scheduleGentleDailyCheckin(enabled: true);
            }
          }
        },
      ),
    );
  }

  Widget _buildWeeklyPulseHero(
      BuildContext context, MoodProvider moodProvider) {
    final primary = Theme.of(context).primaryColor;
    final moods = moodProvider.moodEntries;

    // Create a temporary engine instance to compute streaks
    // Note: This creates a new instance each time, but computeFriendlyDailyStreak
    // reads from SharedPreferences so it will have the correct persisted data
    final engine = QuestsEngine();
    // CHANGED: Use total active days for "No-Guilt" tracking
    // final int streakDays = engine.computeFriendlyDailyStreak();
    final int streakDays = engine.computeTotalActiveDays();

    // Calculate mood trend (last 7 days vs previous 7 days)
    double? avgInRange(DateTime from, DateTime to) {
      final filtered = moods.where((e) {
        final t = e.timestamp.toUtc();
        return t.isAfter(from) && !t.isAfter(to);
      }).toList();
      if (filtered.isEmpty) return null;
      final sum = filtered.fold<int>(0, (s, e) => s + e.moodLevel);
      return sum / filtered.length;
    }

    final now = DateTime.now().toUtc();
    final recentFrom = now.subtract(const Duration(days: 7));
    final prevFrom = now.subtract(const Duration(days: 14));
    final prevTo = now.subtract(const Duration(days: 7));

    final recentAvg = avgInRange(recentFrom, now);
    final prevAvg = avgInRange(prevFrom, prevTo);

    String trendLabel;
    if (recentAvg != null && prevAvg != null) {
      final delta = recentAvg - prevAvg;
      if (delta > 0.15) {
        trendLabel = "Calmer vs last week";
      } else if (delta < -0.15) {
        trendLabel = "Rougher vs last week";
      } else {
        trendLabel = "Steady vs last week";
      }
    } else {
      trendLabel = "Keep checking in";
    }

    // Calculate next badge progress
    int nextBadgeTarget;
    if (streakDays >= 14) {
      nextBadgeTarget = ((streakDays / 7).ceil() + 1) * 7;
    } else if (streakDays >= 7) {
      nextBadgeTarget = 14;
    } else if (streakDays >= 3) {
      nextBadgeTarget = 7;
    } else {
      nextBadgeTarget = 3;
    }
    final int daysToBadge =
        (nextBadgeTarget - streakDays).clamp(0, nextBadgeTarget);
    final String nextBadge = daysToBadge == 0
        ? "Badge earned!"
        : "Next badge: $daysToBadge more day${daysToBadge == 1 ? '' : 's'}";
    final double badgeProgress = (streakDays / nextBadgeTarget).clamp(0.0, 1.0);

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            primary.withValues(alpha: 0.12),
            primary.withValues(alpha: 0.04),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: primary.withValues(alpha: 0.15),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (streakDays > 0) ...[
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.06),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text("🌱", style: TextStyle(fontSize: 14)),
                      const SizedBox(width: 6),
                      Text(
                        "$streakDays days total", // No-Guilt Label
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
              ],
              Text(
                "Weekly Pulse",
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                  color: Colors.grey[700],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            trendLabel,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            height: 32,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.9),
              borderRadius: BorderRadius.circular(10),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                Container(
                  width: 60,
                  height: 4,
                  decoration: BoxDecoration(
                    color: primary.withValues(alpha: 0.25),
                    borderRadius: BorderRadius.circular(2),
                  ),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Container(
                      width: (60 * badgeProgress).clamp(4.0, 60.0),
                      decoration: BoxDecoration(
                        color: primary,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  nextBadge,
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.grey[700],
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Text(
                "See full recap",
                style: TextStyle(
                  color: primary,
                  fontWeight: FontWeight.w700,
                  fontSize: 14,
                ),
              ),
              const SizedBox(width: 4),
              Icon(
                Icons.chevron_right_rounded,
                size: 20,
                color: primary,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════════════════
// R1D4 — GentleQuest Mood Entry Sheet
// Design: docs/design/refs/htmls/GentleQuest_Mood_Entry.html
// Principles: P1 (warmth), P2 (skip anything), P7 (no auto-advance without cancel)
// ════════════════════════════════════════════════════════════════════════════

/// Context factors the user can optionally tag their mood with.
/// Shown as multi-select chips in Zone 3 of the mood entry sheet.
enum _MoodContext {
  work,
  sleep,
  people,
  body,
  money,
  other;

  String get label {
    switch (this) {
      case _MoodContext.work:
        return 'Work';
      case _MoodContext.sleep:
        return 'Sleep';
      case _MoodContext.people:
        return 'People';
      case _MoodContext.body:
        return 'Body';
      case _MoodContext.money:
        return 'Money';
      case _MoodContext.other:
        return 'Other';
    }
  }
}

/// Mood-level → label mapping for the 5-pill row.
/// Labels are verbatim from R1D4 spec:
///   "Heavy" · "Low" · "Okay" · "Good" · "Great"
const _kMoodLabels = ['Heavy', 'Low', 'Okay', 'Good', 'Great'];

/// Emojis paired with each mood label (low → high energy).
const _kMoodEmojis = ['😔', '😕', '😐', '🙂', '😊'];

/// Semantic background colour for each selected mood pill.
/// Heavy/Low use accentSoft; Okay uses primarySoft gradient; Good/Great use
/// their semantic colours at 0.20 opacity.
Color _moodSelectedBg(int moodLevel) {
  // moodLevel is 1-based (1=Heavy … 5=Great)
  switch (moodLevel) {
    case 1: // Heavy — accentSoft (per REVIEW.md token note)
      return GQColors.accentSoft;
    case 2: // Low — accentSoft (per REVIEW.md token note)
      return GQColors.accentSoft;
    case 3: // Okay — lavender
      return GQColors.moodOkay.withValues(alpha: 0.35);
    case 4: // Good — peach
      return GQColors.moodGood.withValues(alpha: 0.35);
    case 5: // Great — green
      return GQColors.moodGreat.withValues(alpha: 0.35);
    default:
      return GQColors.primarySoft;
  }
}

/// Bottom sheet implementing the R1D4 Mood Entry design.
/// Six zones (handle · header+skip · emoji row · context chips · note · CTA).
class _MoodEntrySheet extends StatefulWidget {
  const _MoodEntrySheet({required this.onSave});

  /// Called when the user taps "Log mood".
  /// [moodLevel] is 1-based (1=Heavy … 5=Great).
  final void Function(int moodLevel, List<_MoodContext> contexts, String? note)
      onSave;

  @override
  State<_MoodEntrySheet> createState() => _MoodEntrySheetState();
}

class _MoodEntrySheetState extends State<_MoodEntrySheet> {
  // Default preselected: "Okay" = level 3 (index 2, 1-based = 3)
  int _selectedLevel = 3;
  final Set<_MoodContext> _contexts = {};
  bool _noteExpanded = false;
  final _noteController = TextEditingController();

  // Auto-advance timer — 800ms hold then submit (P7: cancellable)
  Timer? _autoAdvanceTimer;
  bool _autoAdvancePending = false;

  @override
  void dispose() {
    _autoAdvanceTimer?.cancel();
    _noteController.dispose();
    super.dispose();
  }

  void _selectMood(int level) {
    if (_selectedLevel == level && _autoAdvancePending) {
      // Second tap on already-selected = confirm immediately (cancel auto-advance)
      _cancelAutoAdvance();
      _submit();
      return;
    }
    _cancelAutoAdvance();
    setState(() {
      _selectedLevel = level;
      _autoAdvancePending = true;
    });
    HapticFeedback.selectionClick();
    // P7: 800ms auto-advance using GQDurations.autoAdvance (cancellable)
    _autoAdvanceTimer = Timer(GQDurations.autoAdvance, () {
      if (mounted && _autoAdvancePending) {
        _submit();
      }
    });
  }

  void _cancelAutoAdvance() {
    _autoAdvanceTimer?.cancel();
    _autoAdvanceTimer = null;
    if (mounted) {
      setState(() => _autoAdvancePending = false);
    }
  }

  void _submit() {
    widget.onSave(
      _selectedLevel,
      _contexts.toList(),
      _noteExpanded ? _noteController.text : null,
    );
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    // Date header: "TUESDAY · MAY 7" pattern — verbatim from R1D4 spec
    final dateHeader =
        '${DateFormat('EEEE').format(now).toUpperCase()} · ${DateFormat('MMM d').format(now).toUpperCase()}';

    return GestureDetector(
      // Cancel auto-advance when user taps chip or note zone (P7)
      onTap: () {},
      child: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(GQRadii.sheet),
            topRight: Radius.circular(GQRadii.sheet),
          ),
        ),
        // Ensure sheet grows with keyboard
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom + 28,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Zone 0 · drag handle ──────────────────────────────────────
            Padding(
              padding: const EdgeInsets.only(top: 14, bottom: 4),
              child: Center(
                child: Container(
                  width: 44,
                  height: 5,
                  decoration: BoxDecoration(
                    color: const Color(0xFFE5E2EE),
                    borderRadius: BorderRadius.circular(GQRadii.button),
                  ),
                ),
              ),
            ),

            // ── Zone 1 · header + skip CTA (P2: skip always visible) ─────
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 10, 16, 0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          dateHeader,
                          style: const TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: GQColors.ink3,
                            letterSpacing: 0.3,
                          ),
                        ),
                        const SizedBox(height: 4),
                        // Verbatim headline — R1D4 spec
                        const Text(
                          'How are you, right now?',
                          style: TextStyle(
                            fontFamily: GQTypography.displayFamily,
                            fontSize: 22,
                            fontWeight: FontWeight.w800,
                            color: GQColors.ink,
                            letterSpacing: -0.3,
                            height: 1.2,
                          ),
                        ),
                        const SizedBox(height: 4),
                        // Verbatim sub — R1D4 spec
                        const Text(
                          'Takes 5 seconds. Skip anything you want.',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                            color: GQColors.ink3,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  // P2: Skip is visible at top-right throughout
                  GestureDetector(
                    onTap: () {
                      _cancelAutoAdvance();
                      Navigator.of(context, rootNavigator: true).pop();
                    },
                    child: Container(
                      width: 34,
                      height: 34,
                      decoration: BoxDecoration(
                        color: GQColors.softBg,
                        shape: BoxShape.circle,
                        border: Border.all(color: GQColors.hair),
                      ),
                      child: const Icon(
                        Icons.close_rounded,
                        size: 16,
                        color: GQColors.ink3,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // ── Zone 2 · emoji-pill row ───────────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: List.generate(5, (index) {
                  final level = index + 1; // 1-based
                  final isSelected = _selectedLevel == level;
                  return _MoodEmojiButton(
                    emoji: _kMoodEmojis[index],
                    label: _kMoodLabels[index], // verbatim labels from spec
                    isSelected: isSelected,
                    selectedBg: _moodSelectedBg(level),
                    onTap: () => _selectMood(level),
                  );
                }),
              ),
            ),

            // Auto-advance affordance (shown when timer is running)
            AnimatedOpacity(
              opacity: _autoAdvancePending ? 1.0 : 0.0,
              duration: GQDurations.fade,
              child: Padding(
                padding: const EdgeInsets.only(top: 10),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.schedule_rounded,
                      size: 13,
                      color: GQColors.primary,
                    ),
                    const SizedBox(width: 5),
                    const Text(
                      'Submitting in 800ms · tap again to confirm now',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                        color: GQColors.primary,
                        letterSpacing: 0.2,
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Cancel affordance (P7: always cancellable)
                    GestureDetector(
                      onTap: _cancelAutoAdvance,
                      child: const Text(
                        'Cancel',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11.5,
                          fontWeight: FontWeight.w700,
                          color: GQColors.ink3,
                          letterSpacing: 0.2,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            // ── Zone 3 · context chips (optional, multi-select) ───────────
            GestureDetector(
              // Tapping chips cancels auto-advance (P7)
              onTap: _cancelAutoAdvance,
              behavior: HitTestBehavior.translucent,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'What shaped this?',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: GQColors.ink2,
                          ),
                        ),
                        const Text(
                          'OPTIONAL',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: GQColors.ink3,
                            letterSpacing: 0.3,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: _MoodContext.values.map((ctx) {
                        final selected = _contexts.contains(ctx);
                        return _ContextChip(
                          label: ctx.label,
                          isSelected: selected,
                          onTap: () {
                            _cancelAutoAdvance();
                            setState(() {
                              if (selected) {
                                _contexts.remove(ctx);
                              } else {
                                _contexts.add(ctx);
                              }
                            });
                          },
                        );
                      }).toList(),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // ── Zone 4 · optional note (collapsed by default) ────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: AnimatedCrossFade(
                duration: GQDurations.fade,
                crossFadeState: _noteExpanded
                    ? CrossFadeState.showSecond
                    : CrossFadeState.showFirst,
                firstChild: GestureDetector(
                  onTap: () {
                    _cancelAutoAdvance();
                    setState(() => _noteExpanded = true);
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: GQColors.softBg,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: GQColors.hair,
                        // [assumed] dashed border not directly available in Flutter;
                        // using solid hairline as closest token-compliant approximation
                      ),
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.edit_note_rounded,
                          size: 16,
                          color: GQColors.ink2,
                        ),
                        const SizedBox(width: 8),
                        const Expanded(
                          child: Text.rich(
                            TextSpan(
                              text: 'Add a thought ',
                              style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: GQColors.ink2,
                              ),
                              children: [
                                TextSpan(
                                  text: '(optional)',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w600,
                                    color: GQColors.ink3,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const Icon(
                          Icons.keyboard_arrow_down_rounded,
                          size: 16,
                          color: GQColors.ink3,
                        ),
                      ],
                    ),
                  ),
                ),
                secondChild: TextField(
                  controller: _noteController,
                  autofocus: _noteExpanded,
                  // [assumed] 80 char maxLength from HTML annotation (NoteField(maxLength: 80))
                  maxLength: 80,
                  maxLines: 3,
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    color: GQColors.ink,
                  ),
                  decoration: InputDecoration(
                    hintText: 'anything you want me to remember…',
                    hintStyle: const TextStyle(
                      color: GQColors.ink3,
                      fontFamily: GQTypography.bodyFamily,
                    ),
                    filled: true,
                    fillColor: GQColors.softBg,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: const BorderSide(color: GQColors.hair),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: const BorderSide(color: GQColors.hair),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: const BorderSide(
                          color: GQColors.primary, width: 1.5),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 12),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 20),

            // ── Zone 5 · submit CTA ────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: GestureDetector(
                onTap: () {
                  _cancelAutoAdvance();
                  _submit();
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  decoration: BoxDecoration(
                    color: GQColors.primary,
                    borderRadius: BorderRadius.circular(GQRadii.button),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x1A667EEA),
                        blurRadius: 26,
                        offset: Offset(0, 12),
                        spreadRadius: -10,
                      ),
                    ],
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'Log mood',
                        style: TextStyle(
                          fontFamily: GQTypography.displayFamily,
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                          letterSpacing: 0.2,
                        ),
                      ),
                      SizedBox(width: 8),
                      Icon(
                        Icons.check_rounded,
                        color: Colors.white,
                        size: 18,
                      ),
                    ],
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

// ── R1D4 supporting widgets ─────────────────────────────────────────────────

/// Single emoji pill in the mood selection row.
/// Selected state: larger, primary-ring + pulse animation (P7).
class _MoodEmojiButton extends StatefulWidget {
  const _MoodEmojiButton({
    required this.emoji,
    required this.label,
    required this.isSelected,
    required this.selectedBg,
    required this.onTap,
  });

  final String emoji;
  final String label; // verbatim from R1D4 spec
  final bool isSelected;
  final Color selectedBg;
  final VoidCallback onTap;

  @override
  State<_MoodEmojiButton> createState() => _MoodEmojiButtonState();
}

class _MoodEmojiButtonState extends State<_MoodEmojiButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;
  late final Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    );
    _pulse = Tween<double>(begin: 1.0, end: 1.08).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    if (widget.isSelected) _pulseController.repeat(reverse: true);
  }

  @override
  void didUpdateWidget(_MoodEmojiButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isSelected && !oldWidget.isSelected) {
      _pulseController.repeat(reverse: true);
    } else if (!widget.isSelected && oldWidget.isSelected) {
      _pulseController.stop();
      _pulseController.reset();
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final double size = widget.isSelected ? 64.0 : 56.0;
    final double emojiSize = widget.isSelected ? 32.0 : 28.0;
    final translateY = widget.isSelected ? -4.0 : 0.0;

    return GestureDetector(
      onTap: widget.onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          AnimatedBuilder(
            animation: _pulse,
            builder: (_, child) => Transform.translate(
              offset: Offset(0, translateY),
              child: Transform.scale(
                scale: widget.isSelected ? _pulse.value : 1.0,
                child: child,
              ),
            ),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: size,
              height: size,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: widget.isSelected ? widget.selectedBg : GQColors.softBg,
                border: Border.all(
                  color: widget.isSelected
                      ? GQColors.primary
                      : GQColors.hair,
                  width: widget.isSelected ? 2.5 : 1.5,
                ),
              ),
              child: Center(
                child: Text(
                  widget.emoji,
                  style: TextStyle(fontSize: emojiSize, height: 1.0),
                ),
              ),
            ),
          ),
          const SizedBox(height: 6),
          AnimatedDefaultTextStyle(
            duration: const Duration(milliseconds: 200),
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: widget.isSelected ? 12.0 : 11.0,
              fontWeight:
                  widget.isSelected ? FontWeight.w800 : FontWeight.w700,
              color: widget.isSelected ? GQColors.primary : GQColors.ink3,
              letterSpacing: 0.2,
            ),
            child: Text(widget.label),
          ),
        ],
      ),
    );
  }
}

/// Context chip: filled (primary) when selected, ghost when unselected.
class _ContextChip extends StatelessWidget {
  const _ContextChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? GQColors.primary : GQColors.softBg,
          borderRadius: BorderRadius.circular(GQRadii.button),
          border: Border.all(
            color: isSelected ? GQColors.primary : GQColors.hair,
            width: 1.5,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 13,
            fontWeight: isSelected ? FontWeight.w800 : FontWeight.w700,
            color: isSelected ? Colors.white : GQColors.ink,
          ),
        ),
      ),
    );
  }
}
