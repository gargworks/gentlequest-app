import 'dart:ui' show PointMode;
import 'package:flutter/material.dart';
import 'package:ai_buddy_web/theme/gq_theme.dart';

/// Connection state for a failed user message in the chat transcript.
enum ChatErrorState {
  /// First send failure — message queued, silent retry pending.
  failed,

  /// Silent retries exhausted (x2) — server-side outage.
  unreachable,
}

/// The degraded connection state for a single user message in the chat
/// transcript. Replaces the plain-white error path.
///
/// States:
/// - [ChatErrorState.failed] — first send failure. Message is queued; a
///   silent retry will fire automatically. Copy reassures the user their
///   message is saved.
/// - [ChatErrorState.unreachable] — silent retries exhausted (x2). The
///   problem is on the server side. Copy shifts to "our side, not your
///   connection" and the secondary action points to offline tools.
///
/// When the connection returns and the queue flushes, the bubble stays in
/// the transcript as a historical record but [showActions] should be false
/// so the retry / alternate-action row disappears.
class ChatErrorBubble extends StatelessWidget {
  final ChatErrorState state;
  final VoidCallback onRetry;
  final bool showActions;

  const ChatErrorBubble({
    super.key,
    required this.state,
    required this.onRetry,
    this.showActions = true,
  });

  String get _title {
    switch (state) {
      case ChatErrorState.failed:
        return 'That didn\u2019t reach me';
      case ChatErrorState.unreachable:
        return 'Still not connecting';
    }
  }

  String get _body {
    switch (state) {
      case ChatErrorState.failed:
        return 'Your message is saved. I\u2019ll answer as soon as the '
            'connection is back \u2014 nothing was lost.';
      case ChatErrorState.unreachable:
        return 'This one is on our side, not your connection. Both messages '
            'are saved and will send themselves when we\u2019re back.';
    }
  }

  String get _primaryLabel {
    switch (state) {
      case ChatErrorState.failed:
        return 'Try again';
      case ChatErrorState.unreachable:
        return 'Try once more';
    }
  }

  String get _secondaryLabel {
    switch (state) {
      case ChatErrorState.failed:
        return 'Something else instead';
      case ChatErrorState.unreachable:
        return 'Use the offline tools';
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final reduceMotion = MediaQuery.of(context).accessibleNavigation;
    final listWidth = MediaQuery.of(context).size.width;
    final maxBubbleWidth = listWidth * 0.88;

    return Align(
      alignment: Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxBubbleWidth),
        child: Container(
          padding: const EdgeInsets.fromLTRB(14, 13, 14, 13),
          decoration: BoxDecoration(
            color: t.amberSoft,
            border: Border.all(
              color: t.amber.withValues(alpha: 0.28),
              width: 1,
            ),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(18),
              topRight: Radius.circular(18),
              bottomRight: Radius.circular(18),
              bottomLeft: Radius.circular(6),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 17,
                    height: 17,
                    child: CustomPaint(
                      painter: _AlertIconPainter(
                        color: t.amber,
                        strokeWidth: 1.9,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Flexible(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          _title,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                            letterSpacing: -0.2,
                            height: 1.35,
                            color: t.inkOnAmber,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _body,
                          style: TextStyle(
                            fontSize: 13.5,
                            fontWeight: FontWeight.w500,
                            height: 1.45,
                            color: t.inkOnAmber
                                .withValues(alpha: 0.92),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (showActions) ...[
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: _PrimaryButton(
                        label: _primaryLabel,
                        onTap: onRetry,
                        reduceMotion: reduceMotion,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _SecondaryButton(
                        label: _secondaryLabel,
                        onTap: onRetry,
                        reduceMotion: reduceMotion,
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Primary "Try again" / "Try once more" button — amber fill, white label,
/// leading refresh icon, stadium radius, 44px min height.
class _PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final bool reduceMotion;

  const _PrimaryButton({
    required this.label,
    required this.onTap,
    required this.reduceMotion,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      button: true,
      label: label,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(999),
        child: AnimatedContainer(
          duration: reduceMotion ? Duration.zero : const Duration(milliseconds: 120),
          padding: const EdgeInsets.symmetric(horizontal: 16),
          constraints: const BoxConstraints(minHeight: 44),
          decoration: BoxDecoration(
            color: t.amber,
            borderRadius: BorderRadius.circular(999),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SizedBox(
                width: 14,
                height: 14,
                child: CustomPaint(
                  // amber is mode-invariant (GQTheme.dark reuses
                  // GQColors.amber unchanged), so this white icon's
                  // contrast on the fill never shifts by mode — same
                  // CTA-fill-foreground discipline as primaryDk/dangerInk.
                  painter: _RefreshIconPainter(color: Colors.white),
                ),
              ),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  label,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
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

/// Secondary "Something else instead" / "Use the offline tools" button —
/// transparent, amber border, inkOnAmber label, stadium radius, 44px min
/// height.
class _SecondaryButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final bool reduceMotion;

  const _SecondaryButton({
    required this.label,
    required this.onTap,
    required this.reduceMotion,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      button: true,
      label: label,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(999),
        child: AnimatedContainer(
          duration: reduceMotion ? Duration.zero : const Duration(milliseconds: 120),
          padding: const EdgeInsets.symmetric(horizontal: 14),
          constraints: const BoxConstraints(minHeight: 44),
          decoration: BoxDecoration(
            color: Colors.transparent,
            borderRadius: BorderRadius.circular(999),
            border: Border.all(
              color: t.amber.withValues(alpha: 0.35),
              width: 1.5,
            ),
          ),
          child: Center(
            child: Text(
              label,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: t.inkOnAmber,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Triangle alert icon — 17x17, stroke 1.9, drawn in [color].
class _AlertIconPainter extends CustomPainter {
  final Color color;
  final double strokeWidth;

  const _AlertIconPainter({required this.color, required this.strokeWidth});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    final w = size.width;
    final h = size.height;
    final path = Path()
      ..moveTo(w / 2, 1.2)
      ..lineTo(w - 1.2, h - 1.2)
      ..lineTo(1.2, h - 1.2)
      ..close();
    canvas.drawPath(path, paint);

    // Exclamation line + dot
    canvas.drawLine(
      Offset(w / 2, h * 0.42),
      Offset(w / 2, h * 0.66),
      paint,
    );
    canvas.drawPoints(
      PointMode.points,
      [Offset(w / 2, h * 0.78)],
      paint..strokeWidth = strokeWidth * 1.4,
    );
  }

  @override
  bool shouldRepaint(covariant _AlertIconPainter oldDelegate) =>
      oldDelegate.color != color || oldDelegate.strokeWidth != strokeWidth;
}

/// Circular refresh arrow icon — 14x14, drawn in [color].
class _RefreshIconPainter extends CustomPainter {
  final Color color;

  const _RefreshIconPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.8
      ..strokeCap = StrokeCap.round;

    final w = size.width;
    final h = size.height;
    final cx = w / 2;
    final cy = h / 2;
    final r = w * 0.36;

    // 3/4 arc
    final rect = Rect.fromCircle(center: Offset(cx, cy), radius: r);
    canvas.drawArc(rect, 0.5, 4.5, false, paint);

    // Arrowhead
    final arrowPath = Path()
      ..moveTo(cx + r * 0.95, cy - r * 0.6)
      ..lineTo(cx + r * 1.4, cy - r * 0.2)
      ..lineTo(cx + r * 0.7, cy - r * 0.1);
    canvas.drawPath(arrowPath, paint);
  }

  @override
  bool shouldRepaint(covariant _RefreshIconPainter oldDelegate) =>
      oldDelegate.color != color;
}
