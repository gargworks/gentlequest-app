import 'package:flutter/material.dart';

class TaskProvider extends ChangeNotifier {
  bool _isLoading = false;
  String? _error;

  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadTasks() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    // Honest failure: task loading is not implemented yet. Surface the error
    // state to the UI rather than silently reporting success.
    _error = 'Tasks coming soon';
    _isLoading = false;
    notifyListeners();
    throw UnimplementedError('TaskProvider is not yet implemented');
  }
}
