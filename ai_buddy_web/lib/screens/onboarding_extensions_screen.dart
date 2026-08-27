// onboarding_extensions_screen.dart — R1D21 Onboarding Extensions
// Design source: docs/design/refs/htmls/GentleQuest_Onboarding_Extensions.html
// Principles: P1 (neighbor-voice), P2 (no shame), P12 (neighbor-voice), P13 (crisis never off)
//
// Four post-R1D1 onboarding states exposed as separate public widgets:
//
//   A — NotificationOptInSheet
//       Bottom sheet; per-category toggles; streak-nudge OFF by default.
//   B — ReturningUserWelcome
//       Warm re-entry screen; no shame framing for lapsed users.
//   C — PermissionDeniedRecovery
//       Graceful path when system notification permission was denied.
//   D — FirstLaunchTutorialOverlay
//       3-step tooltip overlay on first chat open; dismissible.
//
// Persistence: SharedPreferences only (no backend).
// Keys used:
//   • daily_checkin_enabled      (bool, default true)
//   • streak_nudge_enabled       (bool, default false)
//   • wellness_check_locked      (bool, always true — not user-settable)
//   • tutorial_seen              (bool, default false)
//   • notif_maybe_later_snooze_until  (int epoch-ms, 7-day snooze)
//
// Out of scope: R1D1 modifications, backend persistence, theme refactors.

import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:ai_buddy_web/theme/gq_theme.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';

// ─── SharedPreferences keys ───────────────────────────────────────────────────

abstract final class _Pref {
  static const dailyCheckIn = 'daily_checkin_enabled';
  static const streakNudge = 'streak_nudge_enabled';
  static const wellnessLocked = 'wellness_check_locked';
  static const tutorialSeen = 'tutorial_seen';
  static const maybeLaterSnooze = 'notif_maybe_later_snooze_until';
}

// ─── Notification category model ─────────────────────────────────────────────

/// Notification category kind exposed in the [NotificationOptInSheet.onEnable]
/// callback so callers can act on individual toggle selections.
enum NotifKind { dailyCheckIn, streakNudge, wellnessCheck }

// ═══════════════════════════════════════════════════════════════════════════════
// STATE A — NotificationOptInSheet
// ═══════════════════════════════════════════════════════════════════════════════

/// Bottom sheet that surfaces over a dim'd home preview.
/// Shown post-age-confirmation, pre-home (once only, or after 7-day snooze).
///
/// Usage:
/// ```dart
/// showModalBottomSheet(
///   context: context,
///   isScrollControlled: true,
///   backgroundColor: Colors.transparent,
///   builder: (_) => const NotificationOptInSheet(),
/// );
/// ```
class NotificationOptInSheet extends StatefulWidget {
  /// Called when the user taps "Enable notifications" (primary CTA).
  /// Receives a map of {NotifKind → enabled} so the caller can request
  /// system permission and configure the notification service.
  final void Function(Map<NotifKind, bool> selections)? onEnable;

  /// Called when the user taps "Not now" (snoozes for 7 days).
  final VoidCallback? onMaybeLater;

  const NotificationOptInSheet({
    super.key,
    this.onEnable,
    this.onMaybeLater,
  });

  @override
  State<NotificationOptInSheet> createState() => _NotificationOptInSheetState();
}

class _NotificationOptInSheetState extends State<NotificationOptInSheet>
    with SingleTickerProviderStateMixin {
  // ── Toggle state ────────────────────────────────────────────────────────────
  // dailyCheckIn: ON by default, user-toggleable.
  // streakNudge:  OFF by default (P2 — no streak shame).
  // wellnessCheck: ON, locked (P13 — care-framed, crisis follow-up).
  bool _dailyCheckIn = true;
  bool _streakNudge = false;
  // wellnessCheck is always true and cannot be changed by the user.
  static const bool _wellnessLocked = true;

  bool _saving = false;

  // Bell animation
  late final AnimationController _bellCtrl;
  late final Animation<double> _bellScale;

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
      _bellCtrl.stop();
    } else {
      _bellCtrl.repeat(reverse: true);
    }
  }

  @override
  void initState() {
    super.initState();
    _bellCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _bellScale = Tween<double>(begin: 1.0, end: 1.08).animate(
      CurvedAnimation(parent: _bellCtrl, curve: Curves.easeInOut),
    );
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _dailyCheckIn = prefs.getBool(_Pref.dailyCheckIn) ?? true;
      _streakNudge = prefs.getBool(_Pref.streakNudge) ?? false;
    });
  }

  Future<void> _saveAndEnable() async {
    setState(() => _saving = true);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_Pref.dailyCheckIn, _dailyCheckIn);
    await prefs.setBool(_Pref.streakNudge, _streakNudge);
    await prefs.setBool(_Pref.wellnessLocked, true);
    if (!mounted) return;
    setState(() => _saving = false);
    widget.onEnable?.call({
      NotifKind.dailyCheckIn: _dailyCheckIn,
      NotifKind.streakNudge: _streakNudge,
      NotifKind.wellnessCheck: true,
    });
    Navigator.of(context).pop();
  }

  Future<void> _snooze() async {
    final prefs = await SharedPreferences.getInstance();
    final until = DateTime.now()
        .add(const Duration(days: 7))
        .millisecondsSinceEpoch;
    await prefs.setInt(_Pref.maybeLaterSnooze, until);
    if (!mounted) return;
    widget.onMaybeLater?.call();
    Navigator.of(context).pop();
  }

  @override
  void dispose() {
    _bellCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(GQRadii.sheetLg)),
        boxShadow: [
          BoxShadow(
            color: Color(0x59110D2E),
            blurRadius: 60,
            offset: Offset(0, -20),
          ),
        ],
      ),
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 28,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Drag handle
          const SizedBox(height: 14),
          Center(
            child: Container(
              width: 44,
              height: 5,
              decoration: BoxDecoration(
                color: const Color(0xFFE5E2EE),
                borderRadius: BorderRadius.circular(100),
              ),
            ),
          ),
          const SizedBox(height: 20),
          // Bell icon — animated pulse
          Center(
            child: ScaleTransition(
              scale: _bellScale,
              child: Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [t.primarySoft, t.accentSoft],
                  ),
                  borderRadius: BorderRadius.circular(32),
                ),
                child: Center(
                  child: Icon(Icons.notifications_outlined,
                      size: 28, color: t.primary),
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          // Heading
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 24),
            child: Text(
              'One nudge a day,\nonly if it helps.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: GQTypography.displayFamily,
                fontSize: 24,
                fontWeight: FontWeight.w800,
                height: 1.2,
                letterSpacing: -0.3,
                color: t.ink,
              ),
            ),
          ),
          const SizedBox(height: 10),
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 24),
            child: Text(
              "Here's what we'd send. Toggle anything off, anytime.",
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13.5,
                fontWeight: FontWeight.w500,
                height: 1.55,
                color: t.ink2,
              ),
            ),
          ),
          const SizedBox(height: 20),
          // Preview rows
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Column(
              children: [
                _NotifPreviewRow(
                  icon: Icons.access_time_rounded,
                  iconBg: t.primarySoft,
                  iconColor: t.primary,
                  label: 'Daily check-in reminder',
                  sublabel: 'Around 9 am · skippable',
                  value: _dailyCheckIn,
                  locked: false,
                  onChanged: (v) => setState(() => _dailyCheckIn = v),
                ),
                const SizedBox(height: 8),
                _NotifPreviewRow(
                  icon: Icons.local_fire_department_rounded,
                  iconBg: t.warmSoft,
                  iconColor: const Color(0xFFFF8C42),
                  label: 'Streak gentle nudge',
                  sublabel: 'Off by default — no streak shame',
                  badge: 'OPT-IN',
                  value: _streakNudge,
                  locked: false,
                  onChanged: (v) => setState(() => _streakNudge = v),
                ),
                const SizedBox(height: 8),
                _NotifPreviewRow(
                  icon: Icons.favorite_rounded,
                  iconBg: t.accentSoft,
                  iconColor: t.coral,
                  label: "If I'm worried about you",
                  sublabel: 'Crisis follow-up · always on',
                  value: _wellnessLocked,
                  locked: true,
                  onChanged: null,
                  lockExplanation:
                      'This keeps you safe and cannot be turned off.',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          // Primary CTA
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _saving ? null : _saveAndEnable,
                style: ElevatedButton.styleFrom(
                  backgroundColor: GQColors.primaryDk,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: const StadiumBorder(),
                  textStyle: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                child: _saving
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text('Enable notifications'),
              ),
            ),
          ),
          const SizedBox(height: 12),
          // Secondary — Not now
          TextButton(
            onPressed: _snooze,
            style: TextButton.styleFrom(
              foregroundColor: t.ink2,
              textStyle: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13.5,
                fontWeight: FontWeight.w600,
              ),
            ),
            child: const Text('Not now'),
          ),
        ],
      ),
    );
  }
}

// ─── Notification preview row ─────────────────────────────────────────────────

class _NotifPreviewRow extends StatelessWidget {
  final IconData icon;
  final Color iconBg;
  final Color iconColor;
  final String label;
  final String sublabel;
  final String? badge;
  final bool value;
  final bool locked;
  final ValueChanged<bool>? onChanged;
  final String? lockExplanation;

  const _NotifPreviewRow({
    required this.icon,
    required this.iconBg,
    required this.iconColor,
    required this.label,
    required this.sublabel,
    this.badge,
    required this.value,
    required this.locked,
    required this.onChanged,
    this.lockExplanation,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: t.bg,
        borderRadius: BorderRadius.circular(GQRadii.card),
        border: Border.all(color: t.hair),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Icon container
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: iconBg,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, size: 18, color: iconColor),
              ),
              const SizedBox(width: 12),
              // Labels
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            label,
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 13.5,
                              fontWeight: FontWeight.w800,
                              color: t.ink,
                            ),
                          ),
                        ),
                        if (badge != null) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 7, vertical: 2),
                            decoration: BoxDecoration(
                              color: t.surface,
                              borderRadius: BorderRadius.circular(100),
                              border: Border.all(color: t.hair),
                            ),
                            child: Text(
                              badge!,
                              style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 9.5,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 0.3,
                                color: t.ink2,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      sublabel,
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: t.ink2,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              // Toggle or locked icon
              if (locked)
                Icon(Icons.lock_rounded, size: 18, color: t.ink2)
              else
                Switch(
                  value: value,
                  onChanged: onChanged,
                  activeColor: t.primary,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
            ],
          ),
          // Lock explanation
          if (locked && lockExplanation != null) ...[
            const SizedBox(height: 8),
            Text(
              lockExplanation!,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: t.ink2,
                height: 1.4,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// STATE B — ReturningUserWelcome
// ═══════════════════════════════════════════════════════════════════════════════

/// Full-screen warm re-entry surface shown when a lapsed user returns.
///
/// Constructor parameters:
///   [daysSince] — days since last active session; 0 means "today" (skip state).
///   [userName]  — optional first name for personalisation.
///   [onContinue] — primary CTA callback.
class ReturningUserWelcome extends StatefulWidget {
  final int daysSince;
  final String? userName;
  final VoidCallback? onContinue;

  const ReturningUserWelcome({
    super.key,
    required this.daysSince,
    this.userName,
    this.onContinue,
  });

  @override
  State<ReturningUserWelcome> createState() => _ReturningUserWelcomeState();
}

class _ReturningUserWelcomeState extends State<ReturningUserWelcome>
    with SingleTickerProviderStateMixin {
  late final AnimationController _fadeCtrl;
  late final Animation<double> _fadeAnim;
  late final Animation<Offset> _slideAnim;

  @override
  void initState() {
    super.initState();
    _fadeCtrl = AnimationController(
      vsync: this,
      duration: GQDurations.fade,
    )..forward();
    _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.06),
      end: Offset.zero,
    ).animate(_fadeAnim);
  }

  @override
  void dispose() {
    _fadeCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final name = widget.userName;
    final days = widget.daysSince;

    // Heading copy
    final heading = name != null
        ? 'Welcome back, $name.'
        : 'Welcome back, friend.';

    // Sub-copy: "It's been X days. No judgment — let's just say hi."
    // If daysSince == 1, use "a day".
    final dayLabel = days == 1 ? 'a day' : '$days days';
    final subCopy = "It's been $dayLabel. No judgment — let's just say hi.";

    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: FadeTransition(
            opacity: _fadeAnim,
            child: SlideTransition(
              position: _slideAnim,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Spacer(flex: 2),
                  // Warm illustration placeholder — gradient orb
                  Center(
                    child: Container(
                      width: 120,
                      height: 120,
                      decoration: BoxDecoration(
                        gradient: RadialGradient(
                          colors: [t.accentSoft, t.primarySoft],
                          radius: 0.85,
                        ),
                        borderRadius: BorderRadius.circular(60),
                      ),
                      child: Icon(
                        Icons.favorite_rounded,
                        size: 52,
                        color: t.coral,
                      ),
                    ),
                  ),
                  const SizedBox(height: 36),
                  // Date chip — "TUESDAY · MAY 7" style
                  Text(
                    _todayChip(),
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.3,
                      color: t.ink2,
                    ),
                  ),
                  const SizedBox(height: 8),
                  // Main heading
                  Text(
                    heading,
                    style: TextStyle(
                      fontFamily: GQTypography.displayFamily,
                      fontSize: 30,
                      fontWeight: FontWeight.w800,
                      height: 1.15,
                      letterSpacing: -0.5,
                      color: t.ink,
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Sub-copy — no shame
                  Text(
                    subCopy,
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                      height: 1.5,
                      color: t.ink2,
                    ),
                  ),
                  const SizedBox(height: 8),
                  // Reassurance pill
                  _ReassurancePill(
                    text:
                        'You can always pick up where you left off — or start fresh.',
                  ),
                  const Spacer(flex: 3),
                  // Primary CTA
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: ElevatedButton(
                      onPressed: widget.onContinue,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: GQColors.primaryDk,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: const StadiumBorder(),
                        textStyle: const TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      child: const Text("Let's say hi"),
                    ),
                  ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _todayChip() {
    final now = DateTime.now();
    const days = [
      'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY',
      'FRIDAY', 'SATURDAY', 'SUNDAY',
    ];
    const months = [
      'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
    ];
    final dayName = days[now.weekday - 1];
    final monthName = months[now.month - 1];
    return '$dayName · $monthName ${now.day}';
  }
}

// ─── Reassurance pill ─────────────────────────────────────────────────────────

class _ReassurancePill extends StatelessWidget {
  final String text;
  const _ReassurancePill({required this.text});

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      margin: const EdgeInsets.only(top: 4),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: t.primarySoft,
        borderRadius: BorderRadius.circular(GQRadii.card),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 12.5,
          fontWeight: FontWeight.w600,
          height: 1.45,
          color: t.ink2,
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// STATE C — PermissionDeniedRecovery
// ═══════════════════════════════════════════════════════════════════════════════

/// Full-screen recovery surface shown when the system notification
/// permission is denied.  Offers a deep-link to Settings so the user
/// can enable notifications later — no dead-ends.
///
/// [onGoToSettings] opens the app's system settings page.  If null a
/// sensible default using url_launcher is attempted.
/// [onContinueWithout] proceeds without notifications (primary fallback).
class PermissionDeniedRecovery extends StatefulWidget {
  final VoidCallback? onGoToSettings;
  final VoidCallback? onContinueWithout;

  const PermissionDeniedRecovery({
    super.key,
    this.onGoToSettings,
    this.onContinueWithout,
  });

  @override
  State<PermissionDeniedRecovery> createState() =>
      _PermissionDeniedRecoveryState();
}

class _PermissionDeniedRecoveryState extends State<PermissionDeniedRecovery>
    with SingleTickerProviderStateMixin {
  late final AnimationController _fadeCtrl;
  late final Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _fadeCtrl = AnimationController(vsync: this, duration: GQDurations.fade)
      ..forward();
    _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
  }

  @override
  void dispose() {
    _fadeCtrl.dispose();
    super.dispose();
  }

  Future<void> _openSettings() async {
    if (widget.onGoToSettings != null) {
      widget.onGoToSettings!();
      return;
    }
    // Platform-gated fallback. The `app-settings:` URI is iOS-only — on
    // Android Chrome's canLaunchUrl returns false (dead button) and on web
    // there is no concept of a per-app settings deep-link. Show a SnackBar
    // pointing the user at the right place per surface.
    final messenger = ScaffoldMessenger.maybeOf(context);
    if (kIsWeb) {
      messenger?.showSnackBar(
        const SnackBar(
          content: Text(
            'Open your browser\'s site settings to change permissions',
          ),
        ),
      );
      return;
    }
    if (defaultTargetPlatform == TargetPlatform.iOS) {
      final uri = Uri.parse('app-settings:');
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      }
      return;
    }
    if (defaultTargetPlatform == TargetPlatform.android) {
      // No `app_settings` package wired yet — surface a SnackBar with the
      // manual path. We can swap this for a real deep-link in a follow-up.
      messenger?.showSnackBar(
        const SnackBar(
          content: Text(
            'Open Settings → Apps → GentleQuest → Notifications to change permissions',
          ),
        ),
      );
      return;
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: FadeTransition(
            opacity: _fadeAnim,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Spacer(flex: 2),
                // Illustration — muted bell
                Center(
                  child: Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      color: const Color(0xFFF0EFF8),
                      borderRadius: BorderRadius.circular(50),
                    ),
                    child: Icon(
                      Icons.notifications_off_rounded,
                      size: 44,
                      color: t.ink3,
                    ),
                  ),
                ),
                const SizedBox(height: 36),
                // Heading
                Text(
                  "All good. We'll work\nwithout notifications.",
                  style: TextStyle(
                    fontFamily: GQTypography.displayFamily,
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                    height: 1.2,
                    letterSpacing: -0.4,
                    color: t.ink,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  "Everything works without notifications. "
                  "You can always enable them later from Settings "
                  "if you change your mind.",
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                    height: 1.55,
                    color: t.ink2,
                  ),
                ),
                const SizedBox(height: 24),
                // Settings deep-link card
                _SettingsDeepLinkCard(onTap: _openSettings),
                const Spacer(flex: 3),
                // Primary CTA — continue without
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: widget.onContinueWithout,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: GQColors.primaryDk,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: const StadiumBorder(),
                      textStyle: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    child: const Text('Continue'),
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Settings deep-link card ──────────────────────────────────────────────────

class _SettingsDeepLinkCard extends StatelessWidget {
  final VoidCallback onTap;
  const _SettingsDeepLinkCard({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: Border.all(color: t.hair),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0A1F1B3A),
              blurRadius: 12,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: t.primarySoft,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(Icons.settings_rounded,
                  size: 20, color: t.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Manage in Settings',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: t.ink,
                    ),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'Tap to open your device settings',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: t.ink2,
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded,
                color: t.ink2, size: 20),
          ],
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// STATE D — FirstLaunchTutorialOverlay
// ═══════════════════════════════════════════════════════════════════════════════

/// 3-step tooltip tutorial overlay shown once on first chat open.
///
/// Wrap this around your main app content using a [Stack]:
/// ```dart
/// Stack(
///   children: [
///     YourMainContent(),
///     if (_showTutorial)
///       FirstLaunchTutorialOverlay(
///         anchorKeys: [chatKey, questKey, profileKey],
///         onDismiss: () => setState(() => _showTutorial = false),
///       ),
///   ],
/// );
/// ```
///
/// [anchorKeys] — list of exactly 3 GlobalKeys pointing to the nav items
///   to highlight.  If null or empty, uses centered fallback positions.
/// [onDismiss] — called when tutorial completes or is skipped.
class FirstLaunchTutorialOverlay extends StatefulWidget {
  final List<GlobalKey>? anchorKeys;
  final VoidCallback? onDismiss;

  const FirstLaunchTutorialOverlay({
    super.key,
    this.anchorKeys,
    this.onDismiss,
  });

  @override
  State<FirstLaunchTutorialOverlay> createState() =>
      _FirstLaunchTutorialOverlayState();
}

class _FirstLaunchTutorialOverlayState
    extends State<FirstLaunchTutorialOverlay>
    with SingleTickerProviderStateMixin {
  int _step = 0; // 0-indexed; 3 total steps
  bool _dismissed = false;

  late final AnimationController _fadeCtrl;
  late final Animation<double> _fadeAnim;

  static const _steps = [
    _TutorialStep(
      icon: Icons.chat_bubble_rounded,
      title: 'Chat with GentleQuest',
      body: 'Ask anything, anytime. Your space to check in.',
    ),
    _TutorialStep(
      icon: Icons.explore_rounded,
      title: 'Explore your quests',
      body: 'Daily activities shaped around how you feel today.',
    ),
    _TutorialStep(
      icon: Icons.person_rounded,
      title: 'Your profile & safety plan',
      body: 'Always one tap away — crisis support included.',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _fadeCtrl =
        AnimationController(vsync: this, duration: GQDurations.fade)..forward();
    _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
    _markTutorialSeen();
  }

  Future<void> _markTutorialSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_Pref.tutorialSeen, true);
  }

  void _advance() {
    if (_step < _steps.length - 1) {
      setState(() {
        _step++;
        _fadeCtrl.forward(from: 0);
      });
    } else {
      _dismiss();
    }
  }

  void _dismiss() {
    if (_dismissed) return;
    _dismissed = true;
    _fadeCtrl.reverse().then((_) {
      if (mounted) widget.onDismiss?.call();
    });
  }

  @override
  void dispose() {
    _fadeCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final step = _steps[_step];
    final isLast = _step == _steps.length - 1;

    return FadeTransition(
      opacity: _fadeAnim,
      child: Stack(
        children: [
          // Semi-transparent scrim — tap anywhere (except tooltip) to skip
          GestureDetector(
            onTap: _dismiss,
            child: Container(
              color: const Color(0xBF1F1B3A), // ~75% opacity ink
              width: size.width,
              height: size.height,
            ),
          ),
          // Tooltip card — centered horizontally, positioned in lower-mid area
          Positioned(
            left: 16,
            right: 16,
            bottom: size.height * 0.18,
            child: GestureDetector(
              onTap: () {}, // absorb taps inside card so scrim doesn't close
              child: _TutorialCard(
                step: _step,
                totalSteps: _steps.length,
                stepData: step,
                isLast: isLast,
                onGotIt: _advance,
                onSkip: _dismiss,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Tutorial step data ───────────────────────────────────────────────────────

class _TutorialStep {
  final IconData icon;
  final String title;
  final String body;
  const _TutorialStep({
    required this.icon,
    required this.title,
    required this.body,
  });
}

// ─── Tutorial card ────────────────────────────────────────────────────────────

class _TutorialCard extends StatelessWidget {
  final int step;
  final int totalSteps;
  final _TutorialStep stepData;
  final bool isLast;
  final VoidCallback onGotIt;
  final VoidCallback onSkip;

  const _TutorialCard({
    required this.step,
    required this.totalSteps,
    required this.stepData,
    required this.isLast,
    required this.onGotIt,
    required this.onSkip,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        boxShadow: const [
          BoxShadow(
            color: Color(0x33110D2E),
            blurRadius: 40,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Step indicator dots
          Row(
            children: List.generate(totalSteps, (i) {
              final active = i == step;
              return AnimatedContainer(
                duration: GQDurations.fade,
                margin: const EdgeInsets.only(right: 6),
                width: active ? 20 : 8,
                height: 8,
                decoration: BoxDecoration(
                  color: active ? t.primary : t.primarySoft,
                  borderRadius: BorderRadius.circular(100),
                ),
              );
            }),
          ),
          const SizedBox(height: 16),
          // Icon + title row
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: t.primarySoft,
                  borderRadius: BorderRadius.circular(12),
                ),
                child:
                    Icon(stepData.icon, size: 22, color: t.primary),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  stepData.title,
                  style: TextStyle(
                    fontFamily: GQTypography.displayFamily,
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    height: 1.2,
                    color: t.ink,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          // Body text
          Text(
            stepData.body,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 14,
              fontWeight: FontWeight.w500,
              height: 1.5,
              color: t.ink2,
            ),
          ),
          const SizedBox(height: 20),
          // Actions row
          Row(
            children: [
              // "I'll explore on my own" skip link
              Expanded(
                child: TextButton(
                  onPressed: onSkip,
                  style: TextButton.styleFrom(
                    foregroundColor: t.ink2,
                    padding: EdgeInsets.zero,
                    alignment: Alignment.centerLeft,
                    textStyle: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  child: const Text("I'll explore on my own"),
                ),
              ),
              const SizedBox(width: 12),
              // Got it / Next CTA
              SizedBox(
                height: 40,
                child: ElevatedButton(
                  onPressed: onGotIt,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: GQColors.primaryDk,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: const StadiumBorder(),
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    textStyle: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  child: Text(isLast ? 'Got it' : 'Next'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Utility: check whether the tutorial overlay should be shown.
// ═══════════════════════════════════════════════════════════════════════════════

/// Returns true if the first-launch tutorial has NOT been seen.
/// Call before rendering [FirstLaunchTutorialOverlay].
Future<bool> shouldShowTutorial() async {
  final prefs = await SharedPreferences.getInstance();
  return !(prefs.getBool(_Pref.tutorialSeen) ?? false);
}

/// Returns true if the notification opt-in sheet is NOT snoozed.
/// Pass [now] for testing; defaults to [DateTime.now()].
Future<bool> shouldShowNotifOptIn([DateTime? now]) async {
  final prefs = await SharedPreferences.getInstance();
  final snoozeUntil = prefs.getInt(_Pref.maybeLaterSnooze) ?? 0;
  final reference = (now ?? DateTime.now()).millisecondsSinceEpoch;
  return reference > snoozeUntil;
}
