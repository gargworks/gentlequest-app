import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/gq_tokens.dart';
import '../config/profile_config.dart';
import 'settings_screen.dart';
import 'profile/about_you_card.dart';
import 'profile/profile_prefs_keys.dart';
import 'profile/profile_widgets.dart';
import 'profile/safety_plan_builder.dart';
import 'profile/safety_plan_card.dart';
import 'profile/voice_card.dart';

// Re-export the section libraries so existing `import 'profile_screen.dart'`
// consumers (tests, nav sheets) keep seeing the same public symbols as before
// the lib/screens/profile/ split.
export 'profile/about_you_card.dart';
export 'profile/profile_widgets.dart';
export 'profile/safety_plan_builder.dart';
export 'profile/safety_plan_card.dart';
export 'profile/voice_card.dart';

// profile_screen.dart — Tier 3.6 R1D19
//
// Implements GentleQuest Profile screen per GentleQuest_Profile.html.
// Views:
//   A · Profile home  — About you + How Alex talks + Safety plan hero card
//        (this file; cards live in profile/about_you_card.dart,
//         profile/voice_card.dart, profile/safety_plan_card.dart)
//   B · Safety plan builder — 5 steps (profile/safety_plan_builder.dart)
//
// Profile + safety-plan data persisted via SharedPreferences (this tier).
// secure_storage migration is a separate follow-up.
// Key constants live in profile/profile_prefs_keys.dart.

// ─── Entry point ─────────────────────────────────────────────────────────────

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _showBuilder = false;
  int _builderStep = 0;
  // Bump this key to force _ProfileHome to remount on plan-completion so it
  // re-reads the `safety_plan_filled_v1` flag and flips its card state.
  int _homeRefreshKey = 0;

  void _onBuilderComplete() {
    setState(() {
      _showBuilder = false;
      _builderStep = 0;
      _homeRefreshKey++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.softBg,
      body: _showBuilder
          ? SafetyPlanBuilderStep(
              stepIdx: _builderStep,
              onClose: () => setState(() { _showBuilder = false; _builderStep = 0; }),
              onNext: () => setState(() => _builderStep++),
              onCompleted: _onBuilderComplete,
            )
          : _ProfileHome(
              key: ValueKey('profile_home_$_homeRefreshKey'),
              onBuildPlan: () => setState(() { _showBuilder = true; _builderStep = 0; }),
              onEditPlan: () => setState(() { _showBuilder = true; _builderStep = 0; }),
            ),
    );
  }
}

// ─── View A · Profile home ────────────────────────────────────────────────────

class _ProfileHome extends StatefulWidget {
  final VoidCallback onBuildPlan;
  final VoidCallback onEditPlan;

  const _ProfileHome({
    super.key,
    required this.onBuildPlan,
    required this.onEditPlan,
  });

  @override
  State<_ProfileHome> createState() => _ProfileHomeState();
}

class _ProfileHomeState extends State<_ProfileHome> {
  // Form state — defaults shown until SharedPreferences load completes.
  // `_loaded` gates the nickname TextField rebuild via controller text-sync.
  String _nickname = '';
  int _pronounIndex = -1; // -1 = none selected
  int _avatarIndex = 2;
  int _toneIndex = 0; // 0=Warm, 1=Direct, 2=Quiet
  int _greetingStyleIndex = 0;
  bool _voiceNotes = false;
  bool _planFilled = false; // hydrated from prefs on init

  // Debounce per-key so rapid edits coalesce into one disk write.
  final Map<String, Timer> _debouncers = {};

  // Nickname has a controller so we can sync prefs → field after async load
  // without disturbing the user's cursor mid-type.
  final TextEditingController _nicknameCtrl = TextEditingController();

  static const _pronouns = ['he/him', 'she/her', 'they/them', 'custom', 'prefer not'];
  static const _avatarGradients = [
    [Color(0xFFFFC4A3), Color(0xFFFF8E8E)],
    [Color(0xFFA8D8B9), Color(0xFF5FBA7D)],
    [Color(0xFF9DB4FF), Color(0xFF6F62D6)],
    [Color(0xFFF8C8DC), Color(0xFFD87FB0)],
    [Color(0xFFFFE3A3), Color(0xFFE5A85B)],
    [Color(0xFFC8E1E8), Color(0xFF7FB3C2)],
  ];
  static const _tones = ['Warm', 'Direct', 'Quiet'];
  static const _greetingStyles = [
    ('Casual', '"Hey friend"'),
    ('Formal', '"Good evening"'),
    ('Minimal', '"Hi."')
  ];

  @override
  void initState() {
    super.initState();
    _loadFromPrefs();
  }

  Future<void> _loadFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _nickname = prefs.getString(kProfileNickname) ?? '';
      _pronounIndex = prefs.getInt(kProfilePronoun) ?? -1;
      _avatarIndex = prefs.getInt(kProfileAvatar) ?? 2;
      _toneIndex = prefs.getInt(kProfileTone) ?? 0;
      _greetingStyleIndex = prefs.getInt('profile_greeting_style_v1') ?? 0;
      _voiceNotes = prefs.getBool(kProfileVoiceNotes) ?? false;
      _planFilled = prefs.getBool(kSafetyPlanFilled) ?? false;
      // Sync nickname controller without clobbering an active edit.
      if (_nicknameCtrl.text != _nickname) {
        _nicknameCtrl.text = _nickname;
        _nicknameCtrl.selection = TextSelection.collapsed(offset: _nickname.length);
      }
    });
  }

  // 500ms debounced write — same key resets timer, so only the last value lands.
  // Type-mapping: bool→setBool, int→setInt, String→setString. Other types are
  // dropped with an assert so callers catch unsupported writes during dev.
  void _persistProfile<T>(String key, T value) {
    _debouncers[key]?.cancel();
    _debouncers[key] = Timer(const Duration(milliseconds: 500), () async {
      final prefs = await SharedPreferences.getInstance();
      if (value is bool) {
        await prefs.setBool(key, value);
      } else if (value is int) {
        await prefs.setInt(key, value);
      } else if (value is String) {
        await prefs.setString(key, value);
      } else {
        assert(false, '_persistProfile: unsupported type ${value.runtimeType} for key $key');
      }
    });
  }

  @override
  void dispose() {
    for (final t in _debouncers.values) {
      t.cancel();
    }
    _debouncers.clear();
    _nicknameCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Nav bar
        ProfileNavBar(
          title: 'Your profile',
          showBack: true,
          showClose: true,
          onBack: () => Navigator.maybePop(context),
          onClose: () => Navigator.maybePop(context),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 30),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── ABOUT YOU ────────────────────────────────────────────────
                const SectionLabel('ABOUT YOU'),
                AboutYouCard(
                  nicknameController: _nicknameCtrl,
                  pronounIndex: _pronounIndex,
                  avatarIndex: _avatarIndex,
                  pronouns: _pronouns,
                  avatarGradients: _avatarGradients,
                  onNicknameChanged: (v) {
                    setState(() => _nickname = v);
                    _persistProfile<String>(kProfileNickname, v);
                  },
                  onPronounSelected: (i) {
                    setState(() => _pronounIndex = i);
                    _persistProfile<int>(kProfilePronoun, i);
                  },
                  onAvatarSelected: (i) {
                    setState(() => _avatarIndex = i);
                    _persistProfile<int>(kProfileAvatar, i);
                  },
                ),

                // ── HOW ALEX TALKS TO YOU ─────────────────────────────────
                const SizedBox(height: 14),
                const SectionLabel('HOW ALEX TALKS TO YOU'),
                VoiceCard(
                  toneIndex: _toneIndex,
                  tones: _tones,
                  voiceNotes: _voiceNotes,
                  greetingStyleIndex: _greetingStyleIndex,
                  greetingStyles: _greetingStyles,
                  onToneSelected: (i) {
                    setState(() => _toneIndex = i);
                    _persistProfile<int>(kProfileTone, i);
                    ProfileConfig.setToneIndex(i);
                  },
                  onVoiceNotesToggled: (v) {
                    setState(() => _voiceNotes = v);
                    _persistProfile<bool>(kProfileVoiceNotes, v);
                  },
                  onGreetingStyleSelected: (i) {
                    setState(() => _greetingStyleIndex = i);
                    _persistProfile<int>('profile_greeting_style_v1', i);
                    ProfileConfig.setGreetingStyleIndex(i);
                  },
                ),

                // ── YOUR SAFETY PLAN ──────────────────────────────────────
                const SizedBox(height: 14),
                const SectionLabel('YOUR SAFETY PLAN'),
                SafetyPlanCard(
                  state: _planFilled ? SafetyPlanState.filled : SafetyPlanState.empty,
                  onBuild: widget.onBuildPlan,
                  onEdit: widget.onEditPlan,
                ),

                // Settings link
                const SizedBox(height: 18),
                Center(
                  child: GestureDetector(
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen())),
                    child: Text(
                      'Settings →',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                        color: GQColors.primaryDk,
                        decoration: TextDecoration.underline,
                        decorationColor: GQColors.primaryDk,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
