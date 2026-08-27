import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../models/iip_models.dart';
import '../services/api_service.dart';

final teamsProvider = FutureProvider<List<Team>>((ref) async {
  return ref.read(apiServiceProvider).getTeams();
});

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final teamsAsync = ref.watch(teamsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('IIP Projects')),
      body: teamsAsync.when(
        data: (teams) => ListView.builder(
          itemCount: teams.length,
          itemBuilder: (context, index) {
            final team = teams[index];
            return Card(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: ListTile(
                title: Text(team.teamName, style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text(team.projectFocus),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.people),
                      tooltip: 'Personas',
                      onPressed: () => context.push('/team/${team.teamId}/personas', extra: team.teamName),
                    ),
                    IconButton(
                      icon: Icon(Icons.view_quilt, color: Colors.purple),
                      tooltip: 'CVP Canvas',
                      onPressed: () {
                        context.push('/team/${team.teamId}/cvp', extra: team.teamName);
                      },
                    ),
                    IconButton(
                      icon: Icon(Icons.chat, color: Colors.green),
                      tooltip: 'AI Interview',
                      onPressed: () {
                        context.push('/team/${team.teamId}/chat', extra: team.teamName);
                      },
                    ),
                    IconButton(
                      icon: Icon(Icons.timeline, color: Colors.blue),
                      tooltip: 'MVP Roadmap',
                      onPressed: () {
                        context.push('/team/${team.teamId}/roadmap', extra: team.teamName);
                      },
                    ),
                    IconButton(
                      icon: Icon(Icons.assignment, color: Colors.orange),
                      tooltip: 'Project Tasks',
                      onPressed: () {
                        context.push('/team/${team.teamId}/tasks', extra: team.teamName);
                      },
                    ),
                    IconButton(
                      icon: Icon(Icons.psychology, color: Colors.teal),
                      tooltip: 'Project Brain',
                      onPressed: () {
                        context.push('/team/${team.teamId}/project-chat', extra: team.teamName);
                      },
                    ),
                  ],
                ),

                onTap: () => context.push('/team/${team.teamId}'),
              ),
            );
          },
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // TODO: Implement Create Team Dialog
          // For now, verification relies on pre-seeded data or backend curl
           _showCreateTeamDialog(context, ref);
        },
        child: const Icon(Icons.add),
      ),
    );
  }
  
  void _showCreateTeamDialog(BuildContext context, WidgetRef ref) {
      final nameController = TextEditingController();
      final focusController = TextEditingController();
      
      showDialog(
        context: context, 
        builder: (ctx) => AlertDialog(
          title: const Text("New Project"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameController, decoration: const InputDecoration(labelText: "Team Name")),
              TextField(controller: focusController, decoration: const InputDecoration(labelText: "Project Focus")),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            TextButton(
              onPressed: () async {
                if (nameController.text.isNotEmpty && focusController.text.isNotEmpty) {
                    try {
                        await ref.read(apiServiceProvider).createTeam(
                            Team(teamName: nameController.text, projectFocus: focusController.text)
                        );
                        ref.refresh(teamsProvider); // Reload list
                        if (context.mounted) Navigator.pop(ctx);
                    } catch (e) {
                         // Simple error handling
                        debugPrint(e.toString());
                    }
                }
              }, 
              child: const Text("Create")
            ),
          ],
        )
      );
  }
}
