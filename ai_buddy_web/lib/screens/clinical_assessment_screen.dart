import 'package:flutter/material.dart';
import '../widgets/clinical_assessment_widget.dart';
import '../widgets/app_back_button.dart';

/// Screen for selecting and taking clinical assessments (PHQ-9, GAD-7).
class ClinicalAssessmentScreen extends StatelessWidget {
  const ClinicalAssessmentScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Clinical Assessments'),
        centerTitle: true,
        automaticallyImplyLeading: false,
        leading: Builder(
          builder: (ctx) {
            if (Navigator.of(ctx).canPop()) {
              return const AppBackButton();
            }
            return const SizedBox.shrink();
          },
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'How are you feeling?',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Take a validated screening to better understand your mental health.',
              style: TextStyle(color: Colors.grey[600], fontSize: 14),
            ),
            const SizedBox(height: 24),

            // PHQ-9 Card
            _AssessmentCard(
              title: 'PHQ-9',
              subtitle: 'Depression Screening',
              description:
                  '9 questions to assess depression symptoms over the last 2 weeks.',
              icon: Icons.sentiment_dissatisfied,
              color: Colors.blue,
              onTap: () => _startAssessment(context, 'phq9'),
            ),

            const SizedBox(height: 16),

            // GAD-7 Card
            _AssessmentCard(
              title: 'GAD-7',
              subtitle: 'Anxiety Screening',
              description:
                  '7 questions to assess anxiety symptoms over the last 2 weeks.',
              icon: Icons.psychology,
              color: Colors.purple,
              onTap: () => _startAssessment(context, 'gad7'),
            ),

            const SizedBox(height: 32),

            // Disclaimer
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline, color: Colors.grey[600], size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'These screenings are not diagnostic. If you have concerns, please consult a healthcare professional.',
                      style: TextStyle(color: Colors.grey[600], fontSize: 13),
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

  void _startAssessment(BuildContext context, String type) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => Scaffold(
          appBar: AppBar(
            title: Text(type == 'phq9' ? 'PHQ-9' : 'GAD-7'),
            centerTitle: true,
          ),
          body: ClinicalAssessmentWidget(
            assessmentType: type,
            onComplete: () {
              Navigator.of(context).pop();
            },
          ),
        ),
      ),
    );
  }
}

class _AssessmentCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final String description;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _AssessmentCard({
    required this.title,
    required this.subtitle,
    required this.description,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: color,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: color.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          subtitle,
                          style: TextStyle(
                            fontSize: 11,
                            color: color,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    description,
                    style: TextStyle(
                      color: Colors.grey[700],
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.arrow_forward_ios, color: color, size: 18),
          ],
        ),
      ),
    );
  }
}
