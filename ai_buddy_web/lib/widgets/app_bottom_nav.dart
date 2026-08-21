import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import '../theme/gq_tokens.dart';

/// App-wide bottom navigation.
///
/// Design Authority D5 — 4-tab IA: Home / Chat / Journal / You. `mood`,
/// `quest`, and `community` are retired from the visible nav (their screens
/// are reachable from Home instead, or in `quest`'s case a currently-unwired
/// experiment — see lib/features/leopard/) but the enum cases stay so the
/// not-yet-swept dhiwise/leopard code that still references them keeps
/// compiling. [AppBottomNav] itself only ever renders the 4 live tabs;
/// [HomeShell] treats the 3 retired values as aliases for [home].
enum AppTab { talk, mood, quest, yours, community, home, journal }

class AppBottomNav extends StatelessWidget {
  final AppTab current;
  final ValueChanged<AppTab>? onTap; // if provided, used by HomeShell
  final ValueChanged<AppTab>? onReselect; // called when tapping the active tab

  const AppBottomNav(
      {super.key, required this.current, this.onTap, this.onReselect});

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).padding.bottom;
    final double vPad =
        bottomInset > 0 ? 6.0 : 10.0; // sit lower when inset exists
    const bool kActiveLabelOnlyDemo =
        false; // labels always shown (keep note for future option)

    return Material(
      color: Colors.white,
      elevation: 0, // ensure no shadow
      surfaceTintColor: Colors.transparent, // avoid M3 overlay tint
      child: Padding(
        // shave a few pixels so it visually sits lower without overlapping gestures
        padding: EdgeInsets.only(bottom: (bottomInset - 12).clamp(0.0, 100.0)),
        child: SafeArea(
          top: false,
          bottom: false,
          child: Padding(
            padding:
                EdgeInsets.symmetric(vertical: vPad), // adaptive touch target
            child: FocusTraversalGroup(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildItem(context, Icons.home_rounded, 'Home', AppTab.home,
                      activeLabelOnly: kActiveLabelOnlyDemo),
                  _buildItem(
                      context, Icons.chat_bubble_outline, 'Chat', AppTab.talk,
                      activeLabelOnly: kActiveLabelOnlyDemo),
                  _buildItem(context, Icons.auto_stories_outlined, 'Journal',
                      AppTab.journal,
                      activeLabelOnly: kActiveLabelOnlyDemo),
                  _buildItem(context, Icons.person_outline_rounded, 'You',
                      AppTab.yours,
                      activeLabelOnly: kActiveLabelOnlyDemo),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildItem(
      BuildContext context, IconData icon, String label, AppTab tab,
      {required bool activeLabelOnly}) {
    final bool isActive = current == tab;
    return InkWell(
      onTap: () {
        // Haptic feedback on supported platforms
        if (!kIsWeb) {
          try {
            HapticFeedback.selectionClick();
          } catch (_) {}
        }
        if (tab == current) {
          if (onReselect != null) onReselect!(tab);
          return;
        }
        if (onTap != null) {
          onTap!(tab);
          return;
        }
        // Fallback: navigate to shell which manages tabs via IndexedStack
        Navigator.pushReplacementNamed(context, '/home', arguments: tab);
      },
      borderRadius: BorderRadius.circular(12),
      focusColor: GQColors.primary.withValues(alpha: 0.10),
      hoverColor: GQColors.primary.withValues(alpha: 0.06),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 6.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 28.0,
              color: isActive
                  ? GQColors.primary
                  : GQColors.ink2,
            ),
            const SizedBox(height: 4.0),
            AnimatedOpacity(
              duration: const Duration(milliseconds: 150),
              opacity: (!activeLabelOnly || isActive) ? 1.0 : 0.0,
              child: SizedBox(
                height: 16,
                child: Center(
                  child: Text(
                    label,
                    style: TextStyle(
                      fontSize: 12.0,
                      color: isActive ? GQColors.primary : GQColors.ink2,
                      fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
