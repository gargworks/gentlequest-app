import 'dart:async';

import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';

/// Design Authority D6 — "replaces every SnackBar for user-facing feedback."
///
/// The design audit's specific example: "'Please answer all questions
/// before submitting' arrives as a gray toast sliding over a depression
/// screener." GQBanner is an inline, warm banner instead of a floating
/// system-chrome toast — it can be embedded directly in a screen's layout
/// (the [GQBanner] widget itself), or shown as a top-anchored overlay via
/// [GQBanner.show] for screens not yet restructured to hold banner state
/// (a drop-in swap for `ScaffoldMessenger.showSnackBar`, not the intended
/// end state — prefer embedding the widget where the screen can).
///
/// D6: "Error text is never a raw exception string — GQBanner takes a human
/// sentence; exceptions go to logs." [GQBanner] and [GQBanner.show] both
/// take a plain [message] string; there is no exception/error-object
/// parameter, by design — the caller must already have translated it.
class GQBanner extends StatelessWidget {
  const GQBanner({
    super.key,
    required this.message,
    this.category = GQBannerCategory.info,
    this.onDismiss,
    this.icon,
    this.eyebrow,
    this.child,
  });

  final String message;
  final GQBannerCategory category;

  /// Null renders no dismiss control (for a banner tied to state that
  /// clears itself, e.g. "still loading").
  final VoidCallback? onDismiss;

  /// Overrides the category's default icon.
  final IconData? icon;

  /// Optional small-caps line above [message] (e.g. "WE'RE HERE").
  final String? eyebrow;

  /// Optional content below [message], separated by an [GQSpacing.md] gap —
  /// e.g. embedding [CrisisResourcesWidget] under a follow-up banner. A
  /// legitimate widget-layer extension point, not a screen-local hack.
  final Widget? child;

  @override
  Widget build(BuildContext context) {
    final palette = _paletteFor(category);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: GQSpacing.lg, vertical: GQSpacing.md),
      decoration: BoxDecoration(
        color: palette.soft,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: palette.ink.withValues(alpha: 0.24)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon ?? palette.icon, size: 20, color: palette.ink),
              const SizedBox(width: GQSpacing.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (eyebrow != null) ...[
                      Text(
                        eyebrow!.toUpperCase(),
                        style: GQTypography.micro.copyWith(color: palette.ink),
                      ),
                      const SizedBox(height: GQSpacing.xs),
                    ],
                    Text(
                      message,
                      style: GQTypography.caption.copyWith(color: palette.ink, height: 1.4),
                    ),
                  ],
                ),
              ),
              if (onDismiss != null) ...[
                const SizedBox(width: GQSpacing.sm),
                GestureDetector(
                  onTap: onDismiss,
                  child: Icon(Icons.close_rounded, size: 18, color: palette.ink),
                ),
              ],
            ],
          ),
          if (child != null) ...[
            const SizedBox(height: GQSpacing.md),
            child!,
          ],
        ],
      ),
    );
  }

  /// Drop-in SnackBar replacement: shows [message] as a top-anchored,
  /// slide-in banner over the current screen, auto-dismissing after
  /// [duration]. Prefer embedding [GQBanner] directly once a screen has
  /// somewhere for it to live permanently in the layout.
  static void show(
    BuildContext context, {
    required String message,
    GQBannerCategory category = GQBannerCategory.info,
    Duration duration = const Duration(seconds: 4),
  }) {
    final overlay = Overlay.of(context, rootOverlay: true);
    late OverlayEntry entry;
    Timer? timer;

    void remove() {
      timer?.cancel();
      if (entry.mounted) entry.remove();
    }

    entry = OverlayEntry(
      builder: (context) => _AnimatedBannerOverlay(
        message: message,
        category: category,
        onDismiss: remove,
      ),
    );
    overlay.insert(entry);
    timer = Timer(duration, remove);
  }
}

enum GQBannerCategory { info, warm, amber, danger, success }

class _Palette {
  const _Palette({required this.soft, required this.ink, required this.icon});
  final Color soft;
  final Color ink;
  final IconData icon;
}

_Palette _paletteFor(GQBannerCategory category) {
  switch (category) {
    case GQBannerCategory.info:
      return const _Palette(soft: GQColors.primarySoft, ink: GQColors.primaryDk, icon: Icons.info_outline_rounded);
    case GQBannerCategory.warm:
      return const _Palette(soft: GQColors.accentSoft, ink: GQColors.inkOnCoral, icon: Icons.favorite_outline_rounded);
    case GQBannerCategory.amber:
      return const _Palette(soft: GQColors.amberSoft, ink: GQColors.inkOnAmber, icon: Icons.wifi_off_rounded);
    case GQBannerCategory.danger:
      return const _Palette(soft: GQColors.dangerSoft, ink: GQColors.dangerInk, icon: Icons.error_outline_rounded);
    case GQBannerCategory.success:
      return const _Palette(soft: GQColors.successSoft, ink: GQColors.successInk, icon: Icons.check_circle_outline_rounded);
  }
}

class _AnimatedBannerOverlay extends StatefulWidget {
  const _AnimatedBannerOverlay({
    required this.message,
    required this.category,
    required this.onDismiss,
  });

  final String message;
  final GQBannerCategory category;
  final VoidCallback onDismiss;

  @override
  State<_AnimatedBannerOverlay> createState() => _AnimatedBannerOverlayState();
}

class _AnimatedBannerOverlayState extends State<_AnimatedBannerOverlay> {
  bool _visible = false;

  @override
  void initState() {
    super.initState();
    // Kick the slide-in on the next frame so AnimatedSlide has a from-state.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) setState(() => _visible = true);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: MediaQuery.of(context).padding.top + GQSpacing.sm,
      left: GQSpacing.lg,
      right: GQSpacing.lg,
      child: AnimatedSlide(
        offset: _visible ? Offset.zero : const Offset(0, -1.2),
        duration: GQDurations.sheetSlide,
        curve: GQMotion.standardCurve,
        child: AnimatedOpacity(
          opacity: _visible ? 1 : 0,
          duration: GQDurations.fade,
          child: Material(
            color: Colors.transparent,
            child: GQBanner(
              message: widget.message,
              category: widget.category,
              onDismiss: widget.onDismiss,
            ),
          ),
        ),
      ),
    );
  }
}
