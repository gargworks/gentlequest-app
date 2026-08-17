import 'package:flutter/material.dart';
import '../../models/body_double_session.dart';
import '../../theme/gq_tokens.dart';

/// BodyDoubleStartSheet — Fable #4: Shared Solitude.
///
/// Modal bottom sheet where the user names an intention and picks a duration
/// before sitting down in the shared-solitude room. Follows the same
/// `showXSheet(context)` convention as `showSafetyLegalSheet` /
/// `showProfileNavSheet`.
///
/// Returns null if dismissed without starting (Close / swipe-down /
/// tap-outside). The inverted design replaces the v1.5.0 "Focus together"
/// framing with "Sit with company" — a room, not a timer.
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

/// Sentinel duration meaning "no fixed end — step out when I leave."
/// Encoded as a very large Duration so the existing tick-based controller
/// in `InteractiveChatScreen` simply never reaches zero in practice; the
/// SharedSolitudeSpace "Step out" button is the real exit path for this mode.
const Duration kBodyDoubleOpenEnded = Duration(days: 365);

class _BodyDoubleStartSheetContent extends StatefulWidget {
  const _BodyDoubleStartSheetContent();

  @override
  State<_BodyDoubleStartSheetContent> createState() =>
      _BodyDoubleStartSheetContentState();
}

class _BodyDoubleStartSheetContentState
    extends State<_BodyDoubleStartSheetContent> {
  final TextEditingController _taskController = TextEditingController();

  /// Index into [_durationOptions]. Default to 50 min (index 1).
  int _selectedDurationIndex = 1;

  /// Fake-door toggle: "Just me" (default, unchanged behavior) vs
  /// "With someone" (tags the session for the live-interest signal — see
  /// [BodyDoubleSessionConfig.wantsLive]). No real matching exists yet;
  /// this only measures demand before a matching backend gets built.
  bool _wantsLive = false;

  static const List<_DurationOption> _durationOptions = [
    _DurationOption(label: '25 min', duration: Duration(minutes: 25)),
    _DurationOption(label: '50 min', duration: Duration(minutes: 50)),
    _DurationOption(label: 'When I leave', duration: kBodyDoubleOpenEnded),
  ];

  @override
  void dispose() {
    _taskController.dispose();
    super.dispose();
  }

  void _sitDown() {
    final task = _taskController.text.trim();
    Navigator.of(context).pop(
      BodyDoubleSessionConfig(
        task: task.isEmpty ? 'this' : task,
        duration: _durationOptions[_selectedDurationIndex].duration,
        wantsLive: _wantsLive,
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
                      'Sit with company',
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
                'Work next to others, quietly. Nobody sees you. '
                "Nobody counts you. Quest sits too.",
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: GQColors.ink2),
              ),
              const SizedBox(height: 20),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  ChoiceChip(
                    key: const Key('body_double_solo_chip'),
                    label: const Text('Just me'),
                    selected: !_wantsLive,
                    onSelected: (_) => setState(() => _wantsLive = false),
                    selectedColor: GQColors.primarySoft,
                    labelStyle: TextStyle(
                      color: !_wantsLive ? GQColors.primaryDk : GQColors.ink2,
                      fontWeight: FontWeight.w700,
                    ),
                    side: BorderSide(
                      color: !_wantsLive ? GQColors.primary : GQColors.hair,
                    ),
                  ),
                  ChoiceChip(
                    key: const Key('body_double_live_chip'),
                    label: const Text('With someone'),
                    selected: _wantsLive,
                    onSelected: (_) => setState(() => _wantsLive = true),
                    selectedColor: GQColors.primarySoft,
                    labelStyle: TextStyle(
                      color: _wantsLive ? GQColors.primaryDk : GQColors.ink2,
                      fontWeight: FontWeight.w700,
                    ),
                    side: BorderSide(
                      color: _wantsLive ? GQColors.primary : GQColors.hair,
                    ),
                  ),
                ],
              ),
              if (_wantsLive) ...[
                const SizedBox(height: 8),
                Text(
                  "Live rooms aren't open yet — sitting with Quest for now. "
                  "We'll let you know the moment there's someone else here.",
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: GQColors.ink2, height: 1.4),
                ),
              ],
              const SizedBox(height: 20),
              Text(
                "What's your intention?",
                style: theme.textTheme.labelLarge
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              TextField(
                key: const Key('body_double_task_field'),
                controller: _taskController,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: 'e.g. draft the two emails',
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
                "I'LL STEP OUT AFTER",
                style: theme.textTheme.labelSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: GQColors.ink3,
                  letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: List.generate(_durationOptions.length, (i) {
                  final opt = _durationOptions[i];
                  final selected = i == _selectedDurationIndex;
                  return ChoiceChip(
                    key: Key('body_double_duration_$i'),
                    label: Text(opt.label),
                    selected: selected,
                    onSelected: (_) =>
                        setState(() => _selectedDurationIndex = i),
                    selectedColor: GQColors.primarySoft,
                    labelStyle: TextStyle(
                      color: selected ? GQColors.primaryDk : GQColors.ink2,
                      fontWeight: FontWeight.w700,
                    ),
                    side: BorderSide(
                      color: selected ? GQColors.primary : GQColors.hair,
                    ),
                  );
                }),
              ),
              const SizedBox(height: 20),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: GQColors.softBg,
                  borderRadius: BorderRadius.circular(GQRadii.card),
                ),
                child: Text(
                  "No countdown on screen. Pull down anytime to ask how "
                  "long it's been. The room will tell you when your time's "
                  'up — gently.',
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: GQColors.ink2, height: 1.45),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  key: const Key('body_double_start_button'),
                  onPressed: _sitDown,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: GQColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(GQRadii.button),
                    ),
                  ),
                  child: const Text('Sit down'),
                ),
              ),
              const SizedBox(height: 12),
              Center(
                child: Text(
                  'Camera off. Mic off. Presence is one bit: here.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: GQColors.ink3,
                    fontStyle: FontStyle.italic,
                  ),
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

class _DurationOption {
  const _DurationOption({required this.label, required this.duration});
  final String label;
  final Duration duration;
}
