// Journal — A: empty state. Split from journal_screen.dart (R1D14).

import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';
import '../../widgets/app_back_button.dart';
import 'journal_shared.dart';

// ─────────────────────────────────────────────────────────────────────────────
// A — Empty state
// ─────────────────────────────────────────────────────────────────────────────

class JournalEmptyState extends StatelessWidget {
  const JournalEmptyState({super.key, required this.onStartEntry});

  final Future<void> Function({String? prefill}) onStartEntry;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: AppBar(
        backgroundColor: GQColors.softBg,
        elevation: 0,
        scrolledUnderElevation: 0,
        automaticallyImplyLeading: false,
        leading: Builder(
          builder: (ctx) {
            final canPop = Navigator.of(ctx).canPop();
            final route = ModalRoute.of(ctx);
            final isModal =
                route is PageRoute && route.fullscreenDialog == true;
            if (canPop) return AppBackButton(isModal: isModal);
            return const SizedBox.shrink();
          },
        ),
        title: const Text(
          'Journal',
          style: TextStyle(
            fontFamily: GQTypography.displayFamily,
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: GQColors.ink,
            letterSpacing: -0.3,
          ),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: NavIconButton(
              backgroundColor: GQColors.primarySoft,
              borderColor: Color(0x33667EEA),
              onTap: () => onStartEntry(),
              child: const Icon(
                Icons.add,
                size: 16,
                color: GQColors.primaryDk,
              ),
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(
            height: 1,
            thickness: 1,
            color: GQColors.hair,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 6, 16, 30),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Notebook + leaf illustration
            _EmptyStateIllustration(),
            const SizedBox(height: 18),

            // Headline + sub
            const Text(
              "Your journal starts here.",
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: GQTypography.journalSerif,
                fontSize: 26,
                fontWeight: FontWeight.w600,
                color: GQColors.ink,
                letterSpacing: -0.6,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 8),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Text(
                "Even one line is a journal. We'll keep it for you.",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                  color: GQColors.ink2,
                  height: 1.5,
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Chip starters
            _StarterChips(onStartEntry: onStartEntry),
            const SizedBox(height: 18),

            // Start an entry CTA
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => onStartEntry(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: GQColors.primary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shadowColor: Colors.transparent,
                  padding: const EdgeInsets.symmetric(vertical: 15),
                  shape: const StadiumBorder(),
                  textStyle: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 14.5,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.2,
                  ),
                ),
                child: const Text('Start an entry'),
              ),
            ),
            const SizedBox(height: 14),

            // Privacy footer
            Center(
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0x0F667EEA),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.lock_outline,
                      size: 11,
                      color: GQColors.ink2,
                    ),
                    const SizedBox(width: 5),
                    Text(
                      // Journal entries are device-local only. The backend
                      // /api/journal/* routes were removed in PR #167
                      // (2026-07-02); there is no server sync path. This
                      // copy is now unconditionally true for all users.
                      'Stays on your device. Never synced. Never shared.',
                      style: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink2,
                        letterSpacing: 0.2,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Notebook illustration (static, no animation per widget map)
// ─────────────────────────────────────────────────────────────────────────────

class _EmptyStateIllustration extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: SizedBox(
        width: 200,
        height: 160,
        child: Stack(
          children: [
            // Page
            Positioned.fill(
              child: Transform.rotate(
                angle: -0.052, // ~-3 degrees
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(6),
                      bottomLeft: Radius.circular(6),
                      topRight: Radius.circular(16),
                      bottomRight: Radius.circular(16),
                    ),
                    border: Border.all(
                      color: const Color(0x1A1F1B3A),
                      width: 1,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x4D667EEA),
                        blurRadius: 40,
                        offset: Offset(0, 16),
                        spreadRadius: -12,
                      ),
                      BoxShadow(
                        color: Color(0x0A1F1B3A),
                        blurRadius: 8,
                        offset: Offset(0, 4),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            // Spine binding dots (left edge)
            Positioned(
              left: 0,
              top: 14,
              bottom: 14,
              width: 8,
              child: Transform.rotate(
                angle: -0.052,
                child: CustomPaint(painter: _SpinePainter()),
              ),
            ),
            // Red margin line
            Positioned(
              left: 20,
              top: 0,
              bottom: 0,
              width: 1,
              child: Transform.rotate(
                angle: -0.052,
                child: Container(
                  color: const Color(0x4DFF6B6B),
                ),
              ),
            ),
            // Lines on page
            Positioned(
              left: 36,
              right: 16,
              top: 24,
              bottom: 18,
              child: Transform.rotate(
                angle: -0.052,
                child: CustomPaint(painter: _LinedPagePainter()),
              ),
            ),
            // Handwritten scribble text
            Positioned(
              left: 50,
              top: 36,
              child: Transform.rotate(
                angle: -0.052,
                child: const _NotebookScribble(),
              ),
            ),
            // Leaf SVG (top-right)
            Positioned(
              right: -10,
              top: 18,
              child: Transform.rotate(
                angle: 0.489, // ~28 degrees
                child: const _LeafIcon(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SpinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0x1A1F1B3A)
      ..strokeWidth = 1;
    double y = 0;
    while (y < size.height) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
      y += 9;
    }
  }

  @override
  bool shouldRepaint(_SpinePainter old) => false;
}

class _LinedPagePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0x0F1F1B3A)
      ..strokeWidth = 1;
    double y = 18;
    while (y < size.height) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
      y += 18;
    }
  }

  @override
  bool shouldRepaint(_LinedPagePainter old) => false;
}

// Handwritten-style scribble text rendered as small colored text
// [assumed] Uses Inter since Caveat font is not in assets.
class _NotebookScribble extends StatelessWidget {
  const _NotebookScribble();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        Text(
          'walking helped',
          style: TextStyle(
            fontSize: 12,
            color: Color(0x8C667EEA),
            fontStyle: FontStyle.italic,
          ),
        ),
        SizedBox(height: 4),
        Text(
          'boundaries felt good',
          style: TextStyle(
            fontSize: 12,
            color: Color(0x8C667EEA),
            fontStyle: FontStyle.italic,
          ),
        ),
        SizedBox(height: 4),
        Text(
          'bed by 10',
          style: TextStyle(
            fontSize: 12,
            color: Color(0x8C667EEA),
            fontStyle: FontStyle.italic,
          ),
        ),
      ],
    );
  }
}

class _LeafIcon extends StatelessWidget {
  const _LeafIcon();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 56,
      height: 56,
      child: CustomPaint(painter: _LeafPainter()),
    );
  }
}

class _LeafPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final fillPaint = Paint()
      ..color = GQColors.moodGreat.withValues(alpha: 0.85)
      ..style = PaintingStyle.fill;
    final strokePaint = Paint()
      ..color = GQColors.leafInk
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeJoin = StrokeJoin.round;
    final linePaint = Paint()
      ..color = GQColors.leafInk
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round;

    // Leaf body
    final path = Path()
      ..moveTo(48, 8)
      ..cubicTo(26, 8, 12, 22, 12, 40)
      ..cubicTo(12, 44, 13, 48, 14, 50)
      ..cubicTo(16, 49, 20, 48, 24, 48)
      ..cubicTo(42, 48, 56, 34, 56, 12)
      ..cubicTo(56, 10, 55, 8, 54, 8)
      ..cubicTo(52, 8, 50, 9, 48, 8)
      ..close();
    canvas.drawPath(path, fillPaint);
    canvas.drawPath(path, strokePaint);

    // Central vein
    canvas.drawLine(
      const Offset(14, 50),
      const Offset(44, 20),
      linePaint,
    );
  }

  @override
  bool shouldRepaint(_LeafPainter old) => false;
}

// ─────────────────────────────────────────────────────────────────────────────
// Starter chips (A) — three prompt starters; tap pre-fills editor
// ─────────────────────────────────────────────────────────────────────────────

class _StarterChips extends StatelessWidget {
  const _StarterChips({required this.onStartEntry});

  final Future<void> Function({String? prefill}) onStartEntry;

  static const _prompts = [
    ('a', 'Today, what worked was…'),
    ('b', 'I noticed myself…'),
    ('c', 'I want to remember…'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: _prompts
          .map(
            (p) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _StarterChip(
                label: p.$1,
                text: p.$2,
                onTap: () => onStartEntry(prefill: p.$2),
              ),
            ),
          )
          .toList(),
    );
  }
}

class _StarterChip extends StatelessWidget {
  const _StarterChip({
    required this.label,
    required this.text,
    required this.onTap,
  });

  final String label;
  final String text;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: GQColors.hair),
        ),
        child: Row(
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: GQColors.primarySoft,
                borderRadius: BorderRadius.circular(9),
              ),
              alignment: Alignment.center,
              child: Text(
                label,
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: GQColors.primaryDk,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                text,
                style: const TextStyle(
                  fontFamily: GQTypography.handwritten,
                  fontSize: 17,
                  fontWeight: FontWeight.w500,
                  color: GQColors.ink,
                  letterSpacing: 0.2,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
