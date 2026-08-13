import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../providers/chat_provider.dart';
import '../models/message.dart';
import '../theme/theme_helper.dart';
import '../theme/text_style_helper.dart';
import '../widgets/status_avatar.dart';
import '../config/profile_config.dart';
import '../core/utils/size_utils.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/keyboard_dismissible_scaffold.dart';
import '../widgets/safety_legal_sheet.dart';
import '../widgets/crisis_resources.dart';
import '../models/interactive_exercise.dart';
import '../services/firebase_service.dart';
import '../widgets/exercises/grounding_exercise_widget.dart';
import '../widgets/exercises/journal_prompt_card.dart';
import '../widgets/message_bubble.dart';
import '../theme/gq_tokens.dart';
import '../widgets/profile_nav_sheet.dart';
import '../widgets/ai_thinking_indicator.dart';
import '../widgets/inline_crisis_banner.dart';
import '../widgets/exercise_card_inline.dart';
import '../widgets/sean_ellis_survey_sheet.dart';
import '../providers/survey_provider.dart';
import '../widgets/voice_input_bar.dart';
// import '../widgets/web_mobile_promo_sheet.dart'; // Re-enable in redesign
import '../widgets/web_mobile_banner.dart';
// R1D12 — Offline States
import '../widgets/offline_banner.dart';
// Stage 1 — Companion creature (replaces the old R1D6 CompanionHeader).
import '../widgets/companion_widget.dart';
import 'chat/chat_widgets.dart';
// v1.5.0 ADHD Update — Body-doubling MVP (Workstream 2a)
import '../models/body_double_session.dart';
import '../widgets/body_double/body_double_start_sheet.dart';
import '../widgets/body_double/body_double_timer_bar.dart';

// No re-exports: every symbol extracted to chat/chat_widgets.dart was
// private pre-split, so no external consumer can depend on them.

/// v1.5.0 ADHD Update — active body-doubling session state.
///
/// Tick-based, not wall-clock-based: [remaining] is decremented by exactly
/// one second per `Timer.periodic` tick in `_InteractiveChatScreenState`.
/// Deliberately avoids `DateTime.now().difference(startedAt)` — a
/// backgrounded app losing ticks for a few seconds is an acceptable MVP
/// trade-off, and tick-counting keeps the countdown deterministic under
/// widget-test fake-async pumps (which fake `Timer`, not `DateTime.now()`).
class _BodyDoubleSession {
  _BodyDoubleSession({required this.task, required this.total});

  final String task;
  final Duration total;

  /// Set once the halfway check-in has fired, so it never re-fires.
  bool midpointFired = false;
}

class InteractiveChatScreen extends StatefulWidget {
  final bool showBottomNav;
  final ValueNotifier<int>? reselect;
  const InteractiveChatScreen(
      {super.key, this.showBottomNav = true, this.reselect});

  @override
  State<InteractiveChatScreen> createState() => _InteractiveChatScreenState();
}

class _InteractiveChatScreenState extends State<InteractiveChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _inputFocus = FocusNode();
  double _lastBottomInset = 0.0;
  final GlobalKey _inputBarKey = GlobalKey();
  double _inputBarHeight = 0.0;

  // ── R1D7 Chat Active States ──────────────────────────────────────────────
  /// State B — inline crisis banner visible in chat stream.
  ///
  /// Activation contract: when a user message arrives with riskLevel >= high
  /// (high or crisis — set by the on-device CrisisKeywordDetector in
  /// ChatProvider.sendMessage, OR by the backend's risk_level on the AI
  /// reply), we surface the banner and keep it visible for the entire turn
  /// (user message + subsequent AI reply). The banner is sticky: it does NOT
  /// dismiss when the AI reply lands with riskLevel.none — a backend
  /// misclassification must not hide the safety surface mid-turn. The banner
  /// dismisses only when:
  ///   (a) the user taps "I'm okay" / "Help me find someone" — records the
  ///       triggering user message id in [_crisisBannerDismissedForMessageId]
  ///       so it stays dismissed until a NEW user message with elevated risk
  ///       lands, OR
  ///   (b) a new user message with riskLevel.none is sent — clears the
  ///       sticky turn state so the banner doesn't leak across turns.
  ///
  /// [_crisisTriggerUserMessageId] tracks the user message id that armed the
  /// banner this turn. Set when a user message with elevated risk is
  /// detected; cleared when a subsequent user message with no risk lands.
  /// This is distinct from [_crisisBannerDismissedForMessageId] which records
  /// a user-dismissal for sticky-dismissal semantics.
  bool _showInlineCrisis = false;
  String? _crisisBannerDismissedForMessageId;
  String? _crisisTriggerUserMessageId;
  /// State D — voice input mode active.
  bool _voiceInputActive = false;
  String _voiceTranscript = '';

  // ── R1D12 Offline States ─────────────────────────────────────────────────
  /// True when device has no network connectivity (mid-chat offline).
  bool _isOffline = false;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;

  // ── v1.5.0 ADHD Update — Body-doubling MVP (Workstream 2a) ──────────────
  /// Non-null while a focus session is running. One session at a time —
  /// stacking/queuing multiple sessions is out of scope for the MVP.
  _BodyDoubleSession? _bdSession;
  Timer? _bdTicker;
  Duration _bdRemaining = Duration.zero;

  // Guards 'intervention_accepted' so it fires once per discrete exercise
  // card, not on every rebuild of the message list (was firing on every
  // list-item rebuild — 329 events, top-4 by volume, all noise).
  final Set<String> _acceptedInterventionIds = {};

  // One-time legal acknowledgment key
  static const _prefsLegalAckV1 = 'legal_ack_v1';
  // Global in-flight guard to prevent duplicate Safety & Legal sheet
  static bool _legalSheetShowing = false;
  // (Removed) Chat disclaimer cadence — replaced by ChatGPT-style footer
  // chip that's always visible below the input bar. The old
  // chat_disclaimer_seen_count_v1 SharedPreferences key is left alone so
  // users who already saw the old banner aren't affected on upgrade.

  Future<void> _ensureLegalAck() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final ack = prefs.getBool(_prefsLegalAckV1) ?? false;
      if (!ack && mounted && !kDebugMode) {
        // Prevent double invocation from concurrent mounts/renders
        if (_legalSheetShowing) return;
        _legalSheetShowing = true;
        // Save flag BEFORE showing sheet — prevents re-show if widget is
        // recreated (tab switch) before the post-sheet setBool completes.
        await prefs.setBool(_prefsLegalAckV1, true);
        try {
          await showSafetyLegalSheet(context, requireAcknowledge: true);
        } finally {
          _legalSheetShowing = false;
        }
      }
    } catch (e) {
      if (kDebugMode) debugPrint('Safety & Legal ack check failed: $e');
    }
  }

  void _onReselect() {
    // On re-tap, bring the latest messages into view
    _scrollToBottom();
  }

  Future<void> _showAllCrisisResourcesSheet(
      List<Map<String, dynamic>> numbers) async {
    if (numbers.isEmpty) return;
    FirebaseService().logCrisisResourceAccess();
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      backgroundColor: appTheme.whiteCustom,
      builder: (ctx) {
        return SafeArea(
          top: false,
          child: Padding(
            padding:
                EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: EdgeInsets.fromLTRB(16.h, 12.h, 16.h, 4.h),
                  child: Text(
                    'Crisis resources',
                    style: TextStyleHelper.instance.headline24Bold,
                  ),
                ),
                Flexible(
                  child: ListView.separated(
                    shrinkWrap: true,
                    padding: EdgeInsets.fromLTRB(8.h, 8.h, 8.h, 8.h),
                    itemCount: numbers.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (ctx, i) {
                      final n = numbers[i];
                      final name = (n['name'] ?? '').toString();
                      final number =
                          ((n['number'] ?? n['phone']) ?? '').toString().trim();
                      final textInstr = (n['text'] ?? '').toString().trim();
                      return ListTile(
                        dense: false,
                        title: Text(name.isNotEmpty
                            ? name
                            : (number.isNotEmpty
                                ? number
                                : (textInstr.isNotEmpty
                                    ? textInstr
                                    : 'Resource'))),
                        subtitle: number.isNotEmpty
                            ? Text(number)
                            : (textInstr.isNotEmpty ? Text(textInstr) : null),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (number.isNotEmpty)
                              IconButton(
                                icon: const Icon(Icons.phone_forwarded_rounded),
                                tooltip: 'Call',
                                onPressed: () async {
                                  final uri = Uri(scheme: 'tel', path: number);
                                  if (await canLaunchUrl(uri)) {
                                    await launchUrl(uri,
                                        mode: LaunchMode.externalApplication);
                                  } else {
                                    await Clipboard.setData(
                                        ClipboardData(text: number));
                                    if (mounted) {
                                      ScaffoldMessenger.of(context)
                                          .showSnackBar(
                                        const SnackBar(
                                            content: Text(
                                                'Call not supported. Number copied to clipboard.')),
                                      );
                                    }
                                  }
                                },
                              ),
                            if (textInstr.isNotEmpty)
                              IconButton(
                                icon: const Icon(Icons.sms_rounded),
                                tooltip: 'Text',
                                onPressed: () async {
                                  // Parse patterns like "HOME to 741741" (optionally prefixed by 'Text ')
                                  String s = textInstr.trim();
                                  if (s.toLowerCase().startsWith('text ')) {
                                    s = s.substring(5).trim();
                                  }
                                  final reg = RegExp(r'^(.+?)\s+to\s+(\d+)$',
                                      caseSensitive: false);
                                  final m = reg.firstMatch(s);
                                  if (m != null) {
                                    final body = m.group(1)!.trim();
                                    final to = m.group(2)!.trim();
                                    final uri = Uri(
                                      scheme: 'sms',
                                      path: to,
                                      queryParameters: {'body': body},
                                    );
                                    if (await canLaunchUrl(uri)) {
                                      await launchUrl(uri,
                                          mode: LaunchMode.externalApplication);
                                    } else {
                                      await Clipboard.setData(
                                          ClipboardData(text: textInstr));
                                      if (mounted) {
                                        ScaffoldMessenger.of(context)
                                            .showSnackBar(
                                          const SnackBar(
                                              content: Text(
                                                  'SMS not supported. Instructions copied to clipboard.')),
                                        );
                                      }
                                    }
                                  } else {
                                    // Copy button for non-SMS patterns
                                    final toCopy = number.isNotEmpty
                                        ? number
                                        : (textInstr.isNotEmpty
                                            ? textInstr
                                            : name);
                                    if (toCopy.trim().isNotEmpty) {
                                      await Clipboard.setData(
                                          ClipboardData(text: toCopy.trim()));
                                      if (mounted) {
                                        ScaffoldMessenger.of(context)
                                            .showSnackBar(
                                          const SnackBar(
                                              content:
                                                  Text('Copied to clipboard.')),
                                        );
                                      }
                                    }
                                  }
                                },
                              ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
                SizedBox(height: 12.h),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _showHelpSheet() async {
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      builder: (ctx) {
        final theme = Theme.of(ctx);
        return SafeArea(
          top: false,
          child: Padding(
            padding: EdgeInsets.only(
              left: 16.0,
              right: 16.0,
              bottom: MediaQuery.of(ctx).viewInsets.bottom + 16.0,
              top: 12.0,
            ),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Need help now?',
                          style: theme.textTheme.headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                      ),
                      IconButton(
                        tooltip: 'Close',
                        onPressed: () => Navigator.of(ctx).maybePop(),
                        icon: const Icon(Icons.close),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'If you are in immediate danger, call your local emergency number.',
                    style: theme.textTheme.bodySmall
                        ?.copyWith(color: GQColors.ink2),
                  ),
                  const SizedBox(height: 12),
                  const CrisisResourcesWidget(riskLevel: RiskLevel.high),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      onPressed: () async {
                        Navigator.of(ctx).maybePop();
                        await showSafetyLegalSheet(context);
                      },
                      icon: const Icon(Icons.shield_outlined),
                      label: const Text('Safety & Legal'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  void initState() {
    super.initState();
    // Initialize with some sample messages if empty
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      if (chatProvider.messages.isEmpty) {
        _addSampleMessages(chatProvider);
      }
      // Ensure we start at the latest message
      _scrollToBottom();
      // One-time Safety & Legal acknowledgment — deferred to redesign.
      // Currently too much friction (2 popups before first chat).
      // TODO: Re-enable as a single inline disclosure in the onboarding redesign.
      // _ensureLegalAck();
      // On web only: offer the mobile app once per device. Non-blocking.
      // TODO: Re-enable as a subtle banner, not a blocking popup, in redesign.
      // WebMobilePromoSheet.maybeShow(context);
    });
    _inputFocus.addListener(() {
      if (!mounted) return;
      setState(() {});
    });
    // Listen for tab reselect events
    widget.reselect?.addListener(_onReselect);
    // R1D12 — Offline States: subscribe to connectivity changes.
    // Auto-dismisses OfflineBanner on reconnect (no manual action required).
    _connectivitySub =
        Connectivity().onConnectivityChanged.listen(_onConnectivityChanged);
    // Kick an immediate check so we detect pre-existing offline state.
    Connectivity().checkConnectivity().then(_onConnectivityChanged);
  }

  void _onConnectivityChanged(List<ConnectivityResult> results) {
    if (!mounted) return;
    final nowOffline = results.every((r) => r == ConnectivityResult.none);
    if (nowOffline != _isOffline) {
      setState(() => _isOffline = nowOffline);
    }
  }

  @override
  void didUpdateWidget(covariant InteractiveChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.reselect != widget.reselect) {
      oldWidget.reselect?.removeListener(_onReselect);
      widget.reselect?.addListener(_onReselect);
    }
  }

  void _addSampleMessages(ChatProvider chatProvider) {
    // The ChatProvider already loads initial greeting message
    // No need to add sample messages as the provider handles this
  }

  void _sendMessage() async {
    if (_messageController.text.trim().isEmpty) return;

    HapticFeedback.mediumImpact();

    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    final messageText = _messageController.text.trim();
    _messageController.clear();
    // Keep the input focused (especially on iOS) after sending
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _inputFocus.requestFocus();
    });
    // Fire-and-forget send. Provider will immediately add the user message and set typing.
    // Scroll now to reveal the just-added message, and handle errors non-blockingly.
    _scrollToBottom();
    chatProvider.sendMessage(messageText).then((_) {
      // After the AI reply lands, increment the chat-session counter and
      // check whether the Sean-Ellis PMF survey should be shown. The sheet
      // is non-blocking and only fires once per user (SharedPreferences gate
      // inside SurveyProvider).
      _maybeShowSeanEllisSurvey();
    }).catchError((e) {
      debugPrint('sendMessage error: $e');
    });
  }

  /// Increment the chat-session counter via [SurveyProvider] and, if the
  /// user has now crossed the 3-session threshold and hasn't seen the
  /// survey yet, present the Sean-Ellis bottom sheet. Non-blocking.
  void _maybeShowSeanEllisSurvey() {
    final surveyProvider = context.read<SurveyProvider>();
    surveyProvider.incrementSessionCount().then((_) {
      if (!mounted) return;
      if (!surveyProvider.shouldShowSurvey()) return;
      // Defer to the next frame so the chat UI settles before the sheet
      // slides up — keeps the survey non-blocking w.r.t. the reply render.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        if (!surveyProvider.shouldShowSurvey()) return;
        showSeanEllisSurveySheet(context);
      });
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      final bottomInset = MediaQuery.viewInsetsOf(context).bottom;
      final target = _scrollController.position.maxScrollExtent;
      if (bottomInset > 0) {
        // When keyboard is open, jump to avoid animation lag
        _scrollController.jumpTo(target);
      } else {
        _scrollController.animateTo(
          target,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;
    if (bottomInset != _lastBottomInset) {
      _lastBottomInset = bottomInset;
      // When keyboard shows/hides, keep view pinned to bottom
      WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
    }
    // Measure input bar height post-frame and update padding accordingly
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final ctx = _inputBarKey.currentContext;
      if (ctx != null) {
        final newH = ctx.size?.height ?? 0.0;
        if (newH != _inputBarHeight && mounted) {
          setState(() => _inputBarHeight = newH);
        }
      }
    });
    return KeyboardDismissibleScaffold(
      safeTop: false,
      safeBottom: false,
      bottomNavigationBar: widget.showBottomNav
          ? const AppBottomNav(current: AppTab.talk)
          : null,
      body: PopScope(
        canPop: !_inputFocus.hasFocus,
        onPopInvokedWithResult: (didPop, result) {
          if (!didPop && _inputFocus.hasFocus) {
            // First back press: dismiss keyboard instead of popping
            _inputFocus.unfocus();
          }
        },
        child: Stack(
          children: [
            // Plain themed background
            Container(
              color: Theme.of(context).scaffoldBackgroundColor,
            ),
            // Main Content
            Column(
              children: [
                // Header
                Container(
                  color: appTheme.whiteCustom,
                  padding:
                      EdgeInsets.symmetric(horizontal: 16.h, vertical: 16.h),
                  child: SafeArea(
                    top: true,
                    bottom: false,
                    child: Row(
                      children: [
                        Builder(
                          builder: (ctx) {
                            final route = ModalRoute.of(ctx);
                            final isModal = route is PageRoute &&
                                route.fullscreenDialog == true;
                            // Show back button only when keyboard is open; keep layout stable otherwise
                            return KeyboardAwareBackButton(
                                isModal: isModal, size: 44.h);
                          },
                        ),
                        Expanded(
                          child: Text(
                            ProfileConfig.aiName,
                            textAlign: TextAlign.center,
                            style: TextStyleHelper.instance.headline24Bold,
                          ),
                        ),
                        // v1.5.0 ADHD Update — body-doubling entry point.
                        // Icon swaps to filled + coral while a session is
                        // active as a lightweight "still running" signal.
                        Semantics(
                          label: _bdSession != null
                              ? 'Focus session running'
                              : 'Start focus session',
                          button: true,
                          child: InkWell(
                            key: const Key('body_double_entry_button'),
                            borderRadius: BorderRadius.circular(22),
                            onTap: _startBodyDoubleFlow,
                            child: Padding(
                              padding: const EdgeInsets.all(8),
                              child: Icon(
                                _bdSession != null
                                    ? Icons.timer
                                    : Icons.timer_outlined,
                                color: _bdSession != null
                                    ? GQColors.coral
                                    : GQColors.primary,
                                size: 28,
                              ),
                            ),
                          ),
                        ),
                        // Profile / nav sheet entry point (Tier 2.1)
                        Semantics(
                          label: 'Open navigation menu',
                          button: true,
                          child: InkWell(
                            borderRadius: BorderRadius.circular(22),
                            onTap: () => showProfileNavSheet(context),
                            child: Padding(
                              padding: const EdgeInsets.all(8),
                              child: Icon(
                                Icons.account_circle_outlined,
                                color: GQColors.primary,
                                size: 28,
                              ),
                            ),
                          ),
                        ),
                        // Overflow menu for Safety & Legal access
                        PopupMenuButton<String>(
                          tooltip: 'More',
                          onSelected: (value) async {
                            switch (value) {
                              case 'help':
                                await _showHelpSheet();
                                break;
                              case 'safety':
                                await showSafetyLegalSheet(context);
                                break;
                            }
                          },
                          itemBuilder: (context) => [
                            const PopupMenuItem<String>(
                              value: 'help',
                              child: Text('Help'),
                            ),
                            const PopupMenuItem<String>(
                              value: 'safety',
                              child: Text('Safety & Legal'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                // Divider
                Container(
                  height: 8.h,
                  color: appTheme.colorFFF3F4,
                ),
                // Web-to-phone promo — non-blocking dismissible banner (web
                // only). Replaces the old WebMobilePromoSheet.maybeShow popup.
                if (kIsWeb) const WebMobileBanner(),
                // v1.5.0 ADHD Update — pinned outside the message list (not
                // scrolled with it) so the running timer is always visible
                // while chatting. Check-in text lives in the transcript
                // itself (see _startBodyDoubleSession et al.) — this bar is
                // just the persistent countdown + end-session affordance.
                if (_bdSession != null)
                  BodyDoubleTimerBar(
                    task: _bdSession!.task,
                    remaining: _bdRemaining,
                    total: _bdSession!.total,
                    onEndSession: _abandonBodyDouble,
                  ),
                // Disclaimer moved to a ChatGPT-style footer below the input
                // bar (see end of Column). Was an amber dismissible banner
                // above the greeting — created an "are you in danger?" framing
                // at the exact moment we're trying to build trust with the
                // user. Footer position keeps the compliance copy visible on
                // every screen without competing with first-touch warmth.
                // Chat Messages
                Expanded(
                  child: Consumer<ChatProvider>(
                    builder: (context, chatProvider, child) {
                      // Always keep view pinned to bottom on updates (new msgs/typing)
                      WidgetsBinding.instance
                          .addPostFrameCallback((_) => _scrollToBottom());

                      // R1D7 State B — inline crisis banner activation.
                      //
                      // Turn-sticky semantics (C1 fix): the banner arms the
                      // moment a USER message with riskLevel ∈ {high, crisis}
                      // is sent (set by CrisisKeywordDetector in
                      // ChatProvider.sendMessage) and stays visible through
                      // the subsequent AI reply, even if the backend returns
                      // riskLevel.none on the reply. This closes the window
                      // where a backend misclassification would hide the
                      // safety surface mid-turn.
                      //
                      // The banner also arms when the AI reply itself lands
                      // with elevated risk (backend-driven path — the
                      // original behavior).
                      //
                      // Dismissal paths:
                      //   (a) User taps "I'm okay" / "Help me find someone"
                      //       → records the triggering user msg id in
                      //       _crisisBannerDismissedForMessageId; banner stays
                      //       dismissed until a NEW user message with elevated
                      //       risk lands.
                      //   (b) A new USER message with riskLevel.none is sent
                      //       → clears the sticky turn state so the banner
                      //       doesn't leak across turns.
                      //
                      // Runs post-frame to avoid calling setState during build.
                      WidgetsBinding.instance.addPostFrameCallback((_) {
                        if (!mounted) return;
                        final msgs = chatProvider.messages;
                        if (msgs.isEmpty) return;
                        final last = msgs.last;

                        // A new user message resets the turn state unless it
                        // itself carries elevated risk.
                        if (last.isUser) {
                          final userElevated =
                              last.riskLevel == RiskLevel.high ||
                              last.riskLevel == RiskLevel.crisis;
                          if (userElevated) {
                            // New crisis turn — arm the trigger and dismiss
                            // any prior sticky-dismissal for a different msg.
                            _crisisTriggerUserMessageId = last.id;
                            // If the user dismissed a previous turn's banner,
                            // that dismissal doesn't apply to this new msg.
                            if (_crisisBannerDismissedForMessageId != last.id) {
                              _crisisBannerDismissedForMessageId = null;
                            }
                          } else {
                            // New non-crisis user message — end the turn.
                            _crisisTriggerUserMessageId = null;
                          }
                        }

                        // Banner is shown if either:
                        //   - the current turn was armed by a crisis user msg
                        //     (sticky through the AI reply), OR
                        //   - the last message (typically the AI reply) itself
                        //     carries elevated risk (backend-driven).
                        // Skip if the user dismissed the banner for THIS
                        // turn's triggering user msg.
                        final turnArmed =
                            _crisisTriggerUserMessageId != null;
                        final lastElevated =
                            last.riskLevel == RiskLevel.medium ||
                            last.riskLevel == RiskLevel.high ||
                            last.riskLevel == RiskLevel.crisis;
                        final dismissedForThisTurn =
                            _crisisTriggerUserMessageId != null &&
                            _crisisBannerDismissedForMessageId ==
                                _crisisTriggerUserMessageId;
                        final shouldShow =
                            (turnArmed || lastElevated) &&
                            !dismissedForThisTurn;
                        if (shouldShow != _showInlineCrisis) {
                          setState(() => _showInlineCrisis = shouldShow);
                        }
                      });

                      // Detect empty conversation: only greeting, no user messages
                      final hasUserMessages =
                          chatProvider.messages.any((m) => m.isUser);
                      final hideSuggestions = _inputFocus.hasFocus;
                      // Always show conversation starters for new users
                      // (chips builder handles which functional shortcuts to include)
                      final showSuggestions = !hasUserMessages &&
                          chatProvider.messages.length <= 1 &&
                          !chatProvider.isTyping &&
                          !hideSuggestions;

                      // Normal chat with optional suggestion chips after greeting
                      final msgCount = chatProvider.messages.length;
                      final hasTyping = chatProvider.isTyping;
                      // R1D7: inline crisis banner adds an extra row when active
                      // R1D12: offline banner adds an extra row when offline
                      // Items: messages + (suggestions?) + (crisis banner?) +
                      //        (offline banner?) + (typing?)
                      //
                      // Row indices are computed ONCE here and reused in both
                      // itemCount and the index dispatch below. Previously the
                      // offsets were re-derived per branch with duplicated
                      // (showSuggestions ? 1 : 0) chains — adding a row meant
                      // editing four places and risked drift between
                      // itemCount and the dispatch (crisis row would race
                      // with offline/typing rows). Single source of truth now.
                      final int suggestionsRowCount = showSuggestions ? 1 : 0;
                      final int crisisRowCount = _showInlineCrisis ? 1 : 0;
                      final int offlineRowCount = _isOffline ? 1 : 0;
                      final int typingRowCount = hasTyping ? 1 : 0;

                      final int suggestionsIndex = msgCount;
                      final int crisisIndex =
                          suggestionsIndex + suggestionsRowCount;
                      final int offlineIndex = crisisIndex + crisisRowCount;
                      final int typingIndex = offlineIndex + offlineRowCount;

                      final int count = msgCount +
                          suggestionsRowCount +
                          crisisRowCount +
                          offlineRowCount +
                          typingRowCount;

                      return ListView.builder(
                        controller: _scrollController,
                        padding: EdgeInsets.fromLTRB(
                            16.h, 16.h, 16.h, _inputBarHeight + 8.h),
                        keyboardDismissBehavior:
                            ScrollViewKeyboardDismissBehavior.manual,
                        itemCount: count,
                        itemBuilder: (context, index) {
                          // First-turn warmth block (R1D3)
                          if (showSuggestions && index == suggestionsIndex) {
                            return _buildFirstTurnWarmth();
                          }

                          // R1D7 State B — inline crisis banner after last user msg
                          if (_showInlineCrisis && index == crisisIndex) {
                            return Padding(
                              padding: EdgeInsets.symmetric(horizontal: 4.h),
                              child: _buildInlineCrisisBanner(),
                            );
                          }

                          // R1D12 State A — offline banner near compose area;
                          // auto-hides on reconnect.
                          if (_isOffline && index == offlineIndex) {
                            return Padding(
                              padding: EdgeInsets.symmetric(
                                  horizontal: 4.h, vertical: 4.h),
                              child: AnimatedOpacity(
                                opacity: _isOffline ? 1.0 : 0.0,
                                duration: GQDurations.fade,
                                child: const OfflineBanner(),
                              ),
                            );
                          }

                          // R1D7 State A — thinking indicator
                          if (hasTyping && index == typingIndex) {
                            return _buildTypingBubble();
                          }

                          // Normal message
                          if (index >= msgCount) return const SizedBox.shrink();
                          final message = chatProvider.messages[index];
                          final isLast = index == msgCount - 1 && !hasTyping;
                          return _buildMessageBubble(message, isLast: isLast);
                        },
                      );
                    },
                  ),
                ),
                // Input Area — R1D7: supports 4 active states:
                //   A (thinking)  → input dimmed (opacity 0.55), hint "Alex is thinking…"
                //   B (crisis)    → standard input (banner shown in stream above)
                //   C (exercise)  → input dimmed, hint "Take your time…"
                //   D (voice)     → VoiceInputBar replaces text input in-place
                Container(
                  key: _inputBarKey,
                  color: appTheme.whiteCustom,
                  child: SafeArea(
                    top: false,
                    bottom: true,
                    left: false,
                    right: false,
                    child: Consumer<ChatProvider>(
                      builder: (ctx, chatProvider, _) {
                        final isThinking = chatProvider.isTyping;

                        // State D — Voice input replaces text bar in-place
                        if (_voiceInputActive) {
                          return VoiceInputBar(
                            liveTranscript: _voiceTranscript,
                            onStop: (transcript) {
                              setState(() {
                                _voiceInputActive = false;
                                if (transcript.isNotEmpty) {
                                  _messageController.text = transcript;
                                  _messageController.selection =
                                      TextSelection.fromPosition(
                                    TextPosition(offset: transcript.length),
                                  );
                                }
                              });
                              // R1D7 Phase 1: surface the transcript in the
                              // text field for explicit user review before
                              // sending. Anxious users want a confirmation
                              // step — auto-send (ChatGPT Voice Mode style)
                              // is a Phase 3 conversational-mode behavior,
                              // not Phase 1. Restore focus so the keyboard
                              // raises immediately and the cursor lands at
                              // the end of the inserted transcript.
                              if (transcript.isNotEmpty) {
                                WidgetsBinding.instance.addPostFrameCallback(
                                    (_) => _inputFocus.requestFocus());
                              }
                            },
                            onCancel: () {
                              setState(() {
                                _voiceInputActive = false;
                                _voiceTranscript = '';
                              });
                            },
                            onUnsupported: _onVoiceUnsupported,
                          );
                        }

                        // States A/B/C — standard text input with dim for thinking/exercise
                        final dimInput = isThinking;
                        final hintText = isThinking
                            ? 'Alex is thinking…'
                            : 'Type your message...';

                        return Opacity(
                          opacity: dimInput ? 0.55 : 1.0,
                          child: Padding(
                            padding:
                                EdgeInsets.fromLTRB(16.h, 4.h, 0.h, 16.h),
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Row(
                                  children: [
                                    // R1D7 State D — mic button to activate voice mode
                                    _buildVoiceMicButton(),
                                    SizedBox(width: 8.h),
                                    Expanded(
                                      child: Container(
                                        decoration: BoxDecoration(
                                          color: appTheme.colorFFF3F4,
                                          borderRadius:
                                              BorderRadius.circular(24.h),
                                        ),
                                        child: TextField(
                                          controller: _messageController,
                                          focusNode: _inputFocus,
                                          enabled: !dimInput,
                                          decoration: InputDecoration(
                                            hintText: hintText,
                                            hintStyle: TextStyle(
                                              fontSize: 16.0,
                                              color: GQColors.ink3,
                                            ),
                                            border: InputBorder.none,
                                            contentPadding:
                                                EdgeInsets.symmetric(
                                              horizontal: 16.h,
                                              vertical: 10.h,
                                            ),
                                          ),
                                          style: const TextStyle(
                                            fontSize: 16.0,
                                            color: GQColors.ink,
                                          ),
                                          onSubmitted: (_) {
                                            _sendMessage();
                                            WidgetsBinding.instance
                                                .addPostFrameCallback((_) {
                                              if (mounted) {
                                                _inputFocus.requestFocus();
                                              }
                                            });
                                          },
                                          onEditingComplete: () {},
                                          textInputAction: TextInputAction.send,
                                          keyboardType: TextInputType.multiline,
                                          maxLines: null,
                                          minLines: 1,
                                        ),
                                      ),
                                    ),
                                    SizedBox(width: 8.h),
                                    SizedBox(
                                      width: 44.h,
                                      child: Center(
                                        child: GestureDetector(
                                          onTap:
                                              dimInput ? null : _sendMessage,
                                          child: Container(
                                            padding: EdgeInsets.all(10.h),
                                            decoration: BoxDecoration(
                                              color: dimInput
                                                  ? GQColors.primary
                                                      .withValues(alpha: 0.4)
                                                  : GQColors.primary,
                                              shape: BoxShape.circle,
                                            ),
                                            child: Icon(
                                              Icons.send_rounded,
                                              color: Colors.white,
                                              size: 20.h,
                                            ),
                                          ),
                                        ),
                                      ),
                                    ),
                                    SizedBox(width: 8.h),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
                // ChatGPT-style persistent footer disclaimer. Verbatim
                // compliance copy preserved; placement moved here so it's
                // always visible without competing with the first-touch
                // greeting. Hidden when keyboard is up to free vertical
                // space for typing.
                Builder(builder: (ctx) {
                  final isKb = MediaQuery.viewInsetsOf(ctx).bottom > 0;
                  if (isKb) return const SizedBox.shrink();
                  return Semantics(
                    label: 'Wellness disclaimer',
                    child: Container(
                      width: double.infinity,
                      color: appTheme.whiteCustom,
                      padding: EdgeInsets.fromLTRB(12.h, 0, 12.h, 6.h),
                      child: const Text(
                        // Verbatim compliance copy.
                        'Not medical care. For crisis, call local emergency.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 11.0,
                          color: GQColors.ink3,
                          height: 1.3,
                          fontWeight: FontWeight.w500,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  );
                }),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorBubble(Message message) {
    return Padding(
      padding: EdgeInsets.only(bottom: 16.h),
      child: MessageBubble(
        message: message,
        isError: true,
        onRetry: _retryLastFailedMessage,
      ),
    );
  }

  void _retryLastFailedMessage() {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    final msgs = chatProvider.messages;
    // Retry contract: only the user message IMMEDIATELY preceding the most
    // recent error bubble is eligible. We do not walk further back looking
    // for "any" prior user message — that would retry stale content the
    // user already moved past (e.g. user → ai-ok → user → ai-ok → user
    // → error: only the last user msg is the candidate). If the slot
    // before the error isn't a user message (e.g. two errors in a row, or
    // the error landed before any user input), we skip the retry entirely
    // rather than guess.
    String? errorId;
    String? retryText;
    int errorIndex = -1;
    for (int i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].type == MessageType.error) {
        errorId = msgs[i].id;
        errorIndex = i;
        break;
      }
    }
    if (errorIndex > 0) {
      final prev = msgs[errorIndex - 1];
      if (prev.isUser && prev.type != MessageType.error) {
        retryText = prev.content;
      }
    }
    if (errorId != null) chatProvider.removeMessage(errorId);
    if (retryText != null) chatProvider.sendMessage(retryText);
  }

  Widget _buildMessageBubble(Message message, {bool isLast = false}) {
    // Error bubble — inline alert with retry
    if (message.type == MessageType.error) {
      return _buildErrorBubble(message);
    }
    // Guard: Do not render empty assistant messages (prevents blank bubble on web)
    if (!message.isUser && message.content.trim().isEmpty) {
      if (kDebugMode) {
        debugPrint('[UI] Skipping empty assistant message bubble');
      }
      return const SizedBox.shrink();
    }
    final reduceMotion = MediaQuery.of(context).accessibleNavigation;
    return AnimatedSize(
      duration:
          reduceMotion ? Duration.zero : const Duration(milliseconds: 120),
      curve: Curves.easeOutCubic,
      alignment: Alignment.topCenter,
      child: Container(
        margin: EdgeInsets.only(bottom: isLast ? 4.h : 16.h),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment:
              message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
          children: [
            if (!message.isUser) ...[
              StatusAvatar(
                name: ProfileConfig.aiName,
                imageAsset: ProfileConfig.aiAvatarAsset,
                size: 52.h,
                status: PresenceStatus.none,
                showStatus: false,
              ),
              SizedBox(width: 12.h),
            ],
            Flexible(
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 16.h, vertical: 12.h),
                decoration: BoxDecoration(
                  color: message.isUser
                      ? GQColors.successSoft
                      : appTheme.whiteCustom,
                  borderRadius: BorderRadius.circular(16.h),
                  boxShadow: [
                    BoxShadow(
                      // standard ink-shadow alpha (agent ruling 2026-05-22 keep raw)
                      color: Colors.black.withValues(alpha: 0.1),
                      blurRadius: 4.h,
                      offset: Offset(0, 2.h),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    MarkdownBody(
                      data: message.content,
                      styleSheet: MarkdownStyleSheet(
                        p: TextStyle(
                          fontSize: 16.0,
                          fontWeight: FontWeight.w400,
                          color: appTheme.colorFF1F29,
                          height: 1.4,
                        ),
                        strong: TextStyle(
                          fontSize: 16.0,
                          fontWeight: FontWeight.bold,
                          color: appTheme.colorFF1F29,
                          height: 1.4,
                        ),
                      ),
                    ),
                    // Hidden: do not render internal crisis debug content in UI
                    if (!message.isUser &&
                        (message.crisisNumbers != null &&
                            message.crisisNumbers!.isNotEmpty)) ...[
                      SizedBox(height: 6.h),
                      Wrap(
                        spacing: 8.h,
                        runSpacing: 4.h,
                        children: [
                          for (final n in message.crisisNumbers!.take(3))
                            CrisisChip(
                              name: (n['name'] ?? '').toString(),
                              phone: ((n['number'] ?? n['phone']) ?? '')
                                  .toString(),
                              textInstr: (n['text'] ?? '').toString(),
                            ),
                          if (message.crisisNumbers!.length > 3)
                            Semantics(
                              button: true,
                              label: 'More crisis resources',
                              child: GestureDetector(
                                onTap: () => _showAllCrisisResourcesSheet(
                                    message.crisisNumbers!),
                                child: Container(
                                  padding: EdgeInsets.symmetric(
                                      horizontal: 10.h, vertical: 6.h),
                                  decoration: BoxDecoration(
                                    color: GQColors.primarySoft,
                                    borderRadius: BorderRadius.circular(999),
                                    border: Border.all(
                                        color: GQColors.hair),
                                  ),
                                  child: const Text(
                                    'More…',
                                    style: TextStyle(
                                        fontSize: 12.0,
                                        fontWeight: FontWeight.w600,
                                        color: GQColors.ink),
                                  ),
                                ),
                              ),
                            ),
                        ],
                      ),
                      SizedBox(height: 6.h),
                      Semantics(
                        label: 'Safety note',
                        child: Text(
                          'These resources are informational and not a substitute for professional care. If you\'re in immediate danger, call your local emergency number.',
                          style: TextStyle(
                            fontSize: 11.0,
                            color: GQColors.ink2,
                            height: 1.3,
                          ),
                        ),
                      ),
                    ],
                    if (message.exercise != null) ...[
                      const SizedBox(height: 12),
                      _buildExerciseWidget(message.exercise!),
                    ],
                  ],
                ),
              ),
            ),
            if (message.isUser) ...[
              SizedBox(width: 12.h),
              StatusAvatar(
                name: ProfileConfig.userName,
                imageAsset: ProfileConfig.userAvatarAsset,
                size: 52.h,
                status: PresenceStatus.none,
                showStatus: false,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildExerciseWidget(InteractiveExercise exercise) {
    if (kDebugMode) {
      debugPrint('Rendering exercise: ${exercise.type} - ${exercise.name}');
    }
    // Use exercise name as identifier for tracking
    final exerciseId =
        '${exercise.type.toString().split('.').last}_${exercise.name.hashCode}';

    // Track that user saw/accepted an intervention — guarded so it fires
    // once per discrete exercise card, not on every rebuild of this method
    // (this is a build-time helper, called on every message-list rebuild).
    if (_acceptedInterventionIds.add(exerciseId)) {
      FirebaseService().logEvent('intervention_accepted', {
        'exercise_type': exercise.type.toString().split('.').last,
      });
    }

    switch (exercise.type) {
      case ExerciseType.breathing:
        // R1D7 State C — use ExerciseCardInline for 4-7-8 breathing in chat stream.
        // ExerciseCardInline is the compact inline variant per P11.
        return ExerciseCardInline(
          key: ValueKey(exerciseId),
          totalRounds: 3,
          onDone: () {
            context.read<ChatProvider>().trackExerciseOutcome(
                  exerciseType: 'breathing',
                  outcome: 'completed',
                  interventionId: exerciseId,
                );
            if (kDebugMode) debugPrint('✓ Breathing exercise completed (inline)');
          },
        );
      case ExerciseType.grounding:
        return GroundingExerciseWidget(
          exercise: exercise as GroundingExercise,
          onComplete: () {
            // Track completion via chat provider
            context.read<ChatProvider>().trackExerciseOutcome(
                  exerciseType: 'grounding',
                  outcome: 'completed',
                  interventionId: exerciseId,
                );
            if (kDebugMode) debugPrint('✓ Grounding exercise completed');
          },
        );
      case ExerciseType.journalPrompt:
        return JournalPromptCard(
          exercise: exercise as JournalPrompt,
          onSave: (entry) {
            // Track journal save via chat provider
            context.read<ChatProvider>().trackExerciseOutcome(
                  exerciseType: 'journal',
                  outcome: 'completed',
                  interventionId: exerciseId,
                  feedback: entry.isNotEmpty ? 'Entry saved' : null,
                );
            if (kDebugMode) {
              debugPrint('✓ Journal entry saved: ${entry.length} chars');
            }
          },
        );
    }
  }

  // R1D3 — Chat first-turn warmth block.
  // Renders time-aware greeting, sub-line, and 3 contextual chips.
  // Disappears after the first user message (controlled by showSuggestions gate in ListView).
  Widget _buildFirstTurnWarmth() {
    final hour = DateTime.now().hour;

    // Time-of-day greeting prefix
    final String timeGreeting;
    if (hour >= 5 && hour < 12) {
      timeGreeting = 'Good morning';
    } else if (hour >= 12 && hour < 17) {
      timeGreeting = 'Good afternoon';
    } else {
      timeGreeting = 'Good evening';
    }

    // Name personalisation: ProfileConfig.userName defaults to 'You' when unset.
    // Treat 'You' as the unset sentinel — drop it from greeting to avoid "Good morning, You."
    final rawName = ProfileConfig.userName.trim();
    final knownName = rawName.isNotEmpty && rawName != 'You';
    final greeting = knownName ? '$timeGreeting, $rawName.' : '$timeGreeting.';

    // R1D6 — Named starter set (same 4 across all time-of-day buckets).
    // Reordered: leading with "Today's been heavy" presumed a heavy day for
    // a first-time user. Now leads with the most neutral option ("Just need
    // someone to listen") so the default isn't framing the user's mood.
    const List<String> starters = [
      'Just need someone to listen',
      'I want to vent a little',
      "Today's been heavy",
      'Quick win, please',
    ];

    return Padding(
      padding: EdgeInsets.only(top: 8.h, bottom: 20.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Stage 1 — Companion creature (replaces R1D6 CompanionHeader).
          const CompanionWidget(),
          SizedBox(height: 8.h),
          // Warmth zone background card
          Container(
            margin: EdgeInsets.symmetric(horizontal: 8.h),
            padding: EdgeInsets.symmetric(horizontal: 16.h, vertical: 14.h),
            decoration: BoxDecoration(
              color: GQColors.softBg,
              borderRadius: BorderRadius.circular(GQRadii.card),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // R1D6 — BreathingOrb: gentle 5.6 s pulse.
                Align(
                  alignment: Alignment.center,
                  child: BreathingOrb(),
                ),
                SizedBox(height: 12.h),
                Text(
                  greeting,
                  style: const TextStyle(
                    fontSize: 18.0,
                    fontWeight: FontWeight.w600,
                    color: GQColors.coral,
                  ),
                ),
                SizedBox(height: 4.h),
                Text(
                  'How are you arriving today? Pick one below or type your own.',
                  style: TextStyle(
                    fontSize: 14.0,
                    fontWeight: FontWeight.w400,
                    color: GQColors.ink3,
                  ),
                ),
                SizedBox(height: 12.h),
                // R1D6 — Privacy micro-line.
                Text(
                  'History stays on your phone. We don\'t sell, train, or share.',
                  style: TextStyle(
                    fontSize: 11.0,
                    fontWeight: FontWeight.w400,
                    color: GQColors.ink3,
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: 10.h),
          // Starter chips — auto-send on tap to reduce friction.
          // Was .take(3 * 2 - 1) which hid the 4th chip; now shows all 4.
          // Was fill-input-only (2 taps); now auto-sends (1 tap).
          // GA4 data: 6/8 users who passed compliance didn't chat — reducing
          // taps from 2 to 1 should recover a significant portion.
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: EdgeInsets.only(left: 8.h, right: 16.h),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: starters
                  .expand((prompt) => [
                        _buildChip(prompt, () {
                          _messageController.text = prompt;
                          _sendMessage();
                        }),
                        SizedBox(width: 8.h),
                      ])
                  .take(4 * 2 - 1)
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChip(String label, VoidCallback onTap) {
    return Material(
      color: GQColors.softBg,
      shape: StadiumBorder(
        side: BorderSide(
          color: GQColors.hair,
          width: 1.0,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        customBorder: const StadiumBorder(),
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 14.h, vertical: 8.h),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 13.0,
              fontWeight: FontWeight.w500,
              color: GQColors.ink3,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTypingBubble() {
    // R1D7 State A — AIThinkingIndicator: 3-dot wave pill in chat bubble position.
    // Input bar is dimmed (opacity 0.55) while isTyping is true (handled in build()).
    final reduceMotion = MediaQuery.of(context).accessibleNavigation;
    return AnimatedSize(
      duration:
          reduceMotion ? Duration.zero : const Duration(milliseconds: 120),
      curve: Curves.easeOutCubic,
      alignment: Alignment.topCenter,
      child: Container(
        margin: EdgeInsets.only(bottom: 16.h),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            StatusAvatar(
              name: ProfileConfig.aiName,
              imageAsset: ProfileConfig.aiAvatarAsset,
              size: 52.h,
              status: PresenceStatus.none,
              showStatus: false,
            ),
            SizedBox(width: 12.h),
            // AIThinkingIndicator — GQColors.primary dots, 800ms wave
            const AIThinkingIndicator(),
          ],
        ),
      ),
    );
  }

  /// Builds the R1D7 State B inline crisis banner for insertion in the
  /// message list. Renders above the next AI bubble; never blocks the
  /// conversation (P6: crisis never blocks).
  ///
  /// Dismissal (onImOkay / close-X) pins the dismissed message id so the
  /// post-frame reactivation hook in the `Consumer<ChatProvider>` builder
  /// doesn't immediately re-show the banner for the SAME high-risk message.
  /// The banner re-arms when a newer high-risk message arrives with a
  /// different id.
  Widget _buildInlineCrisisBanner() {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    final lastId = chatProvider.messages.isNotEmpty
        ? chatProvider.messages.last.id
        : null;
    void dismissForCurrentMessage() {
      setState(() {
        _showInlineCrisis = false;
        _crisisBannerDismissedForMessageId = lastId;
      });
    }

    return InlineCrisisBanner(
      onImOkay: dismissForCurrentMessage,
      onHelp: () {
        // Expand inline 988 sheet; does NOT navigate (per design spec)
        dismissForCurrentMessage();
        _showHelpSheet();
      },
    );
  }

  /// R1D7 voice input mic button — enters VoiceInputBar.
  ///
  /// Now backed by speech_to_text (Apple Speech on iOS, Google
  /// SpeechRecognizer on Android) with onDevice: true to honor the
  /// "your voice stays on this device" promise. VoiceInputBar's
  /// onUnsupported callback fires if the device/locale can't do on-device
  /// recognition, in which case we drop the user back to the text bar with
  /// a one-time "voice isn't supported here" SnackBar.
  ///
  /// Hidden on web — Web Speech API silently uses Google Cloud and would
  /// break the on-device privacy promise, so Phase 1 deliberately excludes
  /// web. Returning SizedBox.shrink() also collapses the leading SizedBox
  /// gap next to the text field so the input bar layout stays clean.
  Widget _buildVoiceMicButton() {
    if (kIsWeb) return const SizedBox.shrink();
    return Semantics(
      button: true,
      label: 'Start voice input',
      child: GestureDetector(
        onTap: () {
          HapticFeedback.lightImpact();
          setState(() {
            _voiceInputActive = true;
            _voiceTranscript = '';
          });
        },
        child: Container(
          width: 44,
          height: 44,
          decoration: const BoxDecoration(
            color: GQColors.primarySoft,
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.mic_rounded,
            color: GQColors.primary,
            size: 22,
          ),
        ),
      ),
    );
  }

  /// Handler for VoiceInputBar's onUnsupported callback. Bails out of voice
  /// mode and surfaces a single, honest SnackBar so the user understands why
  /// nothing happened. Avoids the "advertise broken feature" trap.
  void _onVoiceUnsupported() {
    if (!mounted) return;
    setState(() {
      _voiceInputActive = false;
      _voiceTranscript = '';
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text(
          "Voice input isn't supported on this device · please type",
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
        ),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 3),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GQRadii.card),
        ),
        backgroundColor: GQColors.ink2,
      ),
    );
  }

  // ── v1.5.0 ADHD Update — Body-doubling MVP (Workstream 2a) ──────────────
  //
  // Flow: header icon → showBodyDoubleStartSheet (task + duration) →
  // _startBodyDoubleSession fires `body_double_started` at the real action
  // site (here, not in build()) and inserts a start check-in into the real
  // chat transcript → a 1s Timer.periodic ticks _bdRemaining down →
  // _onBdTick fires the midpoint check-in once, then hands off to
  // _completeBodyDouble on natural completion. The pinned BodyDoubleTimerBar
  // lets the user end early via _abandonBodyDouble at any point — always a
  // kind, no-guilt message, never a "you failed" framing (P: no streaks, no
  // shame on abandon — see V1_5_0_ADHD_UPDATE_SCOPE.md Workstream 2a).

  Future<void> _startBodyDoubleFlow() async {
    if (_bdSession != null) {
      // One session at a time for the MVP — surface the existing session
      // instead of silently stacking a second timer.
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('A focus session is already running.')),
      );
      return;
    }
    final config = await showBodyDoubleStartSheet(context);
    if (config == null || !mounted) return; // sheet dismissed without starting
    _startBodyDoubleSession(config);
  }

  void _startBodyDoubleSession(BodyDoubleSessionConfig config) {
    // Real action site for the start event — fires once, right where the
    // user's Start tap actually resolves into a running session.
    FirebaseService().logEvent('body_double_started', {
      'duration_minutes': config.duration.inMinutes,
      'task_length': config.task.length,
    });
    Provider.of<ChatProvider>(context, listen: false).insertCompanionMessage(
      "I'm with you for the next ${config.duration.inMinutes} minutes on "
      "${config.task}. No pressure — start whenever you're ready, and "
      "I'll check in partway through. 🌱",
    );
    _bdTicker?.cancel();
    setState(() {
      _bdSession = _BodyDoubleSession(task: config.task, total: config.duration);
      _bdRemaining = config.duration;
    });
    _bdTicker = Timer.periodic(const Duration(seconds: 1), _onBdTick);
  }

  void _onBdTick(Timer timer) {
    final session = _bdSession;
    if (session == null) {
      timer.cancel();
      return;
    }
    final next = _bdRemaining - const Duration(seconds: 1);
    if (next <= Duration.zero) {
      _completeBodyDouble();
      return;
    }
    if (!session.midpointFired && next <= session.total ~/ 2) {
      session.midpointFired = true;
      Provider.of<ChatProvider>(context, listen: false).insertCompanionMessage(
        "Halfway there — still with me? A bit more on ${session.task} and "
        "we're done. You're doing fine.",
      );
    }
    if (mounted) setState(() => _bdRemaining = next);
  }

  void _completeBodyDouble() {
    final session = _bdSession;
    _bdTicker?.cancel();
    _bdTicker = null;
    if (session == null) return;
    FirebaseService().logEvent('body_double_completed', {
      'duration_minutes': session.total.inMinutes,
    });
    Provider.of<ChatProvider>(context, listen: false).insertCompanionMessage(
      "Time's up! However far you got on ${session.task}, that counts. "
      "Nice work sticking with me. 💜",
    );
    if (mounted) {
      setState(() {
        _bdSession = null;
        _bdRemaining = Duration.zero;
      });
    } else {
      _bdSession = null;
    }
  }

  /// Ends the session early. Never framed as failure — no streak break, no
  /// "you gave up" language. Fires `body_double_abandoned` with the elapsed
  /// time actually spent, then a kind close-out message in the transcript.
  void _abandonBodyDouble() {
    final session = _bdSession;
    _bdTicker?.cancel();
    _bdTicker = null;
    if (session == null) return;
    final elapsed = session.total - _bdRemaining;
    FirebaseService().logEvent('body_double_abandoned', {
      'planned_duration_minutes': session.total.inMinutes,
      'elapsed_seconds':
          elapsed.inSeconds.clamp(0, session.total.inSeconds),
    });
    Provider.of<ChatProvider>(context, listen: false).insertCompanionMessage(
      "No worries — we stopped early. ${session.task} will still be there "
      "whenever you're ready, and so will I.",
    );
    if (mounted) {
      setState(() {
        _bdSession = null;
        _bdRemaining = Duration.zero;
      });
    } else {
      _bdSession = null;
    }
  }

  @override
  void dispose() {
    widget.reselect?.removeListener(_onReselect);
    _connectivitySub?.cancel(); // R1D12 — Offline States
    _bdTicker?.cancel(); // v1.5.0 ADHD Update — body-doubling session timer
    _messageController.dispose();
    _scrollController.dispose();
    _inputFocus.dispose();
    super.dispose();
  }
}

