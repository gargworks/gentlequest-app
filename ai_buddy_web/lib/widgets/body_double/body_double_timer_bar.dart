import 'package:flutter/material.dart';
import '../../theme/gq_tokens.dart';

/// BodyDoubleTimerBar — v1.5.0 ADHD Update, Workstream 2a.
///
/// Pinned status strip shown between the chat header and the message list
/// while a body-doubling session is active. Stateless by design:
/// `InteractiveChatScreen` owns the single ticking `Timer` and passes the
/// current [remaining] down every second, so there's exactly one clock
/// driving the UI — no drift between a widget-local timer and the parent's
/// completion/abandon logic (which also drives the companion check-in
/// messages inserted into the real chat transcript).
class BodyDoubleTimerBar extends StatelessWidget {
  const BodyDoubleTimerBar({
    super.key,
    required this.task,
    required this.remaining,
    required this.total,
    required this.onEndSession,
  });

  final String task;
  final Duration remaining;
  final Duration total;
  final VoidCallback onEndSession;

  String _formatDuration(Duration d) {
    final clamped = d.isNegative ? Duration.zero : d;
    final m = clamped.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = clamped.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    final totalMs = total.inMilliseconds <= 0 ? 1 : total.inMilliseconds;
    final progress =
        (1 - (remaining.inMilliseconds / totalMs)).clamp(0.0, 1.0);
    return Semantics(
      label:
          'Focus session with Alex: $task, ${_formatDuration(remaining)} remaining',
      child: Container(
        margin: const EdgeInsets.fromLTRB(12, 8, 12, 0),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: GQColors.primarySoft,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: Border.all(color: GQColors.primary.withValues(alpha: 0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.timer_outlined,
                    size: 18, color: GQColors.primaryDk),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    task,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: GQColors.ink,
                    ),
                  ),
                ),
                Text(
                  _formatDuration(remaining),
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: GQColors.primaryDk,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(GQRadii.button),
              child: LinearProgressIndicator(
                value: progress,
                minHeight: 5,
                backgroundColor: Colors.white,
                valueColor:
                    const AlwaysStoppedAnimation<Color>(GQColors.primary),
              ),
            ),
            const SizedBox(height: 6),
            Align(
              alignment: Alignment.centerRight,
              child: Semantics(
                button: true,
                label: 'End focus session early',
                child: GestureDetector(
                  onTap: onEndSession,
                  child: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 4),
                    child: Text(
                      'End session',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink2,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
