import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'dart:async';
import '../models/quest.dart';

class QuestProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  List<Quest> _quests = [];
  int _totalXP = 0;
  int _level = 1;
  bool _isLoading = false;

  List<Quest> get quests => _quests;
  int get totalXP => _totalXP;
  int get level => _level;
  bool get isLoading => _isLoading;

  // Getters for different quest categories
  List<Quest> get unlockedQuests =>
      _quests.where((q) => q.status != QuestStatus.locked).toList();
  List<Quest> get inProgressQuests =>
      _quests.where((q) => q.status == QuestStatus.inProgress).toList();
  List<Quest> get completedQuests =>
      _quests.where((q) => q.status == QuestStatus.completed).toList();

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
        }
      } else {
        // Fallback to defaults if backend fails or returns empty
        _quests = List<Quest>.from(defaultQuests);
      }

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading quests from backend: $e');
      _quests = List<Quest>.from(defaultQuests);
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> updateQuestProgress(String questId, int newProgress) async {
    final index = _quests.indexWhere((q) => q.id == questId);
    if (index == -1) return;

    final quest = _quests[index];
    final updatedProgress = newProgress.clamp(0, quest.target);
    final isCompleted = updatedProgress >= quest.target;

    // Optimistic update
    _quests[index] = quest.copyWith(
      progress: updatedProgress,
      status: isCompleted ? QuestStatus.completed : QuestStatus.inProgress,
      completedAt: isCompleted ? DateTime.now() : quest.completedAt,
    );
    notifyListeners();

    try {
      if (isCompleted) {
        final result = await _apiService.post('/api/quests/$questId/complete');
        if (result != null && result['success'] == true) {
          _totalXP = result['new_total_xp'] ?? _totalXP;
          _level = result['new_level'] ?? _level;
        }
      } else {
        // Currently backend doesn't have a dedicated partial progress endpoint for quests,
        // but it tracks status. We might want to add /api/quests/<id>/progress later.
        // For now, only completion is synced.
      }
    } catch (e) {
      debugPrint('Error updating quest on backend: $e');
      // Rollback or handle error
    }
    
    notifyListeners();
  }

  Future<void> resetQuests() async {
    // Backend doesn't have a reset yet, just re-load
    await loadQuests();
  }

  List<Quest> getQuestsByCategory(QuestCategory category) {
    return _quests.where((q) => q.category == category).toList();
  }

  Quest? getQuestById(String questId) {
    try {
      return _quests.firstWhere((q) => q.id == questId);
    } catch (e) {
      return null;
    }
  }
}
