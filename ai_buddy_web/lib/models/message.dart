import 'package:flutter/material.dart';
import 'interactive_exercise.dart';

enum MessageType { text, error, system }

// crisis = imminent/acute — triggers AcuteCrisisTakeover (State B).
// Added in R1D9 to match server-side _enhanced_crisis_detection risk_level values.
enum RiskLevel { none, low, medium, high, crisis }

// WO-6.3 F1 — a bare RiskLevel can't say WHERE a .crisis verdict came from,
// and that distinction is safety-load-bearing: a Tier-1 keyword hit and a
// server model classification both arrive as the same enum value, but only
// the server verdict is trusted enough to interrupt with a full-screen
// takeover (see CrisisResourcesWidget). .server is the default for every
// existing call site — only chat_provider.dart's on-device keyword stamp
// sets .keyword.
enum RiskSource { server, keyword }

class RiskAssessment {
  final RiskLevel level;
  final RiskSource source;
  const RiskAssessment(this.level, this.source);
}

class Message {
  final String id;
  String content;
  final bool isUser;
  final DateTime timestamp;
  final MessageType type;
  final RiskLevel riskLevel;
  final RiskSource riskSource;
  final List<String>? resources;
  final String? crisisMsg;
  final List<Map<String, dynamic>>? crisisNumbers;

  // NEW: Interactive exercise data
  final InteractiveExercise? exercise;

  Message({
    String? id,
    required this.content,
    required this.isUser,
    DateTime? timestamp,
    this.type = MessageType.text,
    this.riskLevel = RiskLevel.none,
    this.riskSource = RiskSource.server,
    this.resources,
    this.crisisMsg,
    this.crisisNumbers,
    this.exercise,
  })  : id = id ?? DateTime.now().millisecondsSinceEpoch.toString(),
        timestamp = timestamp ?? DateTime.now();

  factory Message.fromJson(Map<String, dynamic> json) {
    // Parse interactive exercise if present
    InteractiveExercise? parsedExercise;
    if (json['interactive'] == true && json['exercise'] != null) {
      try {
        parsedExercise = InteractiveExercise.fromJson({
          'type': json['exercise_type'], // Top-level type
          ...json['exercise'] as Map<String, dynamic>, // Merged content
        });
      } catch (e) {
        debugPrint('Error parsing exercise in Message: $e');
      }
    }

    return Message(
      id: json['id'] as String?,
      content: json['content'] as String,
      isUser: json['is_user'] as bool,
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'] as String)
          : null,
      type: MessageType.values.firstWhere(
        (e) => e.toString() == 'MessageType.${json['type'] ?? 'text'}',
        orElse: () => MessageType.text,
      ),
      riskLevel: RiskLevel.values.firstWhere(
        (e) => e.toString() == 'RiskLevel.${json['risk_level'] ?? 'none'}',
        orElse: () => RiskLevel.none,
      ),
      // WO-6.3 F1 / Phase 2a. Absent `risk_source` resolves to .server, and
      // that is correct rather than merely convenient: the ONLY caller of
      // this factory is ApiService.getChatHistory(), so every JSON reaching
      // here is the server's own record. The backend does not emit the field
      // today; parsing it anyway means the day it starts, provenance is
      // honoured instead of silently flattened.
      //
      // The reason this default is safe is load-bearing, so it must not be
      // inherited blindly: if this factory ever parses locally-persisted
      // messages (draft cache, offline queue), absence would no longer imply
      // server origin, and a keyword-stamped .crisis would launder itself
      // into a server verdict — exactly the false positive the full-screen
      // takeover gate exists to prevent. Re-derive this default before
      // adding any such caller.
      riskSource: RiskSource.values.firstWhere(
        (e) => e.toString() == 'RiskSource.${json['risk_source'] ?? 'server'}',
        orElse: () => RiskSource.server,
      ),
      resources: (json['resources'] as List<dynamic>?)?.cast<String>(),
      crisisMsg: json['crisis_msg'] as String?,
      crisisNumbers: (json['crisis_numbers'] as List<dynamic>?)
          ?.map((item) => Map<String, dynamic>.from(item))
          .toList(),
      exercise: parsedExercise,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'content': content,
      'is_user': isUser,
      'timestamp': timestamp.toIso8601String(),
      'type': type.toString().split('.').last,
      'risk_level': riskLevel.toString().split('.').last,
      // Written so a serialize→deserialize round-trip preserves provenance.
      // Nothing calls toJson() today; that is precisely why this is here —
      // the first caller added (offline queue, draft cache) would otherwise
      // silently downgrade a keyword-stamped .crisis to .server on the way
      // back in, and the takeover gate would fire on a false positive.
      'risk_source': riskSource.toString().split('.').last,
      'resources': resources,
      'crisis_msg': crisisMsg,
      'crisis_numbers': crisisNumbers,
    };
  }

  /// Field-preserving copy, for call sites that genuinely mean "same message,
  /// one field changed".
  ///
  /// Note what this deliberately does NOT do: ChatProvider's streaming `meta`
  /// path still constructs by hand. That is not an oversight — `crisisMsg`
  /// and `crisisNumbers` are legitimately nullable there, and copyWith's
  /// null-coalescing would preserve a stale value where the caller means to
  /// clear it. copyWith is the right tool for partial updates, the wrong one
  /// for full re-specification; conflating the two would trade a dropped
  /// field for a stuck one.
  Message copyWith({
    String? id,
    String? content,
    bool? isUser,
    DateTime? timestamp,
    MessageType? type,
    RiskLevel? riskLevel,
    RiskSource? riskSource,
    List<String>? resources,
    String? crisisMsg,
    List<Map<String, dynamic>>? crisisNumbers,
    InteractiveExercise? exercise,
  }) {
    return Message(
      id: id ?? this.id,
      content: content ?? this.content,
      isUser: isUser ?? this.isUser,
      timestamp: timestamp ?? this.timestamp,
      type: type ?? this.type,
      riskLevel: riskLevel ?? this.riskLevel,
      riskSource: riskSource ?? this.riskSource,
      resources: resources ?? this.resources,
      crisisMsg: crisisMsg ?? this.crisisMsg,
      crisisNumbers: crisisNumbers ?? this.crisisNumbers,
      exercise: exercise ?? this.exercise,
    );
  }

  Color getMessageColor(BuildContext context) {
    if (type == MessageType.error) {
      return Theme.of(context).colorScheme.error;
    }
    if (type == MessageType.system) {
      return Theme.of(context).colorScheme.surfaceContainerHighest;
    }
    return isUser
        ? Theme.of(context).colorScheme.primary
        : Theme.of(context).colorScheme.secondaryContainer;
  }

  Color getTextColor(BuildContext context) {
    if (type == MessageType.error) {
      return Theme.of(context).colorScheme.onError;
    }
    if (type == MessageType.system) {
      return Theme.of(context).colorScheme.onSurfaceVariant;
    }
    return isUser
        ? Theme.of(context).colorScheme.onPrimary
        : Theme.of(context).colorScheme.onSecondaryContainer;
  }
}
