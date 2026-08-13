import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/survey_provider.dart';
import '../services/analytics_service.dart';
import '../services/firebase_service.dart';
import '../theme/gq_tokens.dart';

/// Sean-Ellis PMF survey bottom sheet.
///
/// The canonical Sean-Ellis question:
///   "How would you feel if you could no longer use GentleQuest?"
/// with the four standard response options. The >=40% "very disappointed"
/// threshold is the PMF signal computed downstream from the recorded answers.
///
/// Showing logic (session-count gate + once-per-user) lives in
/// [SurveyProvider]; this widget is purely the presentation + submit surface.
/// Callers should check `SurveyProvider.shouldShowSurvey()` before invoking
/// [showSeanEllisSurveySheet].
///
/// On submit the answer is:
///   1. persisted via [SurveyProvider.recordAnswer]
///   2. sent to the backend via [logAnalyticsEvent] with event_type
///      `sean_ellis_survey` and metadata `{answer: <selection>}`
///   3. logged to Firebase via [FirebaseService.logEvent]
Future<void> showSeanEllisSurveySheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    useRootNavigator: true,
    isDismissible: true,
    builder: (_) => const _SeanEllisSurveySheet(),
  );
}

// ─── Options ─────────────────────────────────────────────────────────────────

/// The four canonical Sean-Ellis response options, in presentation order.
const List<String> seanEllisOptions = [
  'Very disappointed',
  'Somewhat disappointed',
  'Not disappointed',
  'N/A - I no longer use it',
];

// ─── Sheet ───────────────────────────────────────────────────────────────────

class _SeanEllisSurveySheet extends StatefulWidget {
  const _SeanEllisSurveySheet();

  @override
  State<_SeanEllisSurveySheet> createState() => _SeanEllisSurveySheetState();
}

class _SeanEllisSurveySheetState extends State<_SeanEllisSurveySheet> {
  int? _selected;

  bool get _canSubmit => _selected != null;

  Future<void> _submit() async {
    if (!_canSubmit) return;
    final answer = seanEllisOptions[_selected!];
    final provider = context.read<SurveyProvider>();

    // Persist + mark shown so it never re-appears.
    await provider.recordAnswer(answer);
    await provider.markShown();

    // Backend analytics log (gated internally by analytics consent).
    try {
      await logAnalyticsEvent(
        'sean_ellis_survey',
        metadata: {'answer': answer},
      );
    } catch (e) {
      if (kDebugMode) debugPrint('[sean_ellis] backend log failed: $e');
    }

    // Firebase analytics log (gated internally by anonymity mode).
    try {
      await FirebaseService().logEvent(
        'sean_ellis_survey',
        {'answer': answer},
      );
    } catch (e) {
      if (kDebugMode) debugPrint('[sean_ellis] firebase log failed: $e');
    }

    if (!mounted) return;
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Container(
      decoration: const BoxDecoration(
        color: GQColors.softBg,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(GQRadii.sheet),
        ),
      ),
      padding: EdgeInsets.fromLTRB(
        24,
        12,
        24,
        MediaQuery.of(context).padding.bottom + 24,
      ),
      child: Column(
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
            'One quick question',
            style: textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w700,
              fontFamily: GQTypography.displayFamily,
              color: GQColors.ink,
            ),
          ),
          const SizedBox(height: 12),

          // The Sean-Ellis question
          Text(
            'How would you feel if you could no longer use GentleQuest?',
            style: textTheme.bodyLarge?.copyWith(
              fontFamily: GQTypography.bodyFamily,
              color: GQColors.ink2,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 20),

          // Options
          for (int i = 0; i < seanEllisOptions.length; i++) ...[
            _OptionTile(
              label: seanEllisOptions[i],
              selected: _selected == i,
              onTap: () => setState(() => _selected = i),
            ),
            if (i < seanEllisOptions.length - 1) const SizedBox(height: 10),
          ],

          const SizedBox(height: 24),

          // Submit button
          SizedBox(
            height: 48,
            child: ElevatedButton(
              onPressed: _canSubmit ? _submit : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: GQColors.primary,
                foregroundColor: Colors.white,
                disabledBackgroundColor: GQColors.primary.withValues(alpha: 0.4),
                disabledForegroundColor: Colors.white70,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(GQRadii.button),
                ),
                elevation: 0,
              ),
              child: Text(
                'Submit',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Option tile ─────────────────────────────────────────────────────────────

class _OptionTile extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _OptionTile({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? GQColors.primarySoft : Colors.white,
      borderRadius: BorderRadius.circular(GQRadii.card),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(GQRadii.card),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(
              color: selected ? GQColors.primary : GQColors.hair,
              width: selected ? 1.5 : 1,
            ),
          ),
          child: Row(
            children: [
              Icon(
                selected
                    ? Icons.radio_button_checked_rounded
                    : Icons.radio_button_unchecked_rounded,
                color: selected ? GQColors.primary : GQColors.ink3,
                size: 22,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 15,
                    fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                    color: GQColors.ink,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
