import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/resource.dart';

class ResourceProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  List<Resource> _resources = [];
  bool _isLoading = false;
  String? _error;
  String? _selectedCategory;
  String _searchQuery = '';

  List<Resource> get resources => _resources;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String? get selectedCategory => _selectedCategory;

  Future<void> fetchResources({String? category, String? search}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final params = <String, String>{};
      if (category != null) params['category'] = category;
      if (search != null && search.isNotEmpty) params['search'] = search;

      final response = await _apiService.get('/api/resources', params: params);

      _resources = (response['resources'] as List)
          .map((r) => Resource.fromJson(r))
          .toList();

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> trackView(int resourceId) async {
    try {
      await _apiService.post('/api/resources/$resourceId/view');
    } catch (e) {
      debugPrint('Error tracking resource view: $e');
    }
  }

  void setCategory(String? category) {
    _selectedCategory = category;
    fetchResources(
        category: category, search: _searchQuery.isEmpty ? null : _searchQuery);
  }

  void setSearch(String query) {
    _searchQuery = query;
    fetchResources(
        category: _selectedCategory, search: query.isEmpty ? null : query);
  }

  void clearFilters() {
    _selectedCategory = null;
    _searchQuery = '';
    fetchResources();
  }
}
