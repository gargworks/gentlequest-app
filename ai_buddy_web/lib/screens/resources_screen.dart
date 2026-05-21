import 'package:flutter/material.dart';
import 'resource_library_screen.dart';

// Stub replaced: redirect to ResourceLibraryScreen.
class ResourcesScreen extends StatelessWidget {
  const ResourcesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (context.mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const ResourceLibraryScreen()),
        );
      }
    });
    return const Scaffold(body: SizedBox.shrink());
  }
}
