import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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

class _GroundingExerciseWidgetState extends State<GroundingExerciseWidget>
    with SingleTickerProviderStateMixin {
  int _currentStepIndex = 0;
  bool _isComplete = false;
  bool _hasStarted = false;
  List<bool> _checkedItems = []; // Track checked items for current step
  
  // Entrance animation
  late AnimationController _entranceController;
  late Animation<double> _slideAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _initCheckedItems();
    
    _entranceController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _slideAnimation = Tween<double>(begin: 20, end: 0).animate(
      CurvedAnimation(parent: _entranceController, curve: Curves.easeOutCubic),
    );
    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _entranceController, curve: Curves.easeOut),
    );
    _entranceController.forward();
  }
  
  @override
  void dispose() {
    _entranceController.dispose();
    super.dispose();
  }
  
  void _initCheckedItems() {
    final step = widget.exercise.steps[_currentStepIndex];
    _checkedItems = List.filled(step.count, false);
  }
  
  void _toggleItem(int index) {
    HapticFeedback.selectionClick();
    setState(() {
      _checkedItems[index] = !_checkedItems[index];
    });
    
    // Check if all items are checked
    if (_checkedItems.every((checked) => checked)) {
      Future.delayed(const Duration(milliseconds: 300), _nextStep);
    }
  }

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
      HapticFeedback.mediumImpact();
      setState(() {
        _currentStepIndex++;
        _initCheckedItems(); // Reset checkboxes for new step
      });
      // Replay entrance animation
      _entranceController.forward(from: 0);
    } else {
      // Report completed when all steps done
      HapticFeedback.heavyImpact();
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

    return AnimatedBuilder(
      animation: _entranceController,
      builder: (context, child) {
        return Transform.translate(
          offset: Offset(0, _slideAnimation.value),
          child: Opacity(
            opacity: _fadeAnimation.value,
            child: Card(
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

            // Interactive checkboxes - tap to check off items
            Wrap(
              alignment: WrapAlignment.center,
              spacing: 8,
              runSpacing: 8,
              children: List.generate(step.count, (index) {
                final isChecked = _checkedItems[index];
                return GestureDetector(
                  onTap: () => _toggleItem(index),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: isChecked ? color : Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isChecked ? color : Colors.grey.shade300,
                        width: 2,
                      ),
                      boxShadow: isChecked
                          ? [
                              BoxShadow(
                                color: color.withValues(alpha: 0.3),
                                blurRadius: 8,
                                spreadRadius: 1,
                              )
                            ]
                          : null,
                    ),
                    child: Center(
                      child: AnimatedSwitcher(
                        duration: const Duration(milliseconds: 150),
                        child: isChecked
                            ? Icon(Icons.check, color: Colors.white, size: 24, key: ValueKey('check_$index'))
                            : Text(
                                '${index + 1}',
                                key: ValueKey('num_$index'),
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.grey.shade500,
                                ),
                              ),
                      ),
                    ),
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
            ),
          ),
        );
      },
    );
  }
}
