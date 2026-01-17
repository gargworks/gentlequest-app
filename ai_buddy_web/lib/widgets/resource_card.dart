import 'package:flutter/material.dart';
import '../models/resource.dart';

class ResourceCard extends StatelessWidget {
  final Resource resource;
  final VoidCallback onTap;

  const ResourceCard({
    Key? key,
    required this.resource,
    required this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  _buildCategoryIcon(),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      resource.title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios,
                      size: 16, color: Colors.grey),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                resource.description,
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 14,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              if (resource.tags.isNotEmpty) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: resource.tags.take(3).map((tag) {
                    return Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        tag,
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey[700],
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryIcon() {
    IconData icon;
    Color color;

    switch (resource.category.toLowerCase()) {
      case 'crisis':
        icon = Icons.emergency;
        color = Colors.red;
        break;
      case 'self_help':
        icon = Icons.self_improvement;
        color = Colors.blue;
        break;
      case 'university':
        icon = Icons.school;
        color = Colors.purple;
        break;
      case 'external':
        icon = Icons.link;
        color = Colors.green;
        break;
      default:
        icon = Icons.help;
        color = Colors.grey;
    }

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: color, size: 20),
    );
  }
}
