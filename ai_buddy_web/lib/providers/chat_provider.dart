import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/message.dart';
import '../models/interactive_exercise.dart';
import '../services/api_service.dart';
import '../services/firebase_service.dart';
import '../services/notification_service.dart';
import '../services/streaming/streaming_sse.dart' as sse;

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

  // Warm greeting variations for personality
  static const List<String> _greetings = [
    "This is your space to think out loud. Share what's on your mind. I'm here when you're ready. 🌱",
    "Hi! Ready when you are. No pressure, just here to listen. 🌱",
    "Hey! What's on your mind today? I'm all ears. 💭",
    "Hello! This is your space to think out loud. How can I help? ✨",
    "Hi there! How's your day going? I'm here whenever you need me. 🌟",
  ];

  // Welcome back messages based on time away
  static const List<String> _welcomeBackMessages = [
    "Welcome back! 👋 Good to see you again.",
    "Hey, you're back! 🌟 How have you been?",
    "Welcome back! I missed our chats. 💜",
  ];

  static const String _lastVisitKey = 'chat_last_visit';

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
    // Time-aware greetings
    if (hour >= 5 && hour < 12) {
      return "Good morning! ☀️ How are you feeling today?";
    } else if (hour >= 22 || hour < 5) {
      return "Hey, night owl! 🌙 What's on your mind?";
    }
    // Random from list for other times
    return _greetings[Random().nextInt(_greetings.length)];
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
  }

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

    // Optimistic UI: show user's message immediately and turn on typing indicator
    final userMessage = Message(content: content, isUser: true);
    _messages.add(userMessage);
    _isTyping = true;
    _isSending =
        false; // Reset debounce immediately so user can queue more messages
    notifyListeners();

    try {
      // Track first message for retention analytics
      final isFirstMessage = _messages.length == 1; // only the user msg we just added
      FirebaseService().logChatMessage(isFirstMessage ? 'first' : 'follow_up');
      if (isFirstMessage) {
        FirebaseService().logEvent('first_chat_message_sent', {
          'message_length': content.length,
        });
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

      // Add error message bubble (user message already added above)
      _messages.add(
        Message(content: errorMessage, isUser: false, type: MessageType.error),
      );
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

      _messages.add(
        Message(
          content: friendly,
          isUser: false,
          type: MessageType.error,
        ),
      );
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
      crisisMsg: aiMessage.crisisMsg,
      crisisNumbers: aiMessage.crisisNumbers,
      exercise: aiMessage.exercise,
    );
    _messages.add(msg);
    _error = null;
    if (_isTyping) _isTyping = false;
    notifyListeners();

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
              if (kDebugMode) {
                debugPrint('🧩 [SSE meta] Error parsing exercise: $e');
              }
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

  void clearChat() {
    _messages.clear();
    _hasShownGreeting = false; // Reset greeting flag
    _apiService.clearSession();
    notifyListeners();
  }

  // Map string risk level to enum if present
  RiskLevel? _mapRisk(dynamic level) {
    if (level == null) return null;
    final s = level.toString().toLowerCase();
    switch (s) {
      case 'high':
      case 'crisis':
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
