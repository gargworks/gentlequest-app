// Journal — B: entry view (read-only) + editor sheet + openJournalEntry
// route-in for external callers. Split from journal_screen.dart (R1D14).

import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';
import '../../widgets/app_back_button.dart';
import 'journal_models.dart';
import 'journal_shared.dart';

/// Public entry point for callers outside Journal (e.g. Weekly Review's
/// standout-card tap-target) to open a specific entry's reader view.
/// Wraps [JournalEntryView] in a Scaffold route so callers don't need
/// to assemble the reader chrome themselves.
///
/// [onDelete] defaults to JournalStorage.remove(entry.id) then pop —
/// preserves the "delete from anywhere" semantic so the in-view trash
/// icon remains functional when opened via Weekly Review tap.
Future<void> openJournalEntry(
  BuildContext context,
  JournalEntry entry, {
  VoidCallback? onDelete,
}) {
  return Navigator.of(context).push(MaterialPageRoute(
    builder: (ctx) => Scaffold(
      body: SafeArea(
        child: JournalEntryView(
          entry: entry,
          onDelete: onDelete ??
              () async {
                await JournalStorage.remove(entry.id);
                if (ctx.mounted) Navigator.of(ctx).pop();
              },
        ),
      ),
    ),
  ));
}

// ─────────────────────────────────────────────────────────────────────────────
// B — Entry view (read-only; edit via overflow)
// ─────────────────────────────────────────────────────────────────────────────

class JournalEntryView extends StatelessWidget {
  const JournalEntryView({
    super.key,
    required this.entry,
    required this.onDelete,
  });

  final JournalEntry entry;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final moodTint = moodColor(entry.mood);
    final moodName = moodLabel(entry.mood);
    final timeStr = formatTime(entry.createdAt);
    final dateStr = formatDateLong(entry.createdAt);

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
                NavIconButton(
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
                      moodTint.withValues(alpha: 0.0),
                      moodTint.withValues(alpha: 0.85),
                      moodTint.withValues(alpha: 0.85),
                      moodTint.withValues(alpha: 0.0),
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
                      moodColor: moodTint,
                      label: moodName,
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

            // Entry body — R1D14 serif intimacy (Fraunces)
            Padding(
              padding: const EdgeInsets.fromLTRB(22, 8, 22, 16),
              child: Text(
                entry.body,
                style: const TextStyle(
                  fontFamily: GQTypography.journalSerif,
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

class JournalEditorSheet extends StatefulWidget {
  const JournalEditorSheet({super.key, required this.initialText});

  final String initialText;

  @override
  State<JournalEditorSheet> createState() => _JournalEditorSheetState();
}

class _JournalEditorSheetState extends State<JournalEditorSheet> {
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
        leading: NavIconButton(
          onTap: _save,
          child: const Icon(
            Icons.arrow_back_ios_new,
            size: 14,
            color: GQColors.ink,
          ),
        ),
        title: Text(
          formatDateLong(DateTime.now()),
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
