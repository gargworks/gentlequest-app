import 'package:flutter/material.dart';
import '../../models/interactive_exercise.dart';
import '../../services/api_service.dart';

class GroundingExerciseWidget extends StatefulWidget {
  final GroundingExercise exercise;
  final VoidCallback? onComplete;

  const GroundingExerciseWidget({
    super.key,
    required this.exercise,
    this.onComplete,
  });

  @override
  State<GroundingExerciseWidget> createState() =>
      _GroundingExerciseWidgetState();
}

class _GroundingExerciseWidgetState extends State<GroundingExerciseWidget> {
  int _currentStepIndex = 0;
  bool _isComplete = false;
  bool _hasStarted = false; // Track if we've reported 'started'

  void _nextStep() {
    // Report started on first interaction
    if (!_hasStarted) {
      _hasStarted = true;
      ApiService().reportExerciseOutcome(
        exerciseType: 'grounding',
        outcome: 'started',
      );
    }
    
    if (_currentStepIndex < widget.exercise.steps.length - 1) {
      setState(() => _currentStepIndex++);
    } else {
      // Report completed when all steps done
      ApiService().reportExerciseOutcome(
        exerciseType: 'grounding',
        outcome: 'completed',
      );
      setState(() => _isComplete = true);
      widget.onComplete?.call();
    }
  }

  IconData _getIconForSense(String sense) {
    switch (sense.toLowerCase()) {
      case 'sight':
        return Icons.visibility;
      case 'touch':
        return Icons.touch_app;
      case 'hear':
        return Icons.hearing;
      case 'smell':
        return Icons.local_florist;
      case 'taste':
        return Icons.restaurant;
      default:
        return Icons.accessibility_new;
    }
  }

  Color _getColorForSense(String sense) {
    switch (sense.toLowerCase()) {
      case 'sight':
        return Colors.blue;
      case 'touch':
        return Colors.green;
      case 'hear':
        return Colors.orange; // Ear/Sound
      case 'smell':
        return Colors.purple;
      case 'taste':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final step = widget.exercise.steps[_currentStepIndex];
    final color = _getColorForSense(step.sense);

    if (_isComplete) {
      return Card(
        elevation: 0,
        color: Colors.green.shade50,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 48),
              const SizedBox(height: 16),
              const Text(
                'Great job!',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'You\'ve completed the grounding exercise.',
                textAlign: TextAlign.center,
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
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header: Sense Icon + Title
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    _getIconForSense(step.sense),
                    color: color,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.exercise.name,
                      style: const TextStyle(
                        fontSize: 14,
                        color: Colors.grey,
                      ),
                    ),
                    Text(
                      step.sense.toUpperCase(),
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: color,
                        letterSpacing: 1.0,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Instruction
            Text(
              step.instruction,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 16),

            // Bullet points placeholder (visual aid)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(step.count, (index) {
                return Container(
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.3),
                    shape: BoxShape.circle,
                  ),
                );
              }),
            ),

            const SizedBox(height: 24),

            // Navigation
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Step Indicator Dots
                Row(
                  children: List.generate(widget.exercise.steps.length, (index) {
                    final isActive = index == _currentStepIndex;
                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      width: isActive ? 24 : 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: isActive ? color : Colors.grey.shade300,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    );
                  }),
                ),
                
                ElevatedButton(
                  onPressed: _nextStep,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: color,
                    foregroundColor: Colors.white,
                    shape: const StadiumBorder(),
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                  child: Text(
                    _currentStepIndex == widget.exercise.steps.length - 1
                        ? 'Finish'
                        : 'Next',
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
