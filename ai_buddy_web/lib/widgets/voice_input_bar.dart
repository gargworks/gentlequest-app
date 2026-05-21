import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../theme/gq_tokens.dart';

/// VoiceInputBar — State D (R1D7 Chat Active States)
///
/// Replaces the standard ChatInputBar in-place during voice recording.
/// Now actually transcribes via the on-device speech_to_text package
/// (Apple Speech on iOS, SpeechRecognizer on Android). Cloud fallback is
/// disabled per the verbatim "your voice is staying on this device" promise.
///
/// Design source: GentleQuest_Chat_Active_States.html — Mockup D.
/// Copy verbatim:
///   "Cancel"
///   "Stop"
///   "your voice is staying on this device"
///
/// Callbacks:
///   onStop        — user taps Stop; caller receives final transcript text
///   onCancel      — user taps Cancel; discards audio + transcript
///   onUnsupported — fires once if on-device speech recognition is not
///                   available (permission denied, language unsupported,
///                   platform unsupported). Caller should swap to a
///                   "Voice input isn't supported here — please type" hint.
///
/// Cap: 60s — auto-stops after 60 seconds.
class VoiceInputBar extends StatefulWidget {
  const VoiceInputBar({
    super.key,
    required this.onStop,
    required this.onCancel,
    this.onUnsupported,
    this.liveTranscript = '',
  });

  final void Function(String transcript) onStop;
  final VoidCallback onCancel;

  /// Optional callback invoked when speech_to_text fails to initialize on
  /// this device (permission denied, no on-device recognizer, etc.). Caller
  /// is expected to dismiss the voice bar and show a graceful fallback hint.
  final VoidCallback? onUnsupported;

  /// Live transcript text — kept for API back-compat. Internal state takes
  /// precedence once recognition starts.
  final String liveTranscript;

  @override
  State<VoiceInputBar> createState() => _VoiceInputBarState();
}

class _VoiceInputBarState extends State<VoiceInputBar>
    with TickerProviderStateMixin {
  // Waveform: 16 bars · 900ms animation · stagger 60–280ms (per HTML spec)
  late final AnimationController _waveCtrl = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
  )..repeat();

  // Ring pulse: 1600ms ease-out per HTML
  late final AnimationController _ringCtrl = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1600),
  )..repeat();

  // Elapsed timer
  late final AnimationController _elapsedCtrl = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 60), // 60s cap
  )..forward();

  // Bar animation delays (60–280ms stagger from HTML)
  static const _barDelays = [
    0, 60, 120, 180, 80, 200, 280, 140,
    240, 100, 220, 160, 40, 280, 120, 200,
  ];
  // Bar heights (from HTML — as fraction of container height)
  static const _barHeights = [
    0.30, 0.55, 0.80, 0.45, 0.95, 0.60, 0.30, 0.75,
    0.50, 0.90, 0.40, 0.65, 0.30, 0.80, 0.55, 0.70,
  ];

  // speech_to_text engine + live transcript state
  final stt.SpeechToText _speech = stt.SpeechToText();
  String _transcript = '';
  bool _engineReady = false;

  @override
  void initState() {
    super.initState();
    _transcript = widget.liveTranscript;
    // Auto-stop at 60s cap
    _elapsedCtrl.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _onStop();
      }
    });
    // Boot the speech engine and start listening. Failures here surface to
    // the caller via onUnsupported so the input bar can swap to a fallback.
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    try {
      final available = await _speech.initialize(
        onStatus: (status) {
          if (kDebugMode) debugPrint('[voice] status=$status');
          // 'done' / 'notListening' after a natural pause → finalize.
          if (status == 'done' || status == 'notListening') {
            if (mounted && _speech.isAvailable && !_speech.isListening) {
              // If we got a transcript, propagate it via onStop; otherwise
              // leave the user to tap Stop manually.
              if (_transcript.trim().isNotEmpty) {
                _onStop();
              }
            }
          }
        },
        onError: (err) {
          if (kDebugMode) debugPrint('[voice] error=${err.errorMsg}');
          // Permission-denied / no-recognizer / network failures all land here.
          // Treat as unsupported and bail out so the caller can fall back.
          if (mounted) widget.onUnsupported?.call();
        },
      );
      if (!available) {
        widget.onUnsupported?.call();
        return;
      }
      if (!mounted) return;
      setState(() => _engineReady = true);
      await _speech.listen(
        onResult: (result) {
          if (!mounted) return;
          setState(() => _transcript = result.recognizedWords);
        },
        // Force on-device recognition to honor the verbatim privacy promise.
        // Devices that don't support on-device for the user's locale will
        // surface via onError → onUnsupported above.
        listenOptions: stt.SpeechListenOptions(
          onDevice: true,
          partialResults: true,
          listenMode: stt.ListenMode.dictation,
          cancelOnError: true,
          listenFor: const Duration(seconds: 60),
          pauseFor: const Duration(seconds: 3),
        ),
      );
    } catch (e) {
      if (kDebugMode) debugPrint('[voice] init exception: $e');
      if (mounted) widget.onUnsupported?.call();
    }
  }

  @override
  void dispose() {
    // Stop any in-flight recognition before tearing down controllers.
    if (_speech.isListening) {
      _speech.cancel();
    }
    _waveCtrl.dispose();
    _ringCtrl.dispose();
    _elapsedCtrl.dispose();
    super.dispose();
  }

  void _onStop() {
    if (_speech.isListening) {
      _speech.stop();
    }
    widget.onStop(_transcript);
  }

  void _onCancel() {
    if (_speech.isListening) {
      _speech.cancel();
    }
    widget.onCancel();
  }

  String _formatElapsed() {
    final secs = (_elapsedCtrl.value * 60).round();
    final m = secs ~/ 60;
    final s = secs % 60;
    return '$m:${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.of(context).accessibleNavigation;

    return Container(
      padding: const EdgeInsets.fromLTRB(12, 14, 12, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Top row: Cancel + elapsed timer with pulsing dot
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 2),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Semantics(
                  button: true,
                  label: 'Cancel voice input',
                  child: GestureDetector(
                    onTap: _onCancel,
                    child: const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      child: Text(
                        // Verbatim from HTML
                        'Cancel',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: GQColors.ink3,
                        ),
                      ),
                    ),
                  ),
                ),
                // Pulsing rec dot + elapsed counter
                AnimatedBuilder(
                  animation: _elapsedCtrl,
                  builder: (ctx, _) {
                    return Row(
                      children: [
                        AnimatedBuilder(
                          animation: _ringCtrl,
                          builder: (ctx, _) {
                            final pulse = math.sin(_ringCtrl.value * math.pi * 2);
                            final opacity = (0.6 + 0.4 * pulse).clamp(0.0, 1.0);
                            return Container(
                              width: 7,
                              height: 7,
                              decoration: BoxDecoration(
                                color: GQColors.coral
                                    .withValues(alpha: opacity),
                                shape: BoxShape.circle,
                              ),
                            );
                          },
                        ),
                        const SizedBox(width: 6),
                        Text(
                          _formatElapsed(),
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            color: GQColors.ink,
                            fontFeatures: [FontFeature.tabularFigures()],
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // Voice input bar with conic gradient ring
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(GQRadii.button),
              // Conic gradient approximated as sweep gradient ring
              gradient: const SweepGradient(
                colors: [GQColors.coral, GQColors.primary, GQColors.coral],
                startAngle: math.pi / 2,
                endAngle: math.pi * 2.5,
              ),
            ),
            padding: const EdgeInsets.all(2),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(GQRadii.button),
              ),
              padding: const EdgeInsets.fromLTRB(14, 6, 6, 6),
              child: Row(
                children: [
                  // Mini waveform inside bar (6 bars per HTML)
                  _buildMiniWaveform(reduceMotion),
                  const SizedBox(width: 8),
                  // Live transcript text
                  Expanded(
                    child: Text(
                      _transcript.isNotEmpty
                          ? _transcript
                          : (_engineReady ? 'Listening…' : 'Starting…'),
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                        color: GQColors.ink3,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Stop button — coral
                  Semantics(
                    button: true,
                    label: 'Stop recording',
                    child: GestureDetector(
                      onTap: _onStop,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 8),
                        decoration: BoxDecoration(
                          color: GQColors.coral,
                          borderRadius: BorderRadius.circular(GQRadii.button),
                          boxShadow: const [
                            BoxShadow(
                              color: Color(0x8CFF6B6B),
                              blurRadius: 18,
                              offset: Offset(0, 8),
                              spreadRadius: -8,
                            ),
                          ],
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 10,
                              height: 10,
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                            const SizedBox(width: 6),
                            const Text(
                              // Verbatim from HTML
                              'Stop',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 10),

          // Full 16-bar waveform below the input bar
          _buildFullWaveform(reduceMotion),
        ],
      ),
    );
  }

  Widget _buildMiniWaveform(bool reduceMotion) {
    // 6 bars for the mini waveform inside the bar
    const miniDelays = [0, 90, 180, 60, 220, 130];
    const miniHeights = [0.60, 0.90, 0.45, 0.75, 0.30, 0.55];

    return SizedBox(
      height: 22,
      child: AnimatedBuilder(
        animation: _waveCtrl,
        builder: (ctx, _) {
          return Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: List.generate(6, (i) {
              final barH = reduceMotion
                  ? 0.5
                  : _waveHeight(i, miniDelays[i], miniHeights[i]);
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 1.5),
                width: 3,
                height: 22 * barH,
                decoration: BoxDecoration(
                  color: GQColors.coral,
                  borderRadius: BorderRadius.circular(2),
                ),
              );
            }),
          );
        },
      ),
    );
  }

  Widget _buildFullWaveform(bool reduceMotion) {
    return SizedBox(
      height: 28,
      child: AnimatedBuilder(
        animation: _waveCtrl,
        builder: (ctx, _) {
          return Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: List.generate(16, (i) {
              final barH = reduceMotion
                  ? 0.5
                  : _waveHeight(i, _barDelays[i], _barHeights[i]);
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 1.5),
                width: 3,
                height: 28 * barH,
                decoration: BoxDecoration(
                  color: GQColors.coral,
                  borderRadius: BorderRadius.circular(2),
                ),
              );
            }),
          );
        },
      ),
    );
  }

  /// Returns the scale factor (0.25–1.0) for a waveform bar.
  /// Matches HTML @keyframes gqWave: 0%/100% scaleY(0.25) → 50% scaleY(1).
  double _waveHeight(int index, int delayMs, double baseHeight) {
    final phaseOffset = (delayMs / 900.0) % 1.0;
    final t = (_waveCtrl.value + phaseOffset) % 1.0;
    // Sine wave: 0.25 at t=0/1, 1.0 at t=0.5
    final scale = 0.25 + 0.75 * math.sin(t * math.pi).clamp(0.0, 1.0);
    return baseHeight * scale;
  }
}

/// Inline privacy nudge shown in chat feed during voice mode.
/// Copy verbatim: "your voice is staying on this device"
class VoicePrivacyNudge extends StatelessWidget {
  const VoicePrivacyNudge({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Center(
        child: Opacity(
          opacity: 0.55,
          child: Text(
            // Verbatim from HTML
            'your voice is staying on this device',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: GQColors.ink3,
              letterSpacing: 0.4,
            ),
          ),
        ),
      ),
    );
  }
}
