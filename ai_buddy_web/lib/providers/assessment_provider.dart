import 'package:flutter/material.dart';

class AssessmentProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  String? _error;

  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> submitAssessment({
    required String assessmentType,
    required List<int> responses,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiService.submitClinicalAssessment(
        assessmentType: assessmentType,
        responses: responses,
      );
      _error = null;
    } catch (e) {
      debugPrint('Error submitting assessment: $e');
      _error = 'Couldn\'t save that. Let\'s try again.';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
