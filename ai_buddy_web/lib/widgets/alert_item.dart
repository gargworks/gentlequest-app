import 'package:flutter/material.dart';
import '../models/counselor_alert.dart';

class AlertItem extends StatelessWidget {
  final CounselorAlert alert;
  final VoidCallback onTap;

  const AlertItem({
    Key? key,
    required this.alert,
    required this.onTap,
  }) : super(key: key);

  Color _getSeverityColor() {
    switch (alert.severity) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.amber;
      default:
        return Colors.blue;
    }
  }

  bool get _isAcknowledged => alert.acknowledgedAt != null;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      elevation: _isAcknowledged ? 0 : 2,
      color: _isAcknowledged ? Colors.grey.shade100 : Colors.white,
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: _isAcknowledged 
              ? Colors.grey.shade300 
              : _getSeverityColor().withOpacity(0.2),
          child: Icon(
            Icons.warning_amber_rounded,
            color: _isAcknowledged ? Colors.grey : _getSeverityColor(),
          ),
        ),
        title: Text(
          alert.triggerMessage,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            fontWeight: _isAcknowledged ? FontWeight.normal : FontWeight.bold,
            color: _isAcknowledged ? Colors.grey.shade700 : Colors.black87,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Row(
              children: [
                _Badge(
                  label: alert.severity.toUpperCase(), 
                  color: _getSeverityColor()
                ),
                const SizedBox(width: 8),
                Text(
                  "Session: ${alert.sessionId.substring(0, 8)}...",
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              alert.sentAt.split("T").join(" ").substring(0, 16),
              style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
            ),
          ],
        ),
        trailing: _isAcknowledged
            ? const Icon(Icons.check_circle, color: Colors.green)
            : const Icon(Icons.chevron_right),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  final String label;
  final Color color;

  const _Badge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
