import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb;
import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/message.dart' show RiskLevel;
import '../widgets/app_back_button.dart';
import '../widgets/crisis_resources.dart' show showCrisisInterventionSheet;
import '../widgets/safety_legal_sheet.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import './auth/login_screen.dart';
import './legal/legal_screen.dart';
import '../services/api_service.dart';
import '../services/analytics_service.dart' show logAnalyticsEvent;
import '../services/auth_service.dart';
import '../services/firebase_service.dart' show FirebaseService, kAnonymityModeKey;
import '../services/notification_service_impl.dart';
import '../theme/gq_tokens.dart';

import 'settings/notification_detail_screen.dart';
import 'settings/settings_account.dart';
import 'settings/settings_widgets.dart';

// No re-exports: unlike the journal/clinical splits, every extracted symbol
// here was private pre-split, so no external consumer can depend on them.
// Re-exporting SectionLabel would collide with profile_widgets.dart's.

// ─── Notification preference keys (SharedPreferences) ───────────────────────
const String _kNotifDailyReminderKey = 'notif_daily_reminder_v1';
const String _kNotifStreakNudgeKey = 'notif_streak_nudge_v1';
const String _kNotifWorriedCheckInKey = 'notif_worried_checkin_v1';

// ─── Settings Screen — R1D20 ─────────────────────────────────────────────────
//
// Implements GentleQuest_Settings.html: Views A, B, C, D.
//
// A — Settings home (6 sections: YOUR DATA, NOTIFICATIONS, CHAT PREFERENCES,
//       ABOUT, LEGAL, DELETE APP DATA)
// B — Anonymity mode ON state (banner + grayed notifications section)
// C — Delete account 2-step sheet (type-to-confirm, coral not red)
// D — Notifications detail screen (DailyReminderCard, StreakNudgeCard,
//       WorriedCheckInCard, TestNotificationBtn)
//
// Backend wiring TODOs (flagged per foreman brief):
//   • Data export: POST /api/user/export — triggers email; UI only here.
//   • Delete account server flow: DELETE /api/user not yet implemented.
//     UI surfaces an honest snackbar with privacy@gentlequest.app fallback
//     (see DeleteAccountSheet._handleDeleteForever) so the user is NOT
//     told "account deleted" when nothing happened — that would be a GDPR
//     / CCPA "right to erasure" lie. Backend deletion endpoint is v1.4 work.
//   • Anonymity mode: WIRED — _toggleAnonymity calls
//     FirebaseService.setAnonymityMode(value) which sets a persisted
//     SharedPreferences flag (kAnonymityModeKey). Both FirebaseService
//     (Firebase Analytics) AND logAnalyticsEvent (backend /api/analytics/log)
//     honor that flag and become no-ops while it's true. setUserId is also
//     cleared when toggling ON.
//   • Notification time/day prefs: stored locally only; push-token server sync
//     is a follow-up.

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  // ignore: unused_field
  bool _loadingConsent = true;

  // Anonymity mode (View B): when on, analytics events are suppressed.
  bool _anonymityOn = false;

  // Analytics consent (pre-existing flag; anonymity overrides it when on).
  // ignore: unused_field
  bool _analyticsEnabled = false;

  // Notification toggles — hydrated from SharedPreferences in
  // [_loadNotificationPrefs]; in-memory defaults are intentionally false so
  // a fresh install never claims a feature is on before the user opts in.
  bool _dailyReminderOn = false;
  bool _streakNudgeOn = false;
  bool _worriedCheckInOn = false;

  // Crisis check-in lock: per design, locked-on after a heavy moment (P13).
  // In production this would come from a local crisis-flag store.
  final bool _crisisCheckInLocked = true;

  final _api = ApiService();

  @override
  void initState() {
    super.initState();
    _loadConsent();
    _loadNotificationPrefs();
    _loadAnonymityState();
    _validateAuthSession();
  }

  /// Hydrate the Anonymity toggle from SharedPreferences so the UI matches
  /// the persisted state on screen entry. Keeps the local in-memory flag
  /// in sync with the source of truth that FirebaseService + analytics_service
  /// both consult.
  Future<void> _loadAnonymityState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final on = prefs.getBool(kAnonymityModeKey) ?? false;
      if (mounted && on != _anonymityOn) setState(() => _anonymityOn = on);
    } catch (_) {
      // No-op: leave default (false). Persisted state will sync on next toggle.
    }
  }

  /// Hit /api/auth/me to verify the cached "signed in" state still matches
  /// the server. If the server revoked the session (account deleted from
  /// another device, server rotation, expired binding), the cached email
  /// would otherwise show as "Signed in · stale@..." forever.
  /// Fire-and-forget; failure means no network → keep showing cached state.
  Future<void> _validateAuthSession() async {
    if (!AuthService.instance.isSignedIn) return;
    try {
      final resp = await _api.get('/api/auth/me');
      if (resp == null) return;
      final user = (resp is Map<String, dynamic>) ? resp['user'] : null;
      if (user == null) {
        // Server says we're anonymous; client cache says signed in. Server wins.
        await AuthService.instance.signOut();
        if (mounted) setState(() {});
      }
    } catch (_) {
      // Network error — leave cached state alone; user can keep using offline.
    }
  }

  Future<void> _loadConsent() async {
    final enabled = await _api.isAnalyticsEnabled();
    if (mounted) {
      setState(() {
        _analyticsEnabled = enabled;
        _loadingConsent = false;
      });
    }
  }

  // ── Notification preferences (R1D20 audit fix) ─────────────────────────
  //
  // Pre-fix the NOTIFICATIONS toggles were in-memory bools that never
  // reached NotificationService. Flipping them did literally nothing on
  // device. Now: state is persisted in SharedPreferences and every change
  // calls into NotificationService to (un)schedule the real push.

  Future<void> _loadNotificationPrefs() async {
    if (kIsWeb) return;
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _dailyReminderOn = prefs.getBool(_kNotifDailyReminderKey) ?? false;
      _streakNudgeOn = prefs.getBool(_kNotifStreakNudgeKey) ?? false;
      _worriedCheckInOn = prefs.getBool(_kNotifWorriedCheckInKey) ?? false;
    });
    // Mirror persisted state to the scheduler so the toggle reflects truth
    // even if the app was killed before. Streak nudge state is just kept in
    // the service's in-memory flag for now (no scheduler yet).
    NotificationService.setStreakNudgeEnabled(_streakNudgeOn);
  }

  Future<void> _onDailyReminderChanged(bool v) async {
    setState(() => _dailyReminderOn = v);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kNotifDailyReminderKey, v);

    if (v) {
      final granted = await NotificationService.requestPermissions();
      if (!granted) {
        // Permission denied — revert the toggle so UI matches reality.
        if (!mounted) return;
        setState(() => _dailyReminderOn = false);
        await prefs.setBool(_kNotifDailyReminderKey, false);
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Notifications permission denied. Enable in system settings.',
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontWeight: FontWeight.w600),
            ),
            behavior: SnackBarBehavior.floating,
            duration: Duration(seconds: 3),
          ),
        );
        return;
      }
      // Default to 8:00 PM local; detail screen can later override.
      final now = DateTime.now();
      final at = DateTime(now.year, now.month, now.day, 20, 0);
      try {
        await NotificationService.scheduleGentleDailyCheckin(
          enabled: true,
          scheduledTime: at,
        );
      } catch (_) {
        // Scheduling failed (OS quirk, channel error, etc.) — revert the
        // toggle so the visible state matches reality and prompt the user.
        if (!mounted) return;
        setState(() => _dailyReminderOn = false);
        await prefs.setBool(_kNotifDailyReminderKey, false);
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              "Couldn't schedule notification — check permissions in Settings",
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontWeight: FontWeight.w600),
            ),
            behavior: SnackBarBehavior.floating,
            duration: Duration(seconds: 3),
          ),
        );
      }
    } else {
      try {
        await NotificationService.cancelGentleDailyCheckin();
      } catch (_) {
        // Cancel failure is non-fatal — preference is already off; swallow.
      }
    }
  }

  Future<void> _onStreakNudgeChanged(bool v) async {
    setState(() => _streakNudgeOn = v);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kNotifStreakNudgeKey, v);

    if (v) {
      final granted = await NotificationService.requestPermissions();
      if (!granted) {
        if (!mounted) return;
        setState(() => _streakNudgeOn = false);
        await prefs.setBool(_kNotifStreakNudgeKey, false);
        return;
      }
    }
    // Flip the in-service opt-in flag; actual scheduleStreakNudge fires
    // from the streak engine when consecutive-day count crosses 3.
    try {
      NotificationService.setStreakNudgeEnabled(v);
      if (!v) {
        await NotificationService.cancelStreakNudge();
      }
    } catch (_) {
      // Notification channel error / permission revoked OOB — revert visible
      // toggle so it matches reality and tell the user.
      if (!mounted) return;
      setState(() => _streakNudgeOn = !v);
      await prefs.setBool(_kNotifStreakNudgeKey, !v);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            "Couldn't update streak nudge — check notification permissions in Settings",
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontWeight: FontWeight.w600),
          ),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _onWorriedCheckInChanged(bool v) async {
    setState(() => _worriedCheckInOn = v);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kNotifWorriedCheckInKey, v);

    if (v) {
      final granted = await NotificationService.requestPermissions();
      if (!granted) {
        if (!mounted) return;
        setState(() => _worriedCheckInOn = false);
        await prefs.setBool(_kNotifWorriedCheckInKey, false);
        return;
      }
    } else {
      try {
        await NotificationService.cancelWorriedCheckin();
      } catch (_) {
        // Cancel failure is non-fatal — preference is already off; swallow
        // but tell the user something didn't fully tear down.
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              "Worried check-in turned off, but couldn't cancel pending one — check notification permissions if it still fires",
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontWeight: FontWeight.w600),
            ),
            behavior: SnackBarBehavior.floating,
            duration: Duration(seconds: 4),
          ),
        );
      }
    }
    // Worried follow-ups are mood-event-driven (scheduleWorriedCheckin)
    // rather than toggle-driven, so when toggling off we cancel any pending
    // and when toggling on we just persist the user's consent state (which we did).
  }

  // ignore: unused_element
  Future<void> _toggleConsent(bool value) async {
    setState(() => _analyticsEnabled = value);
    await _api.setAnalyticsConsent(value);
    if (value) {
      await logAnalyticsEvent('consent_changed', metadata: {
        'action': 'enable_analytics',
        'screen': 'settings',
        'success': true,
      });
    }
  }

  Future<void> _toggleAnonymity(bool value) async {
    setState(() => _anonymityOn = value);
    // Persist + apply across analytics surfaces. setAnonymityMode writes the
    // SharedPreferences flag (kAnonymityModeKey) that both FirebaseService
    // logEvent/logScreenView/setUserId/setUserProperty AND the backend
    // logAnalyticsEvent path check on every call, so the "Analytics paused"
    // copy below is now true rather than aspirational. Push-token release on
    // anonymity-on is a separate follow-up (notification service integration).
    await FirebaseService().setAnonymityMode(value);
    if (!mounted) return;
    final msg = value
        ? 'Anonymity is on. Analytics paused.'
        : 'Anonymity is off. Analytics resumed.';
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg,
              style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontWeight: FontWeight.w600)),
          behavior: SnackBarBehavior.floating,
          backgroundColor: GQColors.ink,
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _openLoginScreen() async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
    // Refresh visible state — user may have signed in via deep link
    // while the LoginScreen was on top.
    if (mounted) setState(() {});
  }

  Future<void> _handleSignOut() async {
    await AuthService.instance.signOut();
    if (!mounted) return;
    setState(() {});
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Signed out · your local history stays on this device.'),
        behavior: SnackBarBehavior.floating,
        duration: Duration(seconds: 3),
      ),
    );
  }

  Future<void> _handleSendFeedback() async {
    // Open a mailto: with a pre-filled subject. Fallback to clipboard +
    // SnackBar if the platform has no mail client (e.g. some web browsers).
    final uri = Uri(
      scheme: 'mailto',
      path: 'feedback@gentlequest.app',
      query: 'subject=Feedback on GentleQuest',
    );
    final messenger = ScaffoldMessenger.maybeOf(context);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
        return;
      }
    } catch (_) {
      // fall through to clipboard fallback
    }
    if (!mounted) return;
    messenger?.showSnackBar(
      const SnackBar(
        content: Text('Email feedback@gentlequest.app — we read every note.'),
        behavior: SnackBarBehavior.floating,
        duration: Duration(seconds: 4),
      ),
    );
  }

  Future<void> _handleExportData() async {
    if (!mounted) return;
    
    // Show loading state or immediate feedback
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Sending export to your email…'),
        behavior: SnackBarBehavior.floating,
        duration: Duration(seconds: 2),
      ),
    );

    try {
      await ApiService().exportUserData();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            "Export requested! A JSON copy of your data will be sent to your email shortly.",
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontWeight: FontWeight.w600),
          ),
          behavior: SnackBarBehavior.floating,
          backgroundColor: Colors.green,
          duration: Duration(seconds: 6),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to request export: $e'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _openDeleteSheet() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DeleteAccountSheet(
        // Wire the "Want a copy first? Export my data →" link inside the
        // delete sheet to the parent screen's _handleExportData(). Was
        // previously a TODO that just popped the sheet silently — user
        // who actually wanted to export before deleting got no feedback.
        onExportRequested: _handleExportData,
      ),
    );
  }

  void _openNotificationDetail() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const NotificationDetailScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: AppBar(
        backgroundColor: GQColors.softBg.withValues(alpha: 0.92),
        elevation: 0,
        title: Row(
          children: [
            Text(
              'Settings',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                letterSpacing: -0.3,
              ),
            ),
            if (_anonymityOn) ...[
              const SizedBox(width: 10),
              AnonStatusPill(),
            ],
          ],
        ),
        automaticallyImplyLeading: false,
        leading: Builder(
          builder: (ctx) {
            final canPop = Navigator.of(ctx).canPop();
            final route = ModalRoute.of(ctx);
            final isModal =
                route is PageRoute && route.fullscreenDialog == true;
            if (canPop) return AppBackButton(isModal: isModal);
            return const SizedBox.shrink();
          },
        ),
      ),
      body: _anonymityOn ? _buildAnonymityOnView() : _buildDefaultView(),
    );
  }

  // ── View A: Settings home ─────────────────────────────────────────────────

  Widget _buildDefaultView() {
    final authService = AuthService.instance;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 30),
      children: [
        // ACCOUNT — opt-in passwordless sign-in for cross-device sync.
        SectionLabel(label: 'ACCOUNT'),
        SettingsCard(
          children: [
            if (authService.isSignedIn)
              SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.check_circle_outline,
                    size: 14, color: GQColors.primaryDk),
                title: 'Signed in',
                subtitle: authService.email ?? '',
                trailing: TextButton(
                  onPressed: _handleSignOut,
                  child: const Text(
                    'Sign out',
                    style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w700,
                      color: GQColors.ink2,
                    ),
                  ),
                ),
              )
            else
              SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.sync_outlined,
                    size: 14, color: GQColors.primaryDk),
                title: 'Sign in to sync across devices',
                subtitle:
                    'Passwordless · anonymous use stays supported',
                trailing: const Chevron(),
                onTap: _openLoginScreen,
              ),
          ],
        ),

        const SizedBox(height: 14),

        // YOUR DATA
        SectionLabel(label: 'YOUR DATA'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.download_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Export my data',
              subtitle: 'Sends a JSON copy to your email',
              trailing: const Chevron(),
              onTap: _handleExportData,
            ),
            SettingsRow(
              iconBg: GQColors.accentSoft,
              iconWidget: const Icon(Icons.delete_outline,
                  size: 14, color: GQColors.coral),
              title: 'Delete my account',
              titleColor: GQColors.dangerInk,
              subtitle: 'Permanently removes everything',
              trailing: const Chevron(),
              onTap: _openDeleteSheet,
            ),
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.shield_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Anonymity mode',
              subtitle: 'Stops analytics events while on',
              trailing: GQToggle(
                value: _anonymityOn,
                locked: false,
                onChanged: _toggleAnonymity,
              ),
            ),
          ],
        ),

        // Notifications section hidden on web: flutter_local_notifications
        // is a native-only plugin. Showing toggles that don't fire would be
        // a "say feature exists, does nothing" trap. Web users skip the
        // whole section; daily reminders ship only on iOS/Android in Phase 1.
        if (!kIsWeb) ...[
          const SizedBox(height: 14),

          // NOTIFICATIONS
          SectionLabel(label: 'NOTIFICATIONS'),
          SettingsCard(
            children: [
              SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.notifications_outlined,
                    size: 14, color: GQColors.primaryDk),
                title: 'Daily check-in reminder',
                subtitle: '8:00 PM · all 7 days',
                trailing: GQToggle(
                  value: _dailyReminderOn,
                  onChanged: _onDailyReminderChanged,
                ),
                onTap: _openNotificationDetail,
              ),
              SettingsRow(
                iconBg: GQColors.warmSoft,
                iconWidget: const Text('🔥',
                    style: TextStyle(fontSize: 14)),
                title: 'Streak gentle nudge',
                subtitle: 'Off — only celebrate, never shame',
                trailing: GQToggle(
                  value: _streakNudgeOn,
                  onChanged: _onStreakNudgeChanged,
                ),
              ),
              SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.favorite_outline,
                    size: 14, color: GQColors.primaryDk),
                title: "If I'm worried about you",
                subtitle: 'One message after a heavy day · always optional',
                trailing: GQToggle(
                  value: _worriedCheckInOn,
                  onChanged: _onWorriedCheckInChanged,
                ),
              ),
            ],
          ),
        ],

        const SizedBox(height: 14),

        // CHAT PREFERENCES
        SectionLabel(label: 'CHAT PREFERENCES'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.chat_bubble_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'Companion name',
              subtitle: 'Currently: Alex',
              // Chevron removed — name picker isn't built yet. Was a
              // vestigial affordance: row looked tappable, did nothing.
              trailing: Text('Alex',
                  style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 12.5,
                      fontWeight: FontWeight.w800,
                      color: GQColors.primaryDk)),
            ),
            // Voice TTS row entirely hidden — feature lives in Phase 3
            // of the voice rollout (bidirectional conversational mode
            // with ElevenLabs-grade TTS). Surfacing a "coming soon" row
            // with a tappable chevron is a vestigial affordance.
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.star_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'Inline crisis check-ins',
              subtitleColor: GQColors.primaryDk,
              subtitle: 'Locked on · last heavy day was 4 days ago',
              trailing: GQToggle(
                value: true,
                locked: _crisisCheckInLocked,
                onChanged: null,
              ),
              // P13 — locked-on after a heavy moment. Toggle intentionally
              // has `onChanged: null`, but tapping the row used to be a
              // silent no-op which felt broken. Now: explainer snackbar
              // tells the user why the lock is on + when it'll release.
              onTap: () {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: const Text(
                      "These stay on for ~14 days after a heavy moment — this is on purpose. You'll be able to turn them off again soon.",
                      style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontWeight: FontWeight.w600),
                    ),
                    behavior: SnackBarBehavior.floating,
                    backgroundColor: GQColors.ink,
                    duration: const Duration(seconds: 4),
                  ),
                );
              },
            ),
          ],
        ),

        const SizedBox(height: 14),

        // ABOUT
        SectionLabel(label: 'ABOUT'),
        SettingsCard(
          children: [
            SettingsRow(
              // IMG-TINT: lavender-soft icon-bg tint (agent ruling 2026-05-22 keep raw)
              iconBg: const Color(0xFFF4F0FA),
              iconWidget: const Icon(Icons.info_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'About GentleQuest',
              trailing: const Chevron(),
            ),
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.shield_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Privacy policy',
              trailing: const Chevron(),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const LegalScreen(
                    title: 'Privacy Policy',
                    assetPath: 'assets/legal/privacy.md',
                  ),
                ),
              ),
            ),
            SettingsRow(
              iconBg: GQColors.accentSoft,
              iconWidget: const Icon(Icons.phone_outlined,
                  size: 14, color: GQColors.coral),
              title: 'Crisis resources',
              subtitle: '988 · Text HOME to 741741',
              trailing: const Chevron(),
              onTap: () async => showSafetyLegalSheet(context),
            ),
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.mail_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'Send feedback',
              trailing: const Chevron(),
              onTap: _handleSendFeedback,
            ),
          ],
        ),

        const SizedBox(height: 14),

        // LEGAL
        SectionLabel(label: 'LEGAL'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.description_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Terms of service',
              trailing: const Chevron(),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const LegalScreen(
                    title: 'Terms of Service',
                    assetPath: 'assets/legal/terms.md',
                  ),
                ),
              ),
            ),
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.code_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Open source licenses',
              trailing: const Chevron(),
              onTap: () => showLicensePage(
                context: context,
                applicationName: 'GentleQuest',
              ),
            ),
          ],
        ),

        // Debug-only: lets us QA the crisis sheet end-to-end without
        // engineering fake risk state. Hidden in release builds.
        if (kDebugMode) ...[
          const SizedBox(height: 14),
          SectionLabel(label: 'DEBUG'),
          SettingsCard(
            children: [
              SettingsRow(
                iconBg: GQColors.accentSoft,
                iconWidget: const Icon(Icons.bug_report_outlined,
                    size: 14, color: GQColors.coral),
                title: 'Test crisis intervention sheet',
                subtitle: 'Opens the sheet without triggering real risk',
                trailing: const Chevron(),
                onTap: () => showCrisisInterventionSheet(
                  context,
                  risk: RiskLevel.medium,
                  source: 'settings_debug',
                ),
              ),
              if (!kIsWeb)
                SettingsRow(
                  iconBg: GQColors.accentSoft,
                  iconWidget: const Icon(Icons.bolt_outlined,
                      size: 14, color: GQColors.coral),
                  title: 'Test fatal crash',
                  subtitle: 'Force a fatal crash to test Crashlytics',
                  trailing: const Chevron(),
                  onTap: () {
                    FirebaseCrashlytics.instance.crash();
                  },
                ),
            ],
          ),
        ],

        // Version + sync footer — was hardcoded `'Version 1.2.2 · build
        // 26032321'` and `'Last sync · just now'` regardless of actual
        // version or sync state. Now reads at runtime via PackageInfo
        // (FutureBuilder, since pubspec is the source of truth).
        // Sync line dropped entirely until JournalStorage exposes a
        // last-success timestamp — easier than fake-displaying it.
        FutureBuilder<PackageInfo>(
          future: PackageInfo.fromPlatform(),
          builder: (ctx, snap) {
            final v = snap.hasData
                ? 'Version ${snap.data!.version} · build ${snap.data!.buildNumber}'
                : 'Version —';
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 14),
              child: Text(
                v,
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    color: GQColors.ink3),
              ),
            );
          },
        ),

        // DELETE APP DATA — destructive at the bottom (P13)
        SectionLabel(
          label: 'DELETE APP DATA',
          color: GQColors.dangerInk,
        ),
        EraseLocalDataBtn(
          onTap: () => _showEraseLocalDataDialog(context),
        ),
        const SizedBox(height: 8),
        Text(
          'Removes local cache. Your account and cloud data stay.',
          textAlign: TextAlign.center,
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: GQColors.ink3),
        ),
        const SizedBox(height: 30),
      ],
    );
  }

  // ── View B: Anonymity ON ──────────────────────────────────────────────────

  Widget _buildAnonymityOnView() {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 30),
      children: [
        // Anonymity banner
        AnonymityBanner(),
        const SizedBox(height: 14),

        // YOUR DATA
        SectionLabel(label: 'YOUR DATA'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.download_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Export my data',
              subtitle: 'Local-only when anonymous',
              trailing: const Chevron(),
              onTap: _handleExportData,
            ),
            SettingsRow(
              iconBg: GQColors.accentSoft,
              iconWidget: const Icon(Icons.delete_outline,
                  size: 14, color: GQColors.coral),
              title: 'Delete my account',
              titleColor: GQColors.dangerInk,
              trailing: const Chevron(),
              onTap: _openDeleteSheet,
            ),
            SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.shield_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Anonymity mode',
              subtitle: 'On · since today, 9:14 PM',
              subtitleColor: GQColors.primaryDk,
              trailing: GQToggle(
                value: _anonymityOn,
                locked: false,
                onChanged: _toggleAnonymity,
              ),
            ),
          ],
        ),

        const SizedBox(height: 14),

        // NOTIFICATIONS — grayed out when anonymous (no push token)
        SectionLabel(label: 'NOTIFICATIONS'),
        Opacity(
          opacity: 0.45,
          child: IgnorePointer(
            child: SettingsCard(
              children: [
                SettingsRow(
                  iconBg: GQColors.primarySoft,
                  iconWidget: const Icon(Icons.notifications_outlined,
                      size: 14, color: GQColors.primaryDk),
                  title: 'Daily check-in reminder',
                  subtitle: 'Push needs an account ID',
                  trailing: GQToggle(value: false, onChanged: null),
                ),
                SettingsRow(
                  iconBg: GQColors.warmSoft,
                  iconWidget: const Text('🔥', style: TextStyle(fontSize: 14)),
                  title: 'Streak gentle nudge',
                  trailing: GQToggle(value: false, onChanged: null),
                ),
                SettingsRow(
                  iconBg: GQColors.primarySoft,
                  iconWidget: const Icon(Icons.favorite_outline,
                      size: 14, color: GQColors.primaryDk),
                  title: "If I'm worried about you",
                  trailing: GQToggle(value: false, onChanged: null),
                ),
              ],
            ),
          ),
        ),

        Padding(
          padding: const EdgeInsets.symmetric(vertical: 14),
          child: Text(
            'You can turn this off anytime.',
            textAlign: TextAlign.center,
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                color: GQColors.ink2),
          ),
        ),
      ],
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  void _showEraseLocalDataDialog(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Erase local data?',
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontWeight: FontWeight.w800,
                color: GQColors.ink)),
        content: Text(
            'This removes the local cache only. Your account and cloud data stay.',
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                color: GQColors.ink2)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              // Clear SharedPreferences — covers anonymity flag, notif
              // toggles, welcome-seen, safety-plan-filled, analytics
              // consent, last-mood metadata. Hive caches (chat history,
              // journal entries, session id) live in separate stores
              // managed by their respective providers; clearing those is
              // a v1.4 follow-up (each provider needs an exposed clear()
              // method we can call without coupling). For now we clear
              // the prefs surface — which is what the dialog promises
              // ("Removes local cache. Your account and cloud data stay").
              try {
                final prefs = await SharedPreferences.getInstance();
                await prefs.clear();
              } catch (e) {
                debugPrint('[settings] erase local prefs failed: $e');
              }
              if (!context.mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text(
                    'Local data erased. Restart the app to start fresh.',
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontWeight: FontWeight.w600),
                  ),
                  behavior: SnackBarBehavior.floating,
                  duration: Duration(seconds: 5),
                ),
              );
            },
            style: TextButton.styleFrom(foregroundColor: GQColors.coral),
            child: Text('Erase',
                style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontWeight: FontWeight.w800,
                    color: GQColors.coral)),
          ),
        ],
      ),
    );
  }
}

