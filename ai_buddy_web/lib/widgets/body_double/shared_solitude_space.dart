import 'dart:async';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/companion_provider.dart';
import '../../theme/gq_tokens.dart';
import '../companion_painter.dart';
import 'body_double_start_sheet.dart';

/// SharedSolitudeSpace — Fable #4: Shared Solitude (body doubling as presence).
///
/// A room, not a timer. The user sits next to others (and Quest) in a dusk
/// gradient with two breathing ambient glow fields. There is NO clock, NO
/// countdown, NO progress bar, NO participant count on screen by default.
///
/// Pull down (or tap the top area) to whisper the elapsed time — never the
/// remaining time. When the chosen duration elapses, the room returns gently:
/// no bell, no vibration. The dusk gradient eases to gq-bg over 45s, two lines
/// fade in, and two buttons offer "I'm done" (+5 XP, silent) or "Stay a while
/// longer" (cancels the return, resumes the dusk from where it stood).
///
/// The silent clock is driven by a tick-based [Timer] owned here (mirroring
/// the original `InteractiveChatScreen` tick model) so widget tests can drive
/// it deterministically with `tester.pump` under fake-async.
class SharedSolitudeSpace extends StatefulWidget {
  const SharedSolitudeSpace({
    super.key,
    required this.intention,
    required this.total,
    required this.onDone,
  });

  /// The user's free-text intention, shown faintly at the top.
  final String intention;

  /// Planned session length. Use [kBodyDoubleOpenEnded] for "When I leave".
  final Duration total;

  /// Called when the user taps "I'm done" on the return screen. The caller
  /// is responsible for the silent +5 XP check-in and navigation pop.
  final VoidCallback onDone;

  @override
  State<SharedSolitudeSpace> createState() => _SharedSolitudeSpaceState();
}

class _SharedSolitudeSpaceState extends State<SharedSolitudeSpace>
    with TickerProviderStateMixin {
  // ── Silent clock ──────────────────────────────────────────────────────────
  Timer? _ticker;
  Duration _elapsed = Duration.zero;
  bool _returned = false;

  // ── Entry transition ──────────────────────────────────────────────────────
  late final AnimationController _enterCtrl;
  late final Animation<double> _enterAnim;

  // ── Glow breathing ────────────────────────────────────────────────────────
  late final AnimationController _glow1Ctrl;
  late final Animation<double> _glow1Anim;
  late final AnimationController _glow2Ctrl;
  late final Animation<double> _glow2Anim;

  // ── Companion breathing (mid-cycle start) ─────────────────────────────────
  late final AnimationController _companionCtrl;
  late final Animation<double> _companionAnim;

  // ── Pull-down time whisper ────────────────────────────────────────────────
  bool _whisperVisible = false;
  Timer? _whisperHideTimer;

  // ── Return transition ─────────────────────────────────────────────────────
  late final AnimationController _returnCtrl;
  late final Animation<double> _returnBgAnim;
  late final AnimationController _returnLinesCtrl;
  late final Animation<double> _returnLinesAnim;

  @override
  void initState() {
    super.initState();

    _enterCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.roomEnter,
    );
    _enterAnim = CurvedAnimation(
      parent: _enterCtrl,
      curve: Curves.easeOut,
    );
    _enterCtrl.forward();

    _glow1Ctrl = AnimationController(
      vsync: this,
      duration: GQDurations.glowBreathe1,
    );
    _glow1Anim = Tween<double>(begin: 0.45, end: 0.75).animate(
      CurvedAnimation(parent: _glow1Ctrl, curve: Curves.easeInOut),
    )..addStatusListener((s) {
        if (s == AnimationStatus.completed) _glow1Ctrl.reverse();
        if (s == AnimationStatus.dismissed) _glow1Ctrl.forward();
      });
    _glow1Ctrl.forward();

    _glow2Ctrl = AnimationController(
      vsync: this,
      duration: GQDurations.glowBreathe2,
    );
    _glow2Anim = Tween<double>(begin: 0.40, end: 0.70).animate(
      CurvedAnimation(parent: _glow2Ctrl, curve: Curves.easeInOut),
    )..addStatusListener((s) {
        if (s == AnimationStatus.completed) _glow2Ctrl.reverse();
        if (s == AnimationStatus.dismissed) _glow2Ctrl.forward();
      });
    _glow2Ctrl.forward();

    _companionCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    );
    _companionAnim = Tween<double>(begin: 0.96, end: 1.04).animate(
      CurvedAnimation(parent: _companionCtrl, curve: Curves.easeInOut),
    )..addStatusListener((s) {
        if (s == AnimationStatus.completed) _companionCtrl.reverse();
        if (s == AnimationStatus.dismissed) _companionCtrl.forward();
      });
    // Mid-cycle start: jump to the middle of the first cycle so the
    // companion is already breathing when it walks in.
    _companionCtrl.value = 0.5;
    _companionCtrl.forward();

    _returnCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.roomReturn,
    );
    _returnBgAnim = CurvedAnimation(
      parent: _returnCtrl,
      curve: Curves.easeInOut,
    );

    _returnLinesCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _returnLinesAnim = CurvedAnimation(
      parent: _returnLinesCtrl,
      curve: Curves.easeIn,
    );

    // Open-ended sessions never auto-return; the "Step out" button is the
    // only exit. For fixed durations, tick the silent clock.
    if (widget.total != kBodyDoubleOpenEnded) {
      _ticker = Timer.periodic(const Duration(seconds: 1), _onTick);
    }
  }

  void _onTick(Timer t) {
    if (_returned) {
      t.cancel();
      return;
    }
    final next = _elapsed + const Duration(seconds: 1);
    if (next >= widget.total) {
      setState(() {
        _elapsed = widget.total;
        _returned = true;
      });
      t.cancel();
      _beginReturn();
      return;
    }
    setState(() => _elapsed = next);
  }

  void _beginReturn() {
    _returnCtrl.forward();
    // At 20s into the 45s return, fade in the lines + buttons.
    Future.delayed(const Duration(seconds: 20), () {
      if (mounted && _returned) {
        _returnLinesCtrl.forward();
      }
    });
  }

  /// "Stay a while longer" — cancels the return transition and resumes the
  /// dusk from where it stood. The silent clock does NOT restart; the user
  /// is now in open-ended mode.
  void _stayLonger() {
    _returnCtrl.stop();
    _returnCtrl.reset();
    _returnLinesCtrl.stop();
    _returnLinesCtrl.reset();
    setState(() => _returned = false);
  }

  /// "I'm done" — silent +5 XP via CompanionProvider.checkIn(), then pop.
  void _imDone() {
    context.read<CompanionProvider>().checkIn();
    widget.onDone();
  }

  /// Step out early (before the room returns on its own).
  void _stepOut() {
    _ticker?.cancel();
    Navigator.of(context).maybePop();
  }

  void _showWhisper() {
    _whisperHideTimer?.cancel();
    setState(() => _whisperVisible = true);
    _whisperHideTimer = Timer(const Duration(milliseconds: 2500), () {
      if (mounted) {
        // 300ms fade-out, then hide.
        setState(() => _whisperVisible = false);
      }
    });
  }

  String _formatElapsed(Duration d) {
    final m = d.inMinutes;
    if (m < 1) return 'less than a minute together';
    return '$m minute${m == 1 ? '' : 's'} together';
  }

  @override
  void dispose() {
    _ticker?.cancel();
    _whisperHideTimer?.cancel();
    _enterCtrl.dispose();
    _glow1Ctrl.dispose();
    _glow2Ctrl.dispose();
    _companionCtrl.dispose();
    _returnCtrl.dispose();
    _returnLinesCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: GestureDetector(
        // Tap anywhere dismisses a visible whisper; pull-down / tap-top shows it.
        onTap: _whisperVisible ? () => setState(() => _whisperVisible = false) : null,
        child: NotificationListener<ScrollNotification>(
          onNotification: (n) {
            if (n is OverscrollNotification && n.overscroll < 0) {
              _showWhisper();
            }
            return false;
          },
          child: _buildStack(context),
        ),
      ),
    );
  }

  Widget _buildStack(BuildContext context) {
    final size = MediaQuery.of(context).size;
    return Stack(
      fit: StackFit.expand,
      children: [
        // ── Dusk gradient (with return fade to gq-bg) ────────────────────────
        AnimatedBuilder(
          animation: _returnBgAnim,
          builder: (context, _) {
            return Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Color.lerp(
                        GQColors.duskTop, GQColors.softBg, _returnBgAnim.value)!,
                    Color.lerp(
                        GQColors.duskMid, GQColors.softBg, _returnBgAnim.value)!,
                    Color.lerp(
                        GQColors.duskBottom, GQColors.softBg, _returnBgAnim.value)!,
                  ],
                ),
              ),
            );
          },
        ),

        // ── Ambient glow fields ─────────────────────────────────────────────
        AnimatedBuilder(
          animation: Listenable.merge([_enterAnim, _glow1Anim]),
          builder: (context, _) {
            return Positioned(
              top: -60,
              left: -40,
              child: IgnorePointer(
                child: Opacity(
                  opacity: _enterAnim.value,
                  child: Container(
                    width: 300,
                    height: 300,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: GQColors.glowTopLeft
                          .withValues(alpha: _glow1Anim.value),
                    ),
                    child: BackdropFilter(
                      filter: ui.ImageFilter.blur(sigmaX: 60, sigmaY: 60),
                      child: const SizedBox.shrink(),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
        AnimatedBuilder(
          animation: Listenable.merge([_enterAnim, _glow2Anim]),
          builder: (context, _) {
            return Positioned(
              top: -40,
              right: -50,
              child: IgnorePointer(
                child: Opacity(
                  opacity: _enterAnim.value,
                  child: Container(
                    width: 280,
                    height: 280,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: GQColors.glowTopRight
                          .withValues(alpha: _glow2Anim.value),
                    ),
                    child: BackdropFilter(
                      filter: ui.ImageFilter.blur(sigmaX: 60, sigmaY: 60),
                      child: const SizedBox.shrink(),
                    ),
                  ),
                ),
              ),
            );
          },
        ),

        // ── Top tap target (pull-down whisper trigger) ──────────────────────
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          height: 120,
          child: GestureDetector(
            behavior: HitTestBehavior.translucent,
            onTap: _showWhisper,
            child: const SizedBox.expand(),
          ),
        ),

        // ── Intention (faint Fraunces serif italic) ─────────────────────────
        Positioned(
          top: 64,
          left: 0,
          right: 0,
          child: Center(
            child: Opacity(
              opacity: _enterAnim.value * 0.8,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Text(
                  widget.intention,
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontFamily: GQTypography.journalSerif,
                    fontStyle: FontStyle.italic,
                    fontSize: 16,
                    color: GQColors.ink2,
                    height: 1.4,
                  ),
                ),
              ),
            ),
          ),
        ),

        // ── Companion (88px, centered, breathing) ───────────────────────────
        Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(height: size.height * 0.18),
              AnimatedBuilder(
                animation: Listenable.merge([_enterAnim, _companionAnim]),
                builder: (context, child) {
                  return Opacity(
                    opacity: _enterAnim.value,
                    child: Transform.scale(
                      scale: _companionAnim.value,
                      child: child,
                    ),
                  );
                },
                child: SizedBox(
                  width: 88,
                  height: 88,
                  child: CustomPaint(
                    key: const Key('shared_solitude_companion'),
                    size: const Size(88, 88),
                    painter: CompanionPainter(
                      stage: context
                              .read<CompanionProvider>()
                              .getGrowthStage(),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 18),
              Opacity(
                opacity: _enterAnim.value,
                child: const Text(
                  'Others are here too.',
                  key: Key('shared_solitude_others_here'),
                  style: TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink2,
                  ),
                ),
              ),
            ],
          ),
        ),

        // ── Step out button (bottom) ────────────────────────────────────────
        Positioned(
          left: 0,
          right: 0,
          bottom: 48,
          child: Center(
            child: Opacity(
              opacity: _enterAnim.value,
              child: ConstrainedBox(
                constraints: const BoxConstraints(minHeight: 44),
                child: Material(
                  color: Colors.white.withValues(alpha: 0.6),
                  shape: StadiumBorder(
                    side: BorderSide(color: GQColors.hair),
                  ),
                  child: InkWell(
                    key: const Key('shared_solitude_step_out'),
                    customBorder: const StadiumBorder(),
                    onTap: _stepOut,
                    child: const Padding(
                      padding:
                          EdgeInsets.symmetric(horizontal: 28, vertical: 12),
                      child: Text(
                        'Step out',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: GQColors.ink2,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),

        // ── Pull-down time whisper pill ─────────────────────────────────────
        if (_whisperVisible)
          Positioned(
            top: 56,
            left: 0,
            right: 0,
            child: Center(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                child: Container(
                  key: const Key('shared_solitude_whisper'),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.7),
                    borderRadius: BorderRadius.circular(GQRadii.button),
                    border: Border.all(color: GQColors.hair),
                  ),
                  child: Text(
                    _formatElapsed(_elapsed),
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: GQColors.ink2,
                    ),
                  ),
                ),
              ),
            ),
          ),

        // ── Return overlay (lines + buttons) ────────────────────────────────
        if (_returned)
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _returnLinesAnim,
              builder: (context, _) {
                return Opacity(
                  opacity: _returnLinesAnim.value,
                  child: _buildReturnOverlay(context),
                );
              },
            ),
          ),
      ],
    );
  }

  Widget _buildReturnOverlay(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Spacer(flex: 3),
          const Text(
            "That's the time you set aside.",
            key: Key('shared_solitude_return_line1'),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: GQTypography.journalSerif,
              fontSize: 19,
              color: GQColors.ink,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'The room keeps no record.',
            key: Key('shared_solitude_return_line2'),
            style: TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w600,
              color: GQColors.ink2,
            ),
          ),
          const Spacer(flex: 2),
          ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 44),
            child: ElevatedButton(
              key: const Key('shared_solitude_im_done'),
              onPressed: _imDone,
              style: ElevatedButton.styleFrom(
                backgroundColor: GQColors.primaryDk,
                foregroundColor: Colors.white,
                padding:
                    const EdgeInsets.symmetric(horizontal: 36, vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(GQRadii.button),
                ),
              ),
              child: const Text(
                "I'm done",
                style: TextStyle(
                  fontSize: 14.5,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          GestureDetector(
            key: const Key('shared_solitude_stay_longer'),
            onTap: _stayLonger,
            behavior: HitTestBehavior.opaque,
            child: const SizedBox(
              height: 44,
              child: Center(
                child: Text(
                  'Stay a while longer',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: GQColors.primaryDk,
                  ),
                ),
              ),
            ),
          ),
          const Spacer(flex: 3),
        ],
      ),
    );
  }
}
