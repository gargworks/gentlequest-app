import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/iip_models.dart';
import '../services/api_service.dart';

final interviewsProvider = FutureProvider.family<List<Interview>, int>((ref, teamId) async {
  return ref.read(apiServiceProvider).getInterviews(teamId);
});

class ResearchViewerScreen extends ConsumerWidget {
  final int teamId;
  const ResearchViewerScreen({super.key, required this.teamId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final interviewsAsync = ref.watch(interviewsProvider(teamId));

    return Scaffold(
      appBar: AppBar(title: const Text('Research Interviews')),
      body: interviewsAsync.when(
        data: (interviews) => ListView.builder(
          itemCount: interviews.length,
          itemBuilder: (context, index) {
            final interview = interviews[index];
            return InterviewCard(interview: interview, teamId: teamId); // Pass teamId
          },
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
           // Basic creation dialog
           _showCreateInterviewDialog(context, ref);
        },
        child: const Icon(Icons.mic),
      ),
    );
  }

  void _showCreateInterviewDialog(BuildContext context, WidgetRef ref) {
      final roleController = TextEditingController();
      final notesController = TextEditingController();
      
      showDialog(
        context: context, 
        builder: (ctx) => AlertDialog(
          title: const Text("Log Interview"),
          content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(controller: roleController, decoration: const InputDecoration(labelText: "Participant Role")),
                  TextField(controller: notesController, maxLines: 3, decoration: const InputDecoration(labelText: "Notes")),
                ],
              ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            TextButton(
              onPressed: () async {
                if (roleController.text.isNotEmpty && notesController.text.isNotEmpty) {
                    try {
                        await ref.read(apiServiceProvider).createInterview(
                            Interview(
                                teamId: teamId,
                                interviewDate: DateTime.now(),
                                participantRole: roleController.text,
                                interviewNotes: notesController.text,
                                insightsExtracted: [],
                            )
                        );
                        ref.refresh(interviewsProvider(teamId));
                        if (context.mounted) Navigator.pop(ctx);
                    } catch (e) {
                        debugPrint(e.toString());
                    }
                }
              }, 
              child: const Text("Save")
            ),
          ],
        )
      );
  }
}

class InterviewCard extends ConsumerWidget {
  final Interview interview;
  final int teamId;

  const InterviewCard({super.key, required this.interview, required this.teamId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final hasInsights = interview.insightsExtracted.isNotEmpty;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(interview.participantRole, style: Theme.of(context).textTheme.titleMedium),
            Text(interview.interviewDate.toString().split(' ')[0], style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            Text(interview.interviewNotes, maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 12),
            if (hasInsights) _buildInsightsList(context) else _buildAnalyzeButton(context, ref),
          ],
        ),
      ),
    );
  }

  Widget _buildAnalyzeButton(BuildContext context, WidgetRef ref) {
    return Align(
        alignment: Alignment.centerRight,
        child: FilledButton.icon(
            onPressed: () async {
                try {
                    await ref.read(apiServiceProvider).analyzeInterview(teamId, interview.interviewId!);
                    // Force refresh to see new insights
                    ref.invalidate(interviewsProvider(teamId));
                } catch (e) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Analysis Failed: $e")));
                }
            }, 
            icon: const Icon(Icons.psychology), 
            label: const Text("Analyze (ANRUM)")
        ),
    );
  }

  Widget _buildInsightsList(BuildContext context) {
      return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
              const Divider(),
              Text("ANRUM Insights", style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 4),
              Wrap(
                  spacing: 4,
                  children: interview.insightsExtracted.map((insight) => Chip(
                      label: Text("${insight.category}: ${insight.insight}"),
                      backgroundColor: _getColorForCategory(insight.category).withOpacity(0.2),
                  )).toList()
              )
          ],
      );
  }

  Color _getColorForCategory(String category) {
      switch (category.toUpperCase()) {
          case 'A': return Colors.red;
          case 'N': return Colors.orange;
          case 'R': return Colors.blue;
          case 'U': return Colors.green;
          case 'M': return Colors.purple;
          default: return Colors.grey;
      }
  }
}
