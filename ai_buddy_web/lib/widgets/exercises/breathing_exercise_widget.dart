import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../models/interactive_exercise.dart';
import '../../services/api_service.dart';

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
    with TickerProviderStateMixin {
  bool _isActive = false;
  int _currentCycle = 1;
  int _currentStepIndex = 0;
  int _timeLeftInStep = 0;
  Timer? _timer;

  // Breathing animation controller
  late AnimationController _breathController;
  late Animation<double> _scaleAnimation;

  // Entrance animation controller
  late AnimationController _entranceController;
  late Animation<double> _slideAnimation;
  late Animation<double> _fadeAnimation;

  // Glow pulse animation
  late AnimationController _glowController;

  @override
  void initState() {
    super.initState();

    // Breathing animation
    _breathController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    );
    _scaleAnimation =
        Tween<double>(begin: 1.0, end: 1.0).animate(_breathController);

    // Entrance animation - slide up and fade in
    _entranceController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _slideAnimation = Tween<double>(begin: 30, end: 0).animate(
      CurvedAnimation(parent: _entranceController, curve: Curves.easeOutCubic),
    );
    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _entranceController, curve: Curves.easeOut),
    );

    // Subtle glow pulse
    _glowController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);

    // Start entrance animation
    _entranceController.forward();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _breathController.dispose();
    _entranceController.dispose();
    _glowController.dispose();
    super.dispose();
  }

  void _startExercise() {
    // Haptic feedback on start
    HapticFeedback.mediumImpact();

    // Report exercise started for session tracking
    ApiService().reportExerciseOutcome(
      exerciseType: 'breathing',
      outcome: 'started',
    );

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
      HapticFeedback.heavyImpact(); // Completion haptic

      // Report exercise completed for session tracking
      ApiService().reportExerciseOutcome(
        exerciseType: 'breathing',
        outcome: 'completed',
        timeSpentSeconds: widget.exercise.totalTimeSeconds,
      );

      setState(() => _isActive = false);
      widget.onComplete?.call();
      return;
    }

    final step = widget.exercise.steps[_currentStepIndex];
    setState(() => _timeLeftInStep = step.duration);

    // Subtle haptic on phase change
    HapticFeedback.lightImpact();

    // Setup animation based on action
    _breathController.duration = Duration(seconds: step.duration);
    if (step.action == 'breathe_in') {
      _scaleAnimation = Tween<double>(begin: 1.0, end: 1.5).animate(
        CurvedAnimation(parent: _breathController, curve: Curves.easeInOut),
      );
      _breathController.forward(from: 0.0);
    } else if (step.action == 'breathe_out') {
      _scaleAnimation = Tween<double>(begin: 1.5, end: 1.0).animate(
        CurvedAnimation(parent: _breathController, curve: Curves.easeInOut),
      );
      _breathController.forward(from: 0.0);
    } else {
      // Hold - keep current scale
      _breathController.stop();
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

  // Get color based on current action
  Color _getPhaseColor(String action) {
    switch (action) {
      case 'breathe_in':
        return const Color(0xFF4FC3F7); // Light blue - inhale
      case 'hold':
        return const Color(0xFF81C784); // Green - hold
      case 'breathe_out':
        return const Color(0xFFB39DDB); // Purple - exhale
      default:
        return const Color(0xFF4FC3F7);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _entranceController,
      builder: (context, child) {
        return Transform.translate(
          offset: Offset(0, _slideAnimation.value),
          child: Opacity(
            opacity: _fadeAnimation.value,
            child: _isActive ? _buildActiveWidget() : _buildStartWidget(),
          ),
        );
      },
    );
  }

  Widget _buildStartWidget() {
    return AnimatedBuilder(
      animation: _glowController,
      builder: (context, child) {
        final glowValue = 0.1 + (_glowController.value * 0.1);
        return Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                const Color(0xFFE3F2FD),
                const Color(0xFFBBDEFB).withValues(alpha: 0.8),
              ],
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF42A5F5).withValues(alpha: glowValue),
                blurRadius: 20,
                spreadRadius: 2,
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.7),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.air_rounded,
                        color: Color(0xFF1976D2),
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        widget.exercise.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: Color(0xFF1565C0),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  widget.exercise.description,
                  style: TextStyle(
                    color: Colors.grey.shade700,
                    fontSize: 14,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: _startExercise,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1976D2),
                      foregroundColor: Colors.white,
                      elevation: 4,
                      shadowColor:
                          const Color(0xFF1976D2).withValues(alpha: 0.4),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(24),
                      ),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.play_arrow_rounded, size: 22),
                        const SizedBox(width: 8),
                        Text(
                          'Start (${widget.exercise.totalTimeSeconds}s)',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildActiveWidget() {
    final currentStep = widget.exercise.steps[_currentStepIndex];
    final phaseColor = _getPhaseColor(currentStep.action);

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.white,
            phaseColor.withValues(alpha: 0.1),
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: phaseColor.withValues(alpha: 0.2),
            blurRadius: 20,
            spreadRadius: 2,
          ),
        ],
      ),
      padding: const EdgeInsets.all(24.0),
      width: double.infinity,
      child: Column(
        children: [
          // Progress indicator
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ...List.generate(widget.exercise.cycles, (index) {
                final isCurrent = index + 1 == _currentCycle;
                final isComplete = index + 1 < _currentCycle;
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    width: isCurrent ? 24 : 8,
                    height: 8,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(4),
                      color: isComplete
                          ? phaseColor
                          : isCurrent
                              ? phaseColor
                              : Colors.grey.shade300,
                    ),
                  ),
                );
              }),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Cycle $_currentCycle of ${widget.exercise.cycles}',
            style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
          ),
          const SizedBox(height: 24),

          // Breathing Circle with ripple effect
          Stack(
            alignment: Alignment.center,
            children: [
              // Outer ripple
              AnimatedBuilder(
                animation: _breathController,
                builder: (context, child) {
                  return Container(
                    width: 160,
                    height: 160,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: phaseColor.withValues(
                            alpha: 0.3 * _scaleAnimation.value),
                        width: 2,
                      ),
                    ),
                  );
                },
              ),
              // Main breathing circle
              AnimatedBuilder(
                animation: _breathController,
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
                            phaseColor.withValues(alpha: 0.8),
                            phaseColor.withValues(alpha: 0.4),
                          ],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: phaseColor.withValues(alpha: 0.4),
                            blurRadius: 30 * _scaleAnimation.value,
                            spreadRadius: 5,
                          )
                        ],
                      ),
                      child: Center(
                        child: Text(
                          '$_timeLeftInStep',
                          style: const TextStyle(
                            fontSize: 40,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Instruction with phase indicator
          Text(
            currentStep.instruction,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w600,
              color: Colors.grey.shade800,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            decoration: BoxDecoration(
              color: phaseColor.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              currentStep.action.toUpperCase().replaceAll('_', ' '),
              style: TextStyle(
                fontSize: 12,
                letterSpacing: 2,
                color: phaseColor,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
