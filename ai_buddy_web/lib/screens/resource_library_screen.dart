import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/resource_provider.dart';
import '../widgets/resource_card.dart';

class ResourceLibraryScreen extends StatefulWidget {
  const ResourceLibraryScreen({Key? key}) : super(key: key);

  @override
  State<ResourceLibraryScreen> createState() => _ResourceLibraryScreenState();
}

class _ResourceLibraryScreenState extends State<ResourceLibraryScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<ResourceProvider>(context, listen: false).fetchResources();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Resources'),
        elevation: 0,
        backgroundColor: Theme.of(context).primaryColor,
      ),
      body: Column(
        children: [
          // Search bar
          Container(
            color: Theme.of(context).primaryColor.withOpacity(0.1),
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search resources...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          Provider.of<ResourceProvider>(context, listen: false)
                              .setSearch('');
                        },
                      )
                    : null,
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
              onChanged: (value) {
                Provider.of<ResourceProvider>(context, listen: false)
                    .setSearch(value);
              },
            ),
          ),

          // Category chips
          Container(
            color: Theme.of(context).primaryColor.withOpacity(0.1),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Consumer<ResourceProvider>(
                builder: (context, provider, child) {
                  return Row(
                    children: [
                      _buildCategoryChip('All', null, provider),
                      const SizedBox(width: 8),
                      _buildCategoryChip('Crisis', 'crisis', provider),
                      const SizedBox(width: 8),
                      _buildCategoryChip('Self-Help', 'self_help', provider),
                      const SizedBox(width: 8),
                      _buildCategoryChip('University', 'university', provider),
                    ],
                  );
                },
              ),
            ),
          ),

          // Resource list
          Expanded(
            child: Consumer<ResourceProvider>(
              builder: (context, provider, child) {
                if (provider.isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (provider.error != null) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline,
                            size: 64, color: Colors.red),
                        const SizedBox(height: 16),
                        Text('Error: ${provider.error}'),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () => provider.fetchResources(),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  );
                }

                if (provider.resources.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.search_off,
                            size: 64, color: Colors.grey),
                        const SizedBox(height: 16),
                        const Text('No resources found'),
                        if (provider.selectedCategory != null ||
                            _searchController.text.isNotEmpty)
                          TextButton(
                            onPressed: () {
                              _searchController.clear();
                              provider.clearFilters();
                            },
                            child: const Text('Clear filters'),
                          ),
                      ],
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: () => provider.fetchResources(
                    category: provider.selectedCategory,
                    search: _searchController.text.isEmpty
                        ? null
                        : _searchController.text,
                  ),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: provider.resources.length,
                    itemBuilder: (context, index) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: ResourceCard(
                          resource: provider.resources[index],
                          onTap: () => _viewResource(provider.resources[index]),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryChip(
      String label, String? category, ResourceProvider provider) {
    final isSelected = provider.selectedCategory == category;
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        provider.setCategory(selected ? category : null);
      },
      selectedColor: Theme.of(context).primaryColor.withOpacity(0.2),
      checkmarkColor: Theme.of(context).primaryColor,
    );
  }

  void _viewResource(resource) {
    Provider.of<ResourceProvider>(context, listen: false)
        .trackView(resource.id);

    if (resource.url != null && resource.url!.isNotEmpty) {
      // Open URL in browser
      // TODO: Use url_launcher package
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(resource.title),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(resource.description),
              const SizedBox(height: 16),
              Text('URL: ${resource.url}',
                  style: const TextStyle(fontSize: 12, color: Colors.blue)),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } else {
      // Show detail dialog
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(resource.title),
          content: Text(resource.description),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    }
  }
}
