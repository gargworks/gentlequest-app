/// Yours screen — the "Your space" tab.
///
/// Surfaces three private destinations in priority order:
///   1. Weekly Review (promoted at top when pending)
///   2. Journal
///   3. Resources
///
/// Each card navigates to its respective screen. The companion creature
/// appears in the header at 52px per the design agent spec.
library;

import 'package:flutter/material.dart';

import '../theme/gq_tokens.dart';
import '../widgets/companion_widget.dart';
import 'journal_screen.dart';
import 'resource_library_screen.dart';
import 'weekly_review_screen.dart';

class YoursScreen extends StatelessWidget {
  const YoursScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        bottom: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
          children: [
            _buildHeader(context),
            const SizedBox(height: 24),
            _YoursCard(
              icon: Icons.insights_outlined,
              title: 'Weekly Review',
              subtitle: 'Your week, gently summarized',
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => WeeklyReviewScreen(
                      data: WeeklyReviewData.stubFull(),
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 12),
            _YoursCard(
              icon: Icons.book_outlined,
              title: 'Journal',
              subtitle: 'Reflections and notes',
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const JournalScreen()),
                );
              },
            ),
            const SizedBox(height: 12),
            _YoursCard(
              icon: Icons.library_books_outlined,
              title: 'Resources',
              subtitle: 'Your library of guides',
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                      builder: (_) => const ResourceLibraryScreen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text(
                'Yours',
                style: TextStyle(
                  fontFamily: GQTypography.displayFamily,
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.4,
                  color: GQColors.ink,
                ),
              ),
              SizedBox(height: 4),
              Text(
                'Your space. Private.',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: GQColors.ink3,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 12),
        SizedBox(
          width: 52,
          height: 52,
          child: const CompanionWidget(),
        ),
      ],
    );
  }
}

class _YoursCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _YoursCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(GQRadii.card),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(GQRadii.card),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(color: GQColors.hair),
          ),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: GQColors.primarySoft,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: Icon(icon, color: GQColors.primary, size: 22),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: GQColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.chevron_right_rounded,
                color: GQColors.ink3,
                size: 24,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
