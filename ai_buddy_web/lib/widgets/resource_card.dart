import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/resource.dart';

class ResourceCard extends StatelessWidget {
  final Resource resource;
  final Function(int) onView;

  const ResourceCard({
    super.key,
    required this.resource,
    required this.onView,
  });

  Future<void> _launchUrl() async {
    final Uri url = Uri.parse(resource.url);
    if (!await launchUrl(url)) {
      throw Exception('Could not launch $url');
    }
    onView(resource.id);
  }

  Color _getCategoryColor() {
    switch (resource.category) {
      case 'crisis':
        return Colors.red.shade100;
      case 'self_help':
        return Colors.blue.shade100;
      case 'university':
        return Colors.purple.shade100;
      default:
        return Colors.grey.shade100;
    }
  }

  IconData _getCategoryIcon() {
    switch (resource.category) {
      case 'crisis':
        return Icons.warning_amber_rounded;
      case 'self_help':
        return Icons.self_improvement;
      case 'university':
        return Icons.school;
      default:
        return Icons.article;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: _launchUrl,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: _getCategoryColor(),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(_getCategoryIcon(), color: Colors.black54),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          resource.title,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (resource.tags.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Wrap(
                              spacing: 4,
                              children: resource.tags.take(3).map((tag) {
                                return Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.grey.shade100,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(
                                    "#$tag",
                                    style: TextStyle(
                                      fontSize: 10,
                                      color: Colors.grey.shade600,
                                    ),
                                  ),
                                );
                              }).toList(),
                            ),
                          ),
                      ],
                    ),
                  ),
                  const Icon(Icons.open_in_new, size: 16, color: Colors.grey),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                resource.description,
                style: TextStyle(color: Colors.grey.shade700, fontSize: 14),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
