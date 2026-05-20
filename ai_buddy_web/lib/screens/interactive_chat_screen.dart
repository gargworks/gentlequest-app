import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'dart:math' as math;
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
import '../widgets/voice_input_bar.dart';
// R1D12 — Offline States
import '../widgets/offline_banner.dart';
// R1D6 — QuestsEngine for streak badge (read-only).
import '../quests/quests_engine.dart';

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
  bool _showInlineCrisis = false;
  /// State D — voice input mode active.
  bool _voiceInputActive = false;
  String _voiceTranscript = '';

  // ── R1D12 Offline States ─────────────────────────────────────────────────
  /// True when device has no network connectivity (mid-chat offline).
  bool _isOffline = false;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;

  // R1D6 — lazy QuestsEngine instance for streak badge (read-only, no side-effects).
  QuestsEngine? _questsEngineForStreak;

  // One-time legal acknowledgment key
  static const _prefsLegalAckV1 = 'legal_ack_v1';
  // Global in-flight guard to prevent duplicate Safety & Legal sheet
  static bool _legalSheetShowing = false;
  // Chat disclaimer cadence: show small top notice for first few sessions
  static const _prefsDisclaimerSeenCount = 'chat_disclaimer_seen_count_v1';
  static const _maxDisclaimerSessions = 3;
  int _disclaimerSeenCount = 0;
  bool _showTopDisclaimer = false;

  Future<void> _ensureLegalAck() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final ack = prefs.getBool(_prefsLegalAckV1) ?? false;
      if (!ack && mounted) {
        // Prevent double invocation from concurrent mounts/renders
        if (_legalSheetShowing) return;
        _legalSheetShowing = true;
        try {
          await showSafetyLegalSheet(context, requireAcknowledge: true);
        } finally {
          _legalSheetShowing = false;
        }
        await prefs.setBool(_prefsLegalAckV1, true);
      }
    } catch (e) {
      if (kDebugMode) debugPrint('Safety & Legal ack check failed: $e');
    }
  }

  Future<void> _loadDisclaimerPrefs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final seen = prefs.getInt(_prefsDisclaimerSeenCount) ?? 0;
      if (!mounted) return;
      setState(() {
        _disclaimerSeenCount = seen;
        _showTopDisclaimer = seen < _maxDisclaimerSessions;
      });
    } catch (e) {
      if (kDebugMode) debugPrint('Disclaimer prefs read failed: $e');
    }
  }

  Future<void> _dismissTopDisclaimer({bool increment = true}) async {
    if (mounted) {
      setState(() => _showTopDisclaimer = false);
    }
    if (!increment) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      final next = (_disclaimerSeenCount + 1).clamp(0, _maxDisclaimerSessions);
      await prefs.setInt(_prefsDisclaimerSeenCount, next);
      if (!mounted) return;
      setState(() => _disclaimerSeenCount = next);
    } catch (e) {
      if (kDebugMode) debugPrint('Disclaimer prefs write failed: $e');
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
                        ?.copyWith(color: Colors.black54),
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
    // R1D6 — init QuestsEngine for streak badge (best-effort; silent on failure).
    try {
      _questsEngineForStreak = QuestsEngine();
    } catch (_) {}
    // Initialize with some sample messages if empty
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      if (chatProvider.messages.isEmpty) {
        _addSampleMessages(chatProvider);
      }
      // Ensure we start at the latest message
      _scrollToBottom();
      // One-time Safety & Legal acknowledgment
      _ensureLegalAck();
      // Load disclaimer cadence and decide whether to show top notice
      _loadDisclaimerPrefs();
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
    chatProvider.sendMessage(messageText).catchError((e) {
      debugPrint('sendMessage error: $e');
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
                // Ephemeral top disclaimer (first few sessions only)
                Builder(builder: (ctx) {
                  final isKb = MediaQuery.viewInsetsOf(ctx).bottom > 0;
                  if (!_showTopDisclaimer || isKb) {
                    return const SizedBox.shrink();
                  }
                  return Semantics(
                    label: 'Wellness disclaimer',
                    child: Container(
                      width: double.infinity,
                      color: Colors.amber.shade50,
                      padding: EdgeInsets.fromLTRB(12.h, 8.h, 4.h, 8.h),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          const Icon(Icons.info_outline,
                              size: 18.0, color: Colors.black54),
                          SizedBox(width: 8.h),
                          Expanded(
                            child: Text.rich(
                              TextSpan(
                                style: const TextStyle(
                                    fontSize: 12.0,
                                    color: Colors.black87,
                                    height: 1.2),
                                children: const [
                                  TextSpan(
                                      text:
                                          'Not medical care. For crisis, call local emergency.'),
                                ],
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          IconButton(
                            tooltip: 'Dismiss',
                            icon: const Icon(Icons.close, size: 18),
                            onPressed: () =>
                                _dismissTopDisclaimer(increment: true),
                          ),
                        ],
                      ),
                    ),
                  );
                }),
                // Chat Messages
                Expanded(
                  child: Consumer<ChatProvider>(
                    builder: (context, chatProvider, child) {
                      // Always keep view pinned to bottom on updates (new msgs/typing)
                      WidgetsBinding.instance
                          .addPostFrameCallback((_) => _scrollToBottom());

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
                      final extraRows = (showSuggestions ? 1 : 0) +
                          (_showInlineCrisis ? 1 : 0) +
                          (_isOffline ? 1 : 0) +
                          (hasTyping ? 1 : 0);
                      final count = msgCount + extraRows;

                      return ListView.builder(
                        controller: _scrollController,
                        padding: EdgeInsets.fromLTRB(
                            16.h, 16.h, 16.h, _inputBarHeight + 8.h),
                        keyboardDismissBehavior:
                            ScrollViewKeyboardDismissBehavior.manual,
                        itemCount: count,
                        itemBuilder: (context, index) {
                          int virtualIndex = index;

                          // First-turn warmth block (R1D3)
                          if (showSuggestions && virtualIndex == msgCount) {
                            return _buildFirstTurnWarmth();
                          }
                          if (showSuggestions && virtualIndex > msgCount) {
                            virtualIndex--; // shift past suggestions row
                          }

                          // R1D7 State B — inline crisis banner after last user msg
                          final crisisIndex =
                              msgCount + (showSuggestions ? 1 : 0);
                          if (_showInlineCrisis && index == crisisIndex) {
                            return Padding(
                              padding: EdgeInsets.symmetric(horizontal: 4.h),
                              child: _buildInlineCrisisBanner(),
                            );
                          }

                          // R1D12 State A — offline banner at top of stream
                          // Shown after suggestions/crisis rows so it sits near
                          // the compose area; auto-hides on reconnect.
                          final offlineIndex = msgCount +
                              (showSuggestions ? 1 : 0) +
                              (_showInlineCrisis ? 1 : 0);
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
                          final typingIndex = msgCount +
                              (showSuggestions ? 1 : 0) +
                              (_showInlineCrisis ? 1 : 0) +
                              (_isOffline ? 1 : 0);
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
                                }
                              });
                              if (transcript.isNotEmpty) {
                                _sendMessage();
                              }
                            },
                            onCancel: () {
                              setState(() {
                                _voiceInputActive = false;
                                _voiceTranscript = '';
                              });
                            },
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
                                              color: Colors.grey[600],
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
                                            color: Colors.black87,
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
    // Walk backwards: find the last error bubble, then the user message before it
    String? errorId;
    String? retryText;
    for (int i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].type == MessageType.error && errorId == null) {
        errorId = msgs[i].id;
      } else if (errorId != null && msgs[i].isUser) {
        retryText = msgs[i].content;
        break;
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
                      ? Colors.green.shade100
                      : appTheme.whiteCustom,
                  borderRadius: BorderRadius.circular(16.h),
                  boxShadow: [
                    BoxShadow(
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
                            _CrisisChip(
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
                                    color: Colors.blueGrey.shade50,
                                    borderRadius: BorderRadius.circular(999),
                                    border: Border.all(
                                        color: Colors.blueGrey.shade200),
                                  ),
                                  child: const Text(
                                    'More…',
                                    style: TextStyle(
                                        fontSize: 12.0,
                                        fontWeight: FontWeight.w600,
                                        color: Colors.black87),
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
                            color: Colors.black54,
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

    // Track that user saw/accepted an intervention
    FirebaseService().logEvent('intervention_accepted', {
      'exercise_type': exercise.type.toString().split('.').last,
    });

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
          // R1D6 — CompanionHeader with optional streak badge.
          _buildCompanionHeader(),
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
                  child: _BreathingOrb(),
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
                  'How are you arriving today?',
                  style: TextStyle(
                    fontSize: 14.0,
                    fontWeight: FontWeight.w400,
                    color: Colors.grey.shade600,
                  ),
                ),
                SizedBox(height: 12.h),
                // R1D6 — Privacy micro-line.
                Text(
                  'History stays on your phone. We don\'t sell, train, or share.',
                  style: TextStyle(
                    fontSize: 11.0,
                    fontWeight: FontWeight.w400,
                    color: Colors.grey.shade400,
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: 10.h),
          // R1D6 — 3 named starter chips (fill input, no auto-send).
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: EdgeInsets.only(left: 8.h, right: 16.h),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: starters
                  .take(3)
                  .expand((prompt) => [
                        _buildChip(prompt, () {
                          // R1D6 — Fill input only; user taps send explicitly (no auto-send).
                          _messageController.text = prompt;
                          _messageController.selection = TextSelection.fromPosition(
                            TextPosition(offset: prompt.length),
                          );
                          FocusScope.of(context).requestFocus(_inputFocus);
                        }),
                        SizedBox(width: 8.h),
                      ])
                  .take(3 * 2 - 1)
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  /// R1D6 — CompanionHeader: app name + recognition-only streak badge (≥2 days).
  Widget _buildCompanionHeader() {
    int streakDays = 0;
    try {
      streakDays = _questsEngineForStreak?.computeDailyStreak() ?? 0;
    } catch (_) {}
    final showStreak = streakDays >= 2;
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 16.h),
      child: Row(
        children: [
          Text(
            'GentleQuest',
            style: const TextStyle(
              fontSize: 15.0,
              fontWeight: FontWeight.w600,
              color: GQColors.coral,
              letterSpacing: 0.2,
            ),
          ),
          if (showStreak) ...[
            SizedBox(width: 8.h),
            Container(
              padding: EdgeInsets.symmetric(horizontal: 8.h, vertical: 3.h),
              decoration: BoxDecoration(
                color: GQColors.accentSoft,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('🌱', style: TextStyle(fontSize: 11)),
                  SizedBox(width: 4.h),
                  Text(
                    '$streakDays days',
                    style: const TextStyle(
                      fontSize: 11.0,
                      fontWeight: FontWeight.w500,
                      color: GQColors.coral,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildChip(String label, VoidCallback onTap) {
    return Material(
      color: Colors.grey.shade50,
      shape: StadiumBorder(
        side: BorderSide(
          color: Colors.grey.shade200,
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
              color: Colors.grey.shade600,
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
  Widget _buildInlineCrisisBanner() {
    return InlineCrisisBanner(
      onImOkay: () {
        setState(() => _showInlineCrisis = false);
      },
      onHelp: () {
        // Expand inline 988 sheet; does NOT navigate (per design spec)
        setState(() => _showInlineCrisis = false);
        _showHelpSheet();
      },
    );
  }

  /// R1D7 voice input mic button for the input bar.
  ///
  /// VoiceInputBar is UI-only — speech_to_text is not yet wired, so opening
  /// it sends the user into a recording UI that always produces an empty
  /// transcript. Until the backend ships, surface a "coming soon" SnackBar
  /// instead of advertising a feature that doesn't work.
  Widget _buildVoiceMicButton() {
    return Semantics(
      button: true,
      label: 'Voice input — coming soon',
      child: GestureDetector(
        onTap: () {
          HapticFeedback.lightImpact();
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text(
                'Voice input is coming soon · for now, please type',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
              ),
              behavior: SnackBarBehavior.floating,
              duration: const Duration(seconds: 2),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(GQRadii.card),
              ),
              backgroundColor: GQColors.ink2,
            ),
          );
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

  @override
  void dispose() {
    widget.reselect?.removeListener(_onReselect);
    _connectivitySub?.cancel(); // R1D12 — Offline States
    _messageController.dispose();
    _scrollController.dispose();
    _inputFocus.dispose();
    super.dispose();
  }
}

// Risk pill removed from UI; actionable chips remain.

class _CrisisChip extends StatelessWidget {
  const _CrisisChip(
      {required this.name, required this.phone, this.textInstr = ''});
  final String name;
  final String
      phone; // may be empty when only text instructions exist (e.g., "HOME to 741741")
  final String textInstr;

  Future<void> _onTap(BuildContext context) async {
    final p = phone.trim();
    final t = textInstr.trim();
    if (p.isNotEmpty) {
      final tel = Uri(scheme: 'tel', path: p);
      try {
        final can = await canLaunchUrl(tel);
        if (can) {
          final ok = await launchUrl(tel, mode: LaunchMode.externalApplication);
          if (!ok) {
            // Fall back to copy
            await Clipboard.setData(ClipboardData(text: p));
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                    content: Text(
                        'Couldn\'t open dialer. Number copied to clipboard.')),
              );
            }
          }
        } else {
          await Clipboard.setData(ClipboardData(text: p));
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                  content:
                      Text('Call not supported. Number copied to clipboard.')),
            );
          }
        }
      } catch (e) {
        if (kDebugMode) debugPrint('tel: launch error: $e');
        await Clipboard.setData(ClipboardData(text: p));
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
                content: Text('Number copied to clipboard. Dial manually.')),
          );
        }
      }
      return;
    }
    if (t.isNotEmpty) {
      // Attempt to parse patterns like "HOME to 741741"
      String s = t;
      if (s.toLowerCase().startsWith('text ')) {
        s = s.substring(5).trim();
      }
      final reg = RegExp(r'^(.+?)\s+to\s+(\d+)$', caseSensitive: false);
      final m = reg.firstMatch(s);
      if (m != null) {
        final body = m.group(1)!.trim();
        final to = m.group(2)!.trim();
        final sms =
            Uri(scheme: 'sms', path: to, queryParameters: {'body': body});
        try {
          final can = await canLaunchUrl(sms);
          if (can) {
            final ok =
                await launchUrl(sms, mode: LaunchMode.externalApplication);
            if (!ok) {
              await Clipboard.setData(ClipboardData(text: t));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                      content:
                          Text('Couldn\'t open SMS. Instructions copied.')),
                );
              }
            }
          } else {
            await Clipboard.setData(ClipboardData(text: t));
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                    content: Text('SMS not supported. Instructions copied.')),
              );
            }
          }
        } catch (e) {
          if (kDebugMode) debugPrint('sms: launch error: $e');
          await Clipboard.setData(ClipboardData(text: t));
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                  content: Text('Instructions copied to clipboard.')),
            );
          }
        }
      } else {
        await Clipboard.setData(ClipboardData(text: t));
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Instructions copied to clipboard.')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final hasName = name.trim().isNotEmpty;
    final hasPhone = phone.trim().isNotEmpty;
    final hasText = textInstr.trim().isNotEmpty;
    final label = () {
      if (hasName && hasPhone) return '$name · ${phone.trim()}';
      if (hasName && hasText) return '$name · ${textInstr.trim()}';
      if (hasPhone) return phone.trim();
      if (hasText) return textInstr.trim();
      if (hasName) return name.trim();
      return '';
    }();
    if (label.isEmpty) return const SizedBox.shrink();
    final semanticsLabel = () {
      if (hasPhone && hasName) return 'Call $name at ${phone.trim()}';
      if (hasPhone) return 'Call ${phone.trim()}';
      if (hasText && hasName) return '$name: ${textInstr.trim()}';
      if (hasText) return textInstr.trim();
      return label;
    }();
    return Semantics(
      button: true,
      label: semanticsLabel,
      onTapHint: (hasPhone || hasText) ? 'Activate' : null,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: (hasPhone || hasText) ? () => _onTap(context) : null,
        onLongPress: (hasPhone || hasText)
            ? () async {
                final toCopy = hasPhone
                    ? phone.trim()
                    : (hasText ? textInstr.trim() : name.trim());
                await Clipboard.setData(ClipboardData(text: toCopy));
                if (kDebugMode) debugPrint('Copied crisis info: $toCopy');
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Copied to clipboard.')),
                  );
                }
              }
            : null,
        child: ConstrainedBox(
          constraints: BoxConstraints(minWidth: 44.h, minHeight: 36.h),
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 12.h, vertical: 8.h),
            decoration: BoxDecoration(
              color: Colors.blueGrey.shade50,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: Colors.blueGrey.shade200),
            ),
            child: Center(
              child: Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(
                    fontSize: 12.0,
                    fontWeight: FontWeight.w500,
                    color: Colors.black87),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _TypingDots extends StatefulWidget {
  const _TypingDots();
  @override
  State<_TypingDots> createState() => _TypingDotsState();
}

class _TypingDotsState extends State<_TypingDots>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1000))
    ..repeat();
  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final baseColor = Colors.grey.shade500;
    final reduceMotion = MediaQuery.of(context).accessibleNavigation;
    if (reduceMotion) {
      if (_c.isAnimating) _c.stop();
      // Static dots for reduced motion
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (i) {
          return Container(
            margin: EdgeInsets.symmetric(horizontal: 3.h),
            width: 8.h,
            height: 8.h,
            decoration: BoxDecoration(
              color: baseColor.withValues(alpha: 0.6),
              shape: BoxShape.circle,
            ),
          );
        }),
      );
    }
    if (!_c.isAnimating) _c.repeat();
    return AnimatedBuilder(
      animation: _c,
      builder: (context, _) {
        double v(int i) {
          final t = (_c.value + (i * 0.2)) % 1.0;
          return (0.5 + 0.5 * math.sin(2 * math.pi * t)).clamp(0.0, 1.0);
        }

        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            return Container(
              margin: EdgeInsets.symmetric(horizontal: 3.h),
              width: 8.h,
              height: 8.h,
              decoration: BoxDecoration(
                color: baseColor.withValues(alpha: v(i)),
                shape: BoxShape.circle,
              ),
            );
          }),
        );
      },
    );
  }
}

/// R1D6 — BreathingOrb: 5.6 s gentle scale pulse using GQDurations.breathe.
/// Renders a soft coral circle that inhales/exhales to create a calming rhythm.
class _BreathingOrb extends StatefulWidget {
  const _BreathingOrb();

  @override
  State<_BreathingOrb> createState() => _BreathingOrbState();
}

class _BreathingOrbState extends State<_BreathingOrb>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: GQDurations.breathe,
    )..repeat(reverse: true);
    _scale = Tween<double>(begin: 0.88, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.of(context).accessibleNavigation;
    if (reduceMotion) {
      return _orbShape(1.0);
    }
    return AnimatedBuilder(
      animation: _scale,
      builder: (_, __) => _orbShape(_scale.value),
    );
  }

  Widget _orbShape(double scale) {
    return Transform.scale(
      scale: scale,
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: GQColors.accentSoft,
          border: Border.all(
            color: GQColors.coral.withValues(alpha: 0.35),
            width: 1.5,
          ),
        ),
        child: const Center(
          child: Icon(
            Icons.favorite_rounded,
            size: 22,
            color: GQColors.coral,
          ),
        ),
      ),
    );
  }
}
