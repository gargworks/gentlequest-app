import 'package:ai_buddy_web/features/leopard/models/leopard_quest.dart';
import 'package:ai_buddy_web/features/leopard/services/leopard_ai_service.dart';
import '../../../../services/api_service.dart';

class MetaphorMapper {
  final LeopardAiService _aiService;

  // Dependency Injection (Defaulting to a fresh instance for the prototype)
  MetaphorMapper({ApiService? apiService})
      : _aiService = LeopardAiService(apiService ?? ApiService());

  LeopardAiService get aiService => _aiService;

  Future<LeopardQuest> generateQuest(String stressInput) async {
    // We keep a small delay for the "Matrix Reveal" dramatic effect,
    // but the real latency comes from the API call itself.

    // Call the AI
    return await _aiService.generateQuestFromStress(stressInput);
  }
}
