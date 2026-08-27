// Interactive chat — shared widgets (crisis chip, typing dots, breathing orb).
// Split from interactive_chat_screen.dart.

import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/utils/size_utils.dart';
import '../../theme/gq_tokens.dart';
import '../../theme/gq_theme.dart';

// Risk pill removed from UI; actionable chips remain.

class CrisisChip extends StatelessWidget {
  const CrisisChip(
      {super.key,
      required this.name,
      required this.phone,
      this.textInstr = ''});
  final String name;
  final String
      phone; // may be empty when only text instructions exist (e.g., "HOME to 741741")
  final String textInstr;

  Future<void> _onTap(BuildContext context) async {
    final p = phone.trim();
    final t = textInstr.trim();
    if (p.isNotEmpty) {
      final tel = Uri(scheme: 'tel', path: p);
      try {
        final can = await canLaunchUrl(tel);
        if (can) {
          final ok = await launchUrl(tel, mode: LaunchMode.externalApplication);
          if (!ok) {
            // Fall back to copy
            await Clipboard.setData(ClipboardData(text: p));
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                    content: Text(
                        'Couldn\'t open dialer. Number copied to clipboard.')),
              );
            }
          }
        } else {
          await Clipboard.setData(ClipboardData(text: p));
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                  content:
                      Text('Call not supported. Number copied to clipboard.')),
            );
          }
        }
      } catch (e) {
        if (kDebugMode) debugPrint('tel: launch error: $e');
        await Clipboard.setData(ClipboardData(text: p));
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
                content: Text('Number copied to clipboard. Dial manually.')),
          );
        }
      }
      return;
    }
    if (t.isNotEmpty) {
      // Attempt to parse patterns like "HOME to 741741"
      String s = t;
      if (s.toLowerCase().startsWith('text ')) {
        s = s.substring(5).trim();
      }
      final reg = RegExp(r'^(.+?)\s+to\s+(\d+)$', caseSensitive: false);
      final m = reg.firstMatch(s);
      if (m != null) {
        final body = m.group(1)!.trim();
        final to = m.group(2)!.trim();
        final sms =
            Uri(scheme: 'sms', path: to, queryParameters: {'body': body});
        try {
          final can = await canLaunchUrl(sms);
          if (can) {
            final ok =
                await launchUrl(sms, mode: LaunchMode.externalApplication);
            if (!ok) {
              await Clipboard.setData(ClipboardData(text: t));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                      content:
                          Text('Couldn\'t open SMS. Instructions copied.')),
                );
              }
            }
          } else {
            await Clipboard.setData(ClipboardData(text: t));
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                    content: Text('SMS not supported. Instructions copied.')),
              );
            }
          }
        } catch (e) {
          if (kDebugMode) debugPrint('sms: launch error: $e');
          await Clipboard.setData(ClipboardData(text: t));
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                  content: Text('Instructions copied to clipboard.')),
            );
          }
        }
      } else {
        await Clipboard.setData(ClipboardData(text: t));
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Instructions copied to clipboard.')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final hasName = name.trim().isNotEmpty;
    final hasPhone = phone.trim().isNotEmpty;
    final hasText = textInstr.trim().isNotEmpty;
    final label = () {
      if (hasName && hasPhone) return '$name · ${phone.trim()}';
      if (hasName && hasText) return '$name · ${textInstr.trim()}';
      if (hasPhone) return phone.trim();
      if (hasText) return textInstr.trim();
      if (hasName) return name.trim();
      return '';
    }();
    if (label.isEmpty) return const SizedBox.shrink();
    final semanticsLabel = () {
      if (hasPhone && hasName) return 'Call $name at ${phone.trim()}';
      if (hasPhone) return 'Call ${phone.trim()}';
      if (hasText && hasName) return '$name: ${textInstr.trim()}';
      if (hasText) return textInstr.trim();
      return label;
    }();
    return Semantics(
      button: true,
      label: semanticsLabel,
      onTapHint: (hasPhone || hasText) ? 'Activate' : null,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: (hasPhone || hasText) ? () => _onTap(context) : null,
        onLongPress: (hasPhone || hasText)
            ? () async {
                final toCopy = hasPhone
                    ? phone.trim()
                    : (hasText ? textInstr.trim() : name.trim());
                await Clipboard.setData(ClipboardData(text: toCopy));
                if (kDebugMode) debugPrint('Copied crisis info: $toCopy');
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Copied to clipboard.')),
                  );
                }
              }
            : null,
        child: ConstrainedBox(
          constraints: BoxConstraints(minWidth: 44.h, minHeight: 36.h),
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 12.h, vertical: 8.h),
            decoration: BoxDecoration(
              color: t.primarySoft,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: t.hair),
            ),
            child: Center(
              child: Text(
                label,
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontSize: 12.0,
                    fontWeight: FontWeight.w500,
                    color: t.ink),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class TypingDots extends StatefulWidget {
  const TypingDots({super.key});
  @override
  State<TypingDots> createState() => _TypingDotsState();
}

class _TypingDotsState extends State<TypingDots>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1000));
  bool _reduceMotion = false;
  // The first didChangeDependencies pass must ALWAYS apply, even when rm
  // equals the initial `false`. Without this the equality guard below
  // early-returns on first mount and the animation is never started at
  // all — the failure is invisible to tests because nothing asserts that
  // a perpetual animation is actually running.
  bool _motionGateInitialised = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // ADR-006: respect quiet-mode reduced motion.
    final rm = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (_motionGateInitialised && rm == _reduceMotion) return;
    _motionGateInitialised = true;
    _reduceMotion = rm;
    if (rm) {
      _c.stop();
    } else {
      _c.repeat();
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // shimmer base — Material default expected (agent ruling 2026-05-22 keep raw)
    final baseColor = Colors.grey.shade500;
    final reduceMotion =
        _reduceMotion || MediaQuery.of(context).accessibleNavigation;
    if (reduceMotion) {
      if (_c.isAnimating) _c.stop();
      // Static dots for reduced motion
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (i) {
          return Container(
            margin: EdgeInsets.symmetric(horizontal: 3.h),
            width: 8.h,
            height: 8.h,
            decoration: BoxDecoration(
              color: baseColor.withValues(alpha: 0.6),
              shape: BoxShape.circle,
            ),
          );
        }),
      );
    }
    if (!_c.isAnimating) _c.repeat();
    return AnimatedBuilder(
      animation: _c,
      builder: (context, _) {
        double v(int i) {
          final t = (_c.value + (i * 0.2)) % 1.0;
          return (0.5 + 0.5 * math.sin(2 * math.pi * t)).clamp(0.0, 1.0);
        }

        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            return Container(
              margin: EdgeInsets.symmetric(horizontal: 3.h),
              width: 8.h,
              height: 8.h,
              decoration: BoxDecoration(
                color: baseColor.withValues(alpha: v(i)),
                shape: BoxShape.circle,
              ),
            );
          }),
        );
      },
    );
  }
}

/// R1D6 — BreathingOrb: 5.6 s gentle scale pulse using GQDurations.breathe.
/// Renders a soft coral circle that inhales/exhales to create a calming rhythm.
class BreathingOrb extends StatefulWidget {
  const BreathingOrb({super.key});

  @override
  State<BreathingOrb> createState() => _BreathingOrbState();
}

class _BreathingOrbState extends State<BreathingOrb>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scale;
  bool _reduceMotion = false;
  // The first didChangeDependencies pass must ALWAYS apply, even when rm
  // equals the initial `false`. Without this the equality guard below
  // early-returns on first mount and the animation is never started at
  // all — the failure is invisible to tests because nothing asserts that
  // a perpetual animation is actually running.
  bool _motionGateInitialised = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // ADR-006: respect quiet-mode reduced motion.
    final rm = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (_motionGateInitialised && rm == _reduceMotion) return;
    _motionGateInitialised = true;
    _reduceMotion = rm;
    if (rm) {
      _controller.stop();
    } else {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    );
    _scale = Tween<double>(begin: 0.88, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduceMotion =
        _reduceMotion || MediaQuery.of(context).accessibleNavigation;
    if (reduceMotion) {
      return _orbShape(1.0);
    }
    return AnimatedBuilder(
      animation: _scale,
      builder: (_, __) => _orbShape(_scale.value),
    );
  }

  Widget _orbShape(double scale) {
    // State.context is in scope here even without a build parameter.
    final t = GQTheme.of(context);
    return Transform.scale(
      scale: scale,
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: t.accentSoft,
          border: Border.all(
            color: t.coral.withValues(alpha: 0.35),
            width: 1.5,
          ),
        ),
        child: Center(
          child: Icon(
            Icons.favorite_rounded,
            size: 22,
            color: t.coral,
          ),
        ),
      ),
    );
  }
}
