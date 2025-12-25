import 'package:flutter/material.dart';
import '../../models/interactive_exercise.dart';

class JournalPromptCard extends StatefulWidget {
  final JournalPrompt exercise;
  final Function(String)? onSave;

  const JournalPromptCard({
    super.key,
    required this.exercise,
    this.onSave,
  });

  @override
  State<JournalPromptCard> createState() => _JournalPromptCardState();
}

class _JournalPromptCardState extends State<JournalPromptCard> {
  final TextEditingController _controller = TextEditingController();
  bool _isSaved = false;

  void _saveEntry() {
    if (_controller.text.trim().isEmpty) return;
    
    widget.onSave?.call(_controller.text);
    setState(() => _isSaved = true);
    
    // Hide keyboard
    FocusScope.of(context).unfocus();
  }

  void _useSuggestion(String suggestion) {
    if (_isSaved) return;
    final current = _controller.text;
    final separator = current.isEmpty ? '' : '\n\n';
    _controller.text = '$current$separator$suggestion';
    // Move cursor to end
    _controller.selection = TextSelection.fromPosition(
      TextPosition(offset: _controller.text.length),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isSaved) {
       return Card(
        elevation: 0,
        color: Colors.amber.shade50,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              Icon(Icons.check_circle_outline, color: Colors.amber.shade800, size: 48),
              const SizedBox(height: 16),
              const Text(
                'Entry Saved',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 8),
              Text(
                'Your reflection has been recorded.',
                style: TextStyle(color: Colors.grey.shade700),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.amber.shade100,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(Icons.edit_note, color: Colors.amber.shade900),
                ),
                const SizedBox(width: 12),
                const Text(
                  'Journal Prompt',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Prompt Text
            Text(
              widget.exercise.prompt,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
                color: Colors.black87,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 16),
            
            // Input Area
            TextField(
              controller: _controller,
              maxLines: 4,
              minLines: 3,
              decoration: InputDecoration(
                hintText: 'Write your thoughts here...',
                filled: true,
                fillColor: Colors.grey.shade50,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.grey.shade300),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.grey.shade300),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.amber.shade400, width: 2),
                ),
              ),
            ),
            const SizedBox(height: 12),
            
            // Suggestions Chips
            if (widget.exercise.suggestions != null && widget.exercise.suggestions!.isNotEmpty)
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: widget.exercise.suggestions!.map((s) {
                  return ActionChip(
                    label: Text(s),
                    backgroundColor: Colors.amber.shade50,
                    labelStyle: TextStyle(color: Colors.amber.shade900, fontSize: 12),
                    onPressed: () => _useSuggestion(s),
                  );
                }).toList(),
              ),
              
            const SizedBox(height: 16),
            
            // Save Button
            ElevatedButton(
              onPressed: _saveEntry,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.amber.shade800,
                foregroundColor: Colors.white,
                shape: const StadiumBorder(),
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
              child: const Text('Save Entry'),
            ),
          ],
        ),
      ),
    );
  }
}
