import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:math';
import 'package:confetti/confetti.dart';

import '../models/quest.dart';
import '../widgets/quest_card.dart';
import '../widgets/profile_header.dart';

class QuestScreen extends StatefulWidget {
  final String apiBaseUrl;
  final String sessionId;

  const QuestScreen({
    Key? key,
    required this.apiBaseUrl,
    required this.sessionId,
  }) : super(key: key);

  @override
  _QuestScreenState createState() => _QuestScreenState();
}

class _QuestScreenState extends State<QuestScreen> {
  // Model Data
  List<Quest> _quests = [];
  Map<String, dynamic> _profile = {
    "level": 1,
    "xp": 0,
    "streak_days": 1
  };
  
  // UI State
  bool _isLoading = true;
  String? _error;
  Set<int> _completingQuests = {}; // IDs of quests currently being completed

  // Effects
  late ConfettiController _confettiController;

  @override
  void initState() {
    super.initState();
    _confettiController = ConfettiController(duration: const Duration(seconds: 3));
    _fetchQuests();
  }

  @override
  void dispose() {
    _confettiController.dispose();
    super.dispose();
  }

  Future<void> _fetchQuests() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await http.get(
        Uri.parse('${widget.apiBaseUrl}/api/quests?session_id=${widget.sessionId}'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _quests = (data['quests'] as List)
              .map((q) => Quest.fromJson(q))
              .toList();
          _profile = data['profile'];
          _isLoading = false;
        });
      } else {
        throw Exception("Failed to load quests: ${response.statusCode}");
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _completeQuest(Quest quest) async {
    setState(() {
      _completingQuests.add(quest.id);
    });

    try {
      final response = await http.post(
        Uri.parse('${widget.apiBaseUrl}/api/quests/${quest.id}/complete'),
        headers: {"Content-Type": "application/json"},
        body: json.encode({"session_id": widget.sessionId}),
      );

      if (response.statusCode == 200) {
        final result = json.decode(response.body);
        
        if (result['success']) {
          // Play confetti if leveled up or just for fun on big quests
          if (result['leveled_up'] == true || quest.xpReward >= 30) {
            _confettiController.play();
          }

          // Refresh data to show new state
          await _fetchQuests();
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text("Quest Complete! +${result['xp_earned']} XP"),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        throw Exception("Failed to complete quest");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
      );
    } finally {
      setState(() {
        _completingQuests.remove(quest.id);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Scaffold(
          backgroundColor: Colors.grey.shade50,
          body: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text("Error loading quests"),
                          ElevatedButton(
                            onPressed: _fetchQuests,
                            child: const Text("Retry"),
                          )
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _fetchQuests,
                      child: CustomScrollView(
                        slivers: [
                          // App Bar / Header
                          SliverToBoxAdapter(
                            child: ProfileHeader(
                              level: _profile['level'] ?? 1,
                              xp: _profile['xp'] ?? 0,
                              streakDays: _profile['streak_days'] ?? 1,
                            ),
                          ),
                          
                          // Section Title
                          SliverToBoxAdapter(
                            child: Padding(
                              padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
                              child: Text(
                                "Today's Quests",
                                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                              ),
                            ),
                          ),

                          // Quest List
                          SliverList(
                            delegate: SliverChildBuilderDelegate(
                              (context, index) {
                                final quest = _quests[index];
                                return QuestCard(
                                  quest: quest,
                                  isLoading: _completingQuests.contains(quest.id),
                                  onTap: () => _completeQuest(quest),
                                );
                              },
                              childCount: _quests.length,
                            ),
                          ),
                          
                          // Bottom Padding
                          const SliverToBoxAdapter(child: SizedBox(height: 100)),
                        ],
                      ),
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
