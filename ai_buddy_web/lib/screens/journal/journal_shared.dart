// Journal — shared helpers: mood color/label, date formatting, nav icon
// button, color darken extension. Split from journal_screen.dart (R1D14).

import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';
import 'journal_models.dart';

Color moodColor(JournalMood? mood) {
  switch (mood) {
    case JournalMood.great:
      return GQColors.moodGreat;
    case JournalMood.good:
      return GQColors.moodGood;
    case JournalMood.okay:
      return GQColors.moodOkay;
    case JournalMood.meh:
      return GQColors.moodMeh;
    case JournalMood.rough:
      return GQColors.moodRough;
    case null:
      return GQColors.ink3;
  }
}

String moodLabel(JournalMood? mood) {
  switch (mood) {
    case JournalMood.great:
      return 'Great';
    case JournalMood.good:
      return 'Good';
    case JournalMood.okay:
      return 'Okay';
    case JournalMood.meh:
      return 'Meh';
    case JournalMood.rough:
      return 'Rough';
    case null:
      return '';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared nav icon button (matches HTML .nav-icon-btn)
// ─────────────────────────────────────────────────────────────────────────────

class NavIconButton extends StatelessWidget {
  const NavIconButton({
    super.key,
    required this.onTap,
    required this.child,
    this.backgroundColor = Colors.white,
    this.borderColor = GQColors.hair,
  });

  final VoidCallback onTap;
  final Widget child;
  final Color backgroundColor;
  final Color borderColor;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: backgroundColor,
          shape: BoxShape.circle,
          border: Border.all(color: borderColor),
        ),
        alignment: Alignment.center,
        child: child,
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Date / time formatting helpers
// ─────────────────────────────────────────────────────────────────────────────

String formatTime(DateTime dt) {
  final hour = dt.hour > 12
      ? dt.hour - 12
      : dt.hour == 0
          ? 12
          : dt.hour;
  final min = dt.minute.toString().padLeft(2, '0');
  final ampm = dt.hour >= 12 ? 'PM' : 'AM';
  return '$hour:$min $ampm';
}

String formatDay(DateTime dt) {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];
  return '${days[dt.weekday - 1]} · ${months[dt.month - 1]} ${dt.day}';
}

String formatDateLong(DateTime dt) {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];
  return '${days[dt.weekday - 1]}, ${months[dt.month - 1]} ${dt.day}';
}

// ─────────────────────────────────────────────────────────────────────────────
// Color extension: darken helper for mood pill text
// ─────────────────────────────────────────────────────────────────────────────

extension ColorDarken on Color {
  Color darken(double amount) {
    assert(amount >= 0 && amount <= 1);
    final hsl = HSLColor.fromColor(this);
    return hsl.withLightness((hsl.lightness - amount).clamp(0.0, 1.0)).toColor();
  }
}
