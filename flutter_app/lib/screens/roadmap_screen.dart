import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/iip_models.dart';
import '../services/api_service.dart';

final roadmapProvider = FutureProvider.family<MVPRoadmap?, int>((ref, teamId) async {
  final apiService = ref.watch(apiServiceProvider);
  return apiService.getRoadmap(teamId);
});

class RoadmapScreen extends ConsumerWidget {
  final int teamId;

  const RoadmapScreen({Key? key, required this.teamId}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final roadmapAsync = ref.watch(roadmapProvider(teamId));

    return Scaffold(
      appBar: AppBar(
        title: Text('MVP Roadmap'),
      ),
      body: roadmapAsync.when(
        data: (roadmap) {
          if (roadmap == null) {
            return _buildEmptyState(context, ref);
          }
          return _buildRoadmapView(roadmap);
        },
        loading: () => Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context, WidgetRef ref) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.map_outlined, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text(
            'No MVP Roadmap yet.',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          SizedBox(height: 8),
          Text('Synthesize a strategy from your CVP Canvas.'),
          SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () async {
              try {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Generating Roadmap... This may take a moment.')),
                );
                await ref.read(apiServiceProvider).generateRoadmap(teamId);
                ref.refresh(roadmapProvider(teamId));
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Generation Failed: $e'), backgroundColor: Colors.red),
                );
              }
            },
            icon: Icon(Icons.auto_awesome),
            label: Text('Generate with AI'),
          ),
        ],
      ),
    );
  }

  Widget _buildRoadmapView(MVPRoadmap roadmap) {
    return RefreshIndicator(
        onRefresh: () async {}, 
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Card(
                  color: Colors.indigo.shade50,
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('PRODUCT VISION', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.indigo)),
                        SizedBox(height: 8),
                        Text(
                          roadmap.visionStatement,
                          style: TextStyle(fontSize: 18, fontStyle: FontStyle.italic),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            SliverPadding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final feature = roadmap.features[index];
                    return Card(
                      margin: EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        title: Text(feature.title, style: TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(height: 4),
                            Text(feature.description),
                            SizedBox(height: 8),
                            Wrap(
                              spacing: 8,
                              children: [
                                _buildBadge(feature.priority, _getPriorityColor(feature.priority)),
                                _buildBadge(feature.complexity, Colors.grey.shade600),
                              ],
                            ),
                          ],
                        ),
                        isThreeLine: true,
                      ),
                    );
                  },
                  childCount: roadmap.features.length,
                ),
              ),
            )
          ],
        ),
    );
  }
  
  Color _getPriorityColor(String priority) {
    switch (priority.toUpperCase()) {
      case 'MUST_HAVE': return Colors.red;
      case 'SHOULD_HAVE': return Colors.orange;
      case 'COULD_HAVE': return Colors.green;
      case 'WONT_HAVE': return Colors.grey;
      default: return Colors.blue;
    }
  }

  Widget _buildBadge(String text, Color color) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        border: Border.all(color: color),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        text.replaceAll('_', ' '), 
        style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold),
      ),
    );
  }
}
