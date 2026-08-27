import 'package:json_annotation/json_annotation.dart';

part 'iip_models.g.dart';

@JsonSerializable()
class Team {
  @JsonKey(name: 'teamid')
  final int? teamId;
  @JsonKey(name: 'teamname')
  final String teamName;
  @JsonKey(name: 'projectfocus')
  final String projectFocus;

  Team({this.teamId, required this.teamName, required this.projectFocus});

  factory Team.fromJson(Map<String, dynamic> json) => _$TeamFromJson(json);
  Map<String, dynamic> toJson() => _$TeamToJson(this);
}

@JsonSerializable()
class Insight {
  final String category; // A, N, R, U, M
  final String insight;
  final String quote;

  Insight({required this.category, required this.insight, required this.quote});

  factory Insight.fromJson(Map<String, dynamic> json) => _$InsightFromJson(json);
  Map<String, dynamic> toJson() => _$InsightToJson(this);
}

@JsonSerializable()
class Interview {
  @JsonKey(name: 'interviewid')
  final int? interviewId;
  @JsonKey(name: 'teamid')
  final int teamId;
  @JsonKey(name: 'interviewdate')
  final DateTime interviewDate;
  @JsonKey(name: 'participantrole')
  final String participantRole;
  @JsonKey(name: 'interviewnotes')
  final String interviewNotes;
  @JsonKey(name: 'insightsextracted', defaultValue: [])
  final List<Insight> insightsExtracted;

  Interview({
    this.interviewId,
    required this.teamId,
    required this.interviewDate,
    required this.participantRole,
    required this.interviewNotes,
    required this.insightsExtracted,
  });

  factory Interview.fromJson(Map<String, dynamic> json) => _$InterviewFromJson(json);
  Map<String, dynamic> toJson() => _$InterviewToJson(this);
}

@JsonSerializable()
class Persona {
  @JsonKey(name: 'personaid')
  final int? personaId;
  @JsonKey(name: 'teamid')
  final int teamId;
  @JsonKey(name: 'name')
  final String name;
  @JsonKey(name: 'age')
  final int? age;
  @JsonKey(name: 'context')
  final String? context;
  @JsonKey(name: 'goals', defaultValue: [])
  final List<String> goals;
  @JsonKey(name: 'frustrations', defaultValue: [])
  final List<String> frustrations;
  @JsonKey(name: 'supportingquotes', defaultValue: [])
  final List<String> supportingQuotes;
  
  // Extension: Traceability
  @JsonKey(name: 'supportinginterviewids', defaultValue: [])
  final List<int> supportingInterviewIds;

  Persona({
    this.personaId,
    required this.teamId,
    required this.name,
    this.age,
    this.context,
    required this.goals,
    required this.frustrations,
    required this.supportingQuotes,
    required this.supportingInterviewIds,
  });

  factory Persona.fromJson(Map<String, dynamic> json) => _$PersonaFromJson(json);
  Map<String, dynamic> toJson() => _$PersonaToJson(this);
}

@JsonSerializable()
class CVPCanvas {
  @JsonKey(name: 'cvpid')
  final int? cvpId;
  @JsonKey(name: 'teamid')
  final int teamId;
  @JsonKey(name: 'customersegment')
  final String customerSegment;
  @JsonKey(name: 'jobstobedone')
  final dynamic jobsToBeDone; // Can be String or List<String>
  @JsonKey(name: 'valueproposition')
  final String valueProposition;
  @JsonKey(name: 'pains', defaultValue: [])
  final List<String> pains;
  @JsonKey(name: 'gains', defaultValue: [])
  final List<String> gains;
  @JsonKey(name: 'painrelievers', defaultValue: [])
  final List<String> painRelievers;
  @JsonKey(name: 'gaincreators', defaultValue: [])
  final List<String> gainCreators;
  @JsonKey(name: 'competitivepositioning')
  final String competitivePositioning;
  @JsonKey(name: 'lastupdated')
  final DateTime? lastUpdated;

  CVPCanvas({
    this.cvpId,
    required this.teamId,
    required this.customerSegment,
    required this.jobsToBeDone,
    required this.valueProposition,
    required this.pains,
    required this.gains,
    required this.painRelievers,
    required this.gainCreators,
    required this.competitivePositioning,
    this.lastUpdated,
  });

  factory CVPCanvas.fromJson(Map<String, dynamic> json) {
    // Helper to safely extract String (handles List by taking first or joining)
    String safeString(dynamic val) {
      if (val == null) return '';
      if (val is String) return val;
      if (val is List) return val.join(', '); // Join list items if strictly string expected
      return val.toString();
    }

    // Helper to safely extract List<String>
    List<String> safeList(dynamic val) {
      if (val == null) return [];
      if (val is List) return val.map((e) => e.toString()).toList();
      if (val is String) return [val];
      return [];
    }

    return CVPCanvas(
      cvpId: (json['cvpid'] as num?)?.toInt(),
      teamId: (json['teamid'] as num).toInt(),
      customerSegment: safeString(json['customersegment']),
      // jobsToBeDone is dynamic, so we just pass it through. 
      // The UI 'cvp_canvas_screen.dart' handles List vs String rendering.
      jobsToBeDone: json['jobstobedone'], 
      valueProposition: safeString(json['valueproposition']),
      competitivePositioning: safeString(json['competitivepositioning']),
      pains: safeList(json['pains']),
      gains: safeList(json['gains']),
      painRelievers: safeList(json['painrelievers']),
      gainCreators: safeList(json['gaincreators']),
      lastUpdated: json['lastupdated'] == null ? null : DateTime.parse(json['lastupdated'] as String),
    );
  }
  
  Map<String, dynamic> toJson() => _$CVPCanvasToJson(this);
}
@JsonSerializable()
class MVPFeature {
  @JsonKey(name: 'feature_id')
  final int? featureId;
  @JsonKey(name: 'roadmap_id')
  final int? roadmapId;
  final String title;
  final String description;
  final String priority;
  final String complexity;
  final String rationale;
  @JsonKey(name: 'related_cvp_element')
  final String relatedCvpElement;

  MVPFeature({
    this.featureId,
    this.roadmapId,
    required this.title,
    required this.description,
    required this.priority,
    required this.complexity,
    required this.rationale,
    required this.relatedCvpElement,
  });

  factory MVPFeature.fromJson(Map<String, dynamic> json) => _$MVPFeatureFromJson(json);
  Map<String, dynamic> toJson() => _$MVPFeatureToJson(this);
}

@JsonSerializable()
class MVPRoadmap {
  @JsonKey(name: 'roadmap_id')
  final int? roadmapId;
  @JsonKey(name: 'team_id')
  final int teamId;
  @JsonKey(name: 'vision_statement')
  final String visionStatement;
  @JsonKey(name: 'created_date')
  final DateTime? createdDate;
  @JsonKey(name: 'last_updated')
  final DateTime? lastUpdated;
  @JsonKey(defaultValue: [])
  final List<MVPFeature> features;

  MVPRoadmap({
    this.roadmapId,
    required this.teamId,
    required this.visionStatement,
    this.createdDate,
    this.lastUpdated,
    required this.features,
  });

  factory MVPRoadmap.fromJson(Map<String, dynamic> json) => _$MVPRoadmapFromJson(json);
  Map<String, dynamic> toJson() => _$MVPRoadmapToJson(this);
}

@JsonSerializable()
class ProjectTask {
  @JsonKey(name: 'task_id')
  final int? taskId;
  @JsonKey(name: 'team_id')
  final int teamId;
  @JsonKey(name: 'roadmap_id')
  final int? roadmapId;
  final String title;
  final String description;
  @JsonKey(defaultValue: 'TODO')
  final String status; // TODO, IN_PROGRESS, DONE
  final String priority;
  @JsonKey(name: 'estimated_hours')
  final int? estimatedHours;
  @JsonKey(name: 'assignee_role')
  final String? assigneeRole;

  ProjectTask({
    this.taskId,
    required this.teamId,
    this.roadmapId,
    required this.title,
    required this.description,
    required this.status,
    required this.priority,
    this.estimatedHours,
    this.assigneeRole,
  });

  factory ProjectTask.fromJson(Map<String, dynamic> json) => _$ProjectTaskFromJson(json);
  Map<String, dynamic> toJson() => _$ProjectTaskToJson(this);
}


@JsonSerializable()
class InterviewSession {
  @JsonKey(name: 'session_id')
  final int? sessionId;
  @JsonKey(name: 'team_id')
  final int teamId;
  final String status;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;
  
  InterviewSession({
    this.sessionId,
    required this.teamId,
    required this.status,
    this.createdAt,
  });

  factory InterviewSession.fromJson(Map<String, dynamic> json) => _$InterviewSessionFromJson(json);
  Map<String, dynamic> toJson() => _$InterviewSessionToJson(this);
}

@JsonSerializable()
class ChatMessage {
  @JsonKey(name: 'message_id')
  final int? messageId;
  @JsonKey(name: 'session_id')
  final int sessionId;
  final String role; // "user" or "assistant"
  final String content;
  final DateTime? timestamp;

  ChatMessage({
    this.messageId,
    required this.sessionId,
    required this.role,
    required this.content,
    this.timestamp,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) => _$ChatMessageFromJson(json);
  Map<String, dynamic> toJson() => _$ChatMessageToJson(this);
}

@JsonSerializable()
class ProjectChatSession {
  @JsonKey(name: 'session_id')
  final int? sessionId;
  @JsonKey(name: 'project_id')
  final int projectId;
  final String title;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;
  
  ProjectChatSession({
    this.sessionId,
    required this.projectId,
    required this.title,
    this.createdAt,
  });

  factory ProjectChatSession.fromJson(Map<String, dynamic> json) => _$ProjectChatSessionFromJson(json);
  Map<String, dynamic> toJson() => _$ProjectChatSessionToJson(this);
}

