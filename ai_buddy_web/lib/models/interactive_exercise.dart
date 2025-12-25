import 'package:flutter/foundation.dart';

enum ExerciseType { breathing, grounding, journalPrompt }

abstract class InteractiveExercise {
  final ExerciseType type;
  final String name;
  final String description;

  InteractiveExercise({
    required this.type,
    required this.name,
    required this.description,
  });

  factory InteractiveExercise.fromJson(Map<String, dynamic> json) {
    try {
      final typeStr = json['type'] as String?;
      final type = ExerciseType.values.firstWhere(
        (e) => e.toString().split('.').last == typeStr,
        orElse: () => throw FormatException('Unknown exercise type: $typeStr'),
      );

      switch (type) {
        case ExerciseType.breathing:
          return BreathingExercise.fromJson(json);
        case ExerciseType.grounding:
          return GroundingExercise.fromJson(json);
        case ExerciseType.journalPrompt:
          return JournalPrompt.fromJson(json);
      }
    } catch (e) {
      if (kDebugMode) {
        debugPrint('Error parsing InteractiveExercise: $e');
      }
      rethrow;
    }
  }
}

class BreathingStep {
  final String action; // 'breathe_in', 'hold', 'breathe_out'
  final int duration;
  final String instruction;

  BreathingStep({
    required this.action,
    required this.duration,
    required this.instruction,
  });

  factory BreathingStep.fromJson(Map<String, dynamic> json) {
    return BreathingStep(
      action: json['action'] as String,
      duration: json['duration'] as int,
      instruction: json['instruction'] as String,
    );
  }
}

class BreathingExercise extends InteractiveExercise {
  final List<BreathingStep> steps;
  final int cycles;
  final int totalTimeSeconds;

  BreathingExercise({
    required super.name,
    required super.description,
    required this.steps,
    required this.cycles,
    required this.totalTimeSeconds,
  }) : super(type: ExerciseType.breathing);

  factory BreathingExercise.fromJson(Map<String, dynamic> json) {
    return BreathingExercise(
      name: json['name'] as String? ?? 'Breathing Exercise',
      description: json['description'] as String? ?? '',
      steps: (json['steps'] as List<dynamic>?)
              ?.map((e) => BreathingStep.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      cycles: json['cycles'] as int? ?? 4,
      totalTimeSeconds: json['total_time_seconds'] as int? ?? 60,
    );
  }
}

class GroundingStep {
  final String sense; // 'sight', 'touch', 'hear', 'smell', 'taste'
  final int count; // e.g., 5, 4, 3...
  final String instruction;

  GroundingStep({
    required this.sense,
    required this.count,
    required this.instruction,
  });

  factory GroundingStep.fromJson(Map<String, dynamic> json) {
    return GroundingStep(
      sense: json['sense'] as String,
      count: json['count'] as int,
      instruction: json['instruction'] as String,
    );
  }
}

class GroundingExercise extends InteractiveExercise {
  final List<GroundingStep> steps; // Renamed from senses for consistency

  GroundingExercise({
    required super.name,
    required super.description,
    required this.steps,
  }) : super(type: ExerciseType.grounding);

  factory GroundingExercise.fromJson(Map<String, dynamic> json) {
    return GroundingExercise(
      name: json['name'] as String? ?? 'Grounding Exercise',
      description: json['description'] as String? ?? '',
      steps: (json['steps'] as List<dynamic>?)
              ?.map((e) => GroundingStep.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class JournalPrompt extends InteractiveExercise {
  final String prompt;
  final List<String>? suggestions;

  JournalPrompt({
    required super.name,
    required super.description,
    required this.prompt,
    this.suggestions,
  }) : super(type: ExerciseType.journalPrompt);

  factory JournalPrompt.fromJson(Map<String, dynamic> json) {
    return JournalPrompt(
      name: json['name'] as String? ?? 'Journal Prompt',
      description: json['description'] as String? ?? '',
      prompt: json['prompt'] as String? ?? '',
      suggestions: (json['suggestions'] as List<dynamic>?)?.cast<String>(),
    );
  }
}
