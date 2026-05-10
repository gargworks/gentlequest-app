import 'package:flutter/material.dart';
import '../theme/gq_tokens.dart';
import '../screens/settings_screen.dart';
import '../screens/journal_screen.dart';
import '../screens/resources_screen.dart';

// profile_nav_sheet.dart — Tier 2.1
//
// Modal bottom-sheet wired to the profile/avatar icon in the chat header.
// Surfaces 3 destinations that exist in lib/screens/ as of Tier 2.1:
//   • Settings (SettingsScreen)  — Privacy, Notifications, Analytics
//   • Journal  (JournalScreen)   — Reflections entry point
//   • Resources (ResourcesScreen) — Self-help library
//
// Deferred (screens do not exist yet, will be Tier 3):
//   • Profile + Safety Plan (no ProfileScreen / SafetyPlanScreen found)
//   • Weekly Review          (no WeeklyReviewScreen found)

Future<void> showProfileNavSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    useRootNavigator: true,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (ctx) => const _ProfileNavSheet(),
  );
}

class _ProfileNavSheet extends StatelessWidget {
  const _ProfileNavSheet();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(GQRadii.sheet),
        ),
      ),
      padding: const EdgeInsets.only(top: 12, bottom: 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Drag handle
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: const Color(0xFFDDDDDD),
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // Section header
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Your space',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: GQColors.primary,
                  letterSpacing: 0.8,
                ),
              ),
            ),
          ),

          // Settings
          _SheetTile(
            icon: Icons.settings_outlined,
            label: 'Settings',
            onTap: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              );
            },
          ),
          const _TileDivider(),

          // Journal
          _SheetTile(
            icon: Icons.book_outlined,
            label: 'Journal',
            onTap: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const JournalScreen()),
              );
            },
          ),
          const _TileDivider(),

          // Resources
          _SheetTile(
            icon: Icons.library_books_outlined,
            label: 'Resources',
            onTap: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ResourcesScreen()),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _SheetTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _SheetTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: GQColors.softBg,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 2),
        leading: Icon(icon, color: GQColors.primary, size: 22),
        title: Text(
          label,
          style: const TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Color(0xFF333333),
          ),
        ),
        trailing: const Icon(
          Icons.chevron_right_rounded,
          color: Color(0xFFAAAAAA),
          size: 20,
        ),
        onTap: onTap,
      ),
    );
  }
}

class _TileDivider extends StatelessWidget {
  const _TileDivider();

  @override
  Widget build(BuildContext context) {
    return const Divider(
      height: 1,
      thickness: 0.5,
      indent: 56,
      endIndent: 0,
      color: Color(0xFFEEEEEE),
    );
  }
}
