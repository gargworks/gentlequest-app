import 'package:flutter/material.dart';
import '../../theme/gq_tokens.dart';

// Shared primitives for the Profile screen family (home, cards, safety-plan
// builder). Pure-move extraction from profile_screen.dart — formerly private
// (underscore) classes renamed public so they can cross library boundaries.

class ProfileNavBar extends StatelessWidget {
  final String title;
  final bool showBack;
  final bool showClose;
  final VoidCallback? onBack;
  final VoidCallback? onClose;

  const ProfileNavBar({
    super.key,
    required this.title,
    this.showBack = false,
    this.showClose = false,
    this.onBack,
    this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    final topPad = MediaQuery.of(context).padding.top;
    return Container(
      height: 54 + topPad,
      padding: EdgeInsets.only(
          left: 18, right: 18, top: topPad, bottom: 0),
      decoration: BoxDecoration(
        color: GQColors.softBg.withValues(alpha: 0.85),
        border: const Border(
          bottom: BorderSide(color: GQColors.hair),
        ),
      ),
      child: Row(
        children: [
          if (showBack)
            IconCircleButton(
              icon: Icons.chevron_left_rounded,
              onTap: onBack ?? () {},
            ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                letterSpacing: -0.3,
              ),
            ),
          ),
          if (showClose)
            IconCircleButton(
              icon: Icons.close_rounded,
              onTap: onClose ?? () {},
            ),
        ],
      ),
    );
  }
}

class BuilderNavBar extends StatelessWidget {
  final int stepIdx;
  final int total;
  final VoidCallback onClose;

  const BuilderNavBar({
    super.key,
    required this.stepIdx,
    required this.total,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    final topPad = MediaQuery.of(context).padding.top;
    return Container(
      height: 54 + topPad,
      padding:
          EdgeInsets.only(left: 18, right: 18, top: topPad),
      decoration: BoxDecoration(
        color: GQColors.softBg.withValues(alpha: 0.85),
        border: const Border(
          bottom: BorderSide(color: GQColors.hair),
        ),
      ),
      child: Row(
        children: [
          const Text(
            'Your safety plan',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
            ),
          ),
          const Spacer(),
          StepDots(active: stepIdx, total: total),
          const SizedBox(width: 8),
          IconCircleButton(
            icon: Icons.close_rounded,
            size: 30,
            iconSize: 16,
            onTap: onClose,
          ),
        ],
      ),
    );
  }
}

class StepDots extends StatelessWidget {
  final int active;
  final int total;

  const StepDots({super.key, required this.active, required this.total});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(total, (i) {
        final isDone = i < active;
        final isActive = i == active;
        return AnimatedContainer(
          duration: GQDurations.fade,
          margin: const EdgeInsets.only(right: 5),
          width: isActive ? 22 : 7,
          height: 7,
          decoration: BoxDecoration(
            color: (isDone || isActive)
                ? GQColors.primary
                : GQColors.ink.withValues(alpha: 0.18),
            borderRadius: BorderRadius.circular(9999),
          ),
        );
      }),
    );
  }
}

class IconCircleButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final double size;
  final double iconSize;

  const IconCircleButton({
    super.key,
    required this.icon,
    required this.onTap,
    this.size = 34,
    this.iconSize = 20,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: Colors.white,
          shape: BoxShape.circle,
          border: Border.all(color: GQColors.hair),
        ),
        child: Icon(icon, size: iconSize, color: GQColors.ink),
      ),
    );
  }
}

class ProfileCard extends StatelessWidget {
  final Widget child;
  const ProfileCard({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: GQColors.hair),
      ),
      child: child,
    );
  }
}

class SectionLabel extends StatelessWidget {
  final String text;
  const SectionLabel(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 6, bottom: 8),
      child: Text(
        text,
        style: const TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 10.5,
          fontWeight: FontWeight.w800,
          color: GQColors.ink2,
          letterSpacing: 0.7,
        ),
      ),
    );
  }
}

class Eyebrow extends StatelessWidget {
  final String text;
  const Eyebrow(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontFamily: GQTypography.bodyFamily,
        fontSize: 10.5,
        fontWeight: FontWeight.w800,
        color: GQColors.ink2,
        letterSpacing: 0.7,
      ),
    );
  }
}

class AvatarDot extends StatelessWidget {
  final List<Color> gradient;
  final bool selected;
  final VoidCallback onTap;

  const AvatarDot({
    super.key,
    required this.gradient,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: gradient,
          ),
          border: selected
              ? Border.all(color: GQColors.primary, width: 2)
              : null,
        ),
        child: selected
            ? Container(
                margin: const EdgeInsets.all(2),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: Colors.white,
                    width: 1,
                  ),
                ),
              )
            : null,
      ),
    );
  }
}

class GQToggle extends StatelessWidget {
  final bool value;
  final ValueChanged<bool> onChanged;

  const GQToggle({super.key, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onChanged(!value),
      child: AnimatedContainer(
        duration: GQDurations.fade,
        width: 36,
        height: 22,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(9999),
          color: value
              ? GQColors.primary
              : GQColors.ink3.withValues(alpha: 0.32),
        ),
        child: Stack(
          children: [
            AnimatedPositioned(
              duration: GQDurations.fade,
              left: value ? 16 : 2,
              top: 2,
              child: Container(
                width: 18,
                height: 18,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white,
                  boxShadow: [
                    BoxShadow(
                      color: Color(0x33000000),
                      blurRadius: 3,
                      offset: Offset(0, 1),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class SafetyPill extends StatelessWidget {
  final String label;
  final IconData? icon;
  final Color? iconColor;

  const SafetyPill({super.key, required this.label, this.icon, this.iconColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.22),
        borderRadius: BorderRadius.circular(9999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 9, color: iconColor ?? Colors.white),
            const SizedBox(width: 5),
          ],
          Text(
            label,
            style: const TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: Colors.white,
              letterSpacing: 0.4,
            ),
          ),
        ],
      ),
    );
  }
}

enum SafetyButtonStyle { ghost, solid }

class SafetyButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final SafetyButtonStyle style;

  const SafetyButton({
    super.key,
    required this.label,
    required this.onTap,
    required this.style,
  });

  @override
  Widget build(BuildContext context) {
    final isGhost = style == SafetyButtonStyle.ghost;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 11),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(9999),
          color: isGhost ? Colors.white.withValues(alpha: 0.16) : Colors.white,
          border: isGhost
              ? Border.all(color: Colors.white.withValues(alpha: 0.28))
              : null,
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 12.5,
            fontWeight: FontWeight.w800,
            color: isGhost ? Colors.white : GQColors.primaryDk,
          ),
        ),
      ),
    );
  }
}

class ContactTextField extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final ValueChanged<String>? onChanged;

  const ContactTextField({
    super.key,
    required this.controller,
    required this.hint,
    this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      onChanged: onChanged,
      style: const TextStyle(
        fontFamily: GQTypography.bodyFamily,
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: GQColors.ink,
      ),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 13,
          fontWeight: FontWeight.w500,
          color: GQColors.ink2,
        ),
        filled: true,
        fillColor: GQColors.softBg,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(11),
          borderSide: const BorderSide(color: GQColors.hair),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(11),
          borderSide: const BorderSide(color: GQColors.hair),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(11),
          borderSide: const BorderSide(color: GQColors.primary),
        ),
      ),
    );
  }
}

class PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const PrimaryButton({super.key, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 13),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(9999),
          // D3: primary fails 4.5:1 with white text (3.66:1); primaryDk
          // passes (5.30:1).
          color: GQColors.primaryDk,
          boxShadow: const [
            BoxShadow(
              color: Color(0x8C4F63C9), // primaryDk at the same alpha
              blurRadius: 26,
              offset: Offset(0, 12),
              spreadRadius: -10,
            ),
          ],
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 13.5,
            fontWeight: FontWeight.w800,
            color: Colors.white,
          ),
        ),
      ),
    );
  }
}

class OutlineButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const OutlineButton({super.key, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(9999),
          color: Colors.white,
          border: Border.all(color: GQColors.hair),
        ),
        child: Text(
          label,
          style: const TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: GQColors.ink2,
          ),
        ),
      ),
    );
  }
}
