// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'iip_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Team _$TeamFromJson(Map<String, dynamic> json) => Team(
  teamId: (json['teamid'] as num?)?.toInt(),
  teamName: json['teamname'] as String,
  projectFocus: json['projectfocus'] as String,
);

Map<String, dynamic> _$TeamToJson(Team instance) => <String, dynamic>{
  'teamid': instance.teamId,
  'teamname': instance.teamName,
  'projectfocus': instance.projectFocus,
};

Insight _$InsightFromJson(Map<String, dynamic> json) => Insight(
  category: json['category'] as String,
  insight: json['insight'] as String,
  quote: json['quote'] as String,
);

Map<String, dynamic> _$InsightToJson(Insight instance) => <String, dynamic>{
  'category': instance.category,
  'insight': instance.insight,
  'quote': instance.quote,
};

Interview _$InterviewFromJson(Map<String, dynamic> json) => Interview(
  interviewId: (json['interviewid'] as num?)?.toInt(),
  teamId: (json['teamid'] as num).toInt(),
  interviewDate: DateTime.parse(json['interviewdate'] as String),
  participantRole: json['participantrole'] as String,
  interviewNotes: json['interviewnotes'] as String,
  insightsExtracted:
      (json['insightsextracted'] as List<dynamic>?)
          ?.map((e) => Insight.fromJson(e as Map<String, dynamic>))
          .toList() ??
      [],
);

Map<String, dynamic> _$InterviewToJson(Interview instance) => <String, dynamic>{
  'interviewid': instance.interviewId,
  'teamid': instance.teamId,
  'interviewdate': instance.interviewDate.toIso8601String(),
  'participantrole': instance.participantRole,
  'interviewnotes': instance.interviewNotes,
  'insightsextracted': instance.insightsExtracted,
};

Persona _$PersonaFromJson(Map<String, dynamic> json) => Persona(
  personaId: (json['personaid'] as num?)?.toInt(),
  teamId: (json['teamid'] as num).toInt(),
  name: json['name'] as String,
  age: (json['age'] as num?)?.toInt(),
  context: json['context'] as String?,
  goals:
      (json['goals'] as List<dynamic>?)?.map((e) => e as String).toList() ?? [],
  frustrations:
      (json['frustrations'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      [],
  supportingQuotes:
      (json['supportingquotes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      [],
  supportingInterviewIds:
      (json['supportinginterviewids'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList() ??
      [],
);

Map<String, dynamic> _$PersonaToJson(Persona instance) => <String, dynamic>{
  'personaid': instance.personaId,
  'teamid': instance.teamId,
  'name': instance.name,
  'age': instance.age,
  'context': instance.context,
  'goals': instance.goals,
  'frustrations': instance.frustrations,
  'supportingquotes': instance.supportingQuotes,
  'supportinginterviewids': instance.supportingInterviewIds,
};

CVPCanvas _$CVPCanvasFromJson(Map<String, dynamic> json) => CVPCanvas(
  cvpId: (json['cvpid'] as num?)?.toInt(),
  teamId: (json['teamid'] as num).toInt(),
  customerSegment: json['customersegment'] as String,
  jobsToBeDone: json['jobstobedone'],
  valueProposition: json['valueproposition'] as String,
  pains:
      (json['pains'] as List<dynamic>?)?.map((e) => e as String).toList() ?? [],
  gains:
      (json['gains'] as List<dynamic>?)?.map((e) => e as String).toList() ?? [],
  painRelievers:
      (json['painrelievers'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      [],
  gainCreators:
      (json['gaincreators'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      [],
  competitivePositioning: json['competitivepositioning'] as String,
  lastUpdated: json['lastupdated'] == null
      ? null
      : DateTime.parse(json['lastupdated'] as String),
);

Map<String, dynamic> _$CVPCanvasToJson(CVPCanvas instance) => <String, dynamic>{
  'cvpid': instance.cvpId,
  'teamid': instance.teamId,
  'customersegment': instance.customerSegment,
  'jobstobedone': instance.jobsToBeDone,
  'valueproposition': instance.valueProposition,
  'pains': instance.pains,
  'gains': instance.gains,
  'painrelievers': instance.painRelievers,
  'gaincreators': instance.gainCreators,
  'competitivepositioning': instance.competitivePositioning,
  'lastupdated': instance.lastUpdated?.toIso8601String(),
};

MVPFeature _$MVPFeatureFromJson(Map<String, dynamic> json) => MVPFeature(
  featureId: (json['feature_id'] as num?)?.toInt(),
  roadmapId: (json['roadmap_id'] as num?)?.toInt(),
  title: json['title'] as String,
  description: json['description'] as String,
  priority: json['priority'] as String,
  complexity: json['complexity'] as String,
  rationale: json['rationale'] as String,
  relatedCvpElement: json['related_cvp_element'] as String,
);

Map<String, dynamic> _$MVPFeatureToJson(MVPFeature instance) =>
    <String, dynamic>{
      'feature_id': instance.featureId,
      'roadmap_id': instance.roadmapId,
      'title': instance.title,
      'description': instance.description,
      'priority': instance.priority,
      'complexity': instance.complexity,
      'rationale': instance.rationale,
      'related_cvp_element': instance.relatedCvpElement,
    };

MVPRoadmap _$MVPRoadmapFromJson(Map<String, dynamic> json) => MVPRoadmap(
  roadmapId: (json['roadmap_id'] as num?)?.toInt(),
  teamId: (json['team_id'] as num).toInt(),
  visionStatement: json['vision_statement'] as String,
  createdDate: json['created_date'] == null
      ? null
      : DateTime.parse(json['created_date'] as String),
  lastUpdated: json['last_updated'] == null
      ? null
      : DateTime.parse(json['last_updated'] as String),
  features:
      (json['features'] as List<dynamic>?)
          ?.map((e) => MVPFeature.fromJson(e as Map<String, dynamic>))
          .toList() ??
      [],
);

Map<String, dynamic> _$MVPRoadmapToJson(MVPRoadmap instance) =>
    <String, dynamic>{
      'roadmap_id': instance.roadmapId,
      'team_id': instance.teamId,
      'vision_statement': instance.visionStatement,
      'created_date': instance.createdDate?.toIso8601String(),
      'last_updated': instance.lastUpdated?.toIso8601String(),
      'features': instance.features,
    };

ProjectTask _$ProjectTaskFromJson(Map<String, dynamic> json) => ProjectTask(
  taskId: (json['task_id'] as num?)?.toInt(),
  teamId: (json['team_id'] as num).toInt(),
  roadmapId: (json['roadmap_id'] as num?)?.toInt(),
  title: json['title'] as String,
  description: json['description'] as String,
  status: json['status'] as String? ?? 'TODO',
  priority: json['priority'] as String,
  estimatedHours: (json['estimated_hours'] as num?)?.toInt(),
  assigneeRole: json['assignee_role'] as String?,
);

Map<String, dynamic> _$ProjectTaskToJson(ProjectTask instance) =>
    <String, dynamic>{
      'task_id': instance.taskId,
      'team_id': instance.teamId,
      'roadmap_id': instance.roadmapId,
      'title': instance.title,
      'description': instance.description,
      'status': instance.status,
      'priority': instance.priority,
      'estimated_hours': instance.estimatedHours,
      'assignee_role': instance.assigneeRole,
    };

InterviewSession _$InterviewSessionFromJson(Map<String, dynamic> json) =>
    InterviewSession(
      sessionId: (json['session_id'] as num?)?.toInt(),
      teamId: (json['team_id'] as num).toInt(),
      status: json['status'] as String,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String),
    );

Map<String, dynamic> _$InterviewSessionToJson(InterviewSession instance) =>
    <String, dynamic>{
      'session_id': instance.sessionId,
      'team_id': instance.teamId,
      'status': instance.status,
      'created_at': instance.createdAt?.toIso8601String(),
    };

ChatMessage _$ChatMessageFromJson(Map<String, dynamic> json) => ChatMessage(
  messageId: (json['message_id'] as num?)?.toInt(),
  sessionId: (json['session_id'] as num).toInt(),
  role: json['role'] as String,
  content: json['content'] as String,
  timestamp: json['timestamp'] == null
      ? null
      : DateTime.parse(json['timestamp'] as String),
);

Map<String, dynamic> _$ChatMessageToJson(ChatMessage instance) =>
    <String, dynamic>{
      'message_id': instance.messageId,
      'session_id': instance.sessionId,
      'role': instance.role,
      'content': instance.content,
      'timestamp': instance.timestamp?.toIso8601String(),
    };

ProjectChatSession _$ProjectChatSessionFromJson(Map<String, dynamic> json) =>
    ProjectChatSession(
      sessionId: (json['session_id'] as num?)?.toInt(),
      projectId: (json['project_id'] as num).toInt(),
      title: json['title'] as String,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String),
    );

Map<String, dynamic> _$ProjectChatSessionToJson(ProjectChatSession instance) =>
    <String, dynamic>{
      'session_id': instance.sessionId,
      'project_id': instance.projectId,
      'title': instance.title,
      'created_at': instance.createdAt?.toIso8601String(),
    };
