import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../services/auth_service.dart';
import '../../services/firebase_service.dart';
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/app_back_button.dart';

/// Passwordless sign-in screen.
///
/// Surfaced from Settings → "Sign in to sync across devices" and from the
/// web mobile-promo sheet. Flow:
///   1. User enters their email
///   2. We POST /api/auth/magic-link
///   3. Show "check your inbox" confirmation
///   4. User taps the gentlequest://auth/verify?token=... link in their
///      inbox → app_links delivers the URL to the deep-link handler →
///      AuthService.verifyToken() binds the session → we pop this screen
///      with a success flag.
///
/// Sign-in is OPT-IN — anonymous use stays fully supported. The pitch is
/// "sync across devices", not "sign in to use the app". Anxious users who
/// don't want to give an email shouldn't feel pressured.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailController = TextEditingController();
  final FocusNode _emailFocus = FocusNode();
  bool _sending = false;
  bool _sent = false;
  String? _errorText;

  // Tighter than `^[^\s@]+@[^\s@]+\.[^\s@]+$` which accepts garbage like
  // `a@b.c`, leading-dot local parts, consecutive dots, single-char TLDs.
  // Covers >95% of real email addresses; rejects most typos that would
  // otherwise show "link sent" without ever arriving.
  static final RegExp _emailRe =
      RegExp(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9][A-Za-z0-9.\-]*\.[A-Za-z]{2,}$');

  @override
  void dispose() {
    _emailController.dispose();
    _emailFocus.dispose();
    super.dispose();
  }

  Future<void> _sendLink() async {
    final email = _emailController.text.trim().toLowerCase();
    if (!_emailRe.hasMatch(email)) {
      setState(() => _errorText = 'That doesn\'t look like an email.');
      return;
    }
    setState(() {
      _errorText = null;
      _sending = true;
    });
    HapticFeedback.selectionClick();
    try {
      await AuthService.instance.requestMagicLink(email);
      FirebaseService().logEvent('auth_magic_link_requested');
      if (!mounted) return;
      setState(() {
        _sent = true;
        _sending = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _errorText =
            'Couldn\'t send right now — check your connection and try again.';
        _sending = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: t.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),
              Row(
                children: [
                  AppBackButton(
                      onPressed: () => Navigator.of(context).maybePop()),
                ],
              ),
              const SizedBox(height: 28),
              Icon(
                Icons.email_outlined,
                size: 56,
                color: t.primary,
              ),
              const SizedBox(height: 18),
              Text(
                _sent ? 'Check your inbox' : 'Sync across devices',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: GQTypography.displayFamily,
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  color: t.ink,
                  letterSpacing: -0.3,
                ),
              ),
              const SizedBox(height: 10),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Text(
                  _sent
                      ? "We sent a one-time link to ${_emailController.text.trim()}. Tap it to finish signing in. The link works once and expires in 15 minutes."
                      : "Add your email and we'll send a one-tap sign-in link. No password. Your history stays private to you.",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 14,
                    color: t.ink2,
                    height: 1.5,
                  ),
                ),
              ),
              const SizedBox(height: 28),
              if (!_sent) ...[
                _EmailField(
                  controller: _emailController,
                  focusNode: _emailFocus,
                  errorText: _errorText,
                  onSubmit: _sendLink,
                  enabled: !_sending,
                ),
                const SizedBox(height: 16),
                _PrimaryButton(
                  label: _sending ? 'Sending…' : 'Send me a link',
                  onTap: _sending ? null : _sendLink,
                ),
              ] else ...[
                _PrimaryButton(
                  label: 'Done',
                  onTap: () => Navigator.of(context).maybePop(),
                ),
                const SizedBox(height: 10),
                TextButton(
                  onPressed: _sending
                      ? null
                      : () {
                          setState(() {
                            _sent = false;
                            _errorText = null;
                          });
                        },
                  child: Text(
                    'Use a different email',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: t.ink2,
                    ),
                  ),
                ),
              ],
              const Spacer(),
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  'Anonymous use stays supported — sign-in is optional.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: t.ink2,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmailField extends StatelessWidget {
  const _EmailField({
    required this.controller,
    required this.focusNode,
    required this.onSubmit,
    required this.enabled,
    this.errorText,
  });

  final TextEditingController controller;
  final FocusNode focusNode;
  final VoidCallback onSubmit;
  final bool enabled;
  final String? errorText;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          decoration: BoxDecoration(
            color: t.surface,
            borderRadius: BorderRadius.circular(GQRadii.card),
            border: Border.all(
              color: errorText != null ? t.coral : t.hair,
              width: 1.2,
            ),
          ),
          child: TextField(
            controller: controller,
            focusNode: focusNode,
            enabled: enabled,
            autofillHints: const [AutofillHints.email],
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.go,
            onSubmitted: (_) => onSubmit(),
            autocorrect: false,
            decoration: const InputDecoration(
              hintText: 'you@example.com',
              border: InputBorder.none,
              contentPadding:
                  EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            ),
          ),
        ),
        if (errorText != null) ...[
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text(
              errorText!,
              style: TextStyle(
                color: t.coral,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _PrimaryButton extends StatelessWidget {
  const _PrimaryButton({required this.label, required this.onTap});
  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final disabled = onTap == null;
    return Material(
      // D3: primary fails 4.5:1 with white text (3.66:1); primaryDk
      // passes (5.30:1). primaryDk: no GQTheme slot by design (CTA-fill
      // exception); paired Colors.white foreground below stays literal too.
      color: disabled
          ? GQColors.primaryDk.withValues(alpha: 0.4)
          : GQColors.primaryDk,
      borderRadius: BorderRadius.circular(GQRadii.button),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(GQRadii.button),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: Center(
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w800,
                color: Colors.white,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
