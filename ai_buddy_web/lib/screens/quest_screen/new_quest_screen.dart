import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:ai_buddy_web/providers/quest_provider.dart';
import 'package:ai_buddy_web/widgets/quest_card.dart';

class NewQuestScreen extends StatelessWidget {
  const NewQuestScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC), // Light, clean background
      body: Consumer<QuestProvider>(
        builder: (context, questProvider, _) {
          if (questProvider.isLoading && questProvider.quests.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          final activeQuests = questProvider.quests
              .where((q) => q.status == QuestStatus.inProgress)
              .toList();
          final availableQuests = questProvider.quests
              .where((q) => q.status == QuestStatus.unlocked)
              .toList();
          final completedQuests = questProvider.quests
              .where((q) => q.status == QuestStatus.completed)
              .toList();

          return RefreshIndicator(
            onRefresh: () => questProvider.loadQuests(),
            child: CustomScrollView(
              slivers: [
                _buildSliverAppBar(context, questProvider),
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (activeQuests.isNotEmpty) ...[
                          _buildSectionHeader(
                              'In Progress', activeQuests.length),
                          const SizedBox(height: 12),
                          ...activeQuests.map((q) => Padding(
                                padding: const EdgeInsets.only(bottom: 12.0),
                                child: QuestCard.fromQuest(
                                  q,
                                  onTap: () => _handleQuestTap(context, q),
                                ),
                              )),
                          const SizedBox(height: 24),
                        ],
                        if (availableQuests.isNotEmpty) ...[
                          _buildSectionHeader(
                              'Available Quests', availableQuests.length),
                          const SizedBox(height: 12),
                          ...availableQuests.map((q) => Padding(
                                padding: const EdgeInsets.only(bottom: 12.0),
                                child: QuestCard.fromQuest(
                                  q,
                                  onTap: () => _handleQuestTap(context, q),
                                ),
                              )),
                          const SizedBox(height: 24),
                        ],
                        if (completedQuests.isNotEmpty) ...[
                          _buildSectionHeader(
                              'Recently Completed', completedQuests.length),
                          const SizedBox(height: 12),
                          ...completedQuests.map((q) => Padding(
                                padding: const EdgeInsets.only(bottom: 12.0),
                                child: Opacity(
                                  opacity: 0.8,
                                  child: QuestCard.fromQuest(
                                    q,
                                    onTap: () => _handleQuestTap(context, q),
                                  ),
                                ),
                              )),
                        ],
                        if (questProvider.quests.isEmpty)
                          _buildEmptyState(theme),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSliverAppBar(BuildContext context, QuestProvider provider) {
    final theme = Theme.of(context);
    final progress = (provider.totalXP % 100) /
        100.0; // Assume 100 XP per level for simple UI

    return SliverAppBar(
      expandedHeight: 180.0,
      floating: false,
      pinned: true,
      elevation: 0,
      backgroundColor: theme.colorScheme.primary,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                theme.colorScheme.primary,
                theme.colorScheme.primary.withValues(alpha: 0.8),
              ],
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),
                  Text(
                    'Level ${provider.level}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(10),
                          child: LinearProgressIndicator(
                            value: progress,
                            backgroundColor:
                                Colors.white.withValues(alpha: 0.3),
                            valueColor: const AlwaysStoppedAnimation<Color>(
                                Colors.white),
                            minHeight: 10,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        '${provider.totalXP} XP',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${(100 - (provider.totalXP % 100)).toInt()} XP to next level',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.8),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        title: const Text('Your Quests',
            style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: false,
      ),
    );
  }

  Widget _buildSectionHeader(String title, int count) {
    return Row(
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1E293B),
          ),
        ),
        const Spacer(),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: const Color(0xFFE2E8F0),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            count.toString(),
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Color(0xFF64748B),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(height: 100),
          Icon(Icons.auto_awesome,
              size: 64,
              color: theme.colorScheme.primary.withValues(alpha: 0.2)),
          const SizedBox(height: 16),
          const Text(
            'No quests found for this week',
            style: TextStyle(fontSize: 16, color: Colors.grey),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () {}, // Trigger reseed or check back later
            child: const Text('Refresh'),
          ),
        ],
      ),
    );
  }

  void _handleQuestTap(BuildContext context, Quest quest) {
    if (quest.status == QuestStatus.completed) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Quest already completed! Great job!')),
      );
      return;
    }

    // Show a simple confirmation or detail sheet
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(quest.title,
                style:
                    const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Text(quest.description,
                style: const TextStyle(fontSize: 16, color: Colors.blackDE)),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.fromSeed(
                    seedColor: Theme.of(context).primaryColor),
                onPressed: () {
                  // Simulate progress or mark complete
                  context
                      .read<QuestProvider>()
                      .updateQuestProgress(quest.id, quest.target);
                  Navigator.pop(context);
                },
                child: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Text('Complete Quest', style: TextStyle(fontSize: 16)),
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}
