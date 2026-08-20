// Settings — account & privacy section: anonymity banner + status pill,
// delete-account 2-step sheet, erase-local-data button.
// Split from settings_screen.dart (R1D20).

import 'package:flutter/material.dart';

import '../../services/api_service.dart';
import '../../services/auth_service.dart';
import '../../theme/gq_tokens.dart';
import '../auth/login_screen.dart';

// ─── Anonymity banner (View B) ────────────────────────────────────────────────

class AnonymityBanner extends StatelessWidget {
  const AnonymityBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: GQColors.primarySoft,
        border: Border.all(
            color: GQColors.primary.withValues(alpha: 0.18), width: 1),
        borderRadius: BorderRadius.circular(14),
      ),
      padding: const EdgeInsets.all(12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 30,
            height: 30,
            decoration: const BoxDecoration(
                color: Colors.white, shape: BoxShape.circle),
            child: const Icon(Icons.shield_outlined,
                size: 14, color: GQColors.primaryDk),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Anonymity is on.',
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: GQColors.ink)),
                const SizedBox(height: 2),
                Text(
                    "We're not collecting events while this is on. Your chats still happen — they just don't get logged for analytics.",
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: GQColors.ink2,
                        height: 1.45)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Anon status pill (shown in nav-bar when anonymity is on) ─────────────────

class AnonStatusPill extends StatelessWidget {
  const AnonStatusPill({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: GQColors.primarySoft,
        border: Border.all(
            color: GQColors.primary.withValues(alpha: 0.30), width: 1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text('ANONYMOUS',
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: GQColors.primaryDk,
              letterSpacing: 0.5)),
    );
  }
}

// ─── Delete account sheet (View C) ───────────────────────────────────────────

class DeleteAccountSheet extends StatefulWidget {
  const DeleteAccountSheet({super.key, this.onExportRequested});

  /// Callback invoked when the user taps "Want a copy first? Export my data"
  /// inside the delete confirmation sheet. The parent screen owns the actual
  /// export flow (`_handleExportData`) so we plumb a callback in rather than
  /// duplicating the snackbar copy here. Sheet pops itself before invoking
  /// the callback so the parent's snackbar isn't covered by this modal.
  final VoidCallback? onExportRequested;

  @override
  State<DeleteAccountSheet> createState() => _DeleteAccountSheetState();
}

class _DeleteAccountSheetState extends State<DeleteAccountSheet> {
  final _controller = TextEditingController();
  bool _confirmed = false;
  bool _deleting = false;

  @override
  void initState() {
    super.initState();
    _controller.addListener(() {
      final match = _controller.text.trim() == 'DELETE';
      if (match != _confirmed) setState(() => _confirmed = match);
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _handleDeleteForever() async {
    if (!_confirmed || _deleting) return;
    setState(() => _deleting = true);

    try {
      // 1. Send delete request to backend
      await ApiService().deleteUserData();
      
      // 2. Clear local auth state
      await AuthService.instance.signOut();
      
      if (!mounted) return;
      
      // 3. Navigate back to login
      Navigator.of(context, rootNavigator: true).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (route) => false,
      );
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Your account has been deleted.'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _deleting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to delete account: $e'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 14,
        bottom: MediaQuery.of(context).viewInsets.bottom + 32,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // drag handle
          Center(
            child: Container(
              width: 44,
              height: 5,
              decoration: BoxDecoration(
                  color: GQColors.hair,
                  borderRadius: BorderRadius.circular(100)),
            ),
          ),
          const SizedBox(height: 16),

          // Warning icon
          Container(
            width: 60,
            height: 60,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                // IMG-TINT: gradient stop paired with accentSoft (agent ruling 2026-05-22 keep raw)
                colors: [GQColors.accentSoft, Color(0xFFFFF1E5)],
              ),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.warning_amber_outlined,
                size: 26, color: GQColors.dangerInk),
          ),
          const SizedBox(height: 12),

          Text(
            'Delete your account?',
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: GQColors.ink,
                letterSpacing: -0.4),
          ),
          const SizedBox(height: 8),
          RichText(
            textAlign: TextAlign.center,
            text: TextSpan(
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: GQColors.ink2,
                  height: 1.5),
              children: const [
                TextSpan(
                    text:
                        'This removes all your chats, mood logs, and settings. '),
                TextSpan(
                    text: "We can't get them back.",
                    style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink)),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Safer path — export first
          GestureDetector(
            onTap: () {
              Navigator.pop(context);
              // Plumbed via parent callback so we don't duplicate the
              // "Data export isn't available yet" honest copy here.
              // Sheet pops first so the export snackbar can render
              // unobscured (modals shadow snackbars).
              widget.onExportRequested?.call();
            },
            child: Container(
              width: double.infinity,
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
              decoration: BoxDecoration(
                color: GQColors.primarySoft,
                border: Border.all(
                    color: GQColors.primary.withValues(alpha: 0.20), width: 1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Want a copy first? Export my data',
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                        color: GQColors.primaryDk),
                  ),
                  const SizedBox(width: 4),
                  const Icon(Icons.arrow_forward_outlined,
                      size: 13, color: GQColors.primaryDk),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Type-to-confirm field
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'TYPE DELETE TO CONTINUE',
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink2,
                  letterSpacing: 0.6),
            ),
          ),
          const SizedBox(height: 6),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            decoration: BoxDecoration(
              // IMG-TINT: pink-soft icon-bg tint (agent ruling 2026-05-22 keep raw)
              color: const Color(0xFFFBF1F4),
              border: Border.all(color: GQColors.coral, width: 1.5),
              borderRadius: BorderRadius.circular(14),
            ),
            child: TextField(
              controller: _controller,
              style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                  color: GQColors.ink,
                  letterSpacing: 1.0),
              decoration: const InputDecoration(
                border: InputBorder.none,
                hintText: 'DELETE',
                hintStyle: TextStyle(
                    fontWeight: FontWeight.w800,
                    color: GQColors.hair,
                    letterSpacing: 1.0),
              ),
              autocorrect: false,
              textCapitalization: TextCapitalization.characters,
            ),
          ),
          const SizedBox(height: 16),

          // Action buttons — Cancel is primary (P13: cancel is easiest exit)
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: GQColors.primaryDk,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: const StadiumBorder(),
                    elevation: 0,
                    shadowColor: Colors.transparent,
                  ),
                  child: Text('Cancel',
                      style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 13.5,
                          fontWeight: FontWeight.w800)),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton(
                  onPressed: _confirmed && !_deleting
                      ? _handleDeleteForever
                      : null,
                  style: ElevatedButton.styleFrom(
                    // Coral — not red (P4 / P13)
                    backgroundColor: GQColors.dangerInk,
                    disabledBackgroundColor:
                        GQColors.coral.withValues(alpha: 0.5),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: const StadiumBorder(),
                    elevation: 0,
                    shadowColor: Colors.transparent,
                  ),
                  child: _deleting
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white))
                      : Text('Delete forever',
                          style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 13.5,
                              fontWeight: FontWeight.w800)),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),
          Text(
            "If you change your mind later, you'll need to sign up again — your data won't be there.",
            textAlign: TextAlign.center,
            style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: GQColors.ink2,
                height: 1.4),
          ),
        ],
      ),
    );
  }
}


/// Coral "Erase everything on this device" button.
class EraseLocalDataBtn extends StatelessWidget {
  final VoidCallback onTap;

  const EraseLocalDataBtn({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 13),
        decoration: BoxDecoration(
          color: GQColors.coral,
          borderRadius: BorderRadius.circular(999),
          boxShadow: [
            BoxShadow(
              color: GQColors.coral.withValues(alpha: 0.5),
              blurRadius: 22,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Text(
          'Erase everything on this device',
          textAlign: TextAlign.center,
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13.5,
              fontWeight: FontWeight.w800,
              color: Colors.white),
        ),
      ),
    );
  }
}
