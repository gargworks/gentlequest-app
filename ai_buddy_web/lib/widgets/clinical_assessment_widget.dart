import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';

import '../models/message.dart' show RiskLevel;
import '../services/api_service.dart';
import '../services/analytics_service.dart' show logAnalyticsEvent;
import '../theme/gq_tokens.dart';
import 'crisis_resources.dart';
import 'q9_crisis_bridge_sheet.dart';

/// Clinical assessment widget for PHQ-9 (depression) and GAD-7 (anxiety) screening.
class ClinicalAssessmentWidget extends StatefulWidget {
  final String assessmentType; // 'phq9' or 'gad7'
  final VoidCallback? onComplete;

  const ClinicalAssessmentWidget({
    super.key,
    required this.assessmentType,
    this.onComplete,
  });

  @override
  State<ClinicalAssessmentWidget> createState() =>
      _ClinicalAssessmentWidgetState();
}

class _ClinicalAssessmentWidgetState extends State<ClinicalAssessmentWidget> {
  final ApiService _apiService = ApiService();

  bool _isLoading = true;
  bool _isSubmitting = false;
  bool _hasError = false;
  String? _errorMessage;

  // Assessment data
  String _assessmentName = '';
  String _assessmentDescription = '';
  List<Map<String, dynamic>> _questions = [];
  List<Map<String, dynamic>> _options = [];
  List<int> _responses = [];
  int _currentQuestionIndex = 0;

  // Result data
  Map<String, dynamic>? _result;

  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }

  Future<void> _loadQuestions() async {
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      final data = await _apiService
          .getClinicalAssessmentQuestions(widget.assessmentType);

      setState(() {
        _assessmentName = data['name'] ?? '';
        _assessmentDescription = data['description'] ?? '';
        _questions = List<Map<String, dynamic>>.from(data['questions'] ?? []);
        _options = List<Map<String, dynamic>>.from(data['options'] ?? []);
        _responses = List.filled(_questions.length, -1); // -1 = unanswered
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _hasError = true;
        _errorMessage = e.toString();
        _isLoading = false;
      });
      if (kDebugMode) debugPrint('Error loading assessment: $e');
    }
  }

  Future<void> _submitAssessment() async {
    // Check all questions answered
    if (_responses.any((r) => r == -1)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please answer all questions before submitting.'),
          backgroundColor: GQColors.amber,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final result = await _apiService.submitClinicalAssessment(
        assessmentType: widget.assessmentType,
        responses: _responses,
      );

      setState(() {
        _result = result;
        _isSubmitting = false;
      });

      if (kDebugMode) debugPrint('Assessment submitted: $result');
    } catch (e) {
      setState(() => _isSubmitting = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: GQColors.coral,
          ),
        );
      }
    }
  }

  void _selectOption(int value) {
    setState(() {
      _responses[_currentQuestionIndex] = value;
    });
  }

  /// True when the user is about to advance/submit from PHQ-9 Q9
  /// with a score of >= 1. The bridge sheet fires once at this gate
  /// per R1D8 Chunk 7 spec.
  bool get _isQ9TriggerArmed =>
      widget.assessmentType == 'phq9' &&
      _currentQuestionIndex == 8 &&
      _responses.length > 8 &&
      _responses[8] >= 1;

  /// Shows the Q9 soft bridge if armed; returns whether the caller may
  /// continue with the underlying submit/next path. Returning false
  /// means the bridge already handled the flow (e.g. talk-now opens
  /// crisis support and submits).
  Future<bool> _maybeShowQ9Bridge() async {
    if (!_isQ9TriggerArmed) return true;
    await logAnalyticsEvent('phq9_q9_bridge_shown',
        metadata: {'score': _responses[8]});
    if (!mounted) return false;
    final action = await Q9CrisisBridgeSheet.show(context);
    if (!mounted) return false;
    await logAnalyticsEvent('phq9_q9_bridge_choice',
        metadata: {'action': action?.name ?? 'dismissed'});
    if (!mounted) return false;
    switch (action) {
      case Q9BridgeAction.talkNow:
        // Submit before any pop so the honest Q9 answer is preserved
        // in the user's record even though the assessment paused.
        await _submitAssessment();
        return false;
      case Q9BridgeAction.heavyMoment:
        await logAnalyticsEvent('q9_heavy_moment_flagged');
        
        // Schedule 24h check-in with the backend
        try {
          await _apiService.scheduleFollowUp();
        } catch (e) {
          debugPrint('Failed to schedule follow-up: $e');
        }
        
        return true;
      case Q9BridgeAction.keepGoing:
      case null:
        return true;
    }
  }

  void _nextQuestion() {
    if (_currentQuestionIndex < _questions.length - 1) {
      setState(() => _currentQuestionIndex++);
    }
  }

  void _previousQuestion() {
    if (_currentQuestionIndex > 0) {
      setState(() => _currentQuestionIndex--);
    }
  }

  Color _getSeverityColor(String severity) {
    switch (severity) {
      case 'minimal':
        return GQColors.moodGreat;
      case 'mild':
        return GQColors.moodGood;
      case 'moderate':
        return GQColors.amber;
      case 'moderately_severe':
        return GQColors.coral;
      case 'severe':
        return GQColors.coral;
      default:
        return GQColors.ink3;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading assessment...'),
          ],
        ),
      );
    }

    if (_hasError) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: GQColors.coral),
            const SizedBox(height: 16),
            Text('Error: $_errorMessage'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadQuestions,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    // Show results if submitted
    if (_result != null) {
      return _buildResultsView();
    }

    // Show question view
    return _buildQuestionView();
  }

  Widget _buildQuestionView() {
    final question = _questions[_currentQuestionIndex];
    final selectedValue = _responses[_currentQuestionIndex];
    final progress = (_currentQuestionIndex + 1) / _questions.length;
    final isLastQuestion = _currentQuestionIndex == _questions.length - 1;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Text(
            _assessmentName,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            _assessmentDescription,
            style: const TextStyle(color: GQColors.ink3, fontSize: 14),
          ),
          const SizedBox(height: 16),

          // Progress indicator
          LinearProgressIndicator(
            value: progress,
            backgroundColor: GQColors.hair,
            color: Theme.of(context).primaryColor,
          ),
          const SizedBox(height: 8),
          Text(
            'Question ${_currentQuestionIndex + 1} of ${_questions.length}',
            style: const TextStyle(color: GQColors.ink3, fontSize: 12),
          ),
          const SizedBox(height: 24),

          // Question text
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: GQColors.primarySoft,
              borderRadius: BorderRadius.circular(GQRadii.card),
            ),
            child: Text(
              question['text'] ?? '',
              style: const TextStyle(fontSize: 16, height: 1.4),
            ),
          ),
          const SizedBox(height: 24),

          // Options
          ..._options.map((option) {
            final value = option['value'] as int;
            final label = option['label'] as String;
            final isSelected = selectedValue == value;

            return GestureDetector(
              onTap: () => _selectOption(value),
              child: Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: isSelected
                      ? Theme.of(context).primaryColor.withValues(alpha: 0.1)
                      : GQColors.softBg,
                  border: Border.all(
                    color: isSelected
                        ? Theme.of(context).primaryColor
                        : GQColors.hair,
                    width: isSelected ? 2 : 1,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 24,
                      height: 24,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isSelected
                            ? Theme.of(context).primaryColor
                            : Colors.transparent,
                        border: Border.all(
                          color: isSelected
                              ? Theme.of(context).primaryColor
                              : GQColors.ink3,
                          width: 2,
                        ),
                      ),
                      child: isSelected
                          ? const Icon(Icons.check,
                              size: 16, color: Colors.white)
                          : null,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        label,
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight:
                              isSelected ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),

          const SizedBox(height: 24),

          // Navigation buttons
          Row(
            children: [
              if (_currentQuestionIndex > 0)
                Expanded(
                  child: OutlinedButton(
                    onPressed: _previousQuestion,
                    child: const Text('Previous'),
                  ),
                ),
              if (_currentQuestionIndex > 0) const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: selectedValue >= 0
                      ? () async {
                          final canContinue = await _maybeShowQ9Bridge();
                          if (!canContinue) return;
                          if (isLastQuestion) {
                            _submitAssessment();
                          } else {
                            _nextQuestion();
                          }
                        }
                      : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).primaryColor,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(isLastQuestion ? 'Submit' : 'Next'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildResultsView() {
    final totalScore = _result!['total_score'] as int;
    final maxScore = _result!['max_score'] as int;
    final severity = _result!['severity'] as String;
    final message = _result!['message'] as String;
    final recommendations =
        List<String>.from(_result!['recommendations'] ?? []);
    final requiresFollowUp = _result!['requires_follow_up'] == true;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Result header
          Center(
            child: Column(
              children: [
                Icon(
                  Icons.check_circle,
                  size: 64,
                  color: _getSeverityColor(severity),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Assessment Complete',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Score card
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: _getSeverityColor(severity).withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: _getSeverityColor(severity)),
            ),
            child: Column(
              children: [
                Text(
                  '$totalScore / $maxScore',
                  style: TextStyle(
                    fontSize: 48,
                    fontWeight: FontWeight.bold,
                    color: _getSeverityColor(severity),
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  decoration: BoxDecoration(
                    color: _getSeverityColor(severity),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    severity.replaceAll('_', ' ').toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Message
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: GQColors.softBg,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              message,
              style: const TextStyle(fontSize: 15, height: 1.5),
            ),
          ),

          // Follow-up warmth — coral (Principle #1: never red),
          // CrisisResourcesWidget surfaces 988 + region-local lines.
          if (requiresFollowUp) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: GQColors.coral.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(GQRadii.card),
                border: Border.all(
                  color: GQColors.coral.withValues(alpha: 0.22),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.favorite_border,
                          color: GQColors.coral, size: 18),
                      SizedBox(width: 8),
                      Text(
                        "WE'RE HERE",
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          color: GQColors.coral,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    "If it's heavy right now, you don't have to be alone with it.",
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 14.5,
                      color: GQColors.ink,
                      fontWeight: FontWeight.w600,
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 12),
                  // requiresFollowUp implies clinical-screen Q9 >= 1 or
                  // PHQ-9 severity ≥ moderate; treat as 'high' so the
                  // inline legacy crisis card surfaces 988 + local lines.
                  const CrisisResourcesWidget(riskLevel: RiskLevel.high),
                ],
              ),
            ),
          ],

          // Recommendations
          if (recommendations.isNotEmpty) ...[
            const SizedBox(height: 24),
            const Text(
              'Recommendations',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            ...recommendations.map((rec) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.arrow_right,
                          size: 20, color: Colors.blue),
                      const SizedBox(width: 8),
                      Expanded(
                          child:
                              Text(rec, style: const TextStyle(fontSize: 14))),
                    ],
                  ),
                )),
          ],

          const SizedBox(height: 32),

          // Done button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                if (widget.onComplete != null) {
                  widget.onComplete!();
                } else {
                  Navigator.of(context).pop();
                }
              },
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text('Done'),
            ),
          ),
        ],
      ),
    );
  }
}
