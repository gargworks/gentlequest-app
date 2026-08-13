import 'package:flutter/material.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';

/// Presence state for the companion avatar status dot.
enum CompanionPresence {
  /// Connected — default. Dot is NOT rendered.
  online,

  /// Mid-chat send failure; silent retries in flight. Amber pulse dot.
  reconnecting,

  /// Silent retries exhausted. Dot removed; companion desaturates
  /// (handled by the avatar widget, not this dot).
  unreachable,
}

/// A small status dot positioned bottom-right of a companion avatar.
///
/// - [CompanionPresence.online]: renders nothing (connected is the default).
/// - [CompanionPresence.reconnecting]: 11x11 amber-soft circle with a 2px
///   amber border, pulsing opacity 0.35→0.9 and scale 1.0→1.06 over 2200ms
///   ease-in-out loop. Under reduced-motion, becomes a static ring.
/// - [CompanionPresence.unreachable]: renders nothing — the companion
///   desaturates via a separate crossfade (handled by the avatar widget).
///
/// Designed to be stacked over a 34px avatar with bottom-right inset of -1
/// (i.e. slightly outside the avatar bounds). Use a [Stack] with
/// [Positioned] in the caller.
class CompanionStatusDot extends StatefulWidget {
  final CompanionPresence presence;

  const CompanionStatusDot({super.key, required this.presence});

  @override
  State<CompanionStatusDot> createState() => _CompanionStatusDotState();
}

class _CompanionStatusDotState extends State<CompanionStatusDot>
    with SingleTickerProviderStateMixin {
  AnimationController? _controller;
  Animation<double>? _opacity;
  Animation<double>? _scale;

  @override
  void initState() {
    super.initState();
    _setupAnimation();
  }

  void _setupAnimation() {
    if (widget.presence != CompanionPresence.reconnecting) {
      _controller?.dispose();
      _controller = null;
      return;
    }
    _controller ??= AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2200),
    );
    _opacity = Tween<double>(begin: 0.35, end: 0.9).animate(
      CurvedAnimation(parent: _controller!, curve: Curves.easeInOut),
    );
    _scale = Tween<double>(begin: 1.0, end: 1.06).animate(
      CurvedAnimation(parent: _controller!, curve: Curves.easeInOut),
    );
    _controller!.repeat(reverse: true);
  }

  @override
  void didUpdateWidget(covariant CompanionStatusDot oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.presence != widget.presence) {
      _setupAnimation();
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.presence == CompanionPresence.online ||
        widget.presence == CompanionPresence.unreachable) {
      return const SizedBox.shrink();
    }

    final reduceMotion = MediaQuery.of(context).accessibleNavigation;

    if (reduceMotion) {
      // Static ring — no pulse.
      return Container(
        width: 11,
        height: 11,
        decoration: BoxDecoration(
          color: GQColors.amberSoft,
          shape: BoxShape.circle,
          border: Border.all(color: GQColors.amber, width: 2),
        ),
      );
    }

    return AnimatedBuilder(
      animation: _controller!,
      builder: (context, child) {
        return Transform.scale(
          scale: _scale?.value ?? 1.0,
          child: Opacity(
            opacity: _opacity?.value ?? 0.35,
            child: child,
          ),
        );
      },
      child: Container(
        width: 11,
        height: 11,
        decoration: BoxDecoration(
          color: GQColors.amberSoft,
          shape: BoxShape.circle,
          border: Border.all(color: GQColors.amber, width: 2),
        ),
      ),
    );
  }
}
