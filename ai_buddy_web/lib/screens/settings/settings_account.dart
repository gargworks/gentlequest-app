// Settings — account & privacy section: anonymity banner + status pill,
// delete-account 2-step sheet, erase-local-data button.
// Split from settings_screen.dart (R1D20). WO-5.3 Parts D/E.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../services/api_service.dart';
import '../../services/auth_service.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/gq/gq.dart';
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
//
// WO-5.3 Part E — PRESERVE EXACTLY: the type-to-confirm DELETE gate, the
// Cancel-as-primary styling, the "Want a copy first? Export my data" escape
// hatch, and the closing "your data won't be there" line. This flow is the
// best-designed thing in the surface (P13 done right) — only the container
// (→ GQSheet) and button/token primitives changed underneath it.

class DeleteAccountSheet extends StatefulWidget {
  const DeleteAccountSheet({super.key, this.onExportRequested});

  /// Callback invoked when the user taps "Want a copy first? Export my data"
  /// inside the delete confirmation sheet. The parent screen owns the actual
  /// export flow (`_handleExportData`) so we plumb a callback in rather than
  /// duplicating the snackbar copy here. Sheet pops itself before invoking
  /// the callback so the parent's banner isn't covered by this modal.
  final VoidCallback? onExportRequested;

  @override
  State<DeleteAccountSheet> createState() => _DeleteAccountSheetState();
}

class _DeleteAccountSheetState extends State<DeleteAccountSheet> {
  final _controller = TextEditingController();
  bool _confirmed = false;
  bool _deleting = false;

  // Persistent, point-of-failure banner (WO-5.3 Part D) — the sheet stays
  // open on failure so the user can retry the same "Delete forever" tap.
  String? _deleteError;

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
    setState(() {
      _deleting = true;
      _deleteError = null;
    });
    HapticFeedback.mediumImpact();

    try {
      // 1. Send delete request to backend
      await ApiService().deleteUserData();

      // 2. Clear local auth state
      await AuthService.instance.signOut();

      if (!mounted) return;

      // Show the confirmation while the sheet's context/overlay is still
      // valid — it anchors to the root Overlay, so it survives the
      // navigation replacement below.
      GQBanner.show(
        context,
        message: 'Your account has been deleted.',
        category: GQBannerCategory.success,
      );

      // 3. Navigate back to login
      Navigator.of(context, rootNavigator: true).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (route) => false,
      );
    } catch (e) {
      // D6: never a raw exception string in user-facing copy — route it to
      // logs only.
      debugPrint('[settings] account delete failed: $e');
      if (!mounted) return;
      setState(() {
        _deleting = false;
        _deleteError =
            "We couldn't complete that. Nothing was deleted — try again?";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Warning icon
        Container(
          width: 60,
          height: 60,
          decoration: const BoxDecoration(
            color: GQColors.dangerSoft,
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.warning_amber_outlined,
              size: 26, color: GQColors.dangerInk),
        ),
        const SizedBox(height: 12),

        Text(
          'Delete your account?',
          style: GQTypography.titleSm.copyWith(color: GQColors.ink),
        ),
        const SizedBox(height: 8),
        RichText(
          textAlign: TextAlign.center,
          text: TextSpan(
            style: GQTypography.body.copyWith(color: GQColors.ink2, height: 1.5),
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
            // Sheet pops first so the export banner can render
            // unobscured (modals shadow banners).
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

        if (_deleteError != null) ...[
          GQBanner(
            message: _deleteError!,
            category: GQBannerCategory.amber,
            onDismiss: () => setState(() => _deleteError = null),
          ),
          const SizedBox(height: GQSpacing.md),
        ],

        // Action buttons — Cancel is primary (P13: cancel is easiest exit).
        // Deliberate: primary for Cancel, crisis (dangerInk) for the
        // affirmative destructive action.
        Row(
          children: [
            Expanded(
              child: GQButton(
                label: 'Cancel',
                fullWidth: false,
                onPressed: () => Navigator.pop(context),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: GQButton(
                label: 'Delete forever',
                variant: GQButtonVariant.crisis,
                fullWidth: false,
                loading: _deleting,
                onPressed: _confirmed && !_deleting
                    ? _handleDeleteForever
                    : null,
              ),
            ),
          ],
        ),

        const SizedBox(height: 16),
        Text(
          "If you change your mind later, you'll need to sign up again — your data won't be there.",
          textAlign: TextAlign.center,
          style: GQTypography.caption.copyWith(color: GQColors.ink2, height: 1.4),
        ),
      ],
    );
  }
}

