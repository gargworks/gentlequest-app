import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/features/leopard/models/leopard_quest.dart';
import 'package:ai_buddy_web/features/leopard/data/leopard_system_prompt.dart';

void main() {
  group('Leopard AI Logic Tests', () {
    test('LeopardQuest.fromJson parses valid JSON correctly', () {
      final jsonString = '''
      {
        "id": "q_123",
        "title": "PROTOCOL: TEST SHIELD",
        "narrative": "A test entity approaches.",
        "bossName": "The Tester",
        "heroArchetype": "QA Engineer",
        "xpReward": 200,
        "steps": [
          {
            "id": "s1",
            "title": "Run Test",
            "instruction": "Execute the script.",
            "type": "Cognitive"
          }
        ]
      }
      ''';

      final Map<String, dynamic> jsonMap = jsonDecode(jsonString);
      final quest = LeopardQuest.fromJson(jsonMap);

      expect(quest.id, 'q_123');
      expect(quest.title, 'PROTOCOL: TEST SHIELD');
      expect(quest.steps.length, 1);
      expect(quest.steps.first.title, 'Run Test');
    });

    test('LeopardQuest.fromJson handles missing fields gracefully', () {
      final jsonString = '{}';
      final Map<String, dynamic> jsonMap = jsonDecode(jsonString);
      final quest = LeopardQuest.fromJson(jsonMap);

      expect(quest.id, 'unknown_id');
      expect(quest.xpReward, 0);
      expect(quest.steps, isEmpty);
    });

    test('System Prompt contains required JSON schema instruction', () {
      expect(LeopardSystemPrompt.prompt.contains('OUTPUT:'), true);
      expect(LeopardSystemPrompt.prompt.contains('ONLY valid JSON'), true);
    });
  });
}
