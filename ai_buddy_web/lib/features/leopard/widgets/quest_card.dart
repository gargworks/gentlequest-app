import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // For Haptics & Clipboard
import 'package:ai_buddy_web/features/leopard/models/leopard_quest.dart';

class QuestCard extends StatefulWidget {
  final LeopardQuest quest;
  final VoidCallback? onCompleted;
  final VoidCallback? onShare; // Callback for sharing logic

  const QuestCard({
    super.key,
    required this.quest,
    this.onCompleted,
    this.onShare,
  });

  @override
  State<QuestCard> createState() => _QuestCardState();
}

class _QuestCardState extends State<QuestCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _blurAnimation;
  late Animation<double> _opacityAnimation;
  bool _isShared = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000), // 2 seconds total reveal
    );

    // Phase 1: Fade In (0ms - 500ms)
    _opacityAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.25, curve: Curves.easeIn),
      ),
    );

    // Phase 2: Sharpen/Deblur (500ms - 2000ms) - "The Matrix Effect"
    _blurAnimation = Tween<double>(begin: 20.0, end: 0.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.25, 1.0, curve: Curves.easeOutExpo),
      ),
    );

    // Trigger animation explicitly on mount
    _controller.forward();
    HapticFeedback.heavyImpact(); // The "Download Started" thud
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onStepToggled(QuestStep step, bool value) {
    setState(() {
      step.isCompleted = value;
    });

    // Check for Victory
    if (widget.quest.steps.every((s) => s.isCompleted)) {
      HapticFeedback.heavyImpact(); // Victory Thud
      widget.onCompleted?.call();
    }
  }

  void _handleShare() {
    HapticFeedback.mediumImpact();
    widget.onShare?.call();
    setState(() {
      _isShared = true;
    });

    // Reset icon after a delay
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        setState(() {
          _isShared = false;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(
              sigmaX: _blurAnimation.value,
              sigmaY: _blurAnimation.value,
            ),
            child: Opacity(
              opacity: _opacityAnimation.value,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.6), // Dark Glass
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: const Color(0xFF667EEA).withOpacity(0.5),
                    width: 1.5,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF667EEA).withOpacity(0.2),
                      blurRadius: 30,
                      spreadRadius: -5,
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildHeader(),
                    const Divider(color: Colors.white10),
                    _buildSteps(),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildHeader() {
    bool allCompleted = widget.quest.steps.every((s) => s.isCompleted);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF667EEA).withOpacity(0.1),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFF667EEA).withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.shield_outlined,
                color: Color(0xFF667EEA), size: 28),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.quest.title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    letterSpacing: 1.5,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  "TARGET: ${widget.quest.bossName.toUpperCase()}",
                  style: const TextStyle(
                    color: Colors.redAccent,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),

          // SHARE BUTTON (Only visible or active if completed)
          IconButton(
            onPressed: allCompleted ? _handleShare : null,
            icon: Icon(
              _isShared ? Icons.check : Icons.share_outlined,
              color: allCompleted
                  ? (_isShared ? Colors.green : const Color(0xFF667EEA))
                  : Colors.white24,
            ),
            tooltip: "Share Protocol Result",
          ),

          const SizedBox(width: 8),

          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.amber.withOpacity(0.5)),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              "+${widget.quest.xpReward} XP",
              style: const TextStyle(
                  color: Colors.amber,
                  fontWeight: FontWeight.bold,
                  fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSteps() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: widget.quest.steps
            .map((step) => _StepRow(
                  step: step,
                  onChanged: (val) => _onStepToggled(step, val),
                ))
            .toList(),
      ),
    );
  }
}

class _StepRow extends StatelessWidget {
  final QuestStep step;
  final ValueChanged<bool> onChanged;

  const _StepRow({required this.step, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final isChecked = step.isCompleted;

    return GestureDetector(
      onTap: () {
        HapticFeedback.mediumImpact();
        onChanged(!isChecked);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isChecked
              ? const Color(0xFF667EEA).withOpacity(0.2)
              : Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isChecked ? const Color(0xFF667EEA) : Colors.white10,
          ),
        ),
        child: Row(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isChecked ? const Color(0xFF667EEA) : Colors.transparent,
                border: Border.all(
                  color: isChecked ? const Color(0xFF667EEA) : Colors.grey,
                  width: 2,
                ),
              ),
              child: isChecked
                  ? const Icon(Icons.check, size: 16, color: Colors.white)
                  : null,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    step.title,
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      decoration: isChecked ? TextDecoration.lineThrough : null,
                      decorationColor: Colors.white54,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    step.instruction,
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                      decoration: isChecked ? TextDecoration.lineThrough : null,
                      decorationColor: Colors.white54,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
