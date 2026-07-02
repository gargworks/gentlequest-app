import 'package:flutter/material.dart';
import '../../models/body_double_session.dart';
import '../../theme/gq_tokens.dart';

/// BodyDoubleStartSheet — v1.5.0 ADHD Update, Workstream 2a.
///
/// Modal bottom sheet where the user names a task and picks a duration
/// before starting a body-doubling session. Follows the same
/// `showXSheet(context)` convention as `showSafetyLegalSheet` /
/// `showProfileNavSheet`.
///
/// Returns null if dismissed without starting (Close / swipe-down /
/// tap-outside). No analytics fire for a dismissal — `body_double_started`
/// is only logged by the caller at the real action site (the Start button
/// tap), once this Future resolves with a non-null config.
Future<BodyDoubleSessionConfig?> showBodyDoubleStartSheet(
    BuildContext context) {
  return showModalBottomSheet<BodyDoubleSessionConfig>(
    context: context,
    showDragHandle: true,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    builder: (ctx) => const _BodyDoubleStartSheetContent(),
  );
}

class _BodyDoubleStartSheetContent extends StatefulWidget {
  const _BodyDoubleStartSheetContent();

  @override
  State<_BodyDoubleStartSheetContent> createState() =>
      _BodyDoubleStartSheetContentState();
}

class _BodyDoubleStartSheetContentState
    extends State<_BodyDoubleStartSheetContent> {
  final TextEditingController _taskController = TextEditingController();
  int _selectedMinutes = kBodyDoubleDurationPresetsMinutes[1]; // default 10

  @override
  void dispose() {
    _taskController.dispose();
    super.dispose();
  }

  void _start() {
    final task = _taskController.text.trim();
    Navigator.of(context).pop(
      BodyDoubleSessionConfig(
        task: task.isEmpty ? 'this' : task,
        duration: Duration(minutes: _selectedMinutes),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SafeArea(
      top: false,
      child: Padding(
        padding: EdgeInsets.only(
          left: 16.0,
          right: 16.0,
          bottom: MediaQuery.of(context).viewInsets.bottom + 16.0,
          top: 8.0,
        ),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Focus together',
                      style: theme.textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Close',
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                "I'll stay with you while you work — no streaks, no "
                'pressure. Just tell me what you\'re doing and I\'ll check '
                'in along the way.',
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: GQColors.ink2),
              ),
              const SizedBox(height: 20),
              Text(
                'What are we doing?',
                style: theme.textTheme.labelLarge
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              TextField(
                key: const Key('body_double_task_field'),
                controller: _taskController,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: 'e.g. tidy the kitchen, answer emails…',
                  filled: true,
                  fillColor: GQColors.softBg,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(GQRadii.card),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 12),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'For how long?',
                style: theme.textTheme.labelLarge
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: kBodyDoubleDurationPresetsMinutes.map((minutes) {
                  final selected = minutes == _selectedMinutes;
                  return ChoiceChip(
                    label: Text('$minutes min'),
                    selected: selected,
                    onSelected: (_) =>
                        setState(() => _selectedMinutes = minutes),
                    selectedColor: GQColors.primarySoft,
                    labelStyle: TextStyle(
                      color: selected ? GQColors.primaryDk : GQColors.ink2,
                      fontWeight: FontWeight.w700,
                    ),
                    side: BorderSide(
                      color: selected ? GQColors.primary : GQColors.hair,
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  key: const Key('body_double_start_button'),
                  onPressed: _start,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: GQColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(GQRadii.button),
                    ),
                  ),
                  child: Text('Start $_selectedMinutes-minute session'),
                ),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}
