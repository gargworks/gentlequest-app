class LeopardQuest {
  final String id;
  final String title; // e.g. "Protocol: Iron Shield"
  final String
      narrative; // "The Voice of Authority attacks. Defend the perimeter."
  final String bossName; // "The Voice of Authority"
  final String heroArchetype; // "Stoic Defender"
  final int xpReward; // 150
  final List<QuestStep> steps;

  LeopardQuest({
    required this.id,
    required this.title,
    required this.narrative,
    required this.bossName,
    required this.heroArchetype,
    required this.xpReward,
    required this.steps,
  });

  factory LeopardQuest.fromJson(Map<String, dynamic> json) {
    return LeopardQuest(
      id: json['id'] as String? ?? 'unknown_id',
      title: json['title'] as String? ?? 'Unknown Protocol',
      narrative: json['narrative'] as String? ?? '',
      bossName: json['bossName'] as String? ?? 'Unknown Entity',
      heroArchetype: json['heroArchetype'] as String? ?? 'Survivor',
      xpReward: json['xpReward'] as int? ?? 0,
      steps: (json['steps'] as List<dynamic>?)
              ?.map((e) => QuestStep.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class QuestStep {
  final String id;
  final String title; // "Armor Up"
  final String instruction; // "Stand tall. Signal strength."
  final String type; // "Physical", "Cognitive", "Social"
  bool isCompleted;

  QuestStep({
    required this.id,
    required this.title,
    required this.instruction,
    required this.type,
    this.isCompleted = false,
  });

  factory QuestStep.fromJson(Map<String, dynamic> json) {
    return QuestStep(
      id: json['id'] as String? ?? 'step_0',
      title: json['title'] as String? ?? 'Action',
      instruction: json['instruction'] as String? ?? '',
      type: json['type'] as String? ?? 'Physical',
      isCompleted: false,
    );
  }
}
