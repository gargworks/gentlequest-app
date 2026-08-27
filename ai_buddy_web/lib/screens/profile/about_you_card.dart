import 'package:flutter/material.dart';
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import 'profile_widgets.dart';

// ─── AboutYouCard ─────────────────────────────────────────────────────────────

class AboutYouCard extends StatelessWidget {
  final TextEditingController nicknameController;
  final int pronounIndex;
  final int avatarIndex;
  final List<String> pronouns;
  final List<List<Color>> avatarGradients;
  final ValueChanged<String> onNicknameChanged;
  final ValueChanged<int> onPronounSelected;
  final ValueChanged<int> onAvatarSelected;

  const AboutYouCard({
    super.key,
    required this.nicknameController,
    required this.pronounIndex,
    required this.avatarIndex,
    required this.pronouns,
    required this.avatarGradients,
    required this.onNicknameChanged,
    required this.onPronounSelected,
    required this.onAvatarSelected,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return ProfileCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Nickname field
          const Eyebrow('NICKNAME · ALEX CALLS YOU'),
          const SizedBox(height: 6),
          TextField(
            controller: nicknameController,
            onChanged: onNicknameChanged,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: t.ink,
            ),
            decoration: InputDecoration(
              hintText: '',
              filled: true,
              fillColor: t.bg,
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(11),
                borderSide: BorderSide(color: t.hair),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(11),
                borderSide: BorderSide(color: t.hair),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(11),
                borderSide: BorderSide(color: t.primary),
              ),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Leave blank and Alex calls you "friend".',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: t.ink2,
            ),
          ),

          // Pronouns picker
          const SizedBox(height: 14),
          const Eyebrow('PRONOUNS'),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: List.generate(pronouns.length, (i) {
              final selected = i == pronounIndex;
              return GestureDetector(
                onTap: () => onPronounSelected(i),
                child: AnimatedContainer(
                  duration: GQDurations.fade,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: selected ? t.primary : t.bg,
                    borderRadius: BorderRadius.circular(9999),
                    border: Border.all(
                      color: selected ? t.primary : t.hair,
                    ),
                  ),
                  // Colors.white (selected) is the foreground on the t.primary
                  // FILL — stays literal, contrast travels with the fill.
                  child: Text(
                    pronouns[i],
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: selected ? Colors.white : t.ink2,
                    ),
                  ),
                ),
              );
            }),
          ),

          // Avatar picker
          const SizedBox(height: 14),
          const Eyebrow('AVATAR'),
          const SizedBox(height: 6),
          Row(
            children: List.generate(avatarGradients.length, (i) {
              final selected = i == avatarIndex;
              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: AvatarDot(
                  gradient: avatarGradients[i],
                  selected: selected,
                  onTap: () => onAvatarSelected(i),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}
