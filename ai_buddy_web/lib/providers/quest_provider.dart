import 'package:flutter/material.dart';
import 'dart:async';
import '../models/quest.dart';
import '../services/api_service.dart';
import '../services/firebase_service.dart';
import '../services/notification_service.dart';

class QuestProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  List<Quest> _quests = [];
  int _totalXP = 0;
  int _level = 1;
  int _streak = 0;
  bool _isLoading = false;

  List<Quest> get quests => _quests;
  int get totalXP => _totalXP;
  int get level => _level;
  int get streak => _streak;
  bool get isLoading => _isLoading;

  // Getters for different quest categories
  List<Quest> get unlockedQuests =>
      _quests.where((q) => q.status != 'locked').toList();
  List<Quest> get inProgressQuests =>
      _quests.where((q) => q.status == 'in_progress').toList();
  List<Quest> get completedQuests =>
      _quests.where((q) => q.status == 'completed').toList();

  // Initialize
  QuestProvider() {
    loadQuests();
  }

  Future<void> loadQuests() async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiService.get('/api/quests');

      if (response != null && response['quests'] != null) {
        final List<dynamic> questsJson = response['quests'];
        _quests = questsJson.map((q) => Quest.fromJson(q)).toList();

        if (response['profile'] != null) {
          _totalXP = response['profile']['xp'] ?? 0;
          _level = response['profile']['level'] ?? 1;
          // streak_days read into _streak for data compat; not displayed
          _streak = response['profile']['streak_days'] ??
              response['profile']['streak'] ??
              0;
          // Streak milestone notifications removed — principle #14 (no-streak-shame).
          // Level-up analytics removed — principle #14.
        }
      } else {
        _quests = _generateMockQuests();
      }

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading quests from backend: $e');
      _quests = _generateMockQuests();
      _isLoading = false;
      notifyListeners();
    }
  }

  List<Quest> _generateMockQuests() {
    return [
      Quest(
        id: 101,
        title: "Morning Check-in",
        description: "Start your day with a quick mood check.",
        type: "check_in",
        xpReward: 15,
        difficulty: 1,
        status: "available",
        target: 1,
      ),
      Quest(
        id: 102,
        title: "Study Sprint",
        description: "Focus on your studies for 25 minutes.",
        type: "task",
        xpReward: 25,
        difficulty: 2,
        status: "available",
        target: 1,
      ),
      Quest(
        id: 201,
        title: "Calm Music",
        description: "Listen to 5 minutes of calming audio.",
        type: "resource",
        xpReward: 15,
        difficulty: 1,
        status: "available",
        target: 1,
      ),
      Quest(
        id: 301,
        title: "CBT Basics",
        description: "Learn about Cognitive Behavioral Therapy.",
        type: "tip",
        xpReward: 10,
        difficulty: 1,
        status: "available",
        target: 1,
      ),
      // --- Expanded Mocks for Explore Tab ---
      Quest(
        id: 401,
        title: "Box Breathing",
        description: "Inhale 4s, hold 4s, exhale 4s, hold 4s.",
        type: "mindfulness",
        xpReward: 25,
        difficulty: 1,
        status: "available",
        target: 1,
      ),
      Quest(
        id: 402,
        title: "Nature Walk",
        description: "Take a 15-min walk outside without phone.",
        type: "activity",
        xpReward: 25,
        difficulty: 2,
        status: "available",
        target: 1,
      ),
      Quest(
        id: 403,
        title: "Phone a Friend",
        description: "Call someone you care about just to say hi.",
        type: "social",
        xpReward: 25,
        difficulty: 2,
        status: "available",
        target: 1,
      ),
      Quest(
        id: 404,
        title: "Cognitive Distortions",
        description: "Identify one unhelpful thought pattern.",
        type: "learning",
        xpReward: 30,
        difficulty: 3,
        status: "available",
        target: 1,
      ),
      Quest(
        id: 405,
        title: "Weekly Reflection",
        description: "Review your mood trends for the week.",
        type: "progress",
        xpReward: 35,
        difficulty: 2,
        status: "available",
        target: 1,
      ),
      Quest(
        id: 406,
        title: "No-Sugar Challenge",
        description: "Avoid added sugar for one whole day.",
        type: "challenge",
        xpReward: 50,
        difficulty: 3,
        status: "available",
        target: 1,
      ),
    ];
  }

  Future<void> updateQuestProgress(int questId, int newProgress) async {
    final index = _quests.indexWhere((q) => q.id == questId);
    if (index == -1) return;

    final quest = _quests[index];
    final updatedProgress = newProgress.clamp(0, quest.target);
    final isCompleted = updatedProgress >= quest.target;

    // Optimistic update - Recreating object since no copyWith
    _quests[index] = Quest(
      id: quest.id,
      title: quest.title,
      description: quest.description,
      type: quest.type,
      xpReward: quest.xpReward,
      difficulty: quest.difficulty,
      status: isCompleted ? 'completed' : 'in_progress',
      target: quest.target,
      progress: updatedProgress,
    );
    notifyListeners();

    try {
      final result = await _apiService.post(
        '/api/quests/$questId/complete',
        data: {'progress': newProgress},
      );
      if (result != null && result['success'] == true) {
        _totalXP = result['new_total_xp'] ?? _totalXP;
        _level = result['new_level'] ?? _level;

        // Quest completion analytics (XP value removed from notification body — principle #14)
        if (isCompleted) {
          FirebaseService().logEvent('quest_completed', {
            'quest_id': questId,
          });
          try {
            NotificationService.scheduleOneShot(
              target: DateTime.now().add(const Duration(seconds: 3)),
              title: 'Quest complete!',
              body: '${quest.title} done',
              payload: 'open_quest',
              debugTag: 'quest_complete_$questId',
            );
          } catch (_) {}
        }
      }
    } catch (e) {
      debugPrint('Error updating quest on backend: $e');
    }

    notifyListeners();
  }

  Future<void> resetQuests() async {
    await loadQuests();
  }

  List<Quest> getQuestsByType(String type) {
    return _quests.where((q) => q.type == type).toList();
  }

  Quest? getQuestById(dynamic id) {
    if (id == null) return null;
    final int? targetId = id is int ? id : int.tryParse(id.toString());
    if (targetId == null) return null;
    try {
      return _quests.firstWhere((q) => q.id == targetId);
    } catch (_) {
      return null;
    }
  }
}
