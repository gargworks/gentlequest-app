// R1D14 — Journal
// Design source: docs/design/refs/htmls/GentleQuest_Journal.html
// REVIEW.md tier: R1D14 (Tier 2)
//
// Three views:
//   A — Empty state  (entries.isEmpty)
//   B — Entry view   (read/edit a single entry)
//   C — Timeline     (chronological list, grouped by week)
//
// Backend persistence: OUT OF SCOPE for this PR.
// Entries are held in-memory only. Encrypted local storage
// (sqflite_sqlcipher or flutter_secure_storage) is a follow-up task
// per REVIEW.md §Implementation Notes #6.
//
// Font notes [assumed]: Fraunces (serif, entry body) and Caveat (handwritten,
// chip starters / notebook scribble) are not included as Flutter font assets.
// System default (sans-serif) is used as the cross-platform fallback until the
// fonts are added to pubspec.yaml + assets/fonts/. Flag for Lokesh review.

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../theme/gq_tokens.dart';
import '../widgets/app_back_button.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Data model + on-device persistence (SharedPreferences).
// Backend journaling API not yet wired — entries stay on the device.
// ─────────────────────────────────────────────────────────────────────────────

enum JournalMood { great, good, okay, meh, rough }

String _moodToKey(JournalMood? m) => switch (m) {
      JournalMood.great => 'great',
      JournalMood.good => 'good',
      JournalMood.okay => 'okay',
      JournalMood.meh => 'meh',
      JournalMood.rough => 'rough',
      null => '',
    };

JournalMood? _moodFromKey(String? k) => switch (k) {
      'great' => JournalMood.great,
      'good' => JournalMood.good,
      'okay' => JournalMood.okay,
      'meh' => JournalMood.meh,
      'rough' => JournalMood.rough,
      _ => null,
    };

/// JournalStorage — on-device persistence for JournalEntry list.
///
/// Backend journaling API is not yet wired; entries live on the device under
/// a single SharedPreferences key. Once the API ships, this class becomes the
/// migration point: load() can pull from server, save() can dual-write.
class JournalStorage {
  static const _key = 'journal_entries_v1';

  static Future<List<JournalEntry>> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_key);
      if (raw == null || raw.isEmpty) return [];
      final List<dynamic> arr = jsonDecode(raw) as List<dynamic>;
      return arr
          .whereType<Map<String, dynamic>>()
          .map(JournalEntry.fromJson)
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<void> save(List<JournalEntry> entries) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = jsonEncode(entries.map((e) => e.toJson()).toList());
      await prefs.setString(_key, raw);
    } catch (_) {
      // Silent — caller already has the entry in memory; next save will retry.
    }
  }

  /// Append a single entry to the persisted list. Returns the updated list.
  /// Used by mood_reflection_sheet so reflections aren't silently discarded.
  static Future<List<JournalEntry>> append(JournalEntry entry) async {
    final entries = await load();
    entries.insert(0, entry);
    await save(entries);
    return entries;
  }
}

class JournalEntry {
  JournalEntry({
    required this.id,
    required this.body,
    required this.createdAt,
    this.mood,
    this.tags = const [],
  });

  final String id;
  final String body;
  final DateTime createdAt;
  final JournalMood? mood;
  final List<String> tags;

  JournalEntry copyWith({
    String? body,
    JournalMood? mood,
    List<String>? tags,
  }) =>
      JournalEntry(
        id: id,
        body: body ?? this.body,
        createdAt: createdAt,
        mood: mood ?? this.mood,
        tags: tags ?? this.tags,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'body': body,
        'createdAt': createdAt.toIso8601String(),
        'mood': _moodToKey(mood),
        'tags': tags,
      };

  factory JournalEntry.fromJson(Map<String, dynamic> j) => JournalEntry(
        id: j['id'] as String,
        body: j['body'] as String,
        createdAt: DateTime.parse(j['createdAt'] as String),
        mood: _moodFromKey(j['mood'] as String?),
        tags: (j['tags'] as List<dynamic>? ?? [])
            .whereType<String>()
            .toList(),
      );
}

Color _moodColor(JournalMood? mood) {
  switch (mood) {
    case JournalMood.great:
      return GQColors.moodGreat;
    case JournalMood.good:
      return GQColors.moodGood;
    case JournalMood.okay:
      return GQColors.moodOkay;
    case JournalMood.meh:
      return GQColors.moodMeh;
    case JournalMood.rough:
      return GQColors.moodRough;
    case null:
      return GQColors.ink3;
  }
}

String _moodLabel(JournalMood? mood) {
  switch (mood) {
    case JournalMood.great:
      return 'Great';
    case JournalMood.good:
      return 'Good';
    case JournalMood.okay:
      return 'Okay';
    case JournalMood.meh:
      return 'Meh';
    case JournalMood.rough:
      return 'Rough';
    case null:
      return '';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// JournalScreen — root screen
// Routes to empty state (A) or timeline (C) based on entry count.
// ─────────────────────────────────────────────────────────────────────────────

class JournalScreen extends StatefulWidget {
  const JournalScreen({super.key});

  @override
  State<JournalScreen> createState() => _JournalScreenState();
}

class _JournalScreenState extends State<JournalScreen> {
  List<JournalEntry> _entries = [];
  bool _loaded = false;

  @override
  void initState() {
    super.initState();
    _loadEntries();
  }

  Future<void> _loadEntries() async {
    final loaded = await JournalStorage.load();
    if (!mounted) return;
    setState(() {
      _entries = loaded;
      _loaded = true;
    });
  }

  void _addEntry(String body) {
    if (body.trim().isEmpty) return;
    setState(() {
      _entries.insert(
        0,
        JournalEntry(
          id: DateTime.now().toIso8601String(),
          body: body.trim(),
          createdAt: DateTime.now(),
        ),
      );
    });
    JournalStorage.save(_entries);
  }

  void _deleteEntry(String id) {
    setState(() {
      _entries.removeWhere((e) => e.id == id);
    });
    JournalStorage.save(_entries);
  }

  Future<void> _openEditor({String? prefill}) async {
    final result = await Navigator.of(context).push<String>(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) =>
            _JournalEditorSheet(initialText: prefill ?? ''),
        transitionsBuilder: (_, anim, __, child) {
          final slide = Tween<Offset>(
            begin: const Offset(0, 1),
            end: Offset.zero,
          ).animate(CurvedAnimation(parent: anim, curve: Curves.easeOut));
          final fade = Tween<double>(begin: 0, end: 1)
              .animate(CurvedAnimation(parent: anim, curve: Curves.easeIn));
          return SlideTransition(
            position: slide,
            child: FadeTransition(opacity: fade, child: child),
          );
        },
        transitionDuration: const Duration(milliseconds: 220),
      ),
    );
    if (result != null) _addEntry(result);
  }

  @override
  Widget build(BuildContext context) {
    // First frame after navigation: show a placeholder while SharedPreferences
    // load. Without this, the screen briefly flashes the empty state even when
    // entries exist on device — a small but jarring blink.
    if (!_loaded) {
      return Scaffold(
        backgroundColor: GQColors.softBg,
        body: const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      );
    }
    if (_entries.isEmpty) {
      return _JournalEmptyState(onStartEntry: _openEditor);
    }
    return _JournalTimelineView(
      entries: _entries,
      onOpenEditor: _openEditor,
      onDeleteEntry: _deleteEntry,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// A — Empty state
// ─────────────────────────────────────────────────────────────────────────────

class _JournalEmptyState extends StatelessWidget {
  const _JournalEmptyState({required this.onStartEntry});

  final Future<void> Function({String? prefill}) onStartEntry;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: AppBar(
        backgroundColor: GQColors.softBg,
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
        title: const Text(
          'Journal',
          style: TextStyle(
            fontFamily: GQTypography.displayFamily,
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: GQColors.ink,
            letterSpacing: -0.3,
          ),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: _NavIconButton(
              backgroundColor: GQColors.primarySoft,
              borderColor: Color(0x33667EEA),
              onTap: () => onStartEntry(),
              child: const Icon(
                Icons.add,
                size: 16,
                color: GQColors.primaryDk,
              ),
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(
            height: 1,
            thickness: 1,
            color: GQColors.hair,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 6, 16, 30),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Notebook + leaf illustration
            _EmptyStateIllustration(),
            const SizedBox(height: 18),

            // Headline + sub
            const Text(
              "What's worth remembering?",
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.w600,
                color: GQColors.ink,
                letterSpacing: -0.6,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 8),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Text(
                "Even one line is a journal. We'll keep it for you.",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                  color: GQColors.ink2,
                  height: 1.5,
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Chip starters
            _StarterChips(onStartEntry: onStartEntry),
            const SizedBox(height: 18),

            // Start an entry CTA
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => onStartEntry(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: GQColors.primary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shadowColor: Colors.transparent,
                  padding: const EdgeInsets.symmetric(vertical: 15),
                  shape: const StadiumBorder(),
                  textStyle: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 14.5,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.2,
                  ),
                ),
                child: const Text('Start an entry'),
              ),
            ),
            const SizedBox(height: 14),

            // Privacy footer
            Center(
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0x0F667EEA),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    Icon(
                      Icons.lock_outline,
                      size: 11,
                      color: GQColors.ink2,
                    ),
                    SizedBox(width: 5),
                    Text(
                      'Stays on your device. Never synced. Never shared.',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink2,
                        letterSpacing: 0.2,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Notebook illustration (static, no animation per widget map)
// ─────────────────────────────────────────────────────────────────────────────

class _EmptyStateIllustration extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: SizedBox(
        width: 200,
        height: 160,
        child: Stack(
          children: [
            // Page
            Positioned.fill(
              child: Transform.rotate(
                angle: -0.052, // ~-3 degrees
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(6),
                      bottomLeft: Radius.circular(6),
                      topRight: Radius.circular(16),
                      bottomRight: Radius.circular(16),
                    ),
                    border: Border.all(
                      color: const Color(0x1A1F1B3A),
                      width: 1,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x4D667EEA),
                        blurRadius: 40,
                        offset: Offset(0, 16),
                        spreadRadius: -12,
                      ),
                      BoxShadow(
                        color: Color(0x0A1F1B3A),
                        blurRadius: 8,
                        offset: Offset(0, 4),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            // Spine binding dots (left edge)
            Positioned(
              left: 0,
              top: 14,
              bottom: 14,
              width: 8,
              child: Transform.rotate(
                angle: -0.052,
                child: CustomPaint(painter: _SpinePainter()),
              ),
            ),
            // Red margin line
            Positioned(
              left: 20,
              top: 0,
              bottom: 0,
              width: 1,
              child: Transform.rotate(
                angle: -0.052,
                child: Container(
                  color: const Color(0x4DFF6B6B),
                ),
              ),
            ),
            // Lines on page
            Positioned(
              left: 36,
              right: 16,
              top: 24,
              bottom: 18,
              child: Transform.rotate(
                angle: -0.052,
                child: CustomPaint(painter: _LinedPagePainter()),
              ),
            ),
            // Handwritten scribble text
            Positioned(
              left: 50,
              top: 36,
              child: Transform.rotate(
                angle: -0.052,
                child: const _NotebookScribble(),
              ),
            ),
            // Leaf SVG (top-right)
            Positioned(
              right: -10,
              top: 18,
              child: Transform.rotate(
                angle: 0.489, // ~28 degrees
                child: const _LeafIcon(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SpinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0x1A1F1B3A)
      ..strokeWidth = 1;
    double y = 0;
    while (y < size.height) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
      y += 9;
    }
  }

  @override
  bool shouldRepaint(_SpinePainter old) => false;
}

class _LinedPagePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0x0F1F1B3A)
      ..strokeWidth = 1;
    double y = 18;
    while (y < size.height) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
      y += 18;
    }
  }

  @override
  bool shouldRepaint(_LinedPagePainter old) => false;
}

// Handwritten-style scribble text rendered as small colored text
// [assumed] Uses Inter since Caveat font is not in assets.
class _NotebookScribble extends StatelessWidget {
  const _NotebookScribble();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        Text(
          'walking helped',
          style: TextStyle(
            fontSize: 12,
            color: Color(0x8C667EEA),
            fontStyle: FontStyle.italic,
          ),
        ),
        SizedBox(height: 4),
        Text(
          'boundaries felt good',
          style: TextStyle(
            fontSize: 12,
            color: Color(0x8C667EEA),
            fontStyle: FontStyle.italic,
          ),
        ),
        SizedBox(height: 4),
        Text(
          'bed by 10',
          style: TextStyle(
            fontSize: 12,
            color: Color(0x8C667EEA),
            fontStyle: FontStyle.italic,
          ),
        ),
      ],
    );
  }
}

class _LeafIcon extends StatelessWidget {
  const _LeafIcon();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 56,
      height: 56,
      child: CustomPaint(painter: _LeafPainter()),
    );
  }
}

class _LeafPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final fillPaint = Paint()
      ..color = GQColors.moodGreat.withValues(alpha: 0.85)
      ..style = PaintingStyle.fill;
    final strokePaint = Paint()
      ..color = const Color(0xFF5C7A48)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeJoin = StrokeJoin.round;
    final linePaint = Paint()
      ..color = const Color(0xFF5C7A48)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round;

    // Leaf body
    final path = Path()
      ..moveTo(48, 8)
      ..cubicTo(26, 8, 12, 22, 12, 40)
      ..cubicTo(12, 44, 13, 48, 14, 50)
      ..cubicTo(16, 49, 20, 48, 24, 48)
      ..cubicTo(42, 48, 56, 34, 56, 12)
      ..cubicTo(56, 10, 55, 8, 54, 8)
      ..cubicTo(52, 8, 50, 9, 48, 8)
      ..close();
    canvas.drawPath(path, fillPaint);
    canvas.drawPath(path, strokePaint);

    // Central vein
    canvas.drawLine(
      const Offset(14, 50),
      const Offset(44, 20),
      linePaint,
    );
  }

  @override
  bool shouldRepaint(_LeafPainter old) => false;
}

// ─────────────────────────────────────────────────────────────────────────────
// Starter chips (A) — three prompt starters; tap pre-fills editor
// ─────────────────────────────────────────────────────────────────────────────

class _StarterChips extends StatelessWidget {
  const _StarterChips({required this.onStartEntry});

  final Future<void> Function({String? prefill}) onStartEntry;

  static const _prompts = [
    ('a', 'Today, what worked was…'),
    ('b', 'I noticed myself…'),
    ('c', 'I want to remember…'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: _prompts
          .map(
            (p) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _StarterChip(
                label: p.$1,
                text: p.$2,
                onTap: () => onStartEntry(prefill: p.$2),
              ),
            ),
          )
          .toList(),
    );
  }
}

class _StarterChip extends StatelessWidget {
  const _StarterChip({
    required this.label,
    required this.text,
    required this.onTap,
  });

  final String label;
  final String text;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: GQColors.hair),
        ),
        child: Row(
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: GQColors.primarySoft,
                borderRadius: BorderRadius.circular(9),
              ),
              alignment: Alignment.center,
              child: Text(
                label,
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: GQColors.primaryDk,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                text,
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                  color: GQColors.ink,
                  letterSpacing: 0.2,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// C — Timeline view
// ─────────────────────────────────────────────────────────────────────────────

enum _TimelineFilter { all, thisWeek, byTag }

class _JournalTimelineView extends StatefulWidget {
  const _JournalTimelineView({
    required this.entries,
    required this.onOpenEditor,
    required this.onDeleteEntry,
  });

  final List<JournalEntry> entries;
  final Future<void> Function({String? prefill}) onOpenEditor;
  final void Function(String id) onDeleteEntry;

  @override
  State<_JournalTimelineView> createState() => _JournalTimelineViewState();
}

class _JournalTimelineViewState extends State<_JournalTimelineView> {
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
        builder: (_) => _JournalEntryView(
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
    final filtered = _filtered;
    final groups = _groupByWeek(filtered);

    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: AppBar(
        backgroundColor: GQColors.softBg,
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
        title: const Text(
          'Journal',
          style: TextStyle(
            fontFamily: GQTypography.displayFamily,
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: GQColors.ink,
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
          child: Divider(height: 1, thickness: 1, color: GQColors.hair),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => widget.onOpenEditor(),
        backgroundColor: GQColors.primary,
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
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: active ? Colors.white : Colors.transparent,
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
            color: active ? GQColors.ink : GQColors.ink2,
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
          const Text(
            '·',
            style: TextStyle(
              fontSize: 10,
              color: GQColors.ink3,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(width: 6),
          const Text(
            'last 30 days',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: GQColors.ink2,
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
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 14, 22, 8),
      child: Text(
        label,
        style: const TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 11,
          fontWeight: FontWeight.w800,
          color: GQColors.ink3,
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
    final moodColor = _moodColor(entry.mood);
    final timeStr = _formatTime(entry.createdAt);
    final dayStr = _formatDay(entry.createdAt);
    final wordCount = entry.body.trim().split(RegExp(r'\s+')).length;

    return GestureDetector(
      onTap: onTap,
      onLongPress: () => _showContextMenu(context),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: GQColors.hair),
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
                color: moodColor,
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
                    style: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink3,
                      letterSpacing: 0.4,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    entry.body,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 13.5,
                      color: GQColors.ink,
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
                          style: const TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 10.5,
                            color: GQColors.ink3,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      const SizedBox(width: 8),
                      Text(
                        '· $wordCount ${wordCount == 1 ? 'word' : 'words'}',
                        style: const TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 10.5,
                          color: GQColors.ink3,
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
              leading: const Icon(Icons.delete_outline, color: GQColors.coral),
              title: const Text(
                'Delete entry',
                style: TextStyle(color: GQColors.coral),
              ),
              onTap: () {
                Navigator.of(context).pop();
                onDelete();
              },
            ),
            ListTile(
              leading: const Icon(Icons.close, color: GQColors.ink2),
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
            children: const [
              Text(
                'No entries with that tag yet.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                  color: GQColors.ink,
                  letterSpacing: -0.2,
                ),
              ),
              SizedBox(height: 4),
              Text(
                'Try writing one.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w600,
                  color: GQColors.ink2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// B — Entry view (read-only; edit via overflow)
// ─────────────────────────────────────────────────────────────────────────────

class _JournalEntryView extends StatelessWidget {
  const _JournalEntryView({
    required this.entry,
    required this.onDelete,
  });

  final JournalEntry entry;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final moodColor = _moodColor(entry.mood);
    final moodLabel = _moodLabel(entry.mood);
    final timeStr = _formatTime(entry.createdAt);
    final dateStr = _formatDateLong(entry.createdAt);

    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: AppBar(
        backgroundColor: GQColors.softBg,
        elevation: 0,
        scrolledUnderElevation: 0,
        automaticallyImplyLeading: false,
        leading: AppBackButton(),
        title: Text(
          dateStr,
          style: const TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 15,
            fontWeight: FontWeight.w800,
            color: GQColors.ink,
            letterSpacing: -0.3,
          ),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Row(
              children: [
                _NavIconButton(
                  onTap: () => _confirmDelete(context),
                  child: const Icon(
                    Icons.more_horiz,
                    size: 16,
                    color: GQColors.ink2,
                  ),
                ),
              ],
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(height: 1, thickness: 1, color: GQColors.hair),
        ),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Mood halo strip
            if (entry.mood != null)
              Container(
                height: 6,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      moodColor.withValues(alpha: 0.0),
                      moodColor.withValues(alpha: 0.85),
                      moodColor.withValues(alpha: 0.85),
                      moodColor.withValues(alpha: 0.0),
                    ],
                    stops: const [0.0, 0.3, 0.7, 1.0],
                  ),
                ),
              ),

            // Mood pill + time
            if (entry.mood != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
                child: Row(
                  children: [
                    _MoodPill(
                      moodColor: moodColor,
                      label: moodLabel,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      timeStr,
                      style: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),

            // Entry body
            Padding(
              padding: const EdgeInsets.fromLTRB(22, 8, 22, 16),
              child: Text(
                entry.body,
                style: const TextStyle(
                  fontSize: 17,
                  height: 1.7,
                  color: GQColors.ink,
                  fontWeight: FontWeight.w400,
                  letterSpacing: -0.1,
                ),
              ),
            ),

            // Auto tags (from entry)
            if (entry.tags.isNotEmpty) ...[
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 0, 18, 6),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'DETECTED · ON-DEVICE',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink3,
                        letterSpacing: 0.7,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: entry.tags
                          .map(
                            (t) => Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 5),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                border: Border.all(color: GQColors.hair),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Text(
                                    '#',
                                    style: TextStyle(
                                      fontFamily: GQTypography.bodyFamily,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w800,
                                      color: GQColors.primaryDk,
                                    ),
                                  ),
                                  Text(
                                    t,
                                    style: const TextStyle(
                                      fontFamily: GQTypography.bodyFamily,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w700,
                                      color: GQColors.ink2,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  void _confirmDelete(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 20, 20, 8),
              child: Text(
                'Delete this entry?',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: GQColors.ink,
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 0, 20, 16),
              child: Text(
                'This cannot be undone.',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  color: GQColors.ink3,
                ),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.delete_outline, color: GQColors.coral),
              title: const Text(
                'Delete',
                style: TextStyle(color: GQColors.coral, fontWeight: FontWeight.w700),
              ),
              onTap: () {
                Navigator.of(context).pop();
                onDelete();
              },
            ),
            ListTile(
              leading: const Icon(Icons.close, color: GQColors.ink2),
              title: const Text('Cancel'),
              onTap: () => Navigator.of(context).pop(),
            ),
          ],
        ),
      ),
    );
  }
}

class _MoodPill extends StatelessWidget {
  const _MoodPill({required this.moodColor, required this.label});

  final Color moodColor;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: moodColor.withValues(alpha: 0.18),
        border: Border.all(color: moodColor.withValues(alpha: 0.35)),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(
              color: moodColor,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            'Mood · $label',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: moodColor.darken(0.3),
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Journal editor sheet (slide-up; used by A, C, and entry view)
// ─────────────────────────────────────────────────────────────────────────────

class _JournalEditorSheet extends StatefulWidget {
  const _JournalEditorSheet({required this.initialText});

  final String initialText;

  @override
  State<_JournalEditorSheet> createState() => _JournalEditorSheetState();
}

class _JournalEditorSheetState extends State<_JournalEditorSheet> {
  late final TextEditingController _ctrl;
  late final FocusNode _focus;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.initialText);
    _focus = FocusNode();
    // Request keyboard in same frame as reveal (per widget map)
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _focus.requestFocus();
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _focus.dispose();
    super.dispose();
  }

  void _save() {
    final text = _ctrl.text.trim();
    Navigator.of(context).pop(text.isNotEmpty ? text : null);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: AppBar(
        backgroundColor: GQColors.softBg,
        elevation: 0,
        scrolledUnderElevation: 0,
        automaticallyImplyLeading: false,
        leading: _NavIconButton(
          onTap: _save,
          child: const Icon(
            Icons.arrow_back_ios_new,
            size: 14,
            color: GQColors.ink,
          ),
        ),
        title: Text(
          _formatDateLong(DateTime.now()),
          style: const TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 15,
            fontWeight: FontWeight.w700,
            color: GQColors.ink2,
          ),
        ),
        actions: [
          TextButton(
            onPressed: _save,
            child: const Text(
              'Save',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 14,
                fontWeight: FontWeight.w700,
                color: GQColors.primaryDk,
              ),
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(height: 1, thickness: 1, color: GQColors.hair),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
        child: TextField(
          controller: _ctrl,
          focusNode: _focus,
          maxLines: null,
          keyboardType: TextInputType.multiline,
          textCapitalization: TextCapitalization.sentences,
          style: const TextStyle(
            fontSize: 17,
            height: 1.7,
            color: GQColors.ink,
            fontWeight: FontWeight.w400,
            letterSpacing: -0.1,
          ),
          decoration: const InputDecoration(
            border: InputBorder.none,
            hintText: 'What\'s on your mind…',
            hintStyle: TextStyle(
              fontSize: 17,
              height: 1.7,
              color: GQColors.ink3,
              fontWeight: FontWeight.w400,
            ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared nav icon button (matches HTML .nav-icon-btn)
// ─────────────────────────────────────────────────────────────────────────────

class _NavIconButton extends StatelessWidget {
  const _NavIconButton({
    required this.onTap,
    required this.child,
    this.backgroundColor = Colors.white,
    this.borderColor = GQColors.hair,
  });

  final VoidCallback onTap;
  final Widget child;
  final Color backgroundColor;
  final Color borderColor;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: backgroundColor,
          shape: BoxShape.circle,
          border: Border.all(color: borderColor),
        ),
        alignment: Alignment.center,
        child: child,
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Date / time formatting helpers
// ─────────────────────────────────────────────────────────────────────────────

String _formatTime(DateTime dt) {
  final hour = dt.hour > 12
      ? dt.hour - 12
      : dt.hour == 0
          ? 12
          : dt.hour;
  final min = dt.minute.toString().padLeft(2, '0');
  final ampm = dt.hour >= 12 ? 'PM' : 'AM';
  return '$hour:$min $ampm';
}

String _formatDay(DateTime dt) {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];
  return '${days[dt.weekday - 1]} · ${months[dt.month - 1]} ${dt.day}';
}

String _formatDateLong(DateTime dt) {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];
  return '${days[dt.weekday - 1]}, ${months[dt.month - 1]} ${dt.day}';
}

// ─────────────────────────────────────────────────────────────────────────────
// Color extension: darken helper for mood pill text
// ─────────────────────────────────────────────────────────────────────────────

extension _ColorDarken on Color {
  Color darken(double amount) {
    assert(amount >= 0 && amount <= 1);
    final hsl = HSLColor.fromColor(this);
    return hsl.withLightness((hsl.lightness - amount).clamp(0.0, 1.0)).toColor();
  }
}
