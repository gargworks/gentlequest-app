import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show HapticFeedback;
import '../theme/gq_theme.dart';
import '../theme/gq_tokens.dart';
import '../navigation/home_tab_deeplink.dart';
import '../widgets/app_bottom_nav.dart';
import '../screens/journal_screen.dart' show JournalEntry, JournalStorage;
import 'gq/gq.dart';

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
Future<void> showMoodGreatReflectionSheet(BuildContext context) {
  // WO-5.2 C1: GQSheet.show owns radius/grabber/keyboard-awareness/320ms
  // slide; useRootNavigator floats above the mood-entry dialog just popped.
  return GQSheet.show<void>(
    context,
    content: const _GreatReflectionSheet(),
    useRootNavigator: true,
  );
}

class _GreatReflectionSheet extends StatefulWidget {
  const _GreatReflectionSheet();

  @override
  State<_GreatReflectionSheet> createState() => _GreatReflectionSheetState();
}

class _GreatReflectionSheetState extends State<_GreatReflectionSheet>
    with TickerProviderStateMixin {
  // Confetti dots (5 dots per spec) — a celebration effect, not a streak
  // surface, so it stays under C4.
  late final AnimationController _confettiCtrl;

  final _thoughtController = TextEditingController();
  bool _saved = false;
  bool _saveFailed = false;

  // Static const field initializer — no BuildContext reachable at this scope
  // (slice-7 resource_library precedent), so this stays GQColors.
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
    _confettiCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..forward();
  }

  @override
  void dispose() {
    _confettiCtrl.dispose();
    _thoughtController.dispose();
    super.dispose();
  }

  void _dismiss() {
    if (mounted) Navigator.of(context).pop();
  }

  Future<void> _saveThought() async {
    final text = _thoughtController.text.trim();
    if (text.isEmpty) {
      _dismiss();
      return;
    }
    setState(() => _saveFailed = false);
    // Persist the reflection as a journal entry. JournalStorage.append is
    // local-only (SharedPreferences) — there is no server sync path, so a
    // failure here means the write genuinely didn't happen; nothing is
    // "pending sync" (verified 2026-08-21, WO-5.2's flagged D4 question —
    // the sync path this catch block used to claim doesn't exist).
    try {
      await JournalStorage.append(JournalEntry(
        id: DateTime.now().toIso8601String(),
        body: text,
        createdAt: DateTime.now(),
      ));
      if (!mounted) return;
      HapticFeedback.mediumImpact();
      setState(() => _saved = true);
      Future.delayed(const Duration(milliseconds: 900), _dismiss);
    } catch (_) {
      if (!mounted) return;
      setState(() => _saveFailed = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _saved ? _buildSavedState() : _buildMainContent(context);
  }

  Widget _buildSavedState() {
    final t = GQTheme.of(context);
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const SizedBox(height: GQSpacing.xl),
        Icon(Icons.check_circle_outline_rounded, color: t.primary, size: 48),
        const SizedBox(height: GQSpacing.md),
        Text('Saved.', style: GQTypography.titleSm.copyWith(color: t.ink)),
        const SizedBox(height: GQSpacing.xl),
      ],
    );
  }

  Widget _buildMainContent(BuildContext context) {
    final t = GQTheme.of(context);
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
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
        const SizedBox(height: GQSpacing.sm),

        // Headline + sub — WO-5.2 C3 exact copy.
        Text(
          'Love that. What worked today?',
          style: GQTypography.titleSm.copyWith(color: t.ink),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: GQSpacing.xs),
        Text(
          "30 seconds — I'll remember it for next time.",
          style: GQTypography.body.copyWith(color: t.ink2),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: GQSpacing.xl),

        // WO-5.2 C4 (non-negotiable): the streak badge that lived here is
        // deleted, not replaced. CompanionProvider's own doc already
        // commits to "no streaks that break, no decay, no shame" —
        // consistent with that, and with the same call made on WO-6's
        // Home screen and WO-5.1's assessment result screen.

        // Single-line field per spec (was multi-line).
        TextField(
          controller: _thoughtController,
          decoration: InputDecoration(
            hintText: 'good food, walked, slept well, said no…',
            hintStyle: GQTypography.body.copyWith(color: t.ink3),
            helperText: 'private to you',
            helperStyle: GQTypography.micro.copyWith(color: t.ink2),
            filled: true,
            fillColor: t.surface,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(GQRadii.card),
              borderSide: BorderSide(color: t.hair),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          ),
          maxLines: 1,
          style: GQTypography.body.copyWith(color: t.ink),
          textInputAction: TextInputAction.done,
          onSubmitted: (_) => _saveThought(),
        ),

        if (_saveFailed) ...[
          const SizedBox(height: GQSpacing.md),
          GQBanner(
            category: GQBannerCategory.amber,
            message: "That didn't save. Your entry is still here — try again?",
            onDismiss: () => setState(() => _saveFailed = false),
          ),
        ],
        const SizedBox(height: GQSpacing.lg),

        GQButton(label: 'Save thought', onPressed: _saveThought),
        const SizedBox(height: GQSpacing.sm),

        Center(
          child: GQButton(
            label: 'Just close',
            variant: GQButtonVariant.ghost,
            fullWidth: false,
            onPressed: _dismiss,
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
        homeTabDeepLink.request(AppTab.talk);
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
            // GQColors.ink used as a FILL here (not text), paired with
            // literal Colors.white/white60 foreground below — same
            // "fill carries white text, must not shift by mode" reasoning
            // as the primaryDk/dangerInk CTA-fill exception (GQTheme class
            // doc). t.ink flips to near-white in dark mode, which would put
            // white text on a white toast. Left static; judgment call.
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
                        // primaryDk: no GQTheme slot by design (CTA-fill
                        // exception, pairs with the literal white text below).
                        color: GQColors.primaryDk,
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
