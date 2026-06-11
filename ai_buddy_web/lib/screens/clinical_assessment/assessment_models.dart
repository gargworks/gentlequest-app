// ─────────────────────────────────────────────────────────────────────────────
// Assessment scale + question bank
// ─────────────────────────────────────────────────────────────────────────────

enum AssessmentScale { phq9, gad7 }

enum AssessmentSeverity { minimal, mild, moderate, moderateSevere, severe }

extension AssessmentScaleX on AssessmentScale {
  String get title => this == AssessmentScale.phq9
      ? 'Depression Check-in (PHQ-9)'
      : 'Anxiety Check-in (GAD-7)';
  String get subtitle => this == AssessmentScale.phq9
      ? 'Depression screener · clinical-grade · ~2 min'
      : 'Anxiety screener · clinical-grade · ~2 min';
  int get totalQuestions => this == AssessmentScale.phq9 ? 9 : 7;
  int get maxScore => totalQuestions * 3;
}

/// Standard 4-option Likert response labels (verbatim from HTML).
const kLikertLabels = [
  'Not at all',
  'Several days',
  'More than half the days',
  'Nearly every day',
];

/// PHQ-9 question bank — verbatim from html + clinical spec.
const kPhq9Questions = [
  'Little interest or pleasure in doing things.',
  'Feeling down, depressed, or hopeless.',
  'Trouble falling or staying asleep, or sleeping too much.',
  // Q4 verbatim from HTML mockup A:
  'Over the last 2 weeks, how often have you felt tired or had little energy?',
  'Poor appetite or overeating.',
  'Feeling bad about yourself — or that you are a failure or have let yourself or your family down.',
  'Trouble concentrating on things, such as reading the newspaper or watching television.',
  'Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual.',
  // Q9 — suicidality question, verbatim from HTML mockup C:
  'Thoughts that you would be better off dead, or of hurting yourself.',
];

/// GAD-7 question bank.
const kGad7Questions = [
  'Feeling nervous, anxious, or on edge.',
  'Not being able to stop or control worrying.',
  'Worrying too much about different things.',
  'Trouble relaxing.',
  'Being so restless that it is hard to sit still.',
  'Becoming easily annoyed or irritable.',
  'Feeling afraid, as if something awful might happen.',
];

/// Compute severity band from PHQ-9 score (0–27).
AssessmentSeverity phq9Severity(int score) {
  if (score <= 4) return AssessmentSeverity.minimal;
  if (score <= 9) return AssessmentSeverity.mild;
  if (score <= 14) return AssessmentSeverity.moderate;
  if (score <= 19) return AssessmentSeverity.moderateSevere;
  return AssessmentSeverity.severe;
}

/// Compute severity band from GAD-7 score (0–21).
AssessmentSeverity gad7Severity(int score) {
  if (score <= 4) return AssessmentSeverity.minimal;
  if (score <= 9) return AssessmentSeverity.mild;
  if (score <= 14) return AssessmentSeverity.moderate;
  return AssessmentSeverity.severe;
}
