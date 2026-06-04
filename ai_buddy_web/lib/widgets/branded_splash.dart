import 'package:flutter/material.dart';

class BrandedSplash extends StatefulWidget {
  const BrandedSplash({super.key});

  @override
  State<BrandedSplash> createState() => _BrandedSplashState();
}

class _BrandedSplashState extends State<BrandedSplash>
    with TickerProviderStateMixin {
  late final AnimationController _breath;
  late final AnimationController _fade;

  @override
  void initState() {
    super.initState();
    _breath = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2400),
    )..repeat(reverse: true);
    _fade = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    )..forward();
  }

  @override
  void dispose() {
    _breath.dispose();
    _fade.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const wordmarkColor = Color(0xFF1F1B3A);
    return Scaffold(
      body: SizedBox.expand(
        child: DecoratedBox(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Color(0xFFF8F7FF), Color(0xFFF8F7FF), Color(0xFFEEF0FE)],
              stops: [0.0, 0.38, 1.0],
            ),
          ),
          child: SafeArea(
            child: FadeTransition(
              opacity: _fade,
              child: AnimatedBuilder(
                animation: _breath,
                builder: (context, _) {
                  final t = Curves.easeInOut.transform(_breath.value);
                  return Stack(
                    fit: StackFit.expand,
                    alignment: Alignment.center,
                    children: [
                      CustomPaint(
                        painter: _AmbientGlowPainter(progress: t),
                      ),
                      Center(
                        child: Transform.translate(
                          offset: const Offset(0, -40),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text(
                                'GentleQuest',
                                style: TextStyle(
                                  fontSize: 34,
                                  fontWeight: FontWeight.w600,
                                  color: wordmarkColor,
                                  letterSpacing: -0.6,
                                ),
                              ),
                              const SizedBox(height: 56),
                              SizedBox(
                                width: 200,
                                height: 200,
                                child: CustomPaint(
                                  painter: _BreathCirclePainter(progress: t),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _AmbientGlowPainter extends CustomPainter {
  _AmbientGlowPainter({required this.progress});
  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2 + 40);
    final ambientR = size.shortestSide * (0.7 + 0.04 * progress);
    final ambient = Paint()
      ..shader = RadialGradient(
        colors: [
          const Color(0xFF667EEA).withValues(alpha: 0.30 + 0.10 * progress),
          const Color(0xFF667EEA).withValues(alpha: 0.13 + 0.05 * progress),
          const Color(0xFF667EEA).withValues(alpha: 0.04),
          Colors.transparent,
        ],
        stops: const [0.0, 0.28, 0.55, 0.72],
      ).createShader(Rect.fromCircle(center: center, radius: ambientR))
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 14);
    canvas.drawCircle(center, ambientR, ambient);

    final under = Paint()
      ..shader = RadialGradient(
        colors: [
          const Color(0xFF4F63C9).withValues(alpha: 0.20),
          const Color(0xFF4F63C9).withValues(alpha: 0.07),
          Colors.transparent,
        ],
        stops: const [0.0, 0.5, 0.8],
      ).createShader(Rect.fromCircle(
        center: Offset(size.width / 2, size.height / 2 + 100),
        radius: size.shortestSide * 0.36,
      ))
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(size.width / 2, size.height / 2 + 100),
        width: size.shortestSide * 0.72,
        height: 56,
      ),
      under,
    );
  }

  @override
  bool shouldRepaint(covariant _AmbientGlowPainter old) =>
      old.progress != progress;
}

class _BreathCirclePainter extends CustomPainter {
  _BreathCirclePainter({required this.progress});
  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final minSide = size.shortestSide;

    final outerR = minSide * (0.42 + 0.06 * progress);
    final midR = minSide * (0.30 + 0.04 * progress);
    final innerR = minSide * (0.18 + 0.02 * progress);
    final orbR = minSide * 0.10;

    final outer = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..color = const Color(0xFFB5C2F3).withValues(alpha: 0.35 + 0.20 * progress);
    canvas.drawCircle(center, outerR, outer);

    final mid = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0
      ..color = const Color(0xFF8FA1ED).withValues(alpha: 0.55 + 0.20 * progress);
    canvas.drawCircle(center, midR, mid);

    final inner = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..color = const Color(0xFF4F63C9).withValues(alpha: 0.75 + 0.15 * progress);
    canvas.drawCircle(center, innerR, inner);

    final orb = Paint()
      ..shader = RadialGradient(
        colors: const [
          Color(0xFF667EEA),
          Color(0xFF4F63C9),
          Color(0xFF1F1B3A),
        ],
        stops: const [0.0, 0.7, 1.0],
      ).createShader(Rect.fromCircle(center: center, radius: orbR));
    canvas.drawCircle(center, orbR, orb);
  }

  @override
  bool shouldRepaint(covariant _BreathCirclePainter old) =>
      old.progress != progress;
}
