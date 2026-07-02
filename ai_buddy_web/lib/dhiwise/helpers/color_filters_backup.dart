/// Color filter helpers, originally used in the Reminder card image.
/// Reused by theme/low_stim_mode.dart (v1.5.0 low-stim "quiet mode",
/// ADR-006) to desaturate the app-wide palette — no longer dormant.
library;

/// Returns a 4x5 saturation color matrix suitable for ColorFilter.matrix.
///
/// s = 1.0 keeps original saturation.
/// s > 1.0 increases saturation.
/// s < 1.0 decreases saturation.
List<double> saturationMatrix(double s) {
  final double a = 0.213 * (1 - s) + s;
  final double b = 0.715 * (1 - s);
  final double c = 0.072 * (1 - s);
  return <double>[
    a,
    b,
    c,
    0,
    0,
    0.213 * (1 - s),
    0.715 * (1 - s) + s,
    0.072 * (1 - s),
    0,
    0,
    0.213 * (1 - s),
    0.715 * (1 - s),
    0.072 * (1 - s) + s,
    0,
    0,
    0,
    0,
    0,
    1,
    0,
  ];
}
