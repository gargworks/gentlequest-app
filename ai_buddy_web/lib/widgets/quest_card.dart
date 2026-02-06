import 'package:flutter/material.dart';
import '../models/quest.dart';

class QuestCard extends StatelessWidget {
  final Quest quest;
  final VoidCallback onTap;
  final bool isLoading;

  const QuestCard({
    super.key,
    required this.quest,
    required this.onTap,
    this.isLoading = false,
  });

  Color _getDifficultyColor() {
    switch (quest.difficulty) {
      case 1:
        return Colors.green.shade100;
      case 2:
        return Colors.orange.shade100;
      case 3:
        return Colors.red.shade100;
      default:
        return Colors.grey.shade100;
    }
  }

  IconData _getTypeIcon() {
    switch (quest.type) {
      case 'task':
        return Icons.check_circle_outline;
      case 'tip':
        return Icons.lightbulb_outline;
      case 'check_in':
        return Icons.assignment_turned_in_outlined;
      case 'progress':
        return Icons.trending_up;
      case 'social':
        return Icons.people_outline;
      case 'learning':
        return Icons.school_outlined;
      case 'challenge':
        return Icons.emoji_events_outlined;
      case 'mindfulness':
        return Icons.self_improvement;
      case 'activity':
        return Icons.directions_walk;
      default:
        return Icons.star_border;
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool isCompleted = quest.isCompleted;

    return Card(
      elevation: isCompleted ? 0 : 2,
      color: isCompleted ? Colors.grey.shade50 : Colors.white,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isCompleted
            ? BorderSide(color: Colors.grey.shade300)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: isCompleted ? null : onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              // Left: Icon container
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: isCompleted
                      ? Colors.grey.shade200
                      : _getDifficultyColor(),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  isCompleted ? Icons.check : _getTypeIcon(),
                  color: isCompleted ? Colors.grey : Colors.black87,
                ),
              ),
              const SizedBox(width: 16),

              // Middle: Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      quest.title,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        decoration:
                            isCompleted ? TextDecoration.lineThrough : null,
                        color: isCompleted ? Colors.grey : Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      quest.description,
                      style: TextStyle(
                        fontSize: 14,
                        color: isCompleted
                            ? Colors.grey.shade400
                            : Colors.grey.shade600,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),

              // Right: Rewards or Loading
              if (isLoading)
                const Padding(
                  padding: EdgeInsets.only(left: 8.0),
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                )
              else if (!isCompleted)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.purple.shade50,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.purple.shade100),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.bolt, size: 14, color: Colors.purple),
                      const SizedBox(width: 4),
                      Text(
                        "${quest.xpReward} XP",
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Colors.purple.shade700,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
