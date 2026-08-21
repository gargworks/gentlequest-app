import 'package:flutter/material.dart';
import '../widgets/mood_tracker.dart';
import '../theme/gq_tokens.dart';
import '../widgets/gq/gq.dart';
import '../widgets/keyboard_dismissible_scaffold.dart';

/// WO-5.2 Part B: title moved from the generic "Mood Tracker" to an
/// invitation, never a feature name. The spec's exact suggested title
/// ("How are you, right now?") turned out to collide verbatim with the
/// in-body mood-trigger card's own headline (MoodTrackerWidget's
/// `_buildMoodInput`) -- same string, two places on one screen. "Let's
/// check in" keeps the invitation register D6 asks for without the
/// duplicate. The 8px gray slab divider (a filled-slab divider, banned
/// per D6) is gone. Dhiwise legacy theme (`TextStyleHelper`, the `.h`
/// sizer extension) is purged.
class MoodTrackerScreen extends StatelessWidget {
  final bool showBottomNav;
  final ValueNotifier<int>?
      reselect; // currently unused; reserved for scroll/refresh on re-tap
  const MoodTrackerScreen(
      {super.key, this.showBottomNav = false, this.reselect});

  @override
  Widget build(BuildContext context) {
    return KeyboardDismissibleScaffold(
      safeTop: false,
      safeBottom: false,
      backgroundColor: GQColors.bg,
      appBar: const GQHeader(title: "Let's check in"),
      body: Column(
        children: [
          const SizedBox(height: GQSpacing.lg),
          Expanded(
            child: Container(
              color: GQColors.surface,
              child: const MoodTrackerWidget(),
            ),
          ),
        ],
      ),
    );
  }
}
