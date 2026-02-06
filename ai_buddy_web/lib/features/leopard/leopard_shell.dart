import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // Added for Clipboard/Haptics
import 'package:ai_buddy_web/features/leopard/quest_engine/metaphor_mapper.dart';
import 'package:ai_buddy_web/features/leopard/models/leopard_quest.dart';
import 'package:ai_buddy_web/features/leopard/widgets/quest_card.dart';
import 'package:ai_buddy_web/services/firebase_service.dart';
import 'package:confetti/confetti.dart';

class LeopardShell extends StatefulWidget {
  const LeopardShell({super.key});

  @override
  State<LeopardShell> createState() => _LeopardShellState();
}

class _LeopardShellState extends State<LeopardShell> {
  int _selectedIndex = 0;
  final TextEditingController _stressController = TextEditingController();
  final MetaphorMapper _mapper = MetaphorMapper();
  final FirebaseService _firebase = FirebaseService();
  late ConfettiController _confettiController;

  LeopardQuest? _currentQuest;
  bool _isGenerating = false;

  @override
  void initState() {
    super.initState();
    _confettiController =
        ConfettiController(duration: const Duration(seconds: 2));
  }

  @override
  void dispose() {
    _confettiController.dispose();
    _stressController.dispose();
    super.dispose();
  }

  void _generateQuest() async {
    if (_stressController.text.isEmpty) return;

    setState(() {
      _isGenerating = true;
      _currentQuest = null;
    });

    // Simulate the "Metaphor Mapping" process
    final quest = await _mapper.generateQuest(_stressController.text);

    if (mounted) {
      setState(() {
        _isGenerating = false;
        _currentQuest = quest;
      });

      _firebase.logEvent('leopard_quest_generated', {
        'boss_name': quest.bossName,
        'xp_reward': quest.xpReward,
      });
    }
  }

  void _onQuestCompleted() {
    // VICTORY LOOP
    _confettiController.play();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("QUEST COMPLETE! +${_currentQuest?.xpReward ?? 0} XP"),
        backgroundColor: Colors.amber[700],
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _reset() {
    setState(() {
      _currentQuest = null;
      _stressController.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121212), // Dark Mode "Gym" Vibe
      appBar: AppBar(
        title: const Text("GentleQuest // LEOPARD",
            style: TextStyle(color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.orange),
            onPressed: _reset,
            tooltip: "Reset Simulation",
          )
        ],
      ),
      body: Stack(
        children: [
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_currentQuest == null && !_isGenerating) ...[
                    // INPUT STATE
                    const Icon(Icons.fitness_center,
                        size: 64, color: Color(0xFF667EEA)),
                    const SizedBox(height: 20),
                    Text(
                      "What is the threat vector?",
                      style:
                          Theme.of(context).textTheme.headlineSmall?.copyWith(
                                color: Colors.white70,
                                fontFamily: 'Inter',
                              ),
                    ),
                    const SizedBox(height: 20),
                    TextField(
                      controller: _stressController,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        hintText: "e.g. 'My boss is overwhelming me'",
                        hintStyle:
                            TextStyle(color: Colors.white.withValues(alpha: 0.3)),
                        filled: true,
                        fillColor: Colors.white.withValues(alpha: 0.05),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: _generateQuest,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF667EEA),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 32, vertical: 16),
                      ),
                      child: const Text("GENERATE PROTOCOL",
                          style: TextStyle(color: Colors.white)),
                    ),
                  ],
                  if (_isGenerating) ...[
                    // LOADING STATE (The Matrix Reveal Placeholder)
                    const CircularProgressIndicator(color: Color(0xFF667EEA)),
                    const SizedBox(height: 20),
                    const Text(
                      "ANALYZING STRESS VECTORS...",
                      style: TextStyle(
                          color: Color(0xFF667EEA),
                          letterSpacing: 2.0,
                          fontWeight: FontWeight.bold),
                    ),
                  ],
                  if (_currentQuest != null) ...[
                    // RESULT STATE (The Final Animated Card)
                    QuestCard(
                      quest: _currentQuest!,
                      onCompleted: _onQuestCompleted,
                      onShare: () => _onShareQuest(_currentQuest!),
                    ),
                  ]
                ],
              ),
            ),
          ),

          // CONFETTI OVERLAY
          Align(
            alignment: Alignment.topCenter,
            child: ConfettiWidget(
              confettiController: _confettiController,
              blastDirectionality: BlastDirectionality.explosive,
              shouldLoop: false,
              colors: const [
                Colors.green,
                Colors.blue,
                Colors.pink,
                Colors.orange,
                Colors.purple
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: const Color(0xFF1E1E1E),
        selectedItemColor: const Color(0xFF667EEA),
        unselectedItemColor: Colors.grey,
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.shield), label: 'Training'),
          BottomNavigationBarItem(icon: Icon(Icons.book), label: 'Codex'),
        ],
      ),
    );
  }

  void _onShareQuest(LeopardQuest quest) {
    _firebase.logEvent('leopard_quest_shared', {
      'quest_title': quest.title,
      'xp_reward': quest.xpReward,
    });

    final story = _mapper.aiService.generateSuccessStory(quest);
    Clipboard.setData(ClipboardData(text: story)).then((_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Protocol victory copied to clipboard! 🛡️"),
            backgroundColor: Color(0xFF667EEA),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    });
  }
}

// _Badge was unused and removed to resolve lint.
