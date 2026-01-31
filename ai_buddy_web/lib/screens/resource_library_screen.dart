import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';

import '../models/resource.dart';
import '../widgets/resource_card.dart';

class ResourceLibraryScreen extends StatefulWidget {
  final String apiBaseUrl;
  final String sessionId;

  const ResourceLibraryScreen({
    super.key,
    required this.apiBaseUrl,
    required this.sessionId,
  });

  @override
  _ResourceLibraryScreenState createState() => _ResourceLibraryScreenState();
}

class _ResourceLibraryScreenState extends State<ResourceLibraryScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounce;

  List<Resource> _resources = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(_handleTabChange);
    _fetchResources();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _handleTabChange() {
    if (_tabController.indexIsChanging) {
      _fetchResources();
    }
  }

  void _onSearchChanged(String query) {
    if (_debounce?.isActive ?? false) _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () {
      _fetchResources();
    });
  }

  String _getCurrentCategory() {
    switch (_tabController.index) {
      case 1:
        return 'self_help';
      case 2:
        return 'crisis';
      case 3:
        return 'university';
      default:
        return '';
    }
  }

  Future<void> _fetchResources() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final category = _getCurrentCategory();
      final search = _searchController.text;

      String url =
          '${widget.apiBaseUrl}/api/resources?session_id=${widget.sessionId}';
      if (category.isNotEmpty) url += '&category=$category';
      if (search.isNotEmpty) url += '&search=$search';

      final response = await http
          .get(Uri.parse(url), headers: {"X-Session-ID": widget.sessionId});

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _resources = (data['resources'] as List)
              .map((r) => Resource.fromJson(r))
              .toList();
          _isLoading = false;
        });
      } else {
        throw Exception("Failed to load resources: ${response.statusCode}");
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _trackView(int resourceId) async {
    try {
      await http.post(
          Uri.parse('${widget.apiBaseUrl}/api/resources/$resourceId/view'),
          headers: {"X-Session-ID": widget.sessionId});
    } catch (e) {
      print("Error tracking view: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text("Library"),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: const [
            Tab(text: "All"),
            Tab(text: "Self-Help"),
            Tab(text: "Crisis Support"),
            Tab(text: "University"),
          ],
        ),
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              onChanged: _onSearchChanged,
              decoration: InputDecoration(
                hintText: "Search resources...",
                prefixIcon: const Icon(Icons.search),
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(30),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 20),
              ),
            ),
          ),

          // Resource List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text("Error loading resources"),
                            ElevatedButton(
                              onPressed: _fetchResources,
                              child: const Text("Retry"),
                            )
                          ],
                        ),
                      )
                    : _resources.isEmpty
                        ? const Center(child: Text("No resources found"))
                        : RefreshIndicator(
                            onRefresh: _fetchResources,
                            child: ListView.builder(
                              padding: const EdgeInsets.all(8),
                              itemCount: _resources.length,
                              itemBuilder: (context, index) {
                                return ResourceCard(
                                  resource: _resources[index],
                                  onView: _trackView,
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}
