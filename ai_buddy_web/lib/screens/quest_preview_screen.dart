import 'package:flutter/material.dart';

import '../theme/gq_tokens.dart';
import '../widgets/app_back_button.dart';

class QuestPreviewScreen extends StatelessWidget {
  const QuestPreviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Quest Screen Preview'),
        automaticallyImplyLeading: false,
        leading: Builder(
          builder: (ctx) {
            final canPop = Navigator.of(ctx).canPop();
            final route = ModalRoute.of(ctx);
            final isModal =
                route is PageRoute && route.fullscreenDialog == true;
            if (canPop) {
              return AppBackButton(isModal: isModal);
            }
            return const SizedBox.shrink();
          },
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildQuestCard(
              context: context,
              title: 'Daily Check-in',
              description: 'Complete your daily mood check-in',
              progress: 0.3,
              icon: Icons.check_circle,
              color: GQColors.primary,
            ),
            const SizedBox(height: 16),
            _buildQuestCard(
              context: context,
              title: 'Meditation Challenge',
              description: 'Meditate for 5 minutes',
              progress: 0.7,
              icon: Icons.self_improvement,
              color: GQColors.moodGreat,
            ),
            const SizedBox(height: 16),
            _buildQuestCard(
              context: context,
              title: 'Gratitude Journal',
              description: 'Write 3 things you\'re grateful for',
              progress: 0.0,
              icon: Icons.book,
              color: GQColors.moodGood,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestCard({
    required BuildContext context,
    required String title,
    required String description,
    required double progress,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: color, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: const TextStyle(
                          fontSize: 14,
                          color: GQColors.ink3,
                        ),
                      ),
                    ],
                  ),
                ),
                ElevatedButton(
                  key: const ValueKey('quest_preview_start_button'),
                  onPressed: () {
                    if (Navigator.of(context).canPop()) {
                      Navigator.of(context).pop();
                    } else {
                      Navigator.of(context).pushNamedAndRemoveUntil(
                        '/home',
                        (route) => false,
                      );
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: color,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                  child: Text(progress > 0 ? 'Continue' : 'Start'),
                ),
              ],
            ),
            if (progress > 0) ...[
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value: progress,
                backgroundColor: GQColors.hair,
                valueColor: AlwaysStoppedAnimation<Color>(color),
                minHeight: 8,
                borderRadius: BorderRadius.circular(4),
              ),
              const SizedBox(height: 4),
              Text(
                '${(progress * 100).toInt()}% complete',
                style: const TextStyle(
                  fontSize: 12,
                  color: GQColors.ink3,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
