import 'package:flutter/material.dart';
import '../theme/gq_tokens.dart';

/// InlineCrisisBanner — State B (R1D7 Chat Active States)
///
/// Soft inline card that slides into the chat stream when a crisis signal is
/// detected. NEVER a modal/full-screen; renders inline above the streaming
/// bubble. Never auto-dismisses (P6: crisis never blocks).
///
/// Design source: GentleQuest_Chat_Active_States.html — Mockup B.
/// Copy verbatim from HTML:
///   "Quick — are you safe right now?"
///   "No wrong answer. We can take a moment."
///   "I'm okay, keep going" / "Help me find someone"
///
/// Callbacks:
///   onImOkay — user taps "I'm okay, keep going"  → caller dismisses banner
///   onHelp   — user taps "Help me find someone"  → caller expands 988 resources
///                                                   inline (does NOT navigate)
class InlineCrisisBanner extends StatefulWidget {
  const InlineCrisisBanner({
    super.key,
    required this.onImOkay,
    required this.onHelp,
  });

  final VoidCallback onImOkay;
  final VoidCallback onHelp;

  @override
  State<InlineCrisisBanner> createState() => _InlineCrisisBannerState();
}

class _InlineCrisisBannerState extends State<InlineCrisisBanner>
    with SingleTickerProviderStateMixin {
  late final AnimationController _entryCtrl = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 700),
  )..forward();

  late final Animation<double> _opacityAnim = CurvedAnimation(
    parent: _entryCtrl,
    curve: Curves.easeOut,
  );

  late final Animation<Offset> _slideAnim = Tween<Offset>(
    begin: const Offset(0, 0.08),
    end: Offset.zero,
  ).animate(CurvedAnimation(parent: _entryCtrl, curve: Curves.easeOut));

  @override
  void dispose() {
    _entryCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Coral banner: rgba(255,107,107,0.14) → rgba(255,107,107,0.08)
    // Border: rgba(255,107,107,0.35)
    // Body text: GQColors.inkOnCoral (#7A2424) — deep coral ink
    const bodyInk = GQColors.inkOnCoral;
    const bannerBg1 = Color(0x24FF6B6B); // ~0.14 opacity
    const bannerBg2 = Color(0x14FF6B6B); // ~0.08 opacity
    const bannerBorder = Color(0x59FF6B6B); // ~0.35 opacity

    return FadeTransition(
      opacity: _opacityAnim,
      child: SlideTransition(
        position: _slideAnim,
        child: Semantics(
          label: 'Crisis check-in card',
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 6),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [bannerBg1, bannerBg2],
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: bannerBorder),
            ),
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Heart icon with white circle halo
                    Container(
                      width: 30,
                      height: 30,
                      decoration: const BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Color(0x2EFF6B6B),
                            blurRadius: 6,
                            offset: Offset(0, 2),
                          ),
                        ],
                      ),
                      child: const Center(
                        child: Icon(
                          Icons.favorite_rounded,
                          color: GQColors.coral,
                          size: 14,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            // Verbatim from HTML
                            'Quick — are you safe right now?',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w800,
                              color: bodyInk,
                              height: 1.3,
                            ),
                          ),
                          SizedBox(height: 3),
                          Text(
                            // Verbatim from HTML
                            'No wrong answer. We can take a moment.',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: bodyInk,
                              height: 1.45,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    // v1.3.2: "Thanks, I have support" replaces the
                    // v1.3.0 "I'm okay, keep going" which read as
                    // dismissive at a high-stakes moment. New copy
                    // signals that the user has an active support
                    // network without sounding like deflection.
                    Expanded(
                      child: Semantics(
                        button: true,
                        label: "Thanks, I have support",
                        child: GestureDetector(
                          onTap: widget.onImOkay,
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius:
                                  BorderRadius.circular(GQRadii.button),
                              border: Border.all(color: bannerBorder),
                            ),
                            child: const Center(
                              child: Text(
                                "Thanks, I have support",
                                style: TextStyle(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w800,
                                  color: bodyInk,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    // "Help me find someone" — coral pill
                    Expanded(
                      child: Semantics(
                        button: true,
                        label: 'Help me find someone',
                        child: GestureDetector(
                          onTap: widget.onHelp,
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: BoxDecoration(
                              color: GQColors.coral,
                              borderRadius:
                                  BorderRadius.circular(GQRadii.button),
                              boxShadow: const [
                                BoxShadow(
                                  color: Color(0x8CFF6B6B),
                                  blurRadius: 20,
                                  offset: Offset(0, 8),
                                ),
                              ],
                            ),
                            child: const Center(
                              child: Text(
                                // Verbatim from HTML
                                'Help me find someone',
                                style: TextStyle(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w800,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
