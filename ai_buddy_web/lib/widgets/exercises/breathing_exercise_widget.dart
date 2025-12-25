import 'dart:async';
import 'package:flutter/material.dart';
import '../../models/interactive_exercise.dart';

class BreathingExerciseWidget extends StatefulWidget {
  final BreathingExercise exercise;
  final VoidCallback? onComplete;

  const BreathingExerciseWidget({
    super.key,
    required this.exercise,
    this.onComplete,
  });

  @override
  State<BreathingExerciseWidget> createState() =>
      _BreathingExerciseWidgetState();
}

class _BreathingExerciseWidgetState extends State<BreathingExerciseWidget>
    with SingleTickerProviderStateMixin {
  bool _isActive = false;
  int _currentCycle = 1;
  int _currentStepIndex = 0;
  int _timeLeftInStep = 0;
  Timer? _timer;
  late AnimationController _animController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4), // Default start
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.0).animate(_animController);
  }

  @override
  void dispose() {
    _timer?.cancel();
    _animController.dispose();
    super.dispose();
  }

  void _startExercise() {
    setState(() {
      _isActive = true;
      _currentCycle = 1;
      _currentStepIndex = 0;
    });
    _runStep();
  }

  void _runStep() {
    if (!mounted) return;
    
    // Check if exercise complete
    if (_currentCycle > widget.exercise.cycles) {
      setState(() => _isActive = false);
      widget.onComplete?.call();
      return;
    }

    final step = widget.exercise.steps[_currentStepIndex];
    setState(() => _timeLeftInStep = step.duration);

    // Setup animation based on action
    _animController.duration = Duration(seconds: step.duration);
    if (step.action == 'breathe_in') {
      _scaleAnimation = Tween<double>(begin: 1.0, end: 1.5).animate(
        CurvedAnimation(parent: _animController, curve: Curves.easeInOut),
      );
      _animController.forward(from: 0.0);
    } else if (step.action == 'breathe_out') {
      _scaleAnimation = Tween<double>(begin: 1.5, end: 1.0).animate(
        CurvedAnimation(parent: _animController, curve: Curves.easeInOut),
      );
      _animController.forward(from: 0.0);
    } else {
      // Hold - keep current scale
      _animController.stop(); 
    }

    // Start countdown
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      setState(() {
        if (_timeLeftInStep > 0) {
          _timeLeftInStep--;
        } else {
          _timer?.cancel();
          _advanceStep();
        }
      });
    });
  }

  void _advanceStep() {
    int nextIndex = _currentStepIndex + 1;
    if (nextIndex >= widget.exercise.steps.length) {
      // Cycle complete
      setState(() {
        _currentCycle++;
        _currentStepIndex = 0;
      });
    } else {
      setState(() => _currentStepIndex = nextIndex);
    }
    _runStep();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isActive) {
      return Card(
        elevation: 0,
        color: Colors.blue.shade50,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                   Icon(Icons.air, color: Colors.blue.shade700),
                   const SizedBox(width: 8),
                   Text(
                     widget.exercise.name,
                     style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                   ),
                ],
              ),
              const SizedBox(height: 8),
              Text(widget.exercise.description),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _startExercise,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  ),
                  child: Text('Start (${widget.exercise.totalTimeSeconds}s)'),
                ),
              ),
            ],
          ),
        ),
      );
    }

    final currentStep = widget.exercise.steps[_currentStepIndex];

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        padding: const EdgeInsets.all(24.0),
        width: double.infinity,
        child: Column(
          children: [
            // Progress
            Text(
              'Cycle $_currentCycle / ${widget.exercise.cycles}',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
            ),
            const SizedBox(height: 24),
            
            // Animation Circle
            AnimatedBuilder(
              animation: _animController,
              builder: (context, child) {
                return Transform.scale(
                  scale: _scaleAnimation.value,
                  child: Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(
                        colors: [
                          Colors.blue.shade200,
                          Colors.blue.shade50,
                        ],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.blue.withValues(alpha: 0.2),
                          blurRadius: 20 * _scaleAnimation.value,
                          spreadRadius: 5,
                        )
                      ],
                    ),
                    child: Center(
                      child: Text(
                        '$_timeLeftInStep',
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue.shade800,
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
            
            const SizedBox(height: 24),
            
            // Instruction
            Text(
              currentStep.instruction,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
             const SizedBox(height: 8),
             Text(
               currentStep.action.toUpperCase().replaceAll('_', ' '),
               style: TextStyle(
                 fontSize: 12,
                 letterSpacing: 1.5,
                 color: Colors.grey.shade500,
                 fontWeight: FontWeight.bold
               ),
             ),
          ],
        ),
      ),
    );
  }
}
