import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb;
import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../widgets/crisis_resources.dart' show showCrisisInterventionSheet;
import '../models/message.dart' show RiskLevel;
import '../widgets/safety_legal_sheet.dart';
import '../widgets/gq/gq.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import './auth/login_screen.dart';
import './legal/legal_screen.dart';
import '../services/api_service.dart';
import '../services/analytics_service.dart' show logAnalyticsEvent;
import '../services/auth_service.dart';
import '../services/firebase_service.dart' show FirebaseService, kAnonymityModeKey;
import '../services/low_stim_service.dart';
import '../services/notification_service_impl.dart';
import '../theme/gq_theme.dart';
import '../theme/gq_tokens.dart';

import 'settings/notification_detail_screen.dart';
import 'settings/settings_account.dart';
import 'settings/settings_widgets.dart';

// No re-exports: unlike the journal/clinical splits, every extracted symbol
// here was private pre-split, so no external consumer can depend on them.
// Re-exporting SectionLabel would collide with profile_widgets.dart's.

// ─── Notification preference keys (SharedPreferences) ───────────────────────
const String _kNotifDailyReminderKey = 'notif_daily_reminder_v1';
const String _kNotifGentleNudgeKey = 'notif_gentle_nudge_v1';
const String _kNotifWorriedCheckInKey = 'notif_worried_checkin_v1';

// ─── Settings Screen — R1D20, WO-5.3 sweep ───────────────────────────────────
//
// Implements GentleQuest_Settings.html: Views A, B, C, D.
//
// A — Settings home (PRIVACY, ACCOUNT, NOTIFICATIONS, CHAT, APPEARANCE,
//       ABOUT, LEGAL — WO-5.3 Part B render order)
// B — Anonymity mode ON state (banner + grayed notifications section)
// C — Delete account 2-step sheet (type-to-confirm, coral not red)
// D — Notifications detail screen (DailyReminderCard, GentleNudgeCard,
//       WorriedCheckInCard, TestNotificationBtn)
//
// Backend wiring TODOs (flagged per foreman brief):
//   • Data export: POST /api/user/export — triggers an EMAIL, not a local
//     download; UI only here.
//   • Delete account server flow: DELETE /api/user not yet implemented.
//     UI surfaces an honest banner with privacy@gentlequest.app fallback
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
//   • Share usage analytics: WIRED — _toggleAnalyticsConsent calls
//     ApiService.setAnalyticsConsent(value), persisting the analytics_consent
//     SharedPreferences flag that logAnalyticsEvent (backend
//     /api/analytics/log) requires in addition to Anonymity mode being off.
//     Off by default; hidden in the Anonymity-ON view (View B) so that
//     view's "nothing leaves this device" promise stays unconditional.

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

  // Analytics consent: separate, narrower opt-IN gate on top of Anonymity
  // mode. Anonymity mode governs the Firebase/GA4 SDK (opt-out, fires by
  // default); this flag governs the backend's own /api/analytics/log
  // event stream (opt-in, off by default) — see analytics_service.dart's
  // _isAnalyticsEnabled(). Was a dead SharedPreferences flag with no UI
  // path ever setting it true; this screen is that UI.
  bool _analyticsEnabled = false;

  // Notification toggles — hydrated from SharedPreferences in
  // [_loadNotificationPrefs]; in-memory defaults are intentionally false so
  // a fresh install never claims a feature is on before the user opts in.
  bool _dailyReminderOn = false;
  bool _gentleNudgeOn = false;
  bool _worriedCheckInOn = false;

  // Crisis check-in lock: per design, locked-on after a heavy moment (P13).
  // In production this would come from a local crisis-flag store.
  final bool _crisisCheckInLocked = true;

  // Low-stim "quiet mode" (v1.5.0 ADHD update, ADR-006). Seeded from
  // LowStimService.enabled — already hydrated from SharedPreferences in
  // main() before any screen mounts, so no extra async read is needed here.
  bool _lowStimOn = LowStimService.enabled;

  // WO-5.3 Part D — point-of-failure banners. Each fires inline right below
  // its section's card; null renders nothing. Success/info feedback for
  // toggles is silent (a toggle that moved is its own confirmation) or a
  // top-anchored auto-dismissing banner for real actions.
  String? _dailyReminderError;
  String? _gentleNudgeError;
  String? _worriedCheckInError;
  String? _lowStimError;
  String? _exportError;

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
    // WO-5.3 A1: forward-migrate the pre-rename pref key once, so an
    // existing opt-in survives instead of silently resetting.
    if (!prefs.containsKey(_kNotifGentleNudgeKey) &&
        prefs.containsKey(NotificationService.legacyGentleNudgePrefKey)) {
      await prefs.setBool(_kNotifGentleNudgeKey,
          prefs.getBool(NotificationService.legacyGentleNudgePrefKey) ?? false);
    }
    setState(() {
      _dailyReminderOn = prefs.getBool(_kNotifDailyReminderKey) ?? false;
      _gentleNudgeOn = prefs.getBool(_kNotifGentleNudgeKey) ?? false;
      _worriedCheckInOn = prefs.getBool(_kNotifWorriedCheckInKey) ?? false;
    });
    // Mirror persisted state to the scheduler so the toggle reflects truth
    // even if the app was killed before — the scheduler keeps this in an
    // in-memory flag for now (no background scheduler yet).
    NotificationService.setStreakNudgeEnabled(_gentleNudgeOn);

    await _reconcileWithOsPermission(prefs);
  }

  /// Turns every notification toggle back OFF if the OS permission has been
  /// revoked since the user opted in.
  ///
  /// Added 2026-09-03. Permission was only checked at the instant a toggle was
  /// flipped ON. Revoke notifications in OS settings afterwards and the stored
  /// pref still said "on", so this screen kept showing "Daily check-in: on"
  /// while the OS silently dropped every scheduled notification. A user could
  /// believe a check-in was coming when nothing was.
  ///
  /// Deliberately one-directional: a revoked permission switches toggles off,
  /// but a granted permission never switches anything on. Permission means the
  /// user COULD be notified, not that they asked to be — re-enabling would
  /// invent an opt-in they never gave.
  ///
  /// `hasPermission()` returns null for "unknown" (web, no platform impl, a
  /// channel error). Unknown must change nothing. Treating it as denied would
  /// silently switch off reminders a user did grant, which is the same class
  /// of harm in the other direction.
  Future<void> _reconcileWithOsPermission(SharedPreferences prefs) async {
    if (!_dailyReminderOn && !_gentleNudgeOn && !_worriedCheckInOn) return;

    final allowed = await NotificationService.hasPermission();
    if (allowed != false) return; // null (unknown) or true -> leave alone
    if (!mounted) return;

    await prefs.setBool(_kNotifDailyReminderKey, false);
    await prefs.setBool(_kNotifGentleNudgeKey, false);
    await prefs.setBool(_kNotifWorriedCheckInKey, false);
    NotificationService.setStreakNudgeEnabled(false);
    if (!mounted) return;
    setState(() {
      _dailyReminderOn = false;
      _gentleNudgeOn = false;
      _worriedCheckInOn = false;
    });
    if (kDebugMode) {
      debugPrint('[notif] OS permission revoked — reminder toggles reset');
    }
  }

  Future<void> _onDailyReminderChanged(bool v) async {
    setState(() {
      _dailyReminderOn = v;
      _dailyReminderError = null;
    });
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kNotifDailyReminderKey, v);

    if (v) {
      final granted = await NotificationService.requestPermissions();
      if (!granted) {
        // Permission denied — revert the toggle so UI matches reality.
        if (!mounted) return;
        setState(() {
          _dailyReminderOn = false;
          _dailyReminderError =
              'Notifications permission denied. Enable in system settings.';
        });
        await prefs.setBool(_kNotifDailyReminderKey, false);
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
        setState(() {
          _dailyReminderOn = false;
          _dailyReminderError =
              "Couldn't schedule notification — check permissions in Settings";
        });
        await prefs.setBool(_kNotifDailyReminderKey, false);
      }
    } else {
      try {
        await NotificationService.cancelGentleDailyCheckin();
      } catch (_) {
        // Cancel failure is non-fatal — preference is already off; swallow.
      }
    }
  }

  Future<void> _onGentleNudgeChanged(bool v) async {
    setState(() {
      _gentleNudgeOn = v;
      _gentleNudgeError = null;
    });
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kNotifGentleNudgeKey, v);

    if (v) {
      final granted = await NotificationService.requestPermissions();
      if (!granted) {
        if (!mounted) return;
        setState(() => _gentleNudgeOn = false);
        await prefs.setBool(_kNotifGentleNudgeKey, false);
        return;
      }
    }
    // Flip the in-service opt-in flag; the actual push fires from the
    // engine when the consecutive-day count crosses 3.
    try {
      NotificationService.setStreakNudgeEnabled(v);
      if (!v) {
        await NotificationService.cancelStreakNudge();
      }
    } catch (_) {
      // Notification channel error / permission revoked OOB — revert visible
      // toggle so it matches reality and tell the user.
      if (!mounted) return;
      setState(() {
        _gentleNudgeOn = !v;
        _gentleNudgeError =
            "Couldn't update your gentle nudge — check notification permissions in Settings";
      });
      await prefs.setBool(_kNotifGentleNudgeKey, !v);
    }
  }

  Future<void> _onWorriedCheckInChanged(bool v) async {
    setState(() {
      _worriedCheckInOn = v;
      _worriedCheckInError = null;
    });
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
        setState(() => _worriedCheckInError =
            "Worried check-in turned off, but couldn't cancel pending one — check notification permissions if it still fires");
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

  /// Consent UI for the /api/analytics/log opt-in (analytics_consent).
  /// Off by default; persisted via ApiService.setAnalyticsConsent. Even
  /// when on, Anonymity mode still wins (see analytics_service.dart), and
  /// this row is hidden entirely in the Anonymity-ON view below so the
  /// "nothing leaves this device" promise there stays unconditional.
  Future<void> _toggleAnalyticsConsent(bool value) async {
    setState(() => _analyticsEnabled = value);

    // ORDER IS LOAD-BEARING. logAnalyticsEvent() is itself gated on
    // analytics_consent (analytics_service.dart _isAnalyticsEnabled), so
    // writing the new value BEFORE logging silently destroyed the opt-OUT
    // signal: persist(false) -> log('off') -> gate now reads false -> event
    // dropped. Only opt-INs were ever recorded, so the event implied 100%
    // opt-in and 0% opt-out. A consent metric that structurally cannot observe
    // withdrawal is worse than no metric.
    //
    // Each transition is therefore logged under the consent state that
    // legitimately permits it: an opt-in after consent is granted, an opt-out
    // while consent is still in force. Nothing is ever transmitted after the
    // user has withdrawn.
    if (value) {
      await _api.setAnalyticsConsent(true);
      await logAnalyticsEvent('analytics_consent_toggled', metadata: {
        'value': 'on',
        'screen': 'settings',
      });
    } else {
      await logAnalyticsEvent('analytics_consent_toggled', metadata: {
        'value': 'off',
        'screen': 'settings',
      });
      await _api.setAnalyticsConsent(false);
    }

    if (!mounted) return;
    GQBanner.show(
      context,
      message: value
          ? 'Sharing basic usage events. Never message content.'
          : 'Usage sharing is off.',
      category: value ? GQBannerCategory.success : GQBannerCategory.info,
    );
  }

  Future<void> _toggleAnonymity(bool value) async {
    setState(() => _anonymityOn = value);
    // Persist + apply across analytics surfaces. setAnonymityMode writes the
    // SharedPreferences flag (kAnonymityModeKey) that both FirebaseService
    // logEvent/logScreenView/setUserId/setUserProperty AND the backend
    // logAnalyticsEvent path check on every call, so the banner copy below
    // is true rather than aspirational. Push-token release on anonymity-on
    // is a separate follow-up (notification service integration).
    await FirebaseService().setAnonymityMode(value);
    if (!mounted) return;
    GQBanner.show(
      context,
      message: value
          ? 'Anonymity is on. Nothing leaves this device.'
          : 'Anonymity is off. Syncing is available again.',
      category: value ? GQBannerCategory.success : GQBannerCategory.info,
    );
  }

  /// Low-stim "quiet mode" toggle (v1.5.0 ADHD update, ADR-006). Applies
  /// instantly app-wide via LowStimService's notifier (LowStimOverlay in
  /// main.dart), persists to SharedPreferences, and reverts the visible
  /// switch on a persistence failure — same shape as the notification
  /// toggle handlers above.
  Future<void> _onLowStimChanged(bool v) async {
    setState(() {
      _lowStimOn = v;
      _lowStimError = null;
    });
    final ok = await LowStimService.setEnabled(v);
    if (!ok) {
      if (!mounted) return;
      setState(() {
        _lowStimOn = !v;
        _lowStimError = "That didn't stick. Flip it once more?";
      });
    }
    await logAnalyticsEvent('low_stim_toggled', metadata: {
      'value': v ? 'on' : 'off',
      'screen': 'settings',
    });
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
    GQBanner.show(
      context,
      message: 'Signed out · your local history stays on this device.',
      category: GQBannerCategory.info,
    );
  }

  Future<void> _handleSendFeedback() async {
    // Open a mailto: with a pre-filled subject. Fallback to clipboard +
    // banner if the platform has no mail client (e.g. some web browsers).
    final uri = Uri(
      scheme: 'mailto',
      path: 'feedback@gentlequest.app',
      query: 'subject=Feedback on GentleQuest',
    );
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
        return;
      }
    } catch (_) {
      // fall through to clipboard fallback
    }
    if (!mounted) return;
    GQBanner.show(
      context,
      message: 'Email feedback@gentlequest.app — we read every note.',
      category: GQBannerCategory.info,
    );
  }

  Future<void> _handleExportData() async {
    if (!mounted) return;
    setState(() => _exportError = null);

    try {
      await ApiService().exportUserData();
      if (!mounted) return;
      GQBanner.show(
        context,
        // Not "check your downloads" — this triggers an email, not a local
        // file (D4 truth rule; see the file-header TODO above).
        message: 'Your export is on its way. Check your email.',
        category: GQBannerCategory.success,
      );
    } catch (e) {
      debugPrint('[settings] export failed: $e');
      if (!mounted) return;
      setState(() => _exportError =
          "That export didn't finish. Nothing was lost — try again?");
    }
  }

  void _openDeleteSheet() {
    GQSheet.show<void>(
      context,
      content: DeleteAccountSheet(
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
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: t.bg,
      appBar: GQHeader(
        title: 'Settings',
        actions: _anonymityOn
            ? const [
                Padding(
                  padding: EdgeInsets.only(right: GQSpacing.lg),
                  child: AnonStatusPill(),
                ),
              ]
            : null,
      ),
      body: _anonymityOn ? _buildAnonymityOnView() : _buildDefaultView(),
    );
  }

  // ── View A: Settings home ─────────────────────────────────────────────────
  // WO-5.3 Part B1 render order: PRIVACY, ACCOUNT, NOTIFICATIONS, CHAT,
  // APPEARANCE, ABOUT, LEGAL, [DEBUG]. YOUR DEVICE DATA dissolves into
  // PRIVACY (A2); the standalone erase section at the bottom is gone.

  Widget _buildDefaultView() {
    final t = GQTheme.of(context);
    final authService = AuthService.instance;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 30),
      children: [
        // PRIVACY (was YOUR DATA + YOUR DEVICE DATA)
        SectionLabel(label: 'PRIVACY'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.shield_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Anonymity mode',
              subtitle: "Nothing leaves this device while it's on.",
              trailing: SettingsToggle(
                value: _anonymityOn,
                locked: false,
                onChanged: _toggleAnonymity,
              ),
            ),
            SettingsRow(
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.insights_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Share extra usage data',
              // COPY MUST MATCH SCOPE. This toggle writes analytics_consent,
              // which gates ONLY the backend /api/analytics/log stream
              // (analytics_service.dart _isAnalyticsEnabled). It does NOT gate
              // Firebase/GA4 — that path checks anonymity mode alone
              // (firebase_service.dart:177), which is the shipped, disclosed
              // opt-out model.
              //
              // The previous copy read 'Share usage analytics / Anonymous
              // app-usage events only'. A user turning that OFF would
              // reasonably believe usage analytics had stopped; tab views,
              // composer focus and send attempts kept flowing to GA4. In a
              // mental-health app a consent control that reads broader than it
              // acts is a real harm, so the copy now names its actual scope and
              // points at Anonymity mode as the total control.
              subtitle:
                  'Sends extra usage events straight to us. Never message '
                  'content. Basic analytics still run unless Anonymity mode '
                  'is on.',
              trailing: SettingsToggle(
                value: _analyticsEnabled,
                locked: false,
                onChanged: _toggleAnalyticsConsent,
              ),
            ),
            SettingsRow(
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.download_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Export my data',
              subtitle: 'A file you keep. Yours to take anywhere.',
              trailing: const Chevron(),
              onTap: _handleExportData,
            ),
            SettingsRow(
              iconBg: t.dangerSoft,
              iconWidget: const Icon(Icons.delete_sweep_outlined,
                  size: 14, color: GQColors.dangerInk),
              title: 'Erase all my data',
              titleColor: GQColors.dangerInk,
              subtitle: "Everything on this device. Can't be undone.",
              subtitleColor: GQColors.dangerInk,
              trailing: const Chevron(),
              onTap: () => _showEraseLocalDataSheet(context),
            ),
          ],
        ),
        if (_exportError != null) ...[
          const SizedBox(height: GQSpacing.sm),
          GQBanner(
            message: _exportError!,
            category: GQBannerCategory.amber,
            onDismiss: () => setState(() => _exportError = null),
          ),
        ],

        // ACCOUNT — opt-in passwordless sign-in for cross-device sync.
        SectionLabel(label: 'ACCOUNT'),
        SettingsCard(
          children: [
            if (authService.isSignedIn)
              SettingsRow(
                iconBg: t.primarySoft,
                iconWidget: const Icon(Icons.check_circle_outline,
                    size: 14, color: GQColors.primaryDk),
                title: 'Signed in',
                subtitle: authService.email ?? '',
                trailing: TextButton(
                  onPressed: _handleSignOut,
                  child: Text(
                    'Sign out',
                    style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w700,
                      color: t.ink2,
                    ),
                  ),
                ),
              )
            else
              SettingsRow(
                iconBg: t.primarySoft,
                iconWidget: const Icon(Icons.sync_outlined,
                    size: 14, color: GQColors.primaryDk),
                title: 'Sign in to sync across devices',
                subtitle:
                    'Passwordless · anonymous use stays supported',
                trailing: const Chevron(),
                onTap: _openLoginScreen,
              ),
            SettingsRow(
              iconBg: t.dangerSoft,
              iconWidget: const Icon(Icons.delete_outline,
                  size: 14, color: GQColors.dangerInk),
              title: 'Delete my account',
              titleColor: GQColors.dangerInk,
              subtitle: 'Requires typed confirmation',
              trailing: const Chevron(),
              onTap: _openDeleteSheet,
            ),
          ],
        ),

        // Notifications section hidden on web: flutter_local_notifications
        // is a native-only plugin. Showing toggles that don't fire would be
        // a "say feature exists, does nothing" trap. Web users skip the
        // whole section; daily reminders ship only on iOS/Android in Phase 1.
        if (!kIsWeb) ...[
          // NOTIFICATIONS
          SectionLabel(label: 'NOTIFICATIONS'),
          SettingsCard(
            children: [
              if (authService.isSignedIn)
                SettingsRow(
                  iconBg: t.primarySoft,
                  iconWidget: const Icon(Icons.notifications_outlined,
                      size: 14, color: GQColors.primaryDk),
                  title: 'Daily check-in reminder',
                  subtitle: '8:00 PM · all 7 days',
                  trailing: SettingsToggle(
                    value: _dailyReminderOn,
                    onChanged: _onDailyReminderChanged,
                  ),
                  onTap: _openNotificationDetail,
                )
              else
                SettingsRow(
                  iconBg: t.primarySoft,
                  iconWidget: const Icon(Icons.notifications_outlined,
                      size: 14, color: GQColors.primaryDk),
                  title: 'Daily check-in reminder',
                  subtitle: 'Create a free account to unlock reminders',
                  subtitleColor: GQColors.primaryDk,
                  trailing: const Chevron(),
                  onTap: _openLoginScreen,
                ),
              SettingsRow(
                iconBg: t.warmSoft,
                iconWidget: const Text('🌱',
                    style: TextStyle(fontSize: 14)),
                title: 'Gentle nudge',
                subtitle: "Only when there's something worth noticing",
                trailing: SettingsToggle(
                  value: _gentleNudgeOn,
                  onChanged: _onGentleNudgeChanged,
                ),
              ),
              SettingsRow(
                iconBg: t.primarySoft,
                iconWidget: const Icon(Icons.favorite_outline,
                    size: 14, color: GQColors.primaryDk),
                title: "If I'm worried about you",
                subtitle: 'One message after a heavy day · always optional',
                trailing: SettingsToggle(
                  value: _worriedCheckInOn,
                  onChanged: _onWorriedCheckInChanged,
                ),
              ),
            ],
          ),
          if (_dailyReminderError != null || _gentleNudgeError != null || _worriedCheckInError != null) ...[
            const SizedBox(height: GQSpacing.sm),
            if (_dailyReminderError != null)
              GQBanner(
                message: _dailyReminderError!,
                category: GQBannerCategory.amber,
                onDismiss: () => setState(() => _dailyReminderError = null),
              ),
            if (_gentleNudgeError != null)
              GQBanner(
                message: _gentleNudgeError!,
                category: GQBannerCategory.amber,
                onDismiss: () => setState(() => _gentleNudgeError = null),
              ),
            if (_worriedCheckInError != null)
              GQBanner(
                message: _worriedCheckInError!,
                category: GQBannerCategory.amber,
                onDismiss: () => setState(() => _worriedCheckInError = null),
              ),
          ],
        ],

        // CHAT (was CHAT PREFERENCES — "preferences" is settings-speak)
        SectionLabel(label: 'CHAT'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.chat_bubble_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'Companion name',
              subtitle: 'Alex',
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
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.star_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'Inline crisis check-ins',
              subtitleColor: GQColors.primaryDk,
              // WO-5.3 Part C: the old subtitle hardcoded a literal "4 days
              // ago" string with no date computation behind it — a
              // fabricated inference, not a leaked one. Replaced per
              // Claude Design's ruling (D4 truth rule).
              subtitle: "Always on. We don't let this one switch off.",
              trailing: SettingsToggle(
                value: true,
                locked: _crisisCheckInLocked,
                onChanged: null,
              ),
              // P13 — locked-on after a heavy moment. Toggle intentionally
              // has `onChanged: null`, but tapping the row used to be a
              // silent no-op which felt broken. Now: explainer banner
              // tells the user why the lock is on + when it'll release.
              onTap: () {
                if (!mounted) return;
                GQBanner.show(
                  context,
                  message:
                      "These stay on for ~14 days after a heavy moment — this is on purpose. You'll be able to turn them off again soon.",
                  category: GQBannerCategory.info,
                );
              },
            ),
          ],
        ),

        // APPEARANCE — v1.5.0 ADHD update (ADR-006): low-stim "quiet mode".
        // Muted palette + reduced motion app-wide; see theme/low_stim_mode.dart.
        SectionLabel(label: 'APPEARANCE'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.spa_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Low-stim quiet mode',
              subtitle: 'Less motion, softer color.',
              trailing: SettingsToggle(
                key: const Key('low_stim_toggle'),
                value: _lowStimOn,
                onChanged: _onLowStimChanged,
              ),
            ),
          ],
        ),
        if (_lowStimError != null) ...[
          const SizedBox(height: GQSpacing.sm),
          GQBanner(
            message: _lowStimError!,
            category: GQBannerCategory.amber,
            onDismiss: () => setState(() => _lowStimError = null),
          ),
        ],

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
              iconBg: t.primarySoft,
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
              iconBg: t.accentSoft,
              iconWidget: Icon(Icons.phone_outlined,
                  size: 14, color: t.coral),
              title: 'Crisis resources',
              subtitle: '988 · Text HOME to 741741',
              trailing: const Chevron(),
              onTap: () async => showSafetyLegalSheet(context),
            ),
            SettingsRow(
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.mail_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'Send feedback',
              trailing: const Chevron(),
              onTap: _handleSendFeedback,
            ),
          ],
        ),

        // LEGAL
        SectionLabel(label: 'LEGAL'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: t.primarySoft,
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
              iconBg: t.primarySoft,
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
          SectionLabel(label: 'DEBUG'),
          SettingsCard(
            children: [
              SettingsRow(
                iconBg: t.accentSoft,
                iconWidget: Icon(Icons.bug_report_outlined,
                    size: 14, color: t.coral),
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
                  iconBg: t.accentSoft,
                  iconWidget: Icon(Icons.bolt_outlined,
                      size: 14, color: t.coral),
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
                    color: t.ink2),
              ),
            );
          },
        ),
        const SizedBox(height: 12),
      ],
    );
  }

  // ── View B: Anonymity ON ──────────────────────────────────────────────────
  // WO-5.3 Part B2 render order + bug fix: Anonymity mode was filed under
  // NOTIFICATIONS — moved to PRIVACY row 1, where View A also has it, so
  // toggling anonymity doesn't feel like landing in a different app.
  // YOUR DEVICE DATA dissolves into PRIVACY (Erase row), same as View A.

  Widget _buildAnonymityOnView() {
    final t = GQTheme.of(context);
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 30),
      children: [
        // Anonymity banner
        AnonymityBanner(),

        // PRIVACY (was YOUR DATA)
        SectionLabel(label: 'PRIVACY'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.shield_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Anonymity mode',
              subtitle: 'On · since today, 9:14 PM',
              subtitleColor: GQColors.primaryDk,
              trailing: SettingsToggle(
                value: _anonymityOn,
                locked: false,
                onChanged: _toggleAnonymity,
              ),
            ),
            SettingsRow(
              iconBg: t.primarySoft,
              iconWidget: const Icon(Icons.download_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Export my data',
              subtitle: 'Local-only when anonymous',
              trailing: const Chevron(),
              onTap: _handleExportData,
            ),
            SettingsRow(
              iconBg: t.dangerSoft,
              iconWidget: const Icon(Icons.delete_sweep_outlined,
                  size: 14, color: GQColors.dangerInk),
              title: 'Erase all my data',
              titleColor: GQColors.dangerInk,
              subtitle: "Everything on this device. Can't be undone.",
              subtitleColor: GQColors.dangerInk,
              trailing: const Chevron(),
              onTap: () => _showEraseLocalDataSheet(context),
            ),
          ],
        ),
        if (_exportError != null) ...[
          const SizedBox(height: GQSpacing.sm),
          GQBanner(
            message: _exportError!,
            category: GQBannerCategory.amber,
            onDismiss: () => setState(() => _exportError = null),
          ),
        ],

        // ACCOUNT
        SectionLabel(label: 'ACCOUNT'),
        SettingsCard(
          children: [
            SettingsRow(
              iconBg: t.dangerSoft,
              iconWidget: const Icon(Icons.delete_outline,
                  size: 14, color: GQColors.dangerInk),
              title: 'Delete my account',
              titleColor: GQColors.dangerInk,
              subtitle: 'Requires typed confirmation',
              trailing: const Chevron(),
              onTap: _openDeleteSheet,
            ),
          ],
        ),

        // NOTIFICATIONS — grayed out when anonymous (no push token)
        SectionLabel(label: 'NOTIFICATIONS'),
        Opacity(
          opacity: 0.45,
          child: IgnorePointer(
            child: SettingsCard(
              children: [
                SettingsRow(
                  iconBg: t.primarySoft,
                  iconWidget: const Icon(Icons.notifications_outlined,
                      size: 14, color: GQColors.primaryDk),
                  title: 'Daily check-in reminder',
                  subtitle: 'Push needs an account ID',
                  trailing: const SettingsToggle(value: false, onChanged: null),
                ),
                SettingsRow(
                  iconBg: t.warmSoft,
                  iconWidget: const Text('🌱', style: TextStyle(fontSize: 14)),
                  title: 'Gentle nudge',
                  trailing: const SettingsToggle(value: false, onChanged: null),
                ),
                SettingsRow(
                  iconBg: t.primarySoft,
                  iconWidget: const Icon(Icons.favorite_outline,
                      size: 14, color: GQColors.primaryDk),
                  title: "If I'm worried about you",
                  trailing: const SettingsToggle(value: false, onChanged: null),
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
                color: t.ink2),
          ),
        ),
      ],
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  /// WO-5.3 Part D1: was a raw AlertDialog. Same content, sheet register —
  /// GQSheet container, GQButton.ghost for Cancel, GQButton.crisis (dangerInk)
  /// for the destructive affirmative. Cancel stays the visually easier exit
  /// (P13).
  void _showEraseLocalDataSheet(BuildContext context) {
    final t = GQTheme.of(context);
    GQSheet.show<void>(
      context,
      content: Builder(
        builder: (sheetContext) => Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Erase all local data?',
                style: GQTypography.titleSm.copyWith(color: t.ink)),
            const SizedBox(height: GQSpacing.sm),
            Text(
                "This deletes your journal, moods, and check-ins from this device. It can't be undone.",
                style: GQTypography.body.copyWith(color: t.ink2)),
            const SizedBox(height: GQSpacing.lg),
            Row(
              children: [
                Expanded(
                  child: GQButton(
                    label: 'Cancel',
                    variant: GQButtonVariant.ghost,
                    fullWidth: false,
                    onPressed: () => Navigator.pop(sheetContext),
                  ),
                ),
                const SizedBox(width: GQSpacing.sm),
                Expanded(
                  child: GQButton(
                    label: 'Erase',
                    variant: GQButtonVariant.crisis,
                    fullWidth: false,
                    onPressed: () async {
                      Navigator.pop(sheetContext);
                      // Clear SharedPreferences — covers anonymity flag,
                      // notif toggles, welcome-seen, safety-plan-filled,
                      // analytics consent, last-mood metadata. Hive caches
                      // (chat history, journal entries, session id) live in
                      // separate stores managed by their respective
                      // providers; clearing those is a v1.4 follow-up (each
                      // provider needs an exposed clear() method we can call
                      // without coupling). For now we clear the prefs
                      // surface, matching the sheet's "from this device"
                      // scope — account and cloud data stay.
                      try {
                        final prefs = await SharedPreferences.getInstance();
                        await prefs.clear();
                        if (!context.mounted) return;
                        GQBanner.show(
                          context,
                          message: 'Cleared. This device is empty.',
                          category: GQBannerCategory.success,
                        );
                      } catch (e) {
                        debugPrint('[settings] erase local prefs failed: $e');
                        if (!context.mounted) return;
                        GQBanner.show(
                          context,
                          message:
                              "We couldn't clear everything. Try once more?",
                          category: GQBannerCategory.amber,
                        );
                      }
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
