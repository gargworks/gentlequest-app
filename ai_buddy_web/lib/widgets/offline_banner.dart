import 'dart:async';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../theme/gq_theme.dart';
import '../theme/gq_tokens.dart';

// ─────────────────────────────────────────────────────────────────────────────
// R1D12 — Offline States
// Source: docs/design/refs/htmls/GentleQuest_Offline_States.html
//         docs/design/refs/REVIEW.md § R1D12
//
// Three surfaces:
//   A. OfflineBanner          — inline amber banner in chat stream mid-chat.
//   B. OfflineColdStartScreen — full-screen amber overlay on cold-start.
//   C. ServerErrorBanner      — inline soft-coral banner for 5xx errors.
//
// Principle alignment:
//   P1 (warmth over utility) — "You're offline right now." is calm, not alarming.
//   P4 (amber not red)       — All offline states use GQColors.amber; never red.
//   P6 (crisis never blocks) — CrisisLineRow is always visible in cold-start;
//                              OfflineBanner always shows 988 footer [P6 invariant].
// ─────────────────────────────────────────────────────────────────────────────

// ─── Shared amber token ───────────────────────────────────────────────────────
//
// _kAmberSoft/_kAmberInk/_kCrisisBg/_kCrisisInk were module-level const
// aliases for GQColors.amberSoft/inkOnAmber/accentSoft/inkOnCoral. All four
// are theme slots (GQTheme.amberSoft/inkOnAmber/accentSoft/inkOnCoral) — a
// top-level const can't call GQTheme.of(context), so the aliases are gone
// and every call site reads t.<slot> directly instead. The two border colors
// below are literal alpha-blended hex, not token references, so they stay
// as module consts unchanged.

/// Amber border opacity factor: rgba(200,146,61,0.28)
const _kAmberBorder = Color(0x47C8923D);

const _kCrisisBorder = Color(0x47FF6B6B);

// ─── A · OfflineBanner ────────────────────────────────────────────────────────

/// Inline amber banner shown at the top of the chat stream when the device
/// loses connectivity mid-chat (State A).
///
/// Copy verbatim (REVIEW.md R1D12):
///   • "You're offline right now."
///   • "I'll resend the moment we reconnect."
///
/// P6 invariant: always includes a 988 crisis affordance footer — even offline.
class OfflineBanner extends StatelessWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      label: 'Offline notice. You\'re offline right now. Call 988 in a crisis.',
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // ── Main amber banner ─────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            decoration: BoxDecoration(
              color: t.amberSoft,
              borderRadius: BorderRadius.circular(GQRadii.card),
              border: Border.all(color: _kAmberBorder),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // wifi-off icon
                Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: t.surface,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.wifi_off_rounded,
                    size: 14,
                    color: t.amber,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        // Verbatim copy from REVIEW.md R1D12
                        "You're offline right now.",
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: t.inkOnAmber,
                        ),
                      ),
                      const SizedBox(height: 1),
                      Text(
                        // Verbatim copy from REVIEW.md R1D12
                        "I'll resend the moment we reconnect.",
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: t.amber,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // ── P6: Crisis 988 footer — always visible (P6: crisis never blocks) ─
          const SizedBox(height: 6),
          _CrisisLineRow(),
        ],
      ),
    );
  }
}

// ─── B · OfflineColdStartScreen ───────────────────────────────────────────────

/// Full-screen offline overlay shown on cold-start when no network is detected.
///
/// Per REVIEW.md R1D12 State B:
///   • Conversation history shown (local cache) — no fake prompt.
///   • 988 resource visible at bottom (P6 invariant).
///   • "Check connection" button triggers a connectivity re-poll.
///   • Auto-routes back to chat on reconnect.
///
/// [onReconnected] is called when connectivity is restored so the caller
/// can dismiss this screen.
class OfflineColdStartScreen extends StatefulWidget {
  const OfflineColdStartScreen({super.key, required this.onReconnected});

  final VoidCallback onReconnected;

  @override
  State<OfflineColdStartScreen> createState() => _OfflineColdStartScreenState();
}

class _OfflineColdStartScreenState extends State<OfflineColdStartScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ringController;
  StreamSubscription<List<ConnectivityResult>>? _sub;
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
      _ringController.stop();
    } else {
      _ringController.repeat();
    }
  }

  @override
  void initState() {
    super.initState();
    _ringController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 18),
    );

    // Listen for reconnection — auto-route back on reconnect.
    _sub = Connectivity().onConnectivityChanged.listen(_onConnectivityChange);
  }

  void _onConnectivityChange(List<ConnectivityResult> results) {
    final online = results.any((r) => r != ConnectivityResult.none);
    if (online && mounted) {
      widget.onReconnected();
    }
  }

  Future<void> _checkConnection() async {
    final results = await Connectivity().checkConnectivity();
    final online = results.any((r) => r != ConnectivityResult.none);
    if (online && mounted) {
      widget.onReconnected();
    }
  }

  @override
  void dispose() {
    _ringController.dispose();
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      label: 'Offline. No network connection.',
      child: Container(
        color: t.bg,
        child: SafeArea(
          child: Column(
            children: [
              // Nav bar with OFFLINE badge
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                decoration: BoxDecoration(
                  color: t.bg,
                  border: Border(
                    bottom: BorderSide(color: t.hair),
                  ),
                ),
                child: Row(
                  children: [
                    Text(
                      'GentleQuest',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: t.ink,
                      ),
                    ),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 9, vertical: 4),
                      decoration: BoxDecoration(
                        color: t.amberSoft,
                        borderRadius:
                            BorderRadius.circular(GQRadii.button),
                        border: Border.all(color: _kAmberBorder),
                      ),
                      child: Text(
                        'OFFLINE',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.4,
                          color: t.inkOnAmber,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(18, 24, 18, 24),
                  child: Column(
                    children: [
                      // Cloud art — animated rings
                      _CloudArt(ringController: _ringController),
                      const SizedBox(height: 14),
                      Text(
                        // Verbatim from HTML State B
                        "We can chat once you're back online.",
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          color: t.ink,
                          letterSpacing: -0.4,
                          height: 1.25,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        child: Text(
                          // Verbatim from HTML State B
                          "In the meantime, here's what works offline:",
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: t.ink2,
                            height: 1.5,
                          ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      // Offline capabilities list
                      _OfflineCapabilityCard(
                        emoji: '🌿',
                        emojiBackground: t.primarySoft,
                        title: 'Log my mood',
                        subtitle:
                            'Saves locally · syncs the moment we reconnect',
                      ),
                      const SizedBox(height: 10),
                      _OfflineCapabilityCard(
                        emoji: '🌬️',
                        emojiBackground: t.warmSoft,
                        title: 'Try a breathing exercise',
                        subtitle: 'All exercises run on your phone',
                      ),
                      const SizedBox(height: 10),
                      _OfflineCapabilityCard(
                        icon: Icons.shield_outlined,
                        // leafInk stays static — mood/nature illustration
                        // hue, static exception (D2).
                        iconColor: GQColors.leafInk,
                        iconBackground: const Color(0xFFF0F5EC),
                        title: 'Open my safety plan',
                        subtitle: 'Always available · encrypted on device',
                      ),
                      const SizedBox(height: 18),
                      // Check connection button
                      OutlinedButton.icon(
                        onPressed: _checkConnection,
                        icon: const Icon(Icons.refresh_rounded, size: 14),
                        label: const Text('Check connection'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: t.ink2,
                          side: BorderSide(color: t.hair),
                          textStyle: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                          ),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 9),
                          shape: const StadiumBorder(),
                        ),
                      ),
                      const SizedBox(height: 18),
                      // P6 — Crisis 988 row — always visible in cold-start offline state
                      _CrisisLineRow(),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── C · ServerErrorBanner ────────────────────────────────────────────────────

/// Inline soft-coral banner shown when the server returns a 5xx error.
///
/// Copy verbatim (REVIEW.md R1D12 State C):
///   • "Couldn't reach Alex." · "Tap to retry"
///
/// Matches HTML State C: coral tint, never bright red.
class ServerErrorBanner extends StatelessWidget {
  const ServerErrorBanner({super.key, required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      label: 'Server error. Couldn\'t reach Alex.',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
        decoration: BoxDecoration(
          // coral tint — accentSoft slot (#FFE8E8 in light) per color discipline
          color: t.accentSoft,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: Border.all(color: _kCrisisBorder),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                color: t.surface,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.error_outline_rounded,
                size: 14,
                color: t.coral,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                // Verbatim copy from REVIEW.md R1D12
                "Couldn't reach Alex.",
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w800,
                  color: t.coral,
                ),
              ),
            ),
            GestureDetector(
              onTap: onRetry,
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
                decoration: BoxDecoration(
                  color: t.surface,
                  borderRadius: BorderRadius.circular(GQRadii.button),
                  border: Border.all(color: _kCrisisBorder),
                ),
                child: Text(
                  // Verbatim copy from REVIEW.md R1D12
                  'Tap to retry',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: t.coral,
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

// ─── Queued message meta-row ───────────────────────────────────────────────────

/// Meta-row shown beneath a queued message bubble.
///
/// Copy verbatim (REVIEW.md R1D12):
///   • "Queued · will send when you're back"
class QueuedMessageMetaRow extends StatefulWidget {
  const QueuedMessageMetaRow({super.key});

  @override
  State<QueuedMessageMetaRow> createState() => _QueuedMessageMetaRowState();
}

class _QueuedMessageMetaRowState extends State<QueuedMessageMetaRow>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;
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
      _pulse.stop();
    } else {
      _pulse.repeat();
    }
  }

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    );
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final reduceMotion =
        _reduceMotion || MediaQuery.of(context).accessibleNavigation;
    return Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        AnimatedBuilder(
          animation: _pulse,
          builder: (_, __) {
            final opacity = reduceMotion
                ? 0.6
                : (0.3 + 0.7 * (0.5 + 0.5 * _pulse.value)).clamp(0.0, 1.0);
            return Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: t.ink2.withValues(alpha: opacity),
                shape: BoxShape.circle,
              ),
            );
          },
        ),
        const SizedBox(width: 5),
        Text(
          // Verbatim copy from REVIEW.md R1D12
          "Queued · will send when you're back",
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w700,
            color: t.ink2,
          ),
        ),
      ],
    );
  }
}

// ─── P6 — CrisisLineRow — always visible offline ─────────────────────────────

/// Crisis line row — always visible on every offline surface (P6 invariant).
///
/// Copy verbatim from HTML State B:
///   "If you're in crisis, please call 988 — it works without internet."
///
/// Tapping the row dials 988.
class _CrisisLineRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Semantics(
      label: 'Crisis resource. Call 988 — works without internet.',
      button: true,
      child: GestureDetector(
        onTap: () async {
          final uri = Uri(scheme: 'tel', path: '988');
          if (await canLaunchUrl(uri)) {
            await launchUrl(uri, mode: LaunchMode.externalApplication);
          }
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            // coral-soft — visually distinct from error, per HTML color discipline
            color: t.accentSoft,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(color: _kCrisisBorder),
          ),
          child: Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: t.surface,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.phone_in_talk_rounded,
                  size: 14,
                  // WO-3 reconciliation retired coralDkDeep (#B33636 — the
                  // exact red already swept everywhere else); icon sits on
                  // white, not the amber tint, so dangerInk not inkOnAmber.
                  // dangerInk is a static exception (destructive/crisis fill
                  // discipline) — stays literal, no theme read needed here.
                  color: GQColors.dangerInk,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text.rich(
                  // Verbatim copy from HTML State B
                  TextSpan(
                    text:
                        "If you're in crisis, please call ",
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      color: t.inkOnCoral,
                      height: 1.4,
                    ),
                    children: [
                      TextSpan(
                        text: '988',
                        style: TextStyle(
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      TextSpan(
                        text: ' — it works without internet.',
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Cloud art widget ─────────────────────────────────────────────────────────

/// Animated cloud illustration for cold-start offline screen (State B).
/// Two dashed rings rotate in opposite directions.
class _CloudArt extends StatelessWidget {
  const _CloudArt({required this.ringController});
  final AnimationController ringController;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return SizedBox(
      width: 160,
      height: 160,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Outer dashed ring
          AnimatedBuilder(
            animation: ringController,
            builder: (_, __) => Transform.rotate(
              angle: ringController.value * 2 * 3.14159,
              child: Container(
                width: 160,
                height: 160,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: t.primary.withValues(alpha: 0.30),
                    width: 1,
                  ),
                ),
              ),
            ),
          ),
          // Inner dashed ring (reverse)
          AnimatedBuilder(
            animation: ringController,
            builder: (_, __) => Transform.rotate(
              angle: -ringController.value * 2 * 3.14159,
              child: Container(
                width: 132,
                height: 132,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: t.primary.withValues(alpha: 0.18),
                    width: 1,
                  ),
                ),
              ),
            ),
          ),
          // Cloud icon with amber slash
          Icon(
            Icons.cloud_off_rounded,
            size: 64,
            color: t.primarySoft,
          ),
          // Amber diagonal slash overlay
          Positioned(
            bottom: 42,
            right: 42,
            child: Container(
              width: 28,
              height: 3,
              decoration: BoxDecoration(
                color: t.amber,
                borderRadius: BorderRadius.circular(2),
              ),
              transform: Matrix4.rotationZ(-0.785), // -45 degrees
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Offline capability card ──────────────────────────────────────────────────

class _OfflineCapabilityCard extends StatelessWidget {
  const _OfflineCapabilityCard({
    this.emoji,
    this.emojiBackground,
    this.icon,
    this.iconColor,
    this.iconBackground,
    required this.title,
    required this.subtitle,
  });

  final String? emoji;
  final Color? emojiBackground;
  final IconData? icon;
  final Color? iconColor;
  final Color? iconBackground;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: t.hair),
      ),
      child: Row(
        children: [
          // Icon cell
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: emojiBackground ?? iconBackground ?? t.primarySoft,
              borderRadius: BorderRadius.circular(11),
            ),
            child: Center(
              child: emoji != null
                  ? Text(emoji!, style: const TextStyle(fontSize: 18))
                  : Icon(icon, size: 18, color: iconColor ?? t.primary),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w800,
                    color: t.ink,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: t.ink2,
                  ),
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right_rounded, size: 18, color: t.ink2),
        ],
      ),
    );
  }
}
