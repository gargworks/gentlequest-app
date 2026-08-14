/// GentleQuest companion creature — CustomPainter for geometric plant stages.
///
/// Converts the design agent's 5-stage SVG illustrations (96×96 viewBox)
/// into Flutter Canvas draw calls. Each [GrowthStage] paints a different
/// plant shape: seed → sprout → sapling → young tree → mature tree.
///
/// Pass [simplified] = true for small render sizes (< 34 px) to drop the
/// shadow ellipse and secondary accents and fatten the main shapes, per
/// the design agent's simplified variants.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/companion.dart';
import '../theme/gq_tokens.dart';

/// Paints the companion creature as geometric plant shapes on a Flutter
/// canvas. The 96×96 SVG viewBox is scaled to fit the given [Size].
class CompanionPainter extends CustomPainter {
  const CompanionPainter({
    required this.stage,
    this.simplified = false,
    this.desaturated = false,
  });

  /// Which growth stage to paint.
  final GrowthStage stage;

  /// When true, drops the shadow ellipse and secondary accent shapes and
  /// fattens the main shapes. Use for render sizes below 34 px.
  final bool simplified;

  /// When true, desaturates the companion for the .unreachable chat state:
  /// foliage → moodSlateLavender, trunk → ink3, accent → #E5E2EE,
  /// avatar backing → surface2.
  final bool desaturated;

  // ── Desaturated color helpers ────────────────────────────────────────────
  Color _foliage(Color normal) =>
      desaturated ? GQColors.moodSlateLavender : normal;
  Color _trunk(Color normal) => desaturated ? GQColors.ink3 : normal;
  Color _accent(Color normal) =>
      desaturated ? const Color(0xFFE5E2EE) : normal;
  Color _backing(Color normal) => desaturated ? GQColors.surface2 : normal;

  /// SVG viewBox dimension — all shape coordinates are in this space.
  static const double _viewBox = 96;

  /// Fattening factor applied to radii/widths in simplified mode.
  static const double _fatFactor = 1.15;

  @override
  void paint(Canvas canvas, Size size) {
    final s = size.width / _viewBox;
    canvas.save();
    canvas.scale(s, s);
    switch (stage) {
      case GrowthStage.seed:
        _paintSeed(canvas);
      case GrowthStage.sprout:
        _paintSprout(canvas);
      case GrowthStage.sapling:
        _paintSapling(canvas);
      case GrowthStage.young:
        _paintYoungTree(canvas);
      case GrowthStage.mature:
        _paintMatureTree(canvas);
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CompanionPainter old) =>
      stage != old.stage ||
      simplified != old.simplified ||
      desaturated != old.desaturated;

  // ── Shape helpers ────────────────────────────────────────────────────────

  /// Fattening multiplier — 1.0 in full mode, [_fatFactor] in simplified.
  double _f(double v) => simplified ? v * _fatFactor : v;

  /// Ground shadow ellipse. Skipped in simplified mode.
  void _shadow(Canvas canvas) {
    if (simplified) return;
    _oval(canvas, 48, 82, 25, 4.5, _backing(GQColors.moodSlateLavender), opacity: 0.6);
  }

  void _oval(
    Canvas canvas,
    double cx,
    double cy,
    double rx,
    double ry,
    Color color, {
    double opacity = 1.0,
  }) {
    final paint = Paint()..color = color.withValues(alpha: opacity);
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(cx, cy),
        width: _f(rx) * 2,
        height: _f(ry) * 2,
      ),
      paint,
    );
  }

  void _rotatedOval(
    Canvas canvas,
    double cx,
    double cy,
    double rx,
    double ry,
    Color color,
    double angleDeg, {
    double opacity = 1.0,
  }) {
    canvas.save();
    canvas.translate(cx, cy);
    canvas.rotate(angleDeg * math.pi / 180);
    final paint = Paint()..color = color.withValues(alpha: opacity);
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset.zero,
        width: _f(rx) * 2,
        height: _f(ry) * 2,
      ),
      paint,
    );
    canvas.restore();
  }

  void _rrect(
    Canvas canvas,
    double x,
    double y,
    double w,
    double h,
    double rx,
    Color color,
  ) {
    // Fatten width symmetrically so the rect stays centered on its midpoint.
    final fw = _f(w);
    final fx = x - (fw - w) / 2;
    final paint = Paint()..color = color;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(fx, y, fw, h),
        Radius.circular(_f(rx)),
      ),
      paint,
    );
  }

  void _circle(
    Canvas canvas,
    double cx,
    double cy,
    double r,
    Color color, {
    double opacity = 1.0,
  }) {
    final paint = Paint()..color = color.withValues(alpha: opacity);
    canvas.drawCircle(Offset(cx, cy), _f(r), paint);
  }

  // ── Stage painters ───────────────────────────────────────────────────────

  /// Stage 1 — Seed (0 XP):
  /// shadow + seed body + highlight.
  void _paintSeed(Canvas canvas) {
    _shadow(canvas);
    _oval(canvas, 48, 71, 9.5, 12, _accent(GQColors.moodCoralPeach));
    if (!simplified) {
      _oval(canvas, 44.5, 66, 2.8, 3.8, _accent(GQColors.moodGood), opacity: 0.9);
    }
  }

  /// Stage 2 — Sprout (50 XP):
  /// shadow + stem + two leaves.
  void _paintSprout(Canvas canvas) {
    _shadow(canvas);
    _rrect(canvas, 46.25, 58, 3.5, 22, 1.75, _trunk(GQColors.primary));
    _rotatedOval(canvas, 38, 60, 9, 5.5, _foliage(GQColors.moodPeri), -16);
    _rotatedOval(canvas, 58, 57, 9, 5.5, _foliage(GQColors.primary), 16);
  }

  /// Stage 3 — Sapling (150 XP):
  /// shadow + trunk + four leaves + top bud.
  void _paintSapling(Canvas canvas) {
    _shadow(canvas);
    _rrect(canvas, 45.75, 30, 4.5, 50, 2.25, _trunk(GQColors.primary));
    _rotatedOval(canvas, 32, 62, 13, 7, _foliage(GQColors.moodSlateLavender), -22);
    _rotatedOval(canvas, 64, 57, 13, 7, _foliage(GQColors.moodPeri), 22);
    _rotatedOval(canvas, 34, 45, 12, 6.5, _foliage(GQColors.moodPeri), -18);
    _rotatedOval(canvas, 62, 40, 12, 6.5, _foliage(GQColors.primary), 18);
    _circle(canvas, 48, 27, 5, _accent(GQColors.moodCoralPeach));
  }

  /// Stage 4 — Young tree (400 XP):
  /// shadow + trunk + canopy + highlight + life accent.
  void _paintYoungTree(Canvas canvas) {
    _shadow(canvas);
    _rrect(canvas, 44, 48, 8, 32, 4, _trunk(GQColors.ink2));
    _circle(canvas, 48, 35, 22, _foliage(GQColors.primary));
    if (!simplified) {
      _circle(canvas, 39, 27, 8.5, _foliage(GQColors.moodPeri), opacity: 0.5);
      _circle(canvas, 65, 23, 5, _accent(GQColors.moodCoralPeach));
    }
  }

  /// Stage 5 — Mature tree (1000 XP):
  /// shadow + trunk + three canopies + life accent + secondary accent.
  void _paintMatureTree(Canvas canvas) {
    _shadow(canvas);
    _rrect(canvas, 43, 44, 10, 36, 5, _trunk(GQColors.ink2));
    _circle(canvas, 29, 40, 17, _foliage(GQColors.moodPeri));
    _circle(canvas, 67, 40, 17, _foliage(GQColors.primaryDk));
    _circle(canvas, 48, 25, 21, _foliage(GQColors.primary));
    if (!simplified) {
      _circle(canvas, 69, 20, 5.5, _accent(GQColors.moodCoralPeach));
      _circle(canvas, 30, 27, 4, _accent(GQColors.moodGood));
    }
  }
}
