import 'package:flutter/material.dart';
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import 'profile_widgets.dart';

// ─── VoiceCard ────────────────────────────────────────────────────────────────

class VoiceCard extends StatelessWidget {
  final int toneIndex;
  final List<String> tones;
  final bool voiceNotes;
  final int greetingStyleIndex;
  final List<(String, String)> greetingStyles;
  final ValueChanged<int> onToneSelected;
  final ValueChanged<bool> onVoiceNotesToggled;
  final ValueChanged<int> onGreetingStyleSelected;

  const VoiceCard({
    super.key,
    required this.toneIndex,
    required this.tones,
    required this.voiceNotes,
    required this.greetingStyleIndex,
    required this.greetingStyles,
    required this.onToneSelected,
    required this.onVoiceNotesToggled,
    required this.onGreetingStyleSelected,
  });

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return ProfileCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Tone segmented control
          const Eyebrow('TONE'),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.all(3),
            decoration: BoxDecoration(
              color: t.bg,
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: t.hair),
            ),
            child: Row(
              children: List.generate(tones.length, (i) {
                final on = i == toneIndex;
                return Expanded(
                  child: GestureDetector(
                    onTap: () => onToneSelected(i),
                    child: AnimatedContainer(
                      duration: GQDurations.fade,
                      padding: const EdgeInsets.symmetric(vertical: 7),
                      decoration: BoxDecoration(
                        color: on ? t.surface : Colors.transparent,
                        borderRadius: BorderRadius.circular(8),
                        boxShadow: on
                            ? [
                                BoxShadow(
                                  color: t.ink.withValues(alpha: 0.08),
                                  blurRadius: 6,
                                  offset: const Offset(0, 2),
                                )
                              ]
                            : null,
                      ),
                      child: Text(
                        tones[i],
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11.5,
                          fontWeight: FontWeight.w800,
                          color: on ? t.ink : t.ink2,
                        ),
                      ),
                    ),
                  ),
                );
              }),
            ),
          ),

          // Greeting style dropdown — popup menu over a tappable row.
          // Audit §10: previously a static display; now persists
          // profile_greeting_style_v1 and feeds the chat system prompt.
          const SizedBox(height: 14),
          const Eyebrow('GREETING STYLE'),
          const SizedBox(height: 6),
          PopupMenuButton<int>(
            initialValue: greetingStyleIndex,
            onSelected: onGreetingStyleSelected,
            itemBuilder: (ctx) => [
              for (var i = 0; i < greetingStyles.length; i++)
                PopupMenuItem<int>(
                  value: i,
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              greetingStyles[i].$1,
                              style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 13.5,
                                fontWeight: FontWeight.w700,
                                color: t.ink,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              greetingStyles[i].$2,
                              style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: t.ink2,
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (i == greetingStyleIndex)
                        Icon(Icons.check_rounded,
                            color: t.primary, size: 18),
                    ],
                  ),
                ),
            ],
            color: t.surface,
            elevation: 12,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            offset: const Offset(0, 50),
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: t.bg,
                borderRadius: BorderRadius.circular(11),
                border: Border.all(color: t.hair),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          greetingStyles[greetingStyleIndex].$1,
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 13.5,
                            fontWeight: FontWeight.w700,
                            color: t.ink,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          greetingStyles[greetingStyleIndex].$2,
                          style: TextStyle(
                            fontFamily: GQTypography.bodyFamily,
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: t.ink2,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Icon(Icons.keyboard_arrow_down_rounded,
                      color: t.ink2, size: 20),
                ],
              ),
            ),
          ),

          // Voice notes toggle
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Voice notes',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13.5,
                        fontWeight: FontWeight.w700,
                        color: t.ink,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Alex sends short voice replies',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: t.ink2,
                      ),
                    ),
                  ],
                ),
              ),
              GQToggle(
                value: voiceNotes,
                onChanged: onVoiceNotesToggled,
              ),
            ],
          ),
        ],
      ),
    );
  }
}
