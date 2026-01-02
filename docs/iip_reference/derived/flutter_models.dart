"""
Flutter Models for IIP Module 6 Project
Generated from: M6W12-D2-IIP-Miro-Export.pdf
Target: Flutter + Python/Java Backend Integration
"""

import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'flutter_models.g.dart';

// ============================================================================
// TEAM & MEMBER MODELS
// ============================================================================

@JsonSerializable()
class Team extends Equatable {
  final int teamId;
  final String teamName;
  final String projectFocus;
  final DateTime createdDate;
  final DateTime updatedDate;
  final List<TeamMember> members;

  const Team({
    required this.teamId,
    required this.teamName,
    required this.projectFocus,
    required this.createdDate,
    required this.updatedDate,
    this.members = const [],
  });

  factory Team.fromJson(Map<String, dynamic> json) => _$TeamFromJson(json);
  Map<String, dynamic> toJson() => _$TeamToJson(this);

  @override
  List<Object?> get props => [
        teamId,
        teamName,
        projectFocus,
        createdDate,
        updatedDate,
        members,
      ];
}

@JsonSerializable()
class TeamMember extends Equatable {
  final int memberId;
  final int teamId;
  final String name;
  final String email;
  final String? role;
  final String? timezone;
  final DateTime createdDate;

  const TeamMember({
    required this.memberId,
    required this.teamId,
    required this.name,
    required this.email,
    this.role,
    this.timezone,
    required this.createdDate,
  });

  factory TeamMember.fromJson(Map<String, dynamic> json) =>
      _$TeamMemberFromJson(json);
  Map<String, dynamic> toJson() => _$TeamMemberToJson(this);

  @override
  List<Object?> get props => [
        memberId,
        teamId,
        name,
        email,
        role,
        timezone,
        createdDate,
      ];
}

// ============================================================================
// POV STATEMENT MODEL
// ============================================================================

@JsonSerializable()
class POVStatement extends Equatable {
  final int povId;
  final int teamId;
  final String usersDescription; // Who?
  final String needDescription; // What?
  final String whyMattersDescription; // Why?
  final String fullStatement; // Complete: Users___ need a way to ___ because ___
  final DateTime createdDate;
  final DateTime updatedDate;
  final String? feedbackFromInstructors;
  final int iterationCount;

  const POVStatement({
    required this.povId,
    required this.teamId,
    required this.usersDescription,
    required this.needDescription,
    required this.whyMattersDescription,
    required this.fullStatement,
    required this.createdDate,
    required this.updatedDate,
    this.feedbackFromInstructors,
    this.iterationCount = 1,
  });

  factory POVStatement.fromJson(Map<String, dynamic> json) =>
      _$POVStatementFromJson(json);
  Map<String, dynamic> toJson() => _$POVStatementToJson(this);

  @override
  List<Object?> get props => [
        povId,
        teamId,
        usersDescription,
        needDescription,
        whyMattersDescription,
        fullStatement,
        createdDate,
        updatedDate,
        feedbackFromInstructors,
        iterationCount,
      ];
}

// ============================================================================
// RESEARCH INTERVIEW MODEL
// ============================================================================

@JsonSerializable()
class ResearchInterview extends Equatable {
  final int interviewId;
  final int teamId;
  final DateTime interviewDate;
  final String participantRole; // e.g., "Student", "Counselor"
  final String participantAnonymizedId; // For privacy
  final String? location;
  final int? durationMinutes;
  final String interviewNotes; // Raw transcript/notes
  final String? recordingUrl;
  final List<String> keyQuotes;
  final List<ANRUMInsight> insightsExtracted;
  final String? researcherBiasNotes;
  final DateTime createdDate;
  final String? researcherName;

  const ResearchInterview({
    required this.interviewId,
    required this.teamId,
    required this.interviewDate,
    required this.participantRole,
    required this.participantAnonymizedId,
    this.location,
    this.durationMinutes,
    required this.interviewNotes,
    this.recordingUrl,
    this.keyQuotes = const [],
    this.insightsExtracted = const [],
    this.researcherBiasNotes,
    required this.createdDate,
    this.researcherName,
  });

  factory ResearchInterview.fromJson(Map<String, dynamic> json) =>
      _$ResearchInterviewFromJson(json);
  Map<String, dynamic> toJson() => _$ResearchInterviewToJson(this);

  @override
  List<Object?> get props => [
        interviewId,
        teamId,
        interviewDate,
        participantRole,
        participantAnonymizedId,
        location,
        durationMinutes,
        interviewNotes,
        recordingUrl,
        keyQuotes,
        insightsExtracted,
        researcherBiasNotes,
        createdDate,
        researcherName,
      ];
}

// ============================================================================
// ANRUM INSIGHT MODEL
// Attitude, Need, Response, Use case, Mental model
// ============================================================================

@JsonSerializable()
class ANRUMInsight extends Equatable {
  final String attitude; // What emotion/belief surfaced?
  final String need; // What unmet need does this reveal?
  final String response; // How did user currently respond?
  final String useCase; // What specific scenario triggered this?
  final String mentalModel; // What assumption does user hold?

  const ANRUMInsight({
    required this.attitude,
    required this.need,
    required this.response,
    required this.useCase,
    required this.mentalModel,
  });

  factory ANRUMInsight.fromJson(Map<String, dynamic> json) =>
      _$ANRUMInsightFromJson(json);
  Map<String, dynamic> toJson() => _$ANRUMInsightToJson(this);

  @override
  List<Object?> get props => [attitude, need, response, useCase, mentalModel];
}

// ============================================================================
// PERSONA MODEL
// ============================================================================

@JsonSerializable()
class Persona extends Equatable {
  final int personaId;
  final int teamId;
  final String name;
  final int? age;
  final String? context; // Demographic, academic level, living situation
  final String? avatarUrl;
  final List<String> goals;
  final List<String> frustrations;
  final List<String> behaviors;
  final List<String> motivations;
  final List<String> barriers;
  final String? environment; // School, dorm, home, support network
  final List<int> supportingInterviewIds;
  final List<String> supportingQuotes;
  final DateTime createdDate;
  final DateTime updatedDate;
  final int version;

  const Persona({
    required this.personaId,
    required this.teamId,
    required this.name,
    this.age,
    this.context,
    this.avatarUrl,
    this.goals = const [],
    this.frustrations = const [],
    this.behaviors = const [],
    this.motivations = const [],
    this.barriers = const [],
    this.environment,
    this.supportingInterviewIds = const [],
    this.supportingQuotes = const [],
    required this.createdDate,
    required this.updatedDate,
    this.version = 1,
  });

  factory Persona.fromJson(Map<String, dynamic> json) =>
      _$PersonaFromJson(json);
  Map<String, dynamic> toJson() => _$PersonaToJson(this);

  @override
  List<Object?> get props => [
        personaId,
        teamId,
        name,
        age,
        context,
        avatarUrl,
        goals,
        frustrations,
        behaviors,
        motivations,
        barriers,
        environment,
        supportingInterviewIds,
        supportingQuotes,
        createdDate,
        updatedDate,
        version,
      ];
}

// ============================================================================
// CVP CANVAS MODEL
// ============================================================================

@JsonSerializable()
class CVPCanvas extends Equatable {
  final int cvpId;
  final int teamId;
  final String? customerSegment;
  final List<String> jobsToBeDone; // Functional, Emotional, Social
  final String? valueProposition;
  final List<String> pains;
  final List<String> painRelievers;
  final List<String> gains;
  final List<String> gainCreators;
  final String? competitivePositioning;
  final List<String> directCompetitors;
  final List<String> indirectCompetitors;
  final String? differentiation;
  final List<String> tradeOffs; // Design trade-off decisions
  final DateTime createdDate;
  final DateTime lastUpdated;
  final int version;

  const CVPCanvas({
    required this.cvpId,
    required this.teamId,
    this.customerSegment,
    this.jobsToBeDone = const [],
    this.valueProposition,
    this.pains = const [],
    this.painRelievers = const [],
    this.gains = const [],
    this.gainCreators = const [],
    this.competitivePositioning,
    this.directCompetitors = const [],
    this.indirectCompetitors = const [],
    this.differentiation,
    this.tradeOffs = const [],
    required this.createdDate,
    required this.lastUpdated,
    this.version = 1,
  });

  factory CVPCanvas.fromJson(Map<String, dynamic> json) =>
      _$CVPCanvasFromJson(json);
  Map<String, dynamic> toJson() => _$CVPCanvasToJson(this);

  @override
  List<Object?> get props => [
        cvpId,
        teamId,
        customerSegment,
        jobsToBeDone,
        valueProposition,
        pains,
        painRelievers,
        gains,
        gainCreators,
        competitivePositioning,
        directCompetitors,
        indirectCompetitors,
        differentiation,
        tradeOffs,
        createdDate,
        lastUpdated,
        version,
      ];
}

// ============================================================================
// EXPERIMENT MODEL
// ============================================================================

enum ExperimentStatus {
  PENDING,
  IN_PROGRESS,
  COMPLETED,
  FAILED,
}

@JsonSerializable()
class Experiment extends Equatable {
  final int expId;
  final int teamId;
  final String hypothesis;
  final String? assumption;
  final String testMethod; // e.g., "A/B Test", "User Interview"
  final String? testDescription;
  final String successMetric;
  final String? learningGoal;
  final ExperimentStatus status;
  final DateTime? startDate;
  final DateTime? endDate;
  final String? resultSummary;
  final double? metricValue;
  final String? metricUnit;
  final String? learnings;
  final DateTime createdDate;

  const Experiment({
    required this.expId,
    required this.teamId,
    required this.hypothesis,
    this.assumption,
    required this.testMethod,
    this.testDescription,
    required this.successMetric,
    this.learningGoal,
    this.status = ExperimentStatus.PENDING,
    this.startDate,
    this.endDate,
    this.resultSummary,
    this.metricValue,
    this.metricUnit,
    this.learnings,
    required this.createdDate,
  });

  factory Experiment.fromJson(Map<String, dynamic> json) =>
      _$ExperimentFromJson(json);
  Map<String, dynamic> toJson() => _$ExperimentToJson(this);

  @override
  List<Object?> get props => [
        expId,
        teamId,
        hypothesis,
        assumption,
        testMethod,
        testDescription,
        successMetric,
        learningGoal,
        status,
        startDate,
        endDate,
        resultSummary,
        metricValue,
        metricUnit,
        learnings,
        createdDate,
      ];
}

// ============================================================================
// REQUEST/RESPONSE MODELS FOR API
// ============================================================================

@JsonSerializable()
class CreateTeamRequest {
  final String teamName;
  final String projectFocus;

  CreateTeamRequest({
    required this.teamName,
    required this.projectFocus,
  });

  factory CreateTeamRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateTeamRequestFromJson(json);
  Map<String, dynamic> toJson() => _$CreateTeamRequestToJson(this);
}

@JsonSerializable()
class CreatePOVStatementRequest {
  final String usersDescription;
  final String needDescription;
  final String whyMattersDescription;

  CreatePOVStatementRequest({
    required this.usersDescription,
    required this.needDescription,
    required this.whyMattersDescription,
  });

  factory CreatePOVStatementRequest.fromJson(Map<String, dynamic> json) =>
      _$CreatePOVStatementRequestFromJson(json);
  Map<String, dynamic> toJson() => _$CreatePOVStatementRequestToJson(this);
}

@JsonSerializable()
class CreateInterviewRequest {
  final DateTime interviewDate;
  final String participantRole;
  final String? participantAnonymizedId;
  final String interviewNotes;
  final String? location;
  final int? durationMinutes;
  final List<String>? keyQuotes;
  final String? researcherBiasNotes;
  final String? researcherName;

  CreateInterviewRequest({
    required this.interviewDate,
    required this.participantRole,
    this.participantAnonymizedId,
    required this.interviewNotes,
    this.location,
    this.durationMinutes,
    this.keyQuotes,
    this.researcherBiasNotes,
    this.researcherName,
  });

  factory CreateInterviewRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateInterviewRequestFromJson(json);
  Map<String, dynamic> toJson() => _$CreateInterviewRequestToJson(this);
}

@JsonSerializable()
class CreatePersonaRequest {
  final String name;
  final int? age;
  final String? context;
  final String? avatarUrl;
  final List<String>? goals;
  final List<String>? frustrations;
  final List<String>? behaviors;
  final List<String>? motivations;
  final List<String>? barriers;
  final String? environment;
  final List<int>? supportingInterviewIds;

  CreatePersonaRequest({
    required this.name,
    this.age,
    this.context,
    this.avatarUrl,
    this.goals,
    this.frustrations,
    this.behaviors,
    this.motivations,
    this.barriers,
    this.environment,
    this.supportingInterviewIds,
  });

  factory CreatePersonaRequest.fromJson(Map<String, dynamic> json) =>
      _$CreatePersonaRequestFromJson(json);
  Map<String, dynamic> toJson() => _$CreatePersonaRequestToJson(this);
}

@JsonSerializable()
class CreateCVPCanvasRequest {
  final String? customerSegment;
  final List<String>? jobsToBeDone;
  final String? valueProposition;
  final List<String>? pains;
  final List<String>? painRelievers;
  final List<String>? gains;
  final List<String>? gainCreators;
  final String? competitivePositioning;
  final List<String>? directCompetitors;
  final List<String>? indirectCompetitors;
  final String? differentiation;
  final List<String>? tradeOffs;

  CreateCVPCanvasRequest({
    this.customerSegment,
    this.jobsToBeDone,
    this.valueProposition,
    this.pains,
    this.painRelievers,
    this.gains,
    this.gainCreators,
    this.competitivePositioning,
    this.directCompetitors,
    this.indirectCompetitors,
    this.differentiation,
    this.tradeOffs,
  });

  factory CreateCVPCanvasRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateCVPCanvasRequestFromJson(json);
  Map<String, dynamic> toJson() => _$CreateCVPCanvasRequestToJson(this);
}

@JsonSerializable()
class CreateExperimentRequest {
  final String hypothesis;
  final String? assumption;
  final String testMethod;
  final String? testDescription;
  final String successMetric;
  final String? learningGoal;

  CreateExperimentRequest({
    required this.hypothesis,
    this.assumption,
    required this.testMethod,
    this.testDescription,
    required this.successMetric,
    this.learningGoal,
  });

  factory CreateExperimentRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateExperimentRequestFromJson(json);
  Map<String, dynamic> toJson() => _$CreateExperimentRequestToJson(this);
}
