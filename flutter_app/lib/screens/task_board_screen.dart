import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/iip_models.dart';
import '../services/api_service.dart';

final projectTasksProvider = FutureProvider.family<List<ProjectTask>, int>((ref, teamId) async {
  final apiService = ref.watch(apiServiceProvider);
  return apiService.getTasks(teamId);
});

class TaskBoardScreen extends ConsumerWidget {
  final int teamId;

  const TaskBoardScreen({Key? key, required this.teamId}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasksAsync = ref.watch(projectTasksProvider(teamId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Engineering Tasks'),
        actions: [
            IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => ref.refresh(projectTasksProvider(teamId)),
            )
        ]
      ),
      body: tasksAsync.when(
        data: (tasks) {
          if (tasks.isEmpty) {
            return _buildEmptyState(context, ref);
          }
          return _buildTaskListView(tasks, ref);
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context, WidgetRef ref) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.assignment_outlined, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          Text(
            'No Engineering Tasks yet.',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          const Text('Break down your Roadmap into actionable tickets.'),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () async {
              try {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Breaking down roadmap... This make take ~30s.')),
                );
                await ref.read(apiServiceProvider).generateTasks(teamId);
                ref.refresh(projectTasksProvider(teamId));
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Generation Failed: $e'), backgroundColor: Colors.red),
                );
              }
            },
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Generate Tasks from Roadmap'),
          ),
        ],
      ),
    );
  }

  Widget _buildTaskListView(List<ProjectTask> tasks, WidgetRef ref) {
    // Sort by status (TODO first, then IN_PROGRESS, then DONE)? 
    // Or just group headers?
    // Let's do a grouped list view logic manually or just a simple list for now.
    
    return ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: tasks.length,
        itemBuilder: (context, index) {
            final task = tasks[index];
            return Card(
                elevation: 1,
                margin: const EdgeInsets.only(bottom: 8),
                shape: Border(left: BorderSide(color: _getStatusColor(task.status), width: 4)),
                child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                            Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    Expanded(
                                        child: Text(
                                            task.title, 
                                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)
                                        )
                                    ),
                                    _buildStatusChip(task.status),
                                ],
                            ),
                            const SizedBox(height: 4),
                            Text(task.description, style: TextStyle(color: Colors.grey[800], fontSize: 13)),
                            const SizedBox(height: 8),
                            Row(
                                children: [
                                    Icon(Icons.person_outline, size: 16, color: Colors.grey[600]),
                                    const SizedBox(width: 4),
                                    Text(task.assigneeRole ?? 'Unassigned', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                                    const SizedBox(width: 16),
                                    Icon(Icons.timer_outlined, size: 16, color: Colors.grey[600]),
                                    const SizedBox(width: 4),
                                    Text('${task.estimatedHours ?? 0}h', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                                    const Spacer(),
                                    if (task.status == 'TODO')
                                      TextButton.icon(
                                        onPressed: () async {
                                          try {
                                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Delegating to Nucleus Agent...')));
                                            await ref.read(apiServiceProvider).delegateTask(task.taskId!);
                                            ref.refresh(projectTasksProvider(teamId));
                                          } catch (e) {
                                            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Delegation Failed: $e'), backgroundColor: Colors.red));
                                          }
                                        },
                                        icon: const Icon(Icons.smart_toy, size: 16),
                                        label: const Text('Delegate'),
                                        style: TextButton.styleFrom(
                                          foregroundColor: Colors.purple,
                                          padding: EdgeInsets.zero,
                                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                        ),
                                      )
                                ],
                            )
                        ],
                    ),
                ),
            );
        },
    );
  }

  
  Color _getStatusColor(String status) {
      switch (status) {
          case 'TODO': return Colors.grey;
          case 'IN_PROGRESS': return Colors.blue;
          case 'DONE': return Colors.green;
          default: return Colors.grey;
      }
  }

  Widget _buildStatusChip(String status) {
      Color color = _getStatusColor(status);
      return Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: color.withOpacity(0.5))
          ),
          child: Text(status, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color)),
      );
  }
}
