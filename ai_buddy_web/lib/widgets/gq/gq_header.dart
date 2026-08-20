import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';

/// Design Authority D6/D5 — "every screen adopts one shared header/back
/// pattern (via GQHeader)."
///
/// The design audit's "header anatomy differs per screen" finding: Journal
/// used AppBar + a custom back-button builder, Mood hand-rolled a header row
/// with an 8px filled gray divider slab, Chat had a custom translucent
/// header, Settings used a stock AppBar — four screens, four header systems,
/// four different back-button behaviors, and one screen used a filled gray
/// divider where the design language calls for a 1px hairline.
///
/// GQHeader is one PreferredSizeWidget with exactly one back behavior
/// (Navigator.maybePop, so it degrades to a no-op instead of throwing if
/// there's nothing to pop) and a hairline bottom border instead of any
/// filled slab. New/swept screens use this instead of AppBar or a hand-
/// rolled Row.
class GQHeader extends StatelessWidget implements PreferredSizeWidget {
  const GQHeader({
    super.key,
    required this.title,
    this.onBack,
    this.showBack = true,
    this.actions,
    this.backgroundColor = GQColors.bg,
  });

  final String title;

  /// Defaults to [Navigator.maybePop] — the one legal back behavior. Only
  /// override for a screen with a genuinely different exit (e.g. a modal
  /// flow that should close instead of pop); do not reintroduce per-screen
  /// pushNamedAndRemoveUntil variance for ordinary back navigation.
  final VoidCallback? onBack;

  final bool showBack;
  final List<Widget>? actions;
  final Color backgroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(top: MediaQuery.of(context).padding.top),
      decoration: BoxDecoration(
        color: backgroundColor,
        border: const Border(bottom: BorderSide(color: GQColors.hair, width: 1)),
      ),
      child: SizedBox(
        height: kToolbarHeight,
        child: Row(
          children: [
            if (showBack)
              SizedBox(
                width: GQA11y.minTouchTarget,
                height: GQA11y.minTouchTarget,
                child: IconButton(
                  icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
                  color: GQColors.ink,
                  onPressed: onBack ?? () => Navigator.of(context).maybePop(),
                  tooltip: 'Back',
                )
              )
            else
              const SizedBox(width: GQSpacing.lg),
            Expanded(
              child: Text(
                title,
                style: GQTypography.titleSm.copyWith(color: GQColors.ink),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (actions != null) ...actions! else const SizedBox(width: GQSpacing.lg),
          ],
        ),
      ),
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}
