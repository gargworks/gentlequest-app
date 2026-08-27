import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/iip_models.dart';
import '../services/api_service.dart';

final personasProvider = FutureProvider.family<List<Persona>, int>((ref, teamId) async {
  final apiService = ref.read(apiServiceProvider);
  return apiService.getPersonas(teamId);
});

class PersonaListScreen extends ConsumerWidget {
  final int teamId;
  final String teamName;

  const PersonaListScreen({super.key, required this.teamId, required this.teamName});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final personasAsyncValue = ref.watch(personasProvider(teamId));

    return Scaffold(
      appBar: AppBar(
        title: Text('Personas: $teamName'),
      ),
      body: personasAsyncValue.when(
        data: (personas) => personas.isEmpty
            ? const Center(child: Text('No personas generated yet.'))
            : ListView.builder(
                itemCount: personas.length,
                itemBuilder: (context, index) {
                  final persona = personas[index];
                  return Card(
                    margin: const EdgeInsets.all(8.0),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(persona.name, style: Theme.of(context).textTheme.headlineSmall),
                          if (persona.age != null) Text('${persona.age} years old'),
                          if (persona.context != null) Text(persona.context!, style: const TextStyle(fontStyle: FontStyle.italic)),
                          const SizedBox(height: 8),
                          if (persona.supportingQuotes.isNotEmpty)
                            Container(
                                padding: const EdgeInsets.all(8),
                                color: Colors.grey[200],
                                child: Text('"${persona.supportingQuotes.first}"', style: const TextStyle(fontStyle: FontStyle.italic))
                            ),
                          const SizedBox(height: 8),
                          const Text("Frustrations:", style: TextStyle(fontWeight: FontWeight.bold)),
                          ...persona.frustrations.take(3).map((e) => Text("• $e")),
                        ],
                      ),
                    ),
                  );
                },
              ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          // Trigger Generation
          try {
            // Show loading dialog
             showDialog(
              context: context,
              barrierDismissible: false,
              builder: (BuildContext context) {
                return const Center(child: CircularProgressIndicator());
              },
            );
            
            final apiService = ref.read(apiServiceProvider);
            await apiService.generatePersonas(teamId);
            
            if (context.mounted) {
               Navigator.pop(context); // Close loading
               ref.refresh(personasProvider(teamId)); // Refresh list
            }
          } catch (e) {
             if (context.mounted) {
               Navigator.pop(context); // Close loading
               ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Generation Failed: $e')));
            }
          }
        },
        label: const Text('Generate Personas'),
        icon: const Icon(Icons.auto_awesome),
      ),
    );
  }
}
