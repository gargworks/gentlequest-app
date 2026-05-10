import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../../../../services/api_service.dart';
import '../models/leopard_quest.dart';
import '../data/leopard_system_prompt.dart';

class LeopardAiService {
  final ApiService _apiService;

  LeopardAiService(this._apiService);

  Future<LeopardQuest> generateQuestFromStress(String stressInput) async {
    try {
      // 1. Construct the Payload
      final fullPrompt = _constructPrompt(stressInput);

      // 2. Send to Gemini (via existing Chat API)
      final responseMessage = await _apiService.sendMessage(fullPrompt);
      final rawContent = responseMessage.content;

      // 3. Parse JSON
      return _parseResponse(rawContent);
    } catch (e) {
      if (kDebugMode) {
        print("🔴 LEOPARD AI ERROR: $e");
      }
      return _getFallbackQuest();
    }
  }

  String _constructPrompt(String input) {
    return '''
${LeopardSystemPrompt.prompt}

---
USER INPUT TARGET:
"$input"
''';
  }

  LeopardQuest _parseResponse(String rawContent) {
    try {
      // Aggressive cleaning of Markdown code blocks if the AI slips up
      String cleaned = rawContent
          .replaceAll(RegExp(r'```json'), '')
          .replaceAll(RegExp(r'```'), '')
          .trim();

      final Map<String, dynamic> jsonMap = jsonDecode(cleaned);
      return LeopardQuest.fromJson(jsonMap);
    } catch (e) {
      throw Exception("JSON Parse Failure: $e");
    }
  }

  LeopardQuest _getFallbackQuest() {
    return LeopardQuest(
      id: "fallback_001",
      title: "PROTOCOL: MANUAL OVERRIDE",
      narrative:
          "Communication link unstable. Defaulting to manual survival protocols. You must stabilize the system yourself.",
      bossName: "The Signal Noise",
      heroArchetype: "System Operator",
      xpReward: 50,
      steps: [
        QuestStep(
          id: "f1",
          title: "Breathe",
          instruction: "Take one deep breath. Hold for 4 seconds. Exhale.",
          type: "Physical",
        ),
        QuestStep(
          id: "f2",
          title: "Reboot",
          instruction: "Drink a glass of water to reset biological sensors.",
          type: "Physical",
        )
      ],
    );
  }

  /// Generates a "Shareable" success story for marketing (Twitter/IH)
  String generateSuccessStory(LeopardQuest quest) {
    // systemPrompt removed as it was unused and causing lint issues.
    return '''
Just defeated "${quest.bossName}" using GentleQuest // LEOPARD.
PROTOCOL: ${quest.title} complete.

No more waitlist silence. 🛡️
Join the protocol: https://gentlequest.app
''';
  }
}
