import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/gq_tokens.dart';
import '../navigation/home_tab_deeplink.dart';
import '../widgets/app_bottom_nav.dart';
import '../screens/journal_screen.dart' show JournalEntry, JournalStorage;

// ─────────────────────────────────────────────────────────────────────────────
// R1D5 — Mood Reflection Sheet
//
// Three post-submit reflection states, triggered from MoodTrackerWidget on
// mood submit based on mood level:
//
//   moodLevel 1–2  → showMoodLowReflectionSheet  (mood_low_reflection_sheet.dart)
//   moodLevel 5    → showMoodGreatReflectionSheet (State B — Great, this file)
//   moodLevel 3–4  → showMoodNeutralToast         (State C — Neutral, this file)
//
// Design reference:
//   docs/design/refs/REVIEW.md § R1D5 — Mood Reflection
//   htmls/GentleQuest_Mood_Reflection.html
//
// Principles applied:
//   • coral-not-red (#1)      → accent = GQColors.coral
//   • no-streak-shame (#11)   → streak shown only as celebration, never guilt
//   • optional>required       → "What worked?" is always optional
//   • save-exit-always        → dismiss always reachable
//
// TODO(backend): "What worked?" text is UI-only; not persisted. Wire to
//   backend journaling API when available (follow-up task).
// ─────────────────────────────────────────────────────────────────────────────

// ═══════════════════════════════════════════════════════════════════════════════
// State B — Great Mood Sheet
// ═══════════════════════════════════════════════════════════════════════════════

/// Shows the "great mood" celebration bottom sheet (State B).
///
/// [streakDays] is the current streak / active-days count. Pass 0 to hide the
/// streak badge.
void showMoodGreatReflectionSheet(
  BuildContext context, {
  int streakDays = 0,
}) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    useRootNavigator: true,
    builder: (_) => _GreatReflectionSheet(streakDays: streakDays),
  );
}

class _GreatReflectionSheet extends StatefulWidget {
  final int streakDays;
  const _GreatReflectionSheet({required this.streakDays});

  @override
  State<_GreatReflectionSheet> createState() => _GreatReflectionSheetState();
}

class _GreatReflectionSheetState extends State<_GreatReflectionSheet>
    with TickerProviderStateMixin {
  late final AnimationController _slideCtrl;
  late final Animation<Offset> _slideAnim;

  // Badge bounce animation
  late final AnimationController _bounceCtrl;
  late final Animation<double> _bounceAnim;

  // Confetti dots (5 dots per spec)
  late final AnimationController _confettiCtrl;

  final _thoughtController = TextEditingController();
  bool _saved = false;

  static const List<Color> _confettiColors = [
    GQColors.coral,
    GQColors.primary,
    Color(0xFF4ECDC4),
    Color(0xFFFFE66D),
    Color(0xFF95E1D3),
  ];

  @override
  void initState() {
    super.initState();

    _slideCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 350),
    );
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _slideCtrl, curve: Curves.easeOutCubic));
    _slideCtrl.forward();

    // Badge bounce — runs once on appear
    _bounceCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _bounceAnim = TweenSequence<double>([
      TweenSequenceItem(tween: Tween(begin: 1.0, end: 1.25), weight: 40),
      TweenSequenceItem(tween: Tween(begin: 1.25, end: 0.92), weight: 30),
      TweenSequenceItem(tween: Tween(begin: 0.92, end: 1.0), weight: 30),
    ]).animate(CurvedAnimation(parent: _bounceCtrl, curve: Curves.easeOut));

    _confettiCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );

    // Stagger: slide in → bounce badge → confetti
    _slideCtrl.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _bounceCtrl.forward();
        _confettiCtrl.forward();
      }
    });
  }

  @override
  void dispose() {
    _slideCtrl.dispose();
    _bounceCtrl.dispose();
    _confettiCtrl.dispose();
    _thoughtController.dispose();
    super.dispose();
  }

  void _dismiss() {
    if (mounted) Navigator.of(context).pop();
  }

  void _saveThought() {
    final text = _thoughtController.text.trim();
    if (text.isEmpty) {
      _dismiss();
      return;
    }
    // Persist the reflection as a journal entry on device. Was a TODO stub —
    // user typed "What worked?" reflection and the text was silently dropped.
    // Now stored under JournalStorage so the user's words survive the session.
    // Backend journaling API not yet built; when it ships, JournalStorage
    // becomes the dual-write integration point.
    JournalStorage.append(JournalEntry(
      id: DateTime.now().toIso8601String(),
      body: text,
      createdAt: DateTime.now(),
    ));
    setState(() => _saved = true);
    Future.delayed(const Duration(milliseconds: 900), _dismiss);
  }

  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnim,
      child: Container(
        decoration: const BoxDecoration(
          color: GQColors.softBg,
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(GQRadii.sheet),
          ),
        ),
        padding: EdgeInsets.fromLTRB(
          24,
          20,
          24,
          MediaQuery.of(context).padding.bottom + 24,
        ),
        child: _saved ? _buildSavedState() : _buildMainContent(context),
      ),
    );
  }

  Widget _buildSavedState() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const SizedBox(height: 24),
        Icon(Icons.check_circle_outline_rounded,
            color: GQColors.primary, size: 48),
        const SizedBox(height: 12),
        const Text(
          'Saved.',
          style: TextStyle(
            fontFamily: 'Inter',
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: Colors.black87,
          ),
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildMainContent(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Drag handle
        Center(
          child: Container(
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.black12,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Confetti row — 5 dots per spec
        AnimatedBuilder(
          animation: _confettiCtrl,
          builder: (context, _) {
            return SizedBox(
              height: 32,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(5, (i) {
                  final progress = (_confettiCtrl.value - i * 0.12).clamp(0.0, 1.0);
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 6),
                    child: Opacity(
                      opacity: progress,
                      child: Transform.translate(
                        offset: Offset(0, -16 * progress),
                        child: Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: _confettiColors[i],
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                    ),
                  );
                }),
              ),
            );
          },
        ),
        const SizedBox(height: 8),

        // Headline
        Text(
          'Quiet wins count.',
          style: textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w700,
            fontFamily: 'Inter',
            color: Colors.black87,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        Text(
          'Good days are worth remembering.',
          style: textTheme.bodyMedium?.copyWith(
            fontFamily: 'Inter',
            color: Colors.black54,
            height: 1.4,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 24),

        // Streak badge (bounce animation)
        if (widget.streakDays > 0) ...[
          Center(
            child: ScaleTransition(
              scale: _bounceAnim,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: GQColors.accentSoft,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('🌱', style: TextStyle(fontSize: 16)),
                    const SizedBox(width: 6),
                    Text(
                      '${widget.streakDays} active days',
                      style: const TextStyle(
                        fontFamily: 'Inter',
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
        ],

        // "What worked?" field
        Text(
          'What worked?',
          style: textTheme.labelLarge?.copyWith(
            fontFamily: 'Inter',
            color: Colors.black87,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _thoughtController,
          decoration: InputDecoration(
            hintText: 'Optional — just for you',
            hintStyle: const TextStyle(
              fontFamily: 'Inter',
              color: Colors.black38,
              fontSize: 14,
            ),
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(GQRadii.card),
              borderSide: BorderSide.none,
            ),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 14,
              vertical: 12,
            ),
          ),
          maxLines: 3,
          style: const TextStyle(fontFamily: 'Inter', fontSize: 14),
          textInputAction: TextInputAction.done,
          onSubmitted: (_) => _saveThought(),
        ),
        const SizedBox(height: 16),

        // Save thought button
        FilledButton(
          onPressed: _saveThought,
          style: FilledButton.styleFrom(
            backgroundColor: GQColors.primary,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(GQRadii.card),
            ),
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
          child: const Text(
            'Save thought',
            style: TextStyle(
              fontFamily: 'Inter',
              fontWeight: FontWeight.w600,
              fontSize: 15,
            ),
          ),
        ),
        const SizedBox(height: 12),

        // Dismiss link
        Center(
          child: TextButton(
            onPressed: _dismiss,
            style: TextButton.styleFrom(foregroundColor: Colors.black45),
            child: const Text(
              'Skip',
              style: TextStyle(
                fontFamily: 'Inter',
                fontSize: 14,
                decoration: TextDecoration.underline,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// State C — Neutral Auto-Dismiss Toast
// ═══════════════════════════════════════════════════════════════════════════════

/// Shows a lightweight auto-dismissing toast for neutral mood (levels 3–4).
///
/// The toast says "Logged. Talk soon." and auto-dismisses after ~3 seconds.
/// It also includes a next-action nudge (tap to chat).
void showMoodNeutralToast(BuildContext context) {
  // Use a custom overlay so it appears above everything and auto-dismisses
  // without blocking the main UI.
  final overlay = Overlay.of(context, rootOverlay: true);
  late OverlayEntry entry;

  entry = OverlayEntry(
    builder: (_) => _NeutralToastOverlay(
      onDismiss: () {
        entry.remove();
      },
      onChatTap: () {
        entry.remove();
        homeTabDeepLink.value = AppTab.talk;
      },
    ),
  );

  overlay.insert(entry);
}

class _NeutralToastOverlay extends StatefulWidget {
  final VoidCallback onDismiss;
  final VoidCallback onChatTap;

  const _NeutralToastOverlay({
    required this.onDismiss,
    required this.onChatTap,
  });

  @override
  State<_NeutralToastOverlay> createState() => _NeutralToastOverlayState();
}

class _NeutralToastOverlayState extends State<_NeutralToastOverlay>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _opacity;
  late final Animation<Offset> _slide;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _opacity = CurvedAnimation(parent: _ctrl, curve: Curves.easeOut);
    _slide = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOutCubic));

    _ctrl.forward();

    // Auto-dismiss after ~3 seconds
    _timer = Timer(const Duration(milliseconds: 3000), _animateOut);
  }

  @override
  void dispose() {
    _timer?.cancel();
    _ctrl.dispose();
    super.dispose();
  }

  void _animateOut() {
    if (!mounted) return;
    _ctrl.reverse().then((_) => widget.onDismiss());
  }

  @override
  Widget build(BuildContext context) {
    return Positioned(
      bottom: MediaQuery.of(context).padding.bottom + 100,
      left: 24,
      right: 24,
      child: FadeTransition(
        opacity: _opacity,
        child: SlideTransition(
          position: _slide,
          child: Material(
            elevation: 8,
            borderRadius: BorderRadius.circular(GQRadii.card),
            color: GQColors.ink,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              child: Row(
                children: [
                  // Message
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text(
                          'Logged. Talk soon.',
                          style: TextStyle(
                            fontFamily: 'Inter',
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Alex is here if you need.',
                          style: TextStyle(
                            fontFamily: 'Inter',
                            fontSize: 13,
                            color: Colors.white60,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  // Next-action nudge
                  GestureDetector(
                    onTap: widget.onChatTap,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 7),
                      decoration: BoxDecoration(
                        color: GQColors.primary,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        'Chat',
                        style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
