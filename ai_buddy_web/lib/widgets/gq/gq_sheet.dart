import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';

/// Design Authority D6 — the one bottom-sheet shape.
///
/// Radius 24 on the top corners only, a 36x4 grabber handle, keyboard-aware
/// padding, and a 320ms slide-in ([GQDurations.sheetSlide]). Screens should
/// call [GQSheet.show] instead of hand-rolling `showModalBottomSheet` with
/// per-screen radius/handle/animation choices.
class GQSheet extends StatelessWidget {
  const GQSheet({super.key, required this.child, this.title});

  final Widget child;
  final String? title;

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    return Padding(
      padding: EdgeInsets.only(bottom: bottomInset),
      child: Container(
        decoration: const BoxDecoration(
          color: GQColors.surface,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(24),
            topRight: Radius.circular(24),
          ),
        ),
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(GQSpacing.xl, GQSpacing.sm, GQSpacing.xl, GQSpacing.xl),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(
                  child: Container(
                    width: 36,
                    height: 4,
                    margin: const EdgeInsets.only(bottom: GQSpacing.lg),
                    decoration: BoxDecoration(
                      color: GQColors.hair,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                if (title != null) ...[
                  Text(title!, style: GQTypography.titleSm.copyWith(color: GQColors.ink)),
                  const SizedBox(height: GQSpacing.lg),
                ],
                child,
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// Shows [content] in a [GQSheet] via the one legal bottom-sheet
  /// animation (320ms slide, [GQMotion.standardCurve]) instead of Material's
  /// default sheet transition.
  static Future<T?> show<T>(
    BuildContext context, {
    required Widget content,
    String? title,
    bool isScrollControlled = true,
  }) {
    return showModalBottomSheet<T>(
      context: context,
      isScrollControlled: isScrollControlled,
      backgroundColor: Colors.transparent,
      barrierColor: GQColors.ink.withValues(alpha: 0.32),
      transitionAnimationController: null,
      builder: (context) => TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: 1),
        duration: GQDurations.sheetSlide,
        curve: GQMotion.standardCurve,
        builder: (context, value, child) => Transform.translate(
          offset: Offset(0, (1 - value) * 40),
          child: Opacity(opacity: value, child: child),
        ),
        child: GQSheet(title: title, child: content),
      ),
    );
  }
}
