import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/message.dart';
import '../models/interactive_exercise.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../services/crisis_keyword_detector.dart';
import '../services/firebase_service.dart';
import '../services/notification_service.dart';
import '../services/streaming/streaming_sse.dart' as sse;
import '../services/voice_notes_service.dart';
import '../widgets/chat_error_bubble.dart';

/// Coarse connection state for the chat surface. Drives the companion
/// status dot, the connection pill, the app-bar label, and the offline
/// safe list.
enum ChatConnectionState {
  /// Connected and sending normally.
  online,

  /// A send failed; silent retries are in flight.
  reconnecting,

  /// Silent retries exhausted (x2) — server-side outage.
  unreachable,

  /// No device connectivity at launch (cold-start offline).
  offline,
}

/// A user message that failed to send and is queued for silent retry.
class _QueuedMessage {
  final String content;
  final String? country;
  final String userMessageId;
  final String errorBubbleId;
  int retryCount = 0;

  _QueuedMessage({
    required this.content,
    this.country,
    required this.userMessageId,
    required this.errorBubbleId,
  });
}

class ChatProvider extends ChangeNotifier {
  final ApiService _apiService;
  final List<Message> _messages = [];
  bool _isLoading = false;
  String? _error;
  bool _hasShownGreeting = false; // Track if greeting has been shown
  bool _isTyping = false; // AI typing indicator state
  bool _isSending = false; // Prevent concurrent sends (tap debouncing)
  final List<StreamSubscription<Map<String, dynamic>>> _subscriptions = [];
  final List<void Function()> _closers = [];

  bool _isOptimisticGreeting =
      false; // Track if we are showing the temporary local greeting

  // ── Chat Error / Offline States ──────────────────────────────────────────
  /// Current connection state for the chat surface.
  ChatConnectionState _connectionState = ChatConnectionState.online;
  ChatConnectionState get connectionState => _connectionState;

  /// Queued user messages awaiting silent retry.
  final List<_QueuedMessage> _outboundQueue = [];

  /// Per-error-bubble state (failed vs unreachable), keyed by error Message ID.
  final Map<String, ChatErrorState> _errorStates = {};

  /// Error bubbles whose action row has been removed (queue flushed on
  /// reconnect — bubble stays in history as a record but loses the retry
  /// / alternate-action buttons).
  final Set<String> _flushedErrorIds = {};

  /// Silent-retry backoff schedule: 2s, then 6s. Two retries max.
  static const List<Duration> _retryBackoffs = [
    Duration(seconds: 2),
    Duration(seconds: 6),
  ];

  Timer? _retryTimer;

  /// Look up the error state for a given error-bubble Message ID.
  /// Returns null if the ID is not a tracked error bubble.
  ChatErrorState? errorStateFor(String messageId) => _errorStates[messageId];

  /// Whether the action row (retry / alternate) should be visible for a
  /// given error bubble. False once the queue has been flushed on reconnect.
  bool errorActionsAvailable(String messageId) =>
      !_flushedErrorIds.contains(messageId);

  /// Number of messages currently queued for retry.
  int get queuedCount => _outboundQueue.length;

  // Welcome back messages based on time away
  static const List<String> _welcomeBackMessages = [
    "Welcome back! 👋 Good to see you again.",
    "Hey, you're back! 🌟 How have you been?",
    "Welcome back! I missed our chats. 💜",
  ];

  static const String _lastVisitKey = 'chat_last_visit';

  // Persisted across sessions so first-message analytics fires exactly once
  // per device. _messages.length == 1 was wrong: after chat history hydration
  // a returning user's "first" send can land at message 50+, undercounting
  // retention. The boolean transitions false→true on the first successful
  // emit; subsequent sends short-circuit. Versioned suffix lets us re-issue
  // the gate without losing history if the contract ever changes.
  static const String _firstChatMessageLoggedKey =
      'first_chat_message_logged_v1';

  Future<String> _getGreetingWithContext() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final lastVisitMs = prefs.getInt(_lastVisitKey);
      final now = DateTime.now();

      // Save current visit time
      await prefs.setInt(_lastVisitKey, now.millisecondsSinceEpoch);

      if (lastVisitMs != null) {
        final lastVisit = DateTime.fromMillisecondsSinceEpoch(lastVisitMs);
        final hoursSinceLastVisit = now.difference(lastVisit).inHours;

        // If more than 24 hours, show welcome back
        if (hoursSinceLastVisit >= 24) {
          final days = (hoursSinceLastVisit / 24).floor();
          if (days >= 7) {
            return "Hey, it's been a while! 🌱 Glad you're back. No pressure, I'm here whenever you need me.";
          } else if (days >= 3) {
            return "Welcome back! 💜 It's been a few days. How are you doing?";
          } else {
            return _welcomeBackMessages[
                Random().nextInt(_welcomeBackMessages.length)];
          }
        }
      }
    } catch (e) {
      debugPrint('Error checking last visit: $e');
    }

    // Default to time-aware greeting for frequent users
    return _getRandomGreeting();
  }

  String _getRandomGreeting() {
    final hour = DateTime.now().hour;
    // Time-aware greetings — buckets MUST mirror the header's
    // _buildFirstTurnWarmth() bucketing in interactive_chat_screen.dart so the
    // bubble greeting and the header greeting agree on the time-of-day word.
    // Header buckets:
    //   morning   5–12   → "Good morning"
    //   afternoon 12–17  → "Good afternoon"
    //   evening   17–22  → "Good evening"  (header collapses 17–5 into evening)
    //   night-owl 22–5   → bubble carves this out for warmth ("night owl 🌙")
    if (hour >= 5 && hour < 12) {
      return "Good morning! ☀️ How are you feeling today?";
    } else if (hour >= 12 && hour < 17) {
      return "Good afternoon! 🌤️ How's your day going?";
    } else if (hour >= 17 && hour < 22) {
      return "Good evening! 🌆 How are you winding down?";
    } else {
      // 22:00–04:59 — header still says "Good evening" but the bubble keeps
      // the warmer night-owl flavour. They agree on bucket boundaries; only
      // the bubble copy differs by design.
      return "Hey, night owl! 🌙 What's on your mind?";
    }
  }

  ChatProvider() : _apiService = ApiService() {
    // Pre-insert a greeting immediately for instant UI; hydrate history in background
    if (_messages.isEmpty && !_hasShownGreeting) {
      _messages.add(
        Message(
          content: _getRandomGreeting(), // Sync fallback
          isUser: false,
          type: MessageType.text,
        ),
      );
      _hasShownGreeting = true;
      _isOptimisticGreeting = true; // Mark as optimistic
      notifyListeners();
      // Update greeting with context asynchronously
      _updateGreetingWithContext();
    }
    _loadChatHistory();

    // Refresh chat history whenever the device's session-binding changes
    // (sign-in adopts the user's canonical session_id; sign-out generates
    // a fresh anonymous one). Cancel any in-flight SSE subscriptions FIRST
    // — a streaming reply from the previous session would otherwise keep
    // mutating _messages after the clear() and bleed across the boundary.
    _authSessionSub ??= AuthService.instance.onSessionChanged.listen((_) {
      for (final sub in _subscriptions) {
        try { sub.cancel(); } catch (_) {}
      }
      for (final c in _closers) {
        try { c(); } catch (_) {}
      }
      _subscriptions.clear();
      _closers.clear();
      _messages.clear();
      _isOptimisticGreeting = false;
      _hasShownGreeting = false;
      notifyListeners();
      _loadChatHistory();
    });
  }

  // ??= above guards against the rare case where a second ChatProvider
  // instance subscribes (hot-reload, leopard variant) — only one stream
  // listener lives per process.
  StreamSubscription<void>? _authSessionSub;

  Future<void> _updateGreetingWithContext() async {
    final contextualGreeting = await _getGreetingWithContext();
    // Only update if we are still showing the optimistic greeting
    if (_isOptimisticGreeting &&
        _messages.isNotEmpty &&
        !_messages.first.isUser) {
      // Only update if it's different from the sync greeting
      if (_messages.first.content != contextualGreeting) {
        _messages[0] = Message(
          content: contextualGreeting,
          isUser: false,
          type: MessageType.text,
        );
        notifyListeners();
      }
    }
  }

  List<Message> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isTyping => _isTyping;

  Future<void> _loadChatHistory() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final history = await _apiService.getChatHistory();
      // Only replace local messages if server has any. If history is empty,
      // keep the pre-inserted greeting for a friendlier first-load UX.
      if (history.isNotEmpty) {
        _messages
          ..clear()
          ..addAll(history);
        _isOptimisticGreeting = false; // History loaded, no longer optimistic
      }
    } catch (e) {
      debugPrint('❌ Error loading chat history: $e');
      _error = 'Couldn\'t load our conversation. Let\'s try again.';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> sendMessage(String content, {String? country}) async {
    if (content.trim().isEmpty) return;
    if (_isSending) return; // debounce concurrent taps
    _isSending = true;
    _error = null;
    _isLoading = true;

    // Optimistic UI: show user's message immediately and turn on typing indicator.
    //
    // C1 safety fix: run the on-device CrisisKeywordDetector against the user's
    // text BEFORE the API call. The backend's risk_level classification is the
    // primary signal, but it can misclassify, return late, or never return
    // (network drop / cold start). The detector is <1ms and deny-list based, so
    // it is a safe belt-and-braces. If it matches, we stamp the user message
    // with RiskLevel.crisis (Tier-1 hit) or RiskLevel.high (Tier-2 hit) so the
    // InlineCrisisBanner in interactive_chat_screen.dart fires on the next
    // frame regardless of what the backend eventually returns. The AI reply
    // bubble's riskLevel (set later from the API response) still drives the
    // banner's sticky-dismissal semantics — but the user message itself now
    // guarantees the surface appears.
    final bool crisisTier1 = CrisisKeywordDetector.matchTier1(content);
    final bool crisisTier2 = !crisisTier1 && CrisisKeywordDetector.match(content);
    final RiskLevel userRisk = crisisTier1
        ? RiskLevel.crisis
        : (crisisTier2 ? RiskLevel.high : RiskLevel.none);
    final userMessage = Message(
      content: content,
      isUser: true,
      riskLevel: userRisk,
      // WO-6.3 F1: this is the one place a message's risk comes from the
      // on-device keyword detector rather than the server. See
      // RiskSource's doc comment — this distinction gates the full-screen
      // takeover.
      riskSource:
          userRisk != RiskLevel.none ? RiskSource.keyword : RiskSource.server,
    );
    _messages.add(userMessage);
    _isTyping = true;
    _isSending =
        false; // Reset debounce immediately so user can queue more messages
    notifyListeners();

    // If the on-device detector fired, log it so we can measure backend-vs-client
    // agreement over time. Do NOT short-circuit the API call — the backend may
    // still produce a more appropriate intervention (crisis_msg + numbers) and
    // the chat reply itself is still useful. The banner is already visible.
    if (userRisk != RiskLevel.none) {
      FirebaseService().logEvent('client_crisis_keyword_match', {
        'tier': crisisTier1 ? 'tier1' : 'tier2',
      });
    }

    try {
      // Track first message for retention analytics.
      //
      // We can't rely on `_messages.length == 1` — chat history hydrates
      // from the server, so a returning user's "first send" can land at
      // message 50+ and never satisfy that predicate (analytics undercount).
      //
      // Source of truth: a SharedPreferences boolean
      // (`first_chat_message_logged_v1`) that transitions false→true on the
      // first successful emit. The legacy `chat_session_started.is_first`
      // payload mirrors the same flag for downstream consumers; we only
      // emit the dedicated `first_chat_message_sent` event on the actual
      // transition, never twice.
      bool isFirstMessage = false;
      SharedPreferences? prefs;
      try {
        prefs = await SharedPreferences.getInstance();
        isFirstMessage = !(prefs.getBool(_firstChatMessageLoggedKey) ?? false);
      } catch (e) {
        debugPrint('first_chat_message pref read failed: $e');
      }
      FirebaseService().logChatMessage(isFirstMessage ? 'first' : 'follow_up');
      FirebaseService().logEvent('chat_session_started', {
        'message_length': content.length,
        'is_first': isFirstMessage,
      });
      if (isFirstMessage) {
        FirebaseService().logEvent('first_chat_message_sent', {
          'message_length': content.length,
        });
        // Flip the gate AFTER the event lands so a crash between read and
        // log doesn't burn the analytics fire. Best-effort write; if prefs
        // is null (read failed above) we accept the rare double-fire risk
        // over silent loss of analytics.
        try {
          await prefs?.setBool(_firstChatMessageLoggedKey, true);
        } catch (e) {
          debugPrint('first_chat_message pref write failed: $e');
        }
      }

      // Try streaming first (web-only, feature-gated). Fallback to non-streaming.
      final handle = await _apiService.streamMessage(content, country: country);
      if (handle != null) {
        await _handleStreamingMessage(handle, content, country);
        // Schedule 24h follow-up notification after first successful chat
        if (isFirstMessage) _scheduleFollowUpNotification();
        return; // streaming path initiated
      }

      // Fallback: non-streaming request, progressively reveal locally
      await _processNonStreamingResponse(content, country: country);

      // Schedule 24h follow-up notification after first successful chat
      if (isFirstMessage) _scheduleFollowUpNotification();
    } on DioException catch (e) {
      debugPrint('🚨 DIO Exception in sendMessage:');
      debugPrint('   Type: ${e.type}');
      debugPrint('   Message: ${e.message}');
      debugPrint('   Status Code: ${e.response?.statusCode}');
      debugPrint('   Response Data: ${e.response?.data}');

      final String errorMessage = _apiService.getErrorMessage(e);
      _error = errorMessage;
      if (_isTyping) _isTyping = false;

      // Queue for silent retry with ChatErrorBubble (failed state).
      _queueFailedSend(content, country, userMessage.id, errorMessage);
    } catch (e) {
      debugPrint('❌ Unexpected error in sendMessage: $e');

      // Surface any user-friendly message from wrapped exceptions (e.g. from
      // ApiService._retryOperation), otherwise fall back to a clearer
      // cold-start style message instead of a generic error.
      final raw = e.toString();
      final cleaned = raw.replaceFirst('Exception: ', '').trim();
      final friendly = cleaned.isNotEmpty && cleaned != 'Exception'
          ? cleaned
          : 'The server is waking up or temporarily unavailable. Please wait a few seconds and try again.';

      _error = friendly;
      if (_isTyping) _isTyping = false;

      // Queue for silent retry with ChatErrorBubble (failed state).
      _queueFailedSend(content, country, userMessage.id, friendly);
    } finally {
      _isSending = false; // reset tap debounce so future sends work
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Extracted logic for non-streaming response with progressive reveal
  Future<void> _processNonStreamingResponse(String content,
      {String? country}) async {
    final aiMessage = await _apiService.sendMessage(
      content,
      country: country,
    );
    if (kDebugMode) {
      debugPrint('🟣 [HTTP chat] risk=${aiMessage.riskLevel}');
      debugPrint(
        '🟣 [HTTP chat] crisis_msg_len=${aiMessage.crisisMsg?.length ?? 0}',
      );
      debugPrint(
        '🟣 [HTTP chat] crisis_numbers=${aiMessage.crisisNumbers?.length ?? 0}',
      );
    }

    // Avoid adding an empty bubble. Delay insertion until first chunk exists.
    final full = aiMessage.content;
    final lines =
        full.contains('\n') ? full.split('\n') : _splitIntoSentences(full);

    if (lines.isEmpty || full.trim().isEmpty) {
      if (_isTyping) _isTyping = false;
      _error = null;
      notifyListeners();
      return;
    }

    final first = lines.first;
    final msg = Message(
      content: first,
      isUser: false,
      type: aiMessage.type,
      riskLevel: aiMessage.riskLevel,
      // Explicit, not inherited from the constructor default: this risk came
      // from the backend classifier, and that provenance is what admits a
      // full-screen takeover. Relying on the default would leave the most
      // consequential branch in the app resting on an unstated assumption.
      riskSource: RiskSource.server,
      crisisMsg: aiMessage.crisisMsg,
      crisisNumbers: aiMessage.crisisNumbers,
      exercise: aiMessage.exercise,
    );
    _messages.add(msg);
    _error = null;
    if (_isTyping) _isTyping = false;
    notifyListeners();

    // Voice notes — speaks the full reply if the user has the Profile
    // toggle ON. Fire-and-forget; the service short-circuits on pref miss
    // and on platform init failure. Audit §7.
    unawaited(VoiceNotesService.instance.maybeSpeak(full));

    // Track exercise offers for analytics
    if (aiMessage.exercise != null) {
      FirebaseService().logEvent('intervention_offered', {
        'exercise_type': aiMessage.exercise!.type,
      });
    }

    for (var i = 1; i < lines.length; i++) {
      final line = lines[i];
      msg.content += '\n$line';
      notifyListeners();
      final ms = (line.trim().length * 15).clamp(120, 600);
      await Future.delayed(Duration(milliseconds: ms));
    }
  }

  /// Implementation of streaming message processing
  Future<void> _handleStreamingMessage(
      sse.SseHandle handle, String originalContent, String? country) async {
    Message? streaming;
    _error = null;
    notifyListeners();

    bool firstToken = true;
    RiskLevel metaRisk = RiskLevel.none;
    String? metaCrisisMsg;
    List<Map<String, dynamic>>? metaCrisisNumbers;
    InteractiveExercise? metaExercise;

    final sub = handle.stream.listen(
      (event) async {
        final type = event['type'] as String?;
        if (type == 'meta') {
          metaRisk = _mapRisk(event['risk_level']) ?? RiskLevel.none;
          metaCrisisMsg = event['crisis_msg'] as String?;
          metaCrisisNumbers =
              (event['crisis_numbers'] as List?)?.cast<Map<String, dynamic>>();

          if (event['interactive'] == true && event['exercise'] != null) {
            try {
              metaExercise = InteractiveExercise.fromJson({
                'type': event['exercise_type'],
                ...(event['exercise'] as Map<String, dynamic>),
              });
            } catch (e) {
              // Don't crash — degrade gracefully (chat bubble renders, just
              // without the exercise card). But surface the failure so we
              // can see malformed Gemini payloads in dev + analytics.
              debugPrint('🧩 [SSE meta] Error parsing exercise: $e');
              final exerciseMap = event['exercise'];
              final rawKeys = exerciseMap is Map
                  ? exerciseMap.keys.join(',')
                  : '<not-a-map>';
              FirebaseService().logEvent('sse_exercise_parse_failed', {
                'error': e.toString(),
                'raw_keys': rawKeys,
              });
            }
          }

          if (streaming != null) {
            final idx = _messages.lastIndexOf(streaming!);
            if (idx != -1) {
              final replaced = Message(
                id: streaming!.id,
                content: streaming!.content,
                isUser: false,
                timestamp: streaming!.timestamp,
                type: MessageType.text,
                riskLevel: metaRisk,
                // Server-classified (SSE `meta`). Explicit for the same
                // reason as the non-streaming path above. Deliberately NOT
                // copyWith here: metaCrisisMsg/metaCrisisNumbers are
                // legitimately nullable, and copyWith's null-coalescing
                // would preserve a stale value instead of clearing it.
                riskSource: RiskSource.server,
                crisisMsg: metaCrisisMsg,
                crisisNumbers: metaCrisisNumbers,
                exercise: metaExercise,
              );
              _messages[idx] = replaced;
              streaming = replaced;
              notifyListeners();
            }
          }
        } else if (type == 'token') {
          final text = (event['text'] as String?) ?? '';
          if (streaming == null) {
            streaming = Message(
              content: '',
              isUser: false,
              type: MessageType.text,
              riskLevel: metaRisk,
              // Server-classified (SSE first `token`).
              riskSource: RiskSource.server,
              crisisMsg: metaCrisisMsg,
              crisisNumbers: metaCrisisNumbers,
              exercise: metaExercise,
            );
            _messages.add(streaming!);
          }
          streaming!.content += text;
          if (firstToken) {
            firstToken = false;
            if (_isTyping) _isTyping = false;
          }
          notifyListeners();
        } else if (type == 'done') {
          if (_isTyping) _isTyping = false;
          notifyListeners();
          // Speak the completed streamed reply if voice-notes is on.
          // Audit §7. No-op when pref is false / on web stub.
          final spoken = streaming?.content;
          if (spoken != null && spoken.trim().isNotEmpty) {
            unawaited(VoiceNotesService.instance.maybeSpeak(spoken));
          }
          handle.close();
        } else if (type == 'error') {
          handle.close();
          if (streaming == null) {
            // Early error: Fallback to non-streaming for a second attempt
            await _processNonStreamingResponse(originalContent,
                country: country);
          } else {
            // Late error: Show error marker
            _messages.add(Message(
                content: 'Stream disconnected.',
                isUser: false,
                type: MessageType.error));
            if (_isTyping) _isTyping = false;
            notifyListeners();
          }
        }
      },
      onError: (e) async {
        handle.close();
        if (streaming == null) {
          await _processNonStreamingResponse(originalContent, country: country);
        } else {
          if (_isTyping) _isTyping = false;
          notifyListeners();
        }
      },
      onDone: () {
        if (_isTyping) _isTyping = false;
        notifyListeners();
      },
      cancelOnError: true,
    );
    _subscriptions.add(sub);
    _closers.add(handle.close);
  }

  // Split a paragraph into sentence-like chunks for smoother progressive rendering
  List<String> _splitIntoSentences(String text) {
    final regex = RegExp(r'(?<=[.!?])\s+');
    final parts = text.split(regex).where((s) => s.isNotEmpty).toList();
    // Fallback: if still one long part, split by commas to add a bit more granularity
    if (parts.length <= 1 && text.contains(',')) {
      return text
          .split(',')
          .map((e) => e.trim())
          .where((s) => s.isNotEmpty)
          .toList();
    }
    return parts;
  }

  /// Schedule a 24h follow-up push notification after the user's first chat.
  void _scheduleFollowUpNotification() {
    try {
      NotificationService.scheduleOneShot(
        target: DateTime.now().add(const Duration(hours: 24)),
        title: 'Alex here',
        body: "How are you doing today? I'm here if you want to talk.",
        payload: 'open_talk',
        debugTag: 'first_chat_followup',
      );
    } catch (e) {
      debugPrint('Notification scheduling error: $e');
    }
  }

  Future<void> prefetchSession() async {
    await _loadChatHistory();
  }

  void removeMessage(String id) {
    _messages.removeWhere((m) => m.id == id);
    _errorStates.remove(id);
    _flushedErrorIds.remove(id);
    notifyListeners();
  }

  // ── Chat Error / Offline: queue, retry, flush ────────────────────────────

  /// Called when a send fails. Adds a tracked error bubble (failed state),
  /// queues the message for silent retry, sets the connection state to
  /// reconnecting, and schedules the first retry after 2s.
  void _queueFailedSend(
    String content,
    String? country,
    String userMessageId,
    String errorText,
  ) {
    final errorBubble = Message(
      content: errorText,
      isUser: false,
      type: MessageType.error,
    );
    _messages.add(errorBubble);
    _errorStates[errorBubble.id] = ChatErrorState.failed;

    _outboundQueue.add(_QueuedMessage(
      content: content,
      country: country,
      userMessageId: userMessageId,
      errorBubbleId: errorBubble.id,
    ));

    if (_connectionState == ChatConnectionState.online) {
      _connectionState = ChatConnectionState.reconnecting;
    }
    _scheduleRetry();
    notifyListeners();
  }

  /// Schedules the next silent retry using the backoff schedule
  /// (2s for retry 0, 6s for retry 1). No-op if the queue is empty or
  /// the retry cap has been reached.
  void _scheduleRetry() {
    _retryTimer?.cancel();
    if (_outboundQueue.isEmpty) return;

    final next = _outboundQueue.first;
    if (next.retryCount >= _retryBackoffs.length) {
      // Two retries exhausted → escalate to unreachable.
      _escalateToUnreachable();
      return;
    }

    final delay = _retryBackoffs[next.retryCount];
    _retryTimer = Timer(delay, _attemptRetry);
  }

  /// Attempts a silent retry of the oldest queued message. On success,
  /// removes the error bubble and processes the AI reply. On failure,
  /// increments the retry count and reschedules (or escalates).
  void _attemptRetry() async {
    if (_outboundQueue.isEmpty) return;
    final queued = _outboundQueue.first;

    try {
      // Try streaming first, then non-streaming — mirrors sendMessage.
      final handle =
          await _apiService.streamMessage(queued.content, country: queued.country);
      if (handle != null) {
        // Remove error bubble before streaming adds the AI reply.
        _messages.removeWhere((m) => m.id == queued.errorBubbleId);
        _errorStates.remove(queued.errorBubbleId);
        _outboundQueue.removeAt(0);
        _connectionState = ChatConnectionState.online;
        notifyListeners();
        await _handleStreamingMessage(handle, queued.content, queued.country);
        _processQueueAfterSuccess();
        return;
      }
      await _processNonStreamingResponse(queued.content, country: queued.country);
      // Success — clean up the error bubble and queue.
      _messages.removeWhere((m) => m.id == queued.errorBubbleId);
      _errorStates.remove(queued.errorBubbleId);
      _outboundQueue.removeAt(0);
      _connectionState = ChatConnectionState.online;
      notifyListeners();
      _processQueueAfterSuccess();
    } catch (e) {
      debugPrint('🔄 Silent retry failed: $e');
      queued.retryCount++;
      if (queued.retryCount >= _retryBackoffs.length) {
        _escalateToUnreachable();
      } else {
        _scheduleRetry();
      }
      notifyListeners();
    }
  }

  /// Escalates the oldest queued message to the unreachable state.
  void _escalateToUnreachable() {
    if (_outboundQueue.isEmpty) return;
    final queued = _outboundQueue.first;
    _errorStates[queued.errorBubbleId] = ChatErrorState.unreachable;
    _connectionState = ChatConnectionState.unreachable;
    notifyListeners();
  }

  /// After a successful retry, if more messages are queued, retry the next
  /// one immediately (flush oldest-first).
  void _processQueueAfterSuccess() {
    if (_outboundQueue.isEmpty) {
      _connectionState = ChatConnectionState.online;
      notifyListeners();
      return;
    }
    // Flush remaining queued messages immediately.
    _attemptRetry();
  }

  /// Called by the UI when device connectivity returns. Flushes the queue
  /// oldest-first. Error bubbles that were retried successfully are removed;
  /// any remaining error bubbles lose their action row (become historical).
  void markConnectionOnline() {
    if (_connectionState == ChatConnectionState.online) return;
    _retryTimer?.cancel();

    if (_outboundQueue.isEmpty) {
      _connectionState = ChatConnectionState.online;
      notifyListeners();
      return;
    }

    // Mark all current error bubbles as flushed (lose action row) and
    // attempt to flush the queue.
    for (final queued in _outboundQueue) {
      _flushedErrorIds.add(queued.errorBubbleId);
    }
    _connectionState = ChatConnectionState.reconnecting;
    notifyListeners();
    _attemptRetry();
  }

  /// Called by the UI when the device goes offline (cold-start or mid-chat).
  void markConnectionOffline() {
    _retryTimer?.cancel();
    _connectionState = ChatConnectionState.offline;
    notifyListeners();
  }

  /// User-initiated retry for a specific error bubble (taps "Try again").
  /// Resets the retry count for that message and fires immediately.
  void retryFromErrorBubble(String errorBubbleId) {
    final idx = _outboundQueue.indexWhere((q) => q.errorBubbleId == errorBubbleId);
    if (idx == -1) return;
    // Move to front and retry immediately.
    final queued = _outboundQueue.removeAt(idx);
    queued.retryCount = 0;
    _outboundQueue.insert(0, queued);
    _flushedErrorIds.remove(errorBubbleId);
    _errorStates[errorBubbleId] = ChatErrorState.failed;
    _connectionState = ChatConnectionState.reconnecting;
    _retryTimer?.cancel();
    notifyListeners();
    _attemptRetry();
  }

  /// Inserts a companion (assistant) message directly into the transcript
  /// without a network round-trip.
  ///
  /// v1.5.0 ADHD Update — body-doubling check-ins (start/midpoint/end/
  /// abandon) need to land on a precise wall-clock schedule and use fixed,
  /// pre-written gentle copy. Round-tripping those through the LLM chat
  /// endpoint would add latency at exactly the moments a time-boxed session
  /// needs to feel responsive, risk off-tone phrasing at a moment where tone
  /// is the whole point (never guilt on abandon), and cost a model call for
  /// text that doesn't need to vary. This reuses the existing Message model
  /// and chat rendering — the message shows up as a normal Alex bubble —
  /// just skips ApiService/the network hop.
  void insertCompanionMessage(String content) {
    _messages.add(Message(content: content, isUser: false));
    notifyListeners();
  }

  void clearChat() {
    _messages.clear();
    _hasShownGreeting = false; // Reset greeting flag
    _apiService.clearSession();
    notifyListeners();
  }

  // Map string risk level to enum if present. C3 fix: preserve the distinct
  // `crisis` tier instead of collapsing it into `high` — the Message model
  // and InlineCrisisBanner activation both branch on RiskLevel.crisis, and
  // demoting it silently made those paths unreachable from API responses.
  RiskLevel? _mapRisk(dynamic level) {
    if (level == null) return null;
    final s = level.toString().toLowerCase();
    switch (s) {
      case 'crisis':
        return RiskLevel.crisis;
      case 'high':
        return RiskLevel.high;
      case 'medium':
        return RiskLevel.medium;
      case 'low':
        return RiskLevel.low;
      default:
        return RiskLevel.none;
    }
  }

  /// Track exercise completion outcome
  void trackExerciseOutcome({
    required String exerciseType,
    required String outcome,
    String? interventionId,
    int? timeSpentSeconds,
    int? moodBefore,
    int? moodAfter,
    double? effectiveness,
    String? feedback,
  }) {
    _apiService.reportExerciseOutcome(
      exerciseType: exerciseType,
      outcome: outcome,
      interventionId: interventionId,
      timeSpentSeconds: timeSpentSeconds,
      moodBefore: moodBefore,
      moodAfter: moodAfter,
      effectiveness: effectiveness,
      feedback: feedback,
    );
    FirebaseService().logExerciseCompleted(exerciseType);
  }

  @override
  void dispose() {
    _retryTimer?.cancel();
    _authSessionSub?.cancel();
    for (final sub in _subscriptions) {
      sub.cancel();
    }
    for (final c in _closers) {
      try {
        c();
      } catch (_) {}
    }
    _subscriptions.clear();
    _closers.clear();
    super.dispose();
  }
}
