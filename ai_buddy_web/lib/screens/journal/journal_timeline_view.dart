// Journal — C: timeline view (chronological list grouped by week).
// Split from journal_screen.dart (R1D14).

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/mood_provider.dart';
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/app_back_button.dart';
import '../../widgets/gq/gq.dart';
import '../weekly_review_screen.dart';
import 'journal_entry_view.dart';
import 'journal_models.dart';
import 'journal_shared.dart';

// ─────────────────────────────────────────────────────────────────────────────
// C — Timeline view
// ─────────────────────────────────────────────────────────────────────────────

enum _TimelineFilter { all, thisWeek, byTag }

class JournalTimelineView extends StatefulWidget {
  const JournalTimelineView({
    super.key,
    required this.entries,
    required this.onOpenEditor,
    required this.onDeleteEntry,
  });

  final List<JournalEntry> entries;
  final Future<void> Function({String? prefill}) onOpenEditor;
  final void Function(String id) onDeleteEntry;

  @override
  State<JournalTimelineView> createState() => _JournalTimelineViewState();
}

class _JournalTimelineViewState extends State<JournalTimelineView> {
  _TimelineFilter _filter = _TimelineFilter.all;

  List<JournalEntry> get _filtered {
    final now = DateTime.now();
    final weekStart = now.subtract(Duration(days: now.weekday - 1));
    switch (_filter) {
      case _TimelineFilter.all:
        return widget.entries;
      case _TimelineFilter.thisWeek:
        return widget.entries
            .where((e) => e.createdAt.isAfter(weekStart))
            .toList();
      case _TimelineFilter.byTag:
        // Tag filter: show entries that have at least one tag [assumed: first tag grouping]
        return widget.entries.where((e) => e.tags.isNotEmpty).toList();
    }
  }

  Map<String, List<JournalEntry>> _groupByWeek(List<JournalEntry> entries) {
    final now = DateTime.now();
    final Map<String, List<JournalEntry>> groups = {};
    for (final e in entries) {
      final diff = now.difference(e.createdAt).inDays;
      String label;
      if (diff < 7) {
        label = 'THIS WEEK';
      } else if (diff < 14) {
        label = 'LAST WEEK';
      } else {
        final weeksAgo = (diff / 7).floor();
        label = '$weeksAgo WEEKS AGO';
      }
      groups.putIfAbsent(label, () => []).add(e);
    }
    return groups;
  }

  void _openEntry(JournalEntry entry) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => JournalEntryView(
          entry: entry,
          onDelete: () {
            Navigator.of(context).pop();
            widget.onDeleteEntry(entry.id);
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final filtered = _filtered;
    final groups = _groupByWeek(filtered);

    return Scaffold(
      backgroundColor: t.bg,
      appBar: AppBar(
        backgroundColor: t.bg,
        elevation: 0,
        scrolledUnderElevation: 0,
        automaticallyImplyLeading: false,
        leading: Builder(
          builder: (ctx) {
            final canPop = Navigator.of(ctx).canPop();
            final route = ModalRoute.of(ctx);
            final isModal =
                route is PageRoute && route.fullscreenDialog == true;
            if (canPop) return AppBackButton(isModal: isModal);
            return const SizedBox.shrink();
          },
        ),
        title: Text(
          'Journal',
          style: TextStyle(
            fontFamily: GQTypography.displayFamily,
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: t.ink,
            letterSpacing: -0.3,
          ),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: _TimelineFilterControl(
              value: _filter,
              onChanged: (f) => setState(() => _filter = f),
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(height: 1, thickness: 1, color: t.hair),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => widget.onOpenEditor(),
        backgroundColor: GQColors.primaryDk,
        elevation: 6,
        child: const Icon(Icons.add, color: Colors.white, size: 22),
      ),
      body: filtered.isEmpty
          ? _EmptyFilterState(filter: _filter)
          : CustomScrollView(
              slivers: [
                // Stat strip
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                    child: _TimelineStatStrip(
                      count: widget.entries.length,
                    ),
                  ),
                ),
                // WO-6.1 Part B: temporary entry point relocated from the
                // old You-tab card — full Journal-tab composition (where
                // this naturally belongs) is its own work order.
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                    child: _WeeklyReviewEntryRow(),
                  ),
                ),
                // Week groups
                for (final label in groups.keys) ...[
                  SliverToBoxAdapter(
                    child: _WeekHeader(label: label),
                  ),
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, i) {
                        final entry = groups[label]![i];
                        return Padding(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                          child: _JournalEntryCard(
                            entry: entry,
                            onTap: () => _openEntry(entry),
                            onDelete: () => widget.onDeleteEntry(entry.id),
                          ),
                        );
                      },
                      childCount: groups[label]!.length,
                    ),
                  ),
                ],
                const SliverToBoxAdapter(child: SizedBox(height: 100)),
              ],
            ),
    );
  }
}

/// WO-6.1 Part B: temporary Weekly Review entry point. Pure navigation
/// (haptic: false, D7).
class _WeeklyReviewEntryRow extends StatelessWidget {
  const _WeeklyReviewEntryRow();

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return GQCard(
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => WeeklyReviewScreen(
            data: WeeklyReviewData.fromMoodEntries(
              Provider.of<MoodProvider>(context, listen: false).moodEntries,
            ),
          ),
        ),
      ),
      haptic: false,
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: t.primarySoft,
              borderRadius: BorderRadius.circular(11),
            ),
            child: Icon(Icons.insights_outlined,
                color: t.primary, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Weekly Review',
                    style: GQTypography.body.copyWith(
                        fontWeight: FontWeight.w700, color: t.ink)),
                const SizedBox(height: 2),
                Text('Your week, gently summarized',
                    style: GQTypography.caption.copyWith(color: t.ink2)),
              ],
            ),
          ),
          Icon(Icons.chevron_right_rounded,
              color: t.ink3, size: 24),
        ],
      ),
    );
  }
}

class _TimelineFilterControl extends StatelessWidget {
  const _TimelineFilterControl({
    required this.value,
    required this.onChanged,
  });

  final _TimelineFilter value;
  final void Function(_TimelineFilter) onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: const Color(0x1A667EEA),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _FilterBtn(label: 'All', active: value == _TimelineFilter.all,
              onTap: () => onChanged(_TimelineFilter.all)),
          _FilterBtn(label: 'Week', active: value == _TimelineFilter.thisWeek,
              onTap: () => onChanged(_TimelineFilter.thisWeek)),
          _FilterBtn(label: 'Tag', active: value == _TimelineFilter.byTag,
              onTap: () => onChanged(_TimelineFilter.byTag)),
        ],
      ),
    );
  }
}

class _FilterBtn extends StatelessWidget {
  const _FilterBtn({
    required this.label,
    required this.active,
    required this.onTap,
  });

  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: active ? t.surface : Colors.transparent,
          borderRadius: BorderRadius.circular(999),
          boxShadow: active
              ? [
                  const BoxShadow(
                    color: Color(0x0F1F1B3A),
                    blurRadius: 6,
                    offset: Offset(0, 2),
                  )
                ]
              : null,
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 11.5,
            fontWeight: FontWeight.w800,
            color: active ? t.ink : t.ink2,
          ),
        ),
      ),
    );
  }
}

class _TimelineStatStrip extends StatelessWidget {
  const _TimelineStatStrip({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: const Color(0x14667EEA),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$count ${count == 1 ? 'ENTRY' : 'ENTRIES'}',
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: GQColors.primaryDk,
              letterSpacing: 0.3,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            '·',
            style: TextStyle(
              fontSize: 10,
              color: t.ink2,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            'last 30 days',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: t.ink2,
            ),
          ),
        ],
      ),
    );
  }
}

class _WeekHeader extends StatelessWidget {
  const _WeekHeader({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 14, 22, 8),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 11,
          fontWeight: FontWeight.w800,
          color: t.ink2,
          letterSpacing: 0.6,
        ),
      ),
    );
  }
}

class _JournalEntryCard extends StatelessWidget {
  const _JournalEntryCard({
    required this.entry,
    required this.onTap,
    required this.onDelete,
  });

  final JournalEntry entry;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final dotColor = moodColor(entry.mood);
    final timeStr = formatTime(entry.createdAt);
    final dayStr = formatDay(entry.createdAt);
    final wordCount = entry.body.trim().split(RegExp(r'\s+')).length;

    return GestureDetector(
      onTap: onTap,
      onLongPress: () => _showContextMenu(context),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: t.surface,
          border: Border.all(color: t.hair),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Mood dot
            Container(
              width: 11,
              height: 11,
              margin: const EdgeInsets.only(top: 5),
              decoration: BoxDecoration(
                color: dotColor,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '$dayStr · $timeStr',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: t.ink2,
                      letterSpacing: 0.4,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    entry.body,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontFamily: GQTypography.journalSerif,
                      fontSize: 13.5,
                      color: t.ink,
                      height: 1.4,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      if (entry.tags.isNotEmpty)
                        Text(
                          '· ${entry.tags.length} ${entry.tags.length == 1 ? 'tag' : 'tags'}',
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 10.5,
                            color: t.ink2,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      const SizedBox(width: 8),
                      Text(
                        '· $wordCount ${wordCount == 1 ? 'word' : 'words'}',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 10.5,
                          color: t.ink2,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showContextMenu(BuildContext context) {
    final t = GQTheme.of(context);
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: Icon(Icons.delete_outline, color: t.coral),
              title: Text(
                'Delete entry',
                style: TextStyle(color: t.coral),
              ),
              onTap: () {
                Navigator.of(context).pop();
                onDelete();
              },
            ),
            ListTile(
              leading: Icon(Icons.close, color: t.ink2),
              title: const Text('Cancel'),
              onTap: () => Navigator.of(context).pop(),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyFilterState extends StatelessWidget {
  const _EmptyFilterState({required this.filter});

  final _TimelineFilter filter;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0x0D667EEA),
            border: Border.all(
              color: const Color(0x33667EEA),
              style: BorderStyle.solid,
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'No entries with that tag yet.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                  color: t.ink,
                  letterSpacing: -0.2,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Try writing one.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w600,
                  color: t.ink2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
