// weekly_letter_screen.dart — Screen host for the WeeklyLetter widget.
//
// Background gradient: #F8F7FF → #F5F3FC → #FBF6F6.
// Takes WeeklyReviewData as a parameter and renders WeeklyLetter inside a
// scrollable SafeArea.

import 'package:flutter/material.dart';

import '../theme/gq_tokens.dart';
import '../widgets/weekly_letter.dart';
import 'weekly_review_screen.dart' show WeeklyReviewData;

class WeeklyLetterScreen extends StatelessWidget {
  const WeeklyLetterScreen({
    super.key,
    required this.data,
    this.onDismiss,
  });

  final WeeklyReviewData data;
  final VoidCallback? onDismiss;

  static const _gradientColors = [
    Color(0xFFF8F7FF),
    Color(0xFFF5F3FC),
    Color(0xFFFBF6F6),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: _gradientColors,
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _TopBar(onClose: onDismiss ?? () => Navigator.of(context).maybePop()),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.only(bottom: 32),
                  child: WeeklyLetter(data: data, onClose: onDismiss),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.onClose});
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Align(
        alignment: Alignment.centerRight,
        child: GestureDetector(
          onTap: onClose,
          child: Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              border: Border.all(color: GQColors.hair),
            ),
            child: const Icon(Icons.close, size: 14, color: GQColors.ink),
          ),
        ),
      ),
    );
  }
}
