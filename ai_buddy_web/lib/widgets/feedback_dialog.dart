import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/app_export.dart';
import '../../../services/analytics_service.dart';

class FeedbackDialog extends StatefulWidget {
  const FeedbackDialog({super.key});

  @override
  State<FeedbackDialog> createState() => _FeedbackDialogState();
}

class _FeedbackDialogState extends State<FeedbackDialog> {
  int _rating = 0;
  final TextEditingController _feedbackController = TextEditingController();
  bool _isSubmitting = false;

  @override
  void dispose() {
    _feedbackController.dispose();
    super.dispose();
  }

  void _submitFeedback() async {
    if (_rating == 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a rating')),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      // Log feedback to analytics
      await logAnalyticsEvent('app_feedback_submitted', metadata: {
        'rating': _rating,
        'has_text': _feedbackController.text.trim().isNotEmpty,
        'trigger': 'after_3rd_checkin',
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      });

      // Store feedback locally (could also send to backend)
      final prefs = await SharedPreferences.getInstance();
      final feedbackList = prefs.getStringList('user_feedback') ?? [];
      feedbackList.add({
        'rating': _rating,
        'feedback': _feedbackController.text.trim(),
        'date': DateTime.now().toIso8601String(),
        'trigger': 'after_3rd_checkin',
      }.toString());
      await prefs.setStringList('user_feedback', feedbackList);

      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Thank you for your feedback! 💙'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Failed to submit feedback. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16.h)),
      child: Padding(
        padding: EdgeInsets.all(24.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'How are you finding GentleQuest?',
              style: TextStyleHelper.instance.title18Regular.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            SizedBox(height: 8.h),
            Text(
              'Your feedback helps us improve the experience for everyone.',
              style: TextStyleHelper.instance.body14Medium.copyWith(
                color: Color(0xFF6B7280),
                fontWeight: FontWeight.w400,
              ),
            ),
            SizedBox(height: 24.h),

            // Rating stars
            Text(
              'Overall experience',
              style: TextStyleHelper.instance.body14Medium,
            ),
            SizedBox(height: 12.h),
            Row(
              children: List.generate(5, (index) {
                return GestureDetector(
                  onTap: () => setState(() => _rating = index + 1),
                  child: Padding(
                    padding: EdgeInsets.only(right: 8.h),
                    child: Icon(
                      index < _rating ? Icons.star : Icons.star_border,
                      size: 32.h,
                      color: Color(0xFFFFC107),
                    ),
                  ),
                );
              }),
            ),
            SizedBox(height: 24.h),

            // Text feedback
            Text(
              'Any specific thoughts or suggestions? (optional)',
              style: TextStyleHelper.instance.body14Medium,
            ),
            SizedBox(height: 12.h),
            TextField(
              controller: _feedbackController,
              maxLines: 3,
              textInputAction: TextInputAction.done,
              decoration: InputDecoration(
                hintText: 'What could we do better? What do you like?',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8.h),
                  borderSide: BorderSide(color: Color(0xFFE5E7EB)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8.h),
                  borderSide: BorderSide(color: Color(0xFFE5E7EB)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8.h),
                  borderSide: BorderSide(color: Color(0xFF3B82F6)),
                ),
              ),
            ),
            SizedBox(height: 24.h),

            // Buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed:
                      _isSubmitting ? null : () => Navigator.of(context).pop(),
                  child: Text(
                    'Maybe later',
                    style: TextStyleHelper.instance.body14Medium.copyWith(
                      color: Color(0xFF6B7280),
                    ),
                  ),
                ),
                SizedBox(width: 16.h),
                ElevatedButton(
                  onPressed: _isSubmitting ? null : _submitFeedback,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Color(0xFF3B82F6),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.h),
                    ),
                  ),
                  child: _isSubmitting
                      ? SizedBox(
                          height: 16.h,
                          width: 16.h,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation(Colors.white),
                          ),
                        )
                      : Text(
                          'Submit',
                          style: TextStyleHelper.instance.body14Medium.copyWith(
                            color: Colors.white,
                          ),
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

// Helper function to show feedback dialog
void showFeedbackDialog(BuildContext context) {
  showDialog(
    context: context,
    barrierDismissible: false,
    builder: (context) => const FeedbackDialog(),
  );
}

// Helper function to check and show feedback if needed
Future<void> checkAndShowFeedback(BuildContext context) async {
  try {
    final prefs = await SharedPreferences.getInstance();
    final checkinCount = prefs.getInt('checkin_count') ?? 0;
    final feedbackShown = prefs.getBool('feedback_shown') ?? false;

    // Show feedback after 3rd check-in if not already shown
    if (checkinCount >= 3 && !feedbackShown) {
      // Mark as shown to avoid showing again
      await prefs.setBool('feedback_shown', true);

      // Show dialog with slight delay to allow UI to settle
      Future.delayed(const Duration(milliseconds: 500), () {
        if (context.mounted) {
          showFeedbackDialog(context);
        }
      });
    }
  } catch (e) {
    // Silently fail to not disrupt user experience
    print('Error checking feedback prompt: $e');
  }
}
