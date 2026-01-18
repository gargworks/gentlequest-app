class Quest {
  final int id;
  final String title;
  final String description;
  final String type; // 'task', 'tip', 'check_in', 'progress'
  final int xpReward;
  final int difficulty;
  final String status; // 'available', 'completed'
  final int target; // e.g. 10 minutes
  final int progress; // current progress

  Quest({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.xpReward,
    required this.difficulty,
    required this.status,
    this.target = 1,
    this.progress = 0,
  });

  factory Quest.fromJson(Map<String, dynamic> json) {
    return Quest(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      type: json['type'] ?? 'task',
      xpReward: json['xp_reward'] ?? 10,
      difficulty: json['difficulty'] ?? 1,
      status: json['status'] ?? 'available',
      target: json['target'] ?? 1,
      progress: json['progress'] ?? 0,
    );
  }

  bool get isCompleted => status == 'completed';
}
