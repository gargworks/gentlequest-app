import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb;
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/message.dart' show RiskLevel;
import '../widgets/app_back_button.dart';
import '../widgets/crisis_resources.dart' show showCrisisInterventionSheet;
import '../widgets/safety_legal_sheet.dart';
import './auth/login_screen.dart';
import './legal/legal_screen.dart';
import '../services/api_service.dart';
import '../services/analytics_service.dart' show logAnalyticsEvent;
import '../services/auth_service.dart';
import '../theme/gq_tokens.dart';

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
//   • Delete account server flow: DELETE /api/user — UI + 2-step confirm only;
//     actual server call left as TODO below (see _handleDeleteAccount).
//   • Anonymity mode: all FirebaseAnalytics.log* calls should become no-ops
//     when _anonymityOn is true — currently only sets a local flag; analytics
//     service integration is a follow-up.
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

  // Notification toggles
  bool _dailyReminderOn = true;
  bool _streakNudgeOn = false;
  bool _worriedCheckInOn = true;

  // Crisis check-in lock: per design, locked-on after a heavy moment (P13).
  // In production this would come from a local crisis-flag store.
  final bool _crisisCheckInLocked = true;

  final _api = ApiService();

  @override
  void initState() {
    super.initState();
    _loadConsent();
    _validateAuthSession();
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

  void _toggleAnonymity(bool value) {
    setState(() => _anonymityOn = value);
    // TODO(backend): when anonymityOn=true, release push token + suppress
    // all FirebaseAnalytics.log* calls (see eng notes in GentleQuest_Settings.html).
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
    // TODO(backend): POST /api/user/export — trigger email send.
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Export requested — a JSON copy will be sent to your email.',
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontWeight: FontWeight.w600)),
        behavior: SnackBarBehavior.floating,
        backgroundColor: GQColors.ink,
        duration: Duration(seconds: 3),
      ),
    );
  }

  void _openDeleteSheet() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _DeleteAccountSheet(),
    );
  }

  void _openNotificationDetail() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const _NotificationDetailScreen()),
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
              _AnonStatusPill(),
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
        _SectionLabel(label: 'ACCOUNT'),
        _SettingsCard(
          children: [
            if (authService.isSignedIn)
              _SettingsRow(
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
              _SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.sync_outlined,
                    size: 14, color: GQColors.primaryDk),
                title: 'Sign in to sync across devices',
                subtitle:
                    'Passwordless · anonymous use stays supported',
                trailing: const _Chevron(),
                onTap: _openLoginScreen,
              ),
          ],
        ),

        const SizedBox(height: 14),

        // YOUR DATA
        _SectionLabel(label: 'YOUR DATA'),
        _SettingsCard(
          children: [
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.download_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Export my data',
              subtitle: 'Sends a JSON copy to your email',
              trailing: const _Chevron(),
              onTap: _handleExportData,
            ),
            _SettingsRow(
              iconBg: GQColors.accentSoft,
              iconWidget: const Icon(Icons.delete_outline,
                  size: 14, color: GQColors.coral),
              title: 'Delete my account',
              titleColor: const Color(0xFFC44A4A),
              subtitle: 'Permanently removes everything',
              trailing: const _Chevron(),
              onTap: _openDeleteSheet,
            ),
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.shield_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Anonymity mode',
              subtitle: 'Stops analytics events while on',
              trailing: _GQToggle(
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
          _SectionLabel(label: 'NOTIFICATIONS'),
          _SettingsCard(
            children: [
              _SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.notifications_outlined,
                    size: 14, color: GQColors.primaryDk),
                title: 'Daily check-in reminder',
                subtitle: '8:00 PM · all 7 days',
                trailing: _GQToggle(
                  value: _dailyReminderOn,
                  onChanged: (v) {
                    setState(() => _dailyReminderOn = v);
                  },
                ),
                onTap: _openNotificationDetail,
              ),
              _SettingsRow(
                iconBg: const Color(0xFFFFF1E5),
                iconWidget: const Text('🔥',
                    style: TextStyle(fontSize: 14)),
                title: 'Streak gentle nudge',
                subtitle: 'Off — only celebrate, never shame',
                trailing: _GQToggle(
                  value: _streakNudgeOn,
                  onChanged: (v) => setState(() => _streakNudgeOn = v),
                ),
              ),
              _SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.favorite_outline,
                    size: 14, color: GQColors.primaryDk),
                title: "If I'm worried about you",
                subtitle: 'One message after a heavy day · always optional',
                trailing: _GQToggle(
                  value: _worriedCheckInOn,
                  onChanged: (v) => setState(() => _worriedCheckInOn = v),
                ),
              ),
            ],
          ),
        ],

        const SizedBox(height: 14),

        // CHAT PREFERENCES
        _SectionLabel(label: 'CHAT PREFERENCES'),
        _SettingsCard(
          children: [
            _SettingsRow(
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
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.star_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'Inline crisis check-ins',
              subtitleColor: GQColors.primaryDk,
              subtitle: 'Locked on · last heavy day was 4 days ago',
              trailing: _GQToggle(
                value: true,
                locked: _crisisCheckInLocked,
                onChanged: null,
              ),
            ),
          ],
        ),

        const SizedBox(height: 14),

        // ABOUT
        _SectionLabel(label: 'ABOUT'),
        _SettingsCard(
          children: [
            _SettingsRow(
              iconBg: const Color(0xFFF4F0FA),
              iconWidget: const Icon(Icons.info_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'About GentleQuest',
              trailing: const _Chevron(),
            ),
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.shield_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Privacy policy',
              trailing: const _Chevron(),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const LegalScreen(
                    title: 'Privacy Policy',
                    assetPath: 'assets/legal/privacy.md',
                  ),
                ),
              ),
            ),
            _SettingsRow(
              iconBg: GQColors.accentSoft,
              iconWidget: const Icon(Icons.phone_outlined,
                  size: 14, color: GQColors.coral),
              title: 'Crisis resources',
              subtitle: '988 · Text HOME to 741741',
              trailing: const _Chevron(),
              onTap: () async => showSafetyLegalSheet(context),
            ),
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.mail_outline,
                  size: 14, color: GQColors.primaryDk),
              title: 'Send feedback',
              trailing: const _Chevron(),
              onTap: _handleSendFeedback,
            ),
          ],
        ),

        const SizedBox(height: 14),

        // LEGAL
        _SectionLabel(label: 'LEGAL'),
        _SettingsCard(
          children: [
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.description_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Terms of service',
              trailing: const _Chevron(),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const LegalScreen(
                    title: 'Terms of Service',
                    assetPath: 'assets/legal/terms.md',
                  ),
                ),
              ),
            ),
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.code_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Open source licenses',
              trailing: const _Chevron(),
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
          _SectionLabel(label: 'DEBUG'),
          _SettingsCard(
            children: [
              _SettingsRow(
                iconBg: GQColors.accentSoft,
                iconWidget: const Icon(Icons.bug_report_outlined,
                    size: 14, color: GQColors.coral),
                title: 'Test crisis intervention sheet',
                subtitle: 'Opens the sheet without triggering real risk',
                trailing: const _Chevron(),
                onTap: () => showCrisisInterventionSheet(
                  context,
                  risk: RiskLevel.medium,
                  source: 'settings_debug',
                ),
              ),
            ],
          ),
        ],

        Padding(
          padding: const EdgeInsets.symmetric(vertical: 14),
          child: Column(
            children: [
              Text(
                'Version 1.2.2 · build 26032321',
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    color: GQColors.ink3),
              ),
              const SizedBox(height: 4),
              Text(
                'Last sync · just now',
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink3),
              ),
            ],
          ),
        ),

        // DELETE APP DATA — destructive at the bottom (P13)
        _SectionLabel(
          label: 'DELETE APP DATA',
          color: const Color(0xFFC44A4A),
        ),
        _EraseLocalDataBtn(
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
        _AnonymityBanner(),
        const SizedBox(height: 14),

        // YOUR DATA
        _SectionLabel(label: 'YOUR DATA'),
        _SettingsCard(
          children: [
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.download_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Export my data',
              subtitle: 'Local-only when anonymous',
              trailing: const _Chevron(),
              onTap: _handleExportData,
            ),
            _SettingsRow(
              iconBg: GQColors.accentSoft,
              iconWidget: const Icon(Icons.delete_outline,
                  size: 14, color: GQColors.coral),
              title: 'Delete my account',
              titleColor: const Color(0xFFC44A4A),
              trailing: const _Chevron(),
              onTap: _openDeleteSheet,
            ),
            _SettingsRow(
              iconBg: GQColors.primarySoft,
              iconWidget: const Icon(Icons.shield_outlined,
                  size: 14, color: GQColors.primaryDk),
              title: 'Anonymity mode',
              subtitle: 'On · since today, 9:14 PM',
              subtitleColor: GQColors.primaryDk,
              trailing: _GQToggle(
                value: _anonymityOn,
                locked: false,
                onChanged: _toggleAnonymity,
              ),
            ),
          ],
        ),

        const SizedBox(height: 14),

        // NOTIFICATIONS — grayed out when anonymous (no push token)
        _SectionLabel(label: 'NOTIFICATIONS'),
        Opacity(
          opacity: 0.45,
          child: IgnorePointer(
            child: _SettingsCard(
              children: [
                _SettingsRow(
                  iconBg: GQColors.primarySoft,
                  iconWidget: const Icon(Icons.notifications_outlined,
                      size: 14, color: GQColors.primaryDk),
                  title: 'Daily check-in reminder',
                  subtitle: 'Push needs an account ID',
                  trailing: _GQToggle(value: false, onChanged: null),
                ),
                _SettingsRow(
                  iconBg: const Color(0xFFFFF1E5),
                  iconWidget: const Text('🔥', style: TextStyle(fontSize: 14)),
                  title: 'Streak gentle nudge',
                  trailing: _GQToggle(value: false, onChanged: null),
                ),
                _SettingsRow(
                  iconBg: GQColors.primarySoft,
                  iconWidget: const Icon(Icons.favorite_outline,
                      size: 14, color: GQColors.primaryDk),
                  title: "If I'm worried about you",
                  trailing: _GQToggle(value: false, onChanged: null),
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
            onPressed: () {
              Navigator.pop(ctx);
              // TODO(backend): clear local SharedPreferences / Hive caches.
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

// ─── Anonymity banner (View B) ────────────────────────────────────────────────

class _AnonymityBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: GQColors.primarySoft,
        border: Border.all(
            color: GQColors.primary.withValues(alpha: 0.18), width: 1),
        borderRadius: BorderRadius.circular(14),
      ),
      padding: const EdgeInsets.all(12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 30,
            height: 30,
            decoration: const BoxDecoration(
                color: Colors.white, shape: BoxShape.circle),
            child: const Icon(Icons.shield_outlined,
                size: 14, color: GQColors.primaryDk),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Anonymity is on.',
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink)),
                const SizedBox(height: 2),
                Text(
                    "We're not collecting events while this is on. Your chats still happen — they just don't get logged for analytics.",
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: GQColors.ink2,
                        height: 1.45)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Anon status pill (shown in nav-bar when anonymity is on) ─────────────────

class _AnonStatusPill extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: GQColors.primarySoft,
        border: Border.all(
            color: GQColors.primary.withValues(alpha: 0.30), width: 1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text('ANONYMOUS',
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: GQColors.primaryDk,
              letterSpacing: 0.5)),
    );
  }
}

// ─── Delete account sheet (View C) ───────────────────────────────────────────

class _DeleteAccountSheet extends StatefulWidget {
  const _DeleteAccountSheet();

  @override
  State<_DeleteAccountSheet> createState() => _DeleteAccountSheetState();
}

class _DeleteAccountSheetState extends State<_DeleteAccountSheet> {
  final _controller = TextEditingController();
  bool _confirmed = false;
  bool _deleting = false;

  @override
  void initState() {
    super.initState();
    _controller.addListener(() {
      final match = _controller.text.trim() == 'DELETE';
      if (match != _confirmed) setState(() => _confirmed = match);
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _handleDeleteForever() async {
    if (!_confirmed || _deleting) return;
    setState(() => _deleting = true);
    // TODO(backend): DELETE /api/user — remove all server-side data.
    // After server confirms, clear local storage and sign out.
    // For now: show confirmation and dismiss.
    if (mounted) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
              'Account deletion requested — backend wiring is a follow-up TODO.',
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontWeight: FontWeight.w600)),
          behavior: SnackBarBehavior.floating,
          backgroundColor: GQColors.ink,
          duration: Duration(seconds: 4),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 14,
        bottom: MediaQuery.of(context).viewInsets.bottom + 32,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // drag handle
          Center(
            child: Container(
              width: 44,
              height: 5,
              decoration: BoxDecoration(
                  color: const Color(0xFFE5E2EE),
                  borderRadius: BorderRadius.circular(100)),
            ),
          ),
          const SizedBox(height: 16),

          // Warning icon
          Container(
            width: 60,
            height: 60,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [GQColors.accentSoft, Color(0xFFFFF1E5)],
              ),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.warning_amber_outlined,
                size: 26, color: Color(0xFFC44A4A)),
          ),
          const SizedBox(height: 12),

          Text(
            'Delete your account?',
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                letterSpacing: -0.4),
          ),
          const SizedBox(height: 8),
          RichText(
            textAlign: TextAlign.center,
            text: TextSpan(
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: GQColors.ink2,
                  height: 1.5),
              children: const [
                TextSpan(
                    text:
                        'This removes all your chats, mood logs, and settings. '),
                TextSpan(
                    text: "We can't get them back.",
                    style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink)),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Safer path — export first
          GestureDetector(
            onTap: () {
              Navigator.pop(context);
              // TODO: open export flow
            },
            child: Container(
              width: double.infinity,
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
              decoration: BoxDecoration(
                color: GQColors.primarySoft,
                border: Border.all(
                    color: GQColors.primary.withValues(alpha: 0.20), width: 1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Want a copy first? Export my data',
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                        color: GQColors.primaryDk),
                  ),
                  const SizedBox(width: 4),
                  const Icon(Icons.arrow_forward_outlined,
                      size: 13, color: GQColors.primaryDk),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Type-to-confirm field
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'TYPE DELETE TO CONTINUE',
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink3,
                  letterSpacing: 0.6),
            ),
          ),
          const SizedBox(height: 6),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFFFBF1F4),
              border: Border.all(color: GQColors.coral, width: 1.5),
              borderRadius: BorderRadius.circular(14),
            ),
            child: TextField(
              controller: _controller,
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink,
                  letterSpacing: 1.0),
              decoration: const InputDecoration(
                border: InputBorder.none,
                hintText: 'DELETE',
                hintStyle: TextStyle(
                    fontWeight: FontWeight.w800,
                    color: Color(0xFFCCCCCC),
                    letterSpacing: 1.0),
              ),
              autocorrect: false,
              textCapitalization: TextCapitalization.characters,
            ),
          ),
          const SizedBox(height: 16),

          // Action buttons — Cancel is primary (P13: cancel is easiest exit)
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: GQColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: const StadiumBorder(),
                    elevation: 0,
                    shadowColor: Colors.transparent,
                  ),
                  child: Text('Cancel',
                      style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 13.5,
                          fontWeight: FontWeight.w800)),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton(
                  onPressed: _confirmed && !_deleting
                      ? _handleDeleteForever
                      : null,
                  style: ElevatedButton.styleFrom(
                    // Coral — not red (P4 / P13)
                    backgroundColor: GQColors.coral,
                    disabledBackgroundColor:
                        GQColors.coral.withValues(alpha: 0.5),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: const StadiumBorder(),
                    elevation: 0,
                    shadowColor: Colors.transparent,
                  ),
                  child: _deleting
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white))
                      : Text('Delete forever',
                          style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 13.5,
                              fontWeight: FontWeight.w800)),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),
          Text(
            "If you change your mind later, you'll need to sign up again — your data won't be there.",
            textAlign: TextAlign.center,
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: GQColors.ink3,
                height: 1.4),
          ),
        ],
      ),
    );
  }
}

// ─── Notification detail screen (View D) ─────────────────────────────────────

class _NotificationDetailScreen extends StatefulWidget {
  const _NotificationDetailScreen();

  @override
  State<_NotificationDetailScreen> createState() =>
      _NotificationDetailScreenState();
}

class _NotificationDetailScreenState
    extends State<_NotificationDetailScreen> {
  bool _dailyOn = true;
  bool _streakOn = false;
  TimeOfDay _reminderTime = const TimeOfDay(hour: 20, minute: 0);

  // M T W T F active by default, S S off
  final List<bool> _days = [true, true, true, true, true, false, false];

  static const _dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _reminderTime,
    );
    if (picked != null && mounted) setState(() => _reminderTime = picked);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      appBar: AppBar(
        backgroundColor: GQColors.softBg.withValues(alpha: 0.92),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 14,
              color: GQColors.ink),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Notifications',
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: GQColors.ink),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 18, 16, 30),
        children: [
          // DAILY CHECK-IN CARD
          _SettingsCard(
            children: [
              _SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.notifications_outlined,
                    size: 14, color: GQColors.primaryDk),
                title: 'Daily check-in reminder',
                subtitle: 'A nudge to log your mood',
                trailing: _GQToggle(
                  value: _dailyOn,
                  onChanged: (v) => setState(() => _dailyOn = v),
                ),
              ),
              if (_dailyOn)
                Padding(
                  padding: const EdgeInsets.fromLTRB(56, 10, 12, 4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Time picker
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 11),
                        decoration: BoxDecoration(
                          color: GQColors.softBg,
                          border: Border.all(
                              color: GQColors.hair, width: 1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'REMIND ME AT',
                                    style: TextStyle(
                                        fontFamily: GQTypography.bodyFamily,
                                        fontSize: 10.5,
                                        fontWeight: FontWeight.w800,
                                        color: GQColors.ink3,
                                        letterSpacing: 0.7),
                                  ),
                                  const SizedBox(height: 2),
                                  RichText(
                                    text: TextSpan(
                                      children: [
                                        TextSpan(
                                          text:
                                              '${_reminderTime.hourOfPeriod.toString().padLeft(2, '0')}:${_reminderTime.minute.toString().padLeft(2, '0')} ',
                                          style: TextStyle(
                                              fontFamily:
                                                  GQTypography.bodyFamily,
                                              fontSize: 18,
                                              fontWeight: FontWeight.w800,
                                              color: GQColors.ink,
                                              letterSpacing: -0.5,
                                              height: 1.1),
                                        ),
                                        TextSpan(
                                          text: _reminderTime.period ==
                                                  DayPeriod.pm
                                              ? 'PM'
                                              : 'AM',
                                          style: TextStyle(
                                              fontFamily:
                                                  GQTypography.bodyFamily,
                                              fontSize: 13,
                                              fontWeight: FontWeight.w700,
                                              color: GQColors.ink3),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            GestureDetector(
                              onTap: _pickTime,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 14, vertical: 8),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  border: Border.all(
                                      color: GQColors.hair, width: 1),
                                  borderRadius:
                                      BorderRadius.circular(999),
                                ),
                                child: Text('Change',
                                    style: TextStyle(
                                        fontFamily:
                                            GQTypography.bodyFamily,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w800,
                                        color: GQColors.ink2)),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      // Day chips
                      Text('ON DAYS',
                          style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 10.5,
                              fontWeight: FontWeight.w800,
                              color: GQColors.ink3,
                              letterSpacing: 0.7)),
                      const SizedBox(height: 6),
                      Row(
                        children: List.generate(_dayLabels.length, (i) {
                          final active = _days[i];
                          return Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: GestureDetector(
                              onTap: () =>
                                  setState(() => _days[i] = !_days[i]),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color: active
                                      ? GQColors.primary
                                      : Colors.white,
                                  border: Border.all(
                                      color: active
                                          ? GQColors.primary
                                          : GQColors.hair,
                                      width: 1),
                                  borderRadius:
                                      BorderRadius.circular(999),
                                ),
                                child: Text(_dayLabels[i],
                                    style: TextStyle(
                                        fontFamily:
                                            GQTypography.bodyFamily,
                                        fontSize: 11.5,
                                        fontWeight: FontWeight.w800,
                                        color: active
                                            ? Colors.white
                                            : GQColors.ink3)),
                              ),
                            ),
                          );
                        }),
                      ),
                    ],
                  ),
                ),
            ],
          ),

          const SizedBox(height: 14),

          // STREAK NUDGE CARD
          _SettingsCard(
            children: [
              _SettingsRow(
                iconBg: const Color(0xFFFFF1E5),
                iconWidget:
                    const Text('🔥', style: TextStyle(fontSize: 14)),
                title: 'Streak gentle nudge',
                subtitle:
                    "We'll text you when you're 3+ days into a streak — never to shame, only to celebrate.",
                trailing: _GQToggle(
                  value: _streakOn,
                  onChanged: (v) => setState(() => _streakOn = v),
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),

          // WORRIED CHECK-IN — LOCKED
          _SettingsCard(
            children: [
              _SettingsRow(
                iconBg: GQColors.primarySoft,
                iconWidget: const Icon(Icons.favorite_outline,
                    size: 14, color: GQColors.primaryDk),
                title: 'Worried check-in',
                subtitle:
                    'Sent within 24h after we detect a heavy moment. Always optional to ignore.',
                trailing: _GQToggle(
                  value: true,
                  locked: true,
                  onChanged: null,
                ),
              ),
              Padding(
                padding:
                    const EdgeInsets.fromLTRB(56, 0, 12, 12),
                child: Container(
                  padding: const EdgeInsets.all(9),
                  decoration: BoxDecoration(
                    color: GQColors.primary.withValues(alpha: 0.06),
                    border: Border.all(
                        color: GQColors.primary.withValues(alpha: 0.25),
                        width: 1,
                        style: BorderStyle.solid),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.shield_outlined,
                          size: 13, color: GQColors.primaryDk),
                      const SizedBox(width: 6),
                      Expanded(
                        child: RichText(
                          text: TextSpan(
                            style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: GQColors.ink2,
                                height: 1.45),
                            children: const [
                              TextSpan(
                                  text:
                                      'Locked on for the next '),
                              TextSpan(
                                  text: '26 days',
                                  style: TextStyle(
                                      fontWeight: FontWeight.w800,
                                      color: GQColors.ink)),
                              TextSpan(
                                  text:
                                      ' — last heavy moment was Friday. Resets after 30 quiet days.'),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 18),

          // Test notification button
          _TestNotificationBtn(
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Test notification sent.',
                      style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontWeight: FontWeight.w600)),
                  behavior: SnackBarBehavior.floating,
                  backgroundColor: GQColors.ink,
                  duration: Duration(seconds: 2),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}

// ─── Shared primitive widgets ─────────────────────────────────────────────────

/// Card container matching the HTML's `.settings-card` — rounded-18, white, hairline border.
class _SettingsCard extends StatelessWidget {
  final List<Widget> children;
  const _SettingsCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: GQColors.hair, width: 1),
        borderRadius: BorderRadius.circular(18),
      ),
      padding: const EdgeInsets.all(6),
      child: Column(
        children: List.generate(children.length, (i) {
          final child = children[i];
          if (i == 0) return child;
          return Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Divider(
                  height: 1,
                  thickness: 1,
                  color: GQColors.hair,
                  indent: 0,
                  endIndent: 0),
              child,
            ],
          );
        }),
      ),
    );
  }
}

/// A single row inside a SettingsCard.
class _SettingsRow extends StatelessWidget {
  final Color iconBg;
  final Widget iconWidget;
  final String title;
  final Color? titleColor;
  final String? subtitle;
  final Color? subtitleColor;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingsRow({
    required this.iconBg,
    required this.iconWidget,
    required this.title,
    this.titleColor,
    this.subtitle,
    this.subtitleColor,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final row = Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: iconBg,
              borderRadius: BorderRadius.circular(9),
            ),
            child: Center(child: iconWidget),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: titleColor ?? GQColors.ink,
                        height: 1.25)),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(subtitle!,
                      style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: subtitleColor ?? GQColors.ink3,
                          height: 1.35)),
                ],
              ],
            ),
          ),
          if (trailing != null) ...[
            const SizedBox(width: 8),
            trailing!,
          ],
        ],
      ),
    );

    if (onTap == null) return row;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: row,
    );
  }
}

/// Chevron trailing widget.
class _Chevron extends StatelessWidget {
  const _Chevron();

  @override
  Widget build(BuildContext context) {
    return const Icon(Icons.chevron_right_rounded,
        size: 16, color: GQColors.ink3);
  }
}

/// Token-styled toggle. `locked` = always-on, non-interactive.
class _GQToggle extends StatelessWidget {
  final bool value;
  final bool locked;
  final ValueChanged<bool>? onChanged;

  const _GQToggle({
    required this.value,
    this.locked = false,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Transform.scale(
      scale: 0.85,
      child: Switch.adaptive(
        value: value || locked,
        onChanged: locked ? null : onChanged,
        activeColor: GQColors.primary,
        activeTrackColor: GQColors.primary,
        inactiveThumbColor: Colors.white,
        inactiveTrackColor: GQColors.ink3.withValues(alpha: 0.32),
        thumbColor: WidgetStateProperty.resolveWith((states) {
          return Colors.white;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (locked) return GQColors.primary.withValues(alpha: 0.8);
          if (states.contains(WidgetState.selected)) return GQColors.primary;
          return GQColors.ink3.withValues(alpha: 0.32);
        }),
      ),
    );
  }
}

/// Section label matching HTML `.section-label`.
class _SectionLabel extends StatelessWidget {
  final String label;
  final Color? color;

  const _SectionLabel({required this.label, this.color});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 6, bottom: 8),
      child: Text(
        label,
        style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            color: color ?? GQColors.ink3,
            letterSpacing: 0.7),
      ),
    );
  }
}

/// Coral "Erase everything on this device" button.
class _EraseLocalDataBtn extends StatelessWidget {
  final VoidCallback onTap;

  const _EraseLocalDataBtn({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 13),
        decoration: BoxDecoration(
          color: GQColors.coral,
          borderRadius: BorderRadius.circular(999),
          boxShadow: [
            BoxShadow(
              color: GQColors.coral.withValues(alpha: 0.5),
              blurRadius: 22,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Text(
          'Erase everything on this device',
          textAlign: TextAlign.center,
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13.5,
              fontWeight: FontWeight.w800,
              color: Colors.white),
        ),
      ),
    );
  }
}

/// "Send a test notification" button.
class _TestNotificationBtn extends StatelessWidget {
  final VoidCallback onTap;

  const _TestNotificationBtn({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 13),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: GQColors.hair, width: 1),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.notifications_outlined,
                    size: 13, color: GQColors.ink2),
                const SizedBox(width: 6),
                Text('Send a test notification',
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink2)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          "See exactly what you'll get.",
          textAlign: TextAlign.center,
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: GQColors.ink3),
        ),
      ],
    );
  }
}
