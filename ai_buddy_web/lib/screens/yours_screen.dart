/// Yours screen — the "You" tab. WO-6.1: inlines ProfileScreen's content
/// (About You / How Alex Talks / Safety Plan) directly rather than linking
/// to it — the profile-avatar entry point in Chat's header is retired
/// alongside this, so this tab is now the only way in.
///
/// Weekly Review, Journal, and Resource Library moved out (Part B): Journal
/// is a root tab, Weekly Review lives inside it, Library is a Home quick
/// lane (already wired). This screen owns Check-in and Settings as its only
/// outbound rows.
library;

import 'package:flutter/material.dart';

import '../theme/gq_tokens.dart';
import '../widgets/companion_widget.dart';
import '../widgets/gq/gq.dart';
import 'clinical_assessment_screen.dart';
import 'profile_screen.dart';
import 'settings_screen.dart';

class YoursScreen extends StatefulWidget {
  const YoursScreen({super.key});

  @override
  State<YoursScreen> createState() => _YoursScreenState();
}

class _YoursScreenState extends State<YoursScreen> {
  bool _showBuilder = false;
  int _builderStep = 0;
  // Bump to force ProfileHomeBody to remount on plan-completion so it
  // re-reads the safety_plan_filled_v1 flag and flips its card state.
  int _homeRefreshKey = 0;

  void _onBuilderComplete() {
    setState(() {
      _showBuilder = false;
      _builderStep = 0;
      _homeRefreshKey++;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_showBuilder) {
      return Scaffold(
        backgroundColor: GQColors.softBg,
        body: SafetyPlanBuilderStep(
          stepIdx: _builderStep,
          onClose: () => setState(() {
            _showBuilder = false;
            _builderStep = 0;
          }),
          onNext: () => setState(() => _builderStep++),
          onCompleted: _onBuilderComplete,
        ),
      );
    }
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: SafeArea(
        bottom: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
          children: [
            _buildHeader(context),
            const SizedBox(height: 24),
            ProfileHomeBody(
              key: ValueKey('yours_profile_$_homeRefreshKey'),
              onBuildPlan: () => setState(() {
                _showBuilder = true;
                _builderStep = 0;
              }),
              onEditPlan: () => setState(() {
                _showBuilder = true;
                _builderStep = 0;
              }),
            ),
            const SizedBox(height: 14),
            _YoursRow(
              icon: Icons.self_improvement_outlined,
              title: 'Check in',
              subtitle: 'A few questions, at your pace.',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                    builder: (_) => const ClinicalAssessmentScreen()),
              ),
            ),
            const SizedBox(height: 10),
            _YoursRow(
              icon: Icons.settings_outlined,
              title: 'Settings',
              subtitle: 'Privacy, notifications, account.',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              ),
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
                  // D3: 14px is text, not decoration — ink3 doesn't qualify.
                  color: GQColors.ink2,
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

/// A Check-in / Settings row — pure navigation (haptic: false per the D7
/// consequence-vs-motion ruling), GQCard + GQType per D6/D3.
class _YoursRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _YoursRow({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GQCard(
      onTap: onTap,
      haptic: false,
      child: ConstrainedBox(
        constraints: const BoxConstraints(minHeight: 56 - 2 * GQSpacing.lg),
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
                  Text(title, style: GQTypography.body.copyWith(fontWeight: FontWeight.w700, color: GQColors.ink)),
                  const SizedBox(height: 2),
                  Text(subtitle, style: GQTypography.caption.copyWith(color: GQColors.ink2)),
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
    );
  }
}
