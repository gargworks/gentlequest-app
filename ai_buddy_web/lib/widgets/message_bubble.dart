import 'package:flutter/material.dart';
import 'package:ai_buddy_web/models/message.dart';
import 'package:ai_buddy_web/theme/gq_tokens.dart';

class MessageBubble extends StatelessWidget {
  final Message message;
  final bool isError;
  final VoidCallback? onRetry;

  const MessageBubble({
    super.key,
    required this.message,
    this.isError = false,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (isError) {
      return Align(
        alignment: Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 8),
          decoration: BoxDecoration(
            color: GQColors.coral.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.error_outline,
                      size: 16, color: GQColors.coral),
                  const SizedBox(width: 6),
                  Flexible(
                    child: Text(
                      message.content,
                      style: const TextStyle(color: Colors.black87),
                    ),
                  ),
                ],
              ),
              if (onRetry != null)
                TextButton(
                  onPressed: onRetry,
                  style: TextButton.styleFrom(
                    foregroundColor: GQColors.primary,
                    padding:
                        const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  child: const Text('Retry'),
                ),
            ],
          ),
        ),
      );
    }

    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: message.getMessageColor(context),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(
          message.content,
          style: TextStyle(
            color: message.getTextColor(context),
          ),
        ),
      ),
    );
  }
}
