import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:math';
import 'package:confetti/confetti.dart';

import '../models/quest.dart';
import '../providers/quest_provider.dart';
import '../widgets/quest_card.dart';
import '../widgets/profile_header.dart';

class QuestScreen extends StatefulWidget {
  const QuestScreen({super.key});

  @override
  State<QuestScreen> createState() => _QuestScreenState();
}

class _QuestScreenState extends State<QuestScreen> {
  // Effects
  late ConfettiController _confettiController;

  @override
  void initState() {
    super.initState();
    _confettiController =
        ConfettiController(duration: const Duration(seconds: 3));
    // Load quests on init
    Future.microtask(() {
      if (!mounted) return;
      Provider.of<QuestProvider>(context, listen: false).loadQuests();
    });
  }

  @override
  void dispose() {
    _confettiController.dispose();
    super.dispose();
  }

  Future<void> _completeQuest(Quest quest) async {
    final provider = Provider.of<QuestProvider>(context, listen: false);

    // Confetti on every completion (celebration, not XP gate — principle #14)
    _confettiController.play();

    // Complete it!
    await provider.updateQuestProgress(quest.id, quest.target);

    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("${quest.title} complete!"),
        backgroundColor: Colors.green,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Scaffold(
          backgroundColor: Colors.grey.shade50,
          body: Consumer<QuestProvider>(
            builder: (context, questProvider, child) {
              if (questProvider.isLoading) {
                return const Center(child: CircularProgressIndicator());
              }

              return RefreshIndicator(
                onRefresh: questProvider.loadQuests,
                child: CustomScrollView(
                  slivers: [
                    // App Bar / Header
                    SliverToBoxAdapter(
                      child: ProfileHeader(
                        level: questProvider.level,
                        xp: questProvider.totalXP,
                        streakDays:
                            1, // Store doesn't have streak yet, defaulted
                      ),
                    ),

                    // Section Title
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
                        child: Text(
                          "Today's Quests",
                          style:
                              Theme.of(context).textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                        ),
                      ),
                    ),

                    // Quest List
                    SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) {
                          final quest = questProvider.quests[index];
                          return QuestCard(
                            quest: quest,
                            isLoading:
                                false, // Provider handles loading state globally mostly
                            onTap: () => _completeQuest(quest),
                          );
                        },
                        childCount: questProvider.quests.length,
                      ),
                    ),

                    // Bottom Padding
                    const SliverToBoxAdapter(child: SizedBox(height: 100)),
                  ],
                ),
              );
            },
          ),
        ),

        // Confetti Overlay
        Align(
          alignment: Alignment.topCenter,
          child: ConfettiWidget(
            confettiController: _confettiController,
            blastDirection: pi / 2,
            maxBlastForce: 5,
            minBlastForce: 2,
            emissionFrequency: 0.05,
            numberOfParticles: 50,
            gravity: 0.1,
          ),
        ),
      ],
    );
  }
}
