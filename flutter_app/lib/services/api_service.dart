import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/iip_models.dart';

final apiServiceProvider = Provider((ref) => ApiService());

class ApiService {
  // Use 10.0.2.2 for Android Emulator, localhost for iOS/Web
  // For simplicity regarding the user's setup (mac), we default to localhost
  // Platform-agnostic Base URL (configurable via --dart-define=BASE_URL=...)
  // Defaults to localhost:8000 as per README
  static const String baseUrl = String.fromEnvironment('BASE_URL', defaultValue: 'http://localhost:8000/api/v1');

  Future<List<Team>> getTeams() async {
    final response = await http.get(Uri.parse('$baseUrl/teams'));
    if (response.statusCode == 200) {
      final List<dynamic> body = jsonDecode(response.body);
      return body.map((e) => Team.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load teams');
    }
  }

  Future<Team> createTeam(Team team) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(team.toJson()),
    );
    if (response.statusCode == 200 || response.statusCode == 201) { // Support 201 as expected
      return Team.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to create team: ${response.statusCode}');
    }
  }

  Future<List<Interview>> getInterviews(int teamId) async {
    final response = await http.get(Uri.parse('$baseUrl/teams/$teamId/interviews'));
    if (response.statusCode == 200) {
      final List<dynamic> body = jsonDecode(response.body);
      return body.map((e) => Interview.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load interviews');
    }
  }

  Future<Interview> createInterview(Interview interview) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams/${interview.teamId}/interviews'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(interview.toJson()),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return Interview.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to create interview: ${response.statusCode}');
    }
  }

  Future<void> analyzeInterview(int teamId, int interviewId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams/$teamId/interviews/$interviewId/analyze'),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to analyze interview');
    }
  }

  // --- Personas ---

  Future<List<Persona>> getPersonas(int teamId) async {
    final response = await http.get((Uri.parse('$baseUrl/teams/$teamId/personas')));
    if (response.statusCode == 200) {
      final List<dynamic> body = jsonDecode(response.body);
      return body.map((e) => Persona.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load personas');
    }
  }

  Future<Persona> createPersona(Persona persona) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams/${persona.teamId}/personas'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(persona.toJson()),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return Persona.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to create persona: ${response.statusCode}');
    }
  }

  Future<List<Persona>> generatePersonas(int teamId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams/$teamId/personas/generate'),
    ).timeout(const Duration(seconds: 120));
    if (response.statusCode == 200 || response.statusCode == 201) {
      final List<dynamic> body = jsonDecode(response.body);
      return body.map((e) => Persona.fromJson(e)).toList();
    } else {
      throw Exception('Failed to generate personas: ${response.statusCode}');
    }
  }

  // CVP Canvas Implementation
  Future<CVPCanvas?> getCVPCanvas(int teamId) async {
    final response = await http.get(Uri.parse('$baseUrl/teams/$teamId/cvp'));
    if (response.statusCode == 200) {
      return CVPCanvas.fromJson(jsonDecode(response.body));
    } else if (response.statusCode == 404) {
      return null; // 404 handled gracefully
    } else {
      throw Exception('Failed to load CVP Canvas: ${response.statusCode}');
    }
  }

  Future<CVPCanvas> createCVPCanvas(int teamId, CVPCanvas canvas) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams/$teamId/cvp'),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(canvas.toJson()),
    );
    if (response.statusCode == 201 || response.statusCode == 200) {
      return CVPCanvas.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to save CVP Canvas: ${response.statusCode}');
    }
  }

  Future<CVPCanvas> generateCVPCanvas(int teamId) async {
    final response = await http.post(Uri.parse('$baseUrl/teams/$teamId/cvp/generate'))
        .timeout(const Duration(seconds: 120));
    if (response.statusCode == 200 || response.statusCode == 201) {
      return CVPCanvas.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to generate CVP Canvas: ${response.statusCode}');
    }
  }

  // MVP Roadmap Implementation
  Future<MVPRoadmap?> getRoadmap(int teamId) async {
    final response = await http.get(Uri.parse('$baseUrl/teams/$teamId/roadmap'));
    if (response.statusCode == 200) {
      return MVPRoadmap.fromJson(jsonDecode(response.body));
    } else if (response.statusCode == 404) {
      return null;
    } else {
      throw Exception('Failed to load MVP Roadmap: ${response.statusCode}');
    }
  }

  Future<MVPRoadmap> generateRoadmap(int teamId) async {
    final response = await http.post(Uri.parse('$baseUrl/teams/$teamId/roadmap/generate'))
        .timeout(const Duration(seconds: 120));
    if (response.statusCode == 200 || response.statusCode == 201) {
      return MVPRoadmap.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to generate MVP Roadmap: ${response.statusCode}');
    }
  }

  // Project Tasks Implementation
  Future<List<ProjectTask>> getTasks(int teamId) async {
    final response = await http.get(Uri.parse('$baseUrl/teams/$teamId/tasks'));
    if (response.statusCode == 200) {
      final List<dynamic> body = jsonDecode(response.body);
      return body.map((e) => ProjectTask.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load project tasks');
    }
  }

  Future<List<ProjectTask>> generateTasks(int teamId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams/$teamId/tasks/generate'),
    ).timeout(const Duration(seconds: 180)); // Longer timeout for task breakdown
    if (response.statusCode == 200 || response.statusCode == 201) {
      final List<dynamic> body = jsonDecode(response.body);
      return body.map((e) => ProjectTask.fromJson(e)).toList();
    } else {
      throw Exception('Failed to generate project tasks: ${response.statusCode}');
    }
  }

  Future<ProjectTask> updateTaskStatus(int taskId, String status) async {
    final response = await http.put(
      Uri.parse('$baseUrl/tasks/$taskId?status=$status'),
    );
     if (response.statusCode == 200) {
      return ProjectTask.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to update task status: ${response.statusCode}');
    }
  }

  // --- Interaction / Chat ---
  Future<InterviewSession> startChatSession(int teamId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams/$teamId/chat/start'),
    );
     if (response.statusCode == 200) {
      return InterviewSession.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to start chat session: ${response.statusCode}');
    }
  }

  Future<ChatMessage> sendChatMessage(int sessionId, String content) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat/$sessionId/message'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({"content": content}),
    );
    if (response.statusCode == 200) {
      return ChatMessage.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to send message: ${response.statusCode}');
    }
  }

  Future<Interview> finalizeChatSession(int sessionId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat/$sessionId/finalize'),
    );
     if (response.statusCode == 200) {
      return Interview.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to finalize chat session: ${response.statusCode}');
    }
  }

  // --- Project Chat (RAG) ---
  Future<ProjectChatSession> startProjectChat(int teamId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/teams/$teamId/project-chat/start'), // Updated URL
    );
     if (response.statusCode == 200) {
      return ProjectChatSession.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to start project chat session: ${response.statusCode}');
    }
  }

  Future<ChatMessage> sendProjectChatMessage(int projectId, int sessionId, String content) async {
    final response = await http.post(
      Uri.parse('$baseUrl/projects/$projectId/chat/$sessionId/message'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({"content": content}),
    );
    if (response.statusCode == 200) {
      return ChatMessage.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to send project message: ${response.statusCode}');
    }
  }

  // --- Nucleus Delegation ---
  Future<void> delegateTask(int taskId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/tasks/$taskId/delegate'),
    );
     if (response.statusCode != 200) {
      throw Exception('Failed to delegate task: ${response.statusCode}');
    }
  }

  // --- Generic REST Methods ---
  Future<dynamic> get(String path, {Map<String, String>? params}) async {
    final uri = Uri.parse('$baseUrl$path').replace(queryParameters: params);
    final response = await http.get(uri);
    return _handleResponse(response);
  }

  Future<dynamic> post(String path, {dynamic body}) async {
    final response = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: body != null ? jsonEncode(body) : null,
    );
    return _handleResponse(response);
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return null;
      return jsonDecode(response.body);
    } else {
      throw Exception('API Error (${response.statusCode}): ${response.body}');
    }
  }
}




