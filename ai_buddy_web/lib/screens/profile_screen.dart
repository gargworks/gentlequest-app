import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/gq_tokens.dart';
import '../widgets/crisis_resources.dart';
import 'settings_screen.dart';

// profile_screen.dart — Tier 3.6 R1D19
//
// Implements GentleQuest Profile screen per GentleQuest_Profile.html.
// Views:
//   A · Profile home  — About you + How Alex talks + Safety plan hero card
//   B · Safety plan builder — 5 steps, content varies per step:
//        Step 1: Warning signs (3 fields)
//        Step 2: Coping strategies (3 fields)
//        Step 3: Two people I can call (2 contact cards)
//        Step 4: Places I feel safe (3 fields)
//        Step 5: Why this is worth it (1 large field)
//
// Profile + safety-plan data persisted via SharedPreferences (this tier).
// secure_storage migration is a separate follow-up.

// SharedPreferences key constants (centralised so reads + writes stay in sync).
const String _kProfileNickname = 'profile_nickname_v1';
const String _kProfilePronoun = 'profile_pronoun_v1';
const String _kProfileAvatar = 'profile_avatar_v1';
const String _kProfileTone = 'profile_tone_v1';
const String _kProfileVoiceNotes = 'profile_voice_notes_v1';
const String _kSafetyPlanFilled = 'safety_plan_filled_v1';

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

  @override
  void initState() {
    super.initState();
    _loadFromPrefs();
  }

  Future<void> _loadFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _nickname = prefs.getString(_kProfileNickname) ?? '';
      _pronounIndex = prefs.getInt(_kProfilePronoun) ?? -1;
      _avatarIndex = prefs.getInt(_kProfileAvatar) ?? 2;
      _toneIndex = prefs.getInt(_kProfileTone) ?? 0;
      _voiceNotes = prefs.getBool(_kProfileVoiceNotes) ?? false;
      _planFilled = prefs.getBool(_kSafetyPlanFilled) ?? false;
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
        _NavBar(
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
                const _SectionLabel('ABOUT YOU'),
                AboutYouCard(
                  nicknameController: _nicknameCtrl,
                  pronounIndex: _pronounIndex,
                  avatarIndex: _avatarIndex,
                  pronouns: _pronouns,
                  avatarGradients: _avatarGradients,
                  onNicknameChanged: (v) {
                    setState(() => _nickname = v);
                    _persistProfile<String>(_kProfileNickname, v);
                  },
                  onPronounSelected: (i) {
                    setState(() => _pronounIndex = i);
                    _persistProfile<int>(_kProfilePronoun, i);
                  },
                  onAvatarSelected: (i) {
                    setState(() => _avatarIndex = i);
                    _persistProfile<int>(_kProfileAvatar, i);
                  },
                ),

                // ── HOW ALEX TALKS TO YOU ─────────────────────────────────
                const SizedBox(height: 14),
                const _SectionLabel('HOW ALEX TALKS TO YOU'),
                VoiceCard(
                  toneIndex: _toneIndex,
                  tones: _tones,
                  voiceNotes: _voiceNotes,
                  onToneSelected: (i) {
                    setState(() => _toneIndex = i);
                    _persistProfile<int>(_kProfileTone, i);
                  },
                  onVoiceNotesToggled: (v) {
                    setState(() => _voiceNotes = v);
                    _persistProfile<bool>(_kProfileVoiceNotes, v);
                  },
                ),

                // ── YOUR SAFETY PLAN ──────────────────────────────────────
                const SizedBox(height: 14),
                const _SectionLabel('YOUR SAFETY PLAN'),
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
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Nickname field
          const _Eyebrow('NICKNAME · ALEX CALLS YOU'),
          const SizedBox(height: 6),
          TextField(
            controller: nicknameController,
            onChanged: onNicknameChanged,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: GQColors.ink,
            ),
            decoration: InputDecoration(
              hintText: '',
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
          ),
          const SizedBox(height: 6),
          Text(
            'Leave blank and Alex calls you "friend".',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: GQColors.ink3,
            ),
          ),

          // Pronouns picker
          const SizedBox(height: 14),
          const _Eyebrow('PRONOUNS'),
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
                    color: selected ? GQColors.primary : GQColors.softBg,
                    borderRadius: BorderRadius.circular(9999),
                    border: Border.all(
                      color: selected ? GQColors.primary : GQColors.hair,
                    ),
                  ),
                  child: Text(
                    pronouns[i],
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: selected ? Colors.white : GQColors.ink2,
                    ),
                  ),
                ),
              );
            }),
          ),

          // Avatar picker
          const SizedBox(height: 14),
          const _Eyebrow('AVATAR'),
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

// ─── VoiceCard ────────────────────────────────────────────────────────────────

class VoiceCard extends StatelessWidget {
  final int toneIndex;
  final List<String> tones;
  final bool voiceNotes;
  final ValueChanged<int> onToneSelected;
  final ValueChanged<bool> onVoiceNotesToggled;

  const VoiceCard({
    super.key,
    required this.toneIndex,
    required this.tones,
    required this.voiceNotes,
    required this.onToneSelected,
    required this.onVoiceNotesToggled,
  });

  @override
  Widget build(BuildContext context) {
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Tone segmented control
          const _Eyebrow('TONE'),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.all(3),
            decoration: BoxDecoration(
              color: GQColors.softBg,
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: GQColors.hair),
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
                        color: on ? Colors.white : Colors.transparent,
                        borderRadius: BorderRadius.circular(8),
                        boxShadow: on
                            ? [
                                BoxShadow(
                                  color: GQColors.ink.withValues(alpha: 0.08),
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
                          color: on ? GQColors.ink : GQColors.ink3,
                        ),
                      ),
                    ),
                  ),
                );
              }),
            ),
          ),

          // Greeting style dropdown (static display)
          const SizedBox(height: 14),
          const _Eyebrow('GREETING STYLE'),
          const SizedBox(height: 6),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: GQColors.softBg,
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: GQColors.hair),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Casual',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 13.5,
                          fontWeight: FontWeight.w700,
                          color: GQColors.ink,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '"Hey friend"',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: GQColors.ink3,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.keyboard_arrow_down_rounded,
                    color: GQColors.ink2, size: 20),
              ],
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
                        color: GQColors.ink,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Alex sends short voice replies',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: GQColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),
              _GQToggle(
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

// ─── SafetyPlanCard ───────────────────────────────────────────────────────────

enum SafetyPlanState { empty, partial, filled }

class SafetyPlanCard extends StatelessWidget {
  final SafetyPlanState state;
  final VoidCallback onBuild;
  final VoidCallback onEdit;

  const SafetyPlanCard({
    super.key,
    required this.state,
    required this.onBuild,
    required this.onEdit,
  });

  @override
  Widget build(BuildContext context) {
    if (state == SafetyPlanState.empty) {
      return _SafetyPlanEmpty(onBuild: onBuild);
    }
    return _SafetyPlanFilled(onEdit: onEdit);
  }
}

class _SafetyPlanFilled extends StatefulWidget {
  final VoidCallback onEdit;
  const _SafetyPlanFilled({required this.onEdit});

  @override
  State<_SafetyPlanFilled> createState() => _SafetyPlanFilledState();
}

class _SafetyPlanFilledState extends State<_SafetyPlanFilled> {
  // Universal crisis line — always shown so the contact list never
  // lies-by-omission even if the user skipped the contact step in the
  // builder. Per P6 ("crisis never blocks"), 988 stays present.
  static const _crisisContact = SafetyContact(
    initial: '988',
    name: 'Crisis line',
    detail: 'Free, 24/7, confidential',
    isCrisis: true,
    phone: '988',
  );

  /// Contacts list rendered in the filled-state card.
  /// Hydrated on initState from the SharedPreferences keys that
  /// SafetyPlanBuilderStep writes in Step 2
  /// (`safety_plan_step2_contact_{1,2}_{name,rel,phone}_v1`).
  /// Fallback is crisis-line-only — never empty.
  List<SafetyContact> _contacts = const [_crisisContact];

  @override
  void initState() {
    super.initState();
    _loadContacts();
  }

  Future<void> _loadContacts() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final c1Name = (prefs.getString('safety_plan_step2_contact_1_name_v1') ?? '').trim();
      final c1Rel = (prefs.getString('safety_plan_step2_contact_1_rel_v1') ?? '').trim();
      final c1Phone = (prefs.getString('safety_plan_step2_contact_1_phone_v1') ?? '').trim();
      final c2Name = (prefs.getString('safety_plan_step2_contact_2_name_v1') ?? '').trim();
      final c2Rel = (prefs.getString('safety_plan_step2_contact_2_rel_v1') ?? '').trim();
      final c2Phone = (prefs.getString('safety_plan_step2_contact_2_phone_v1') ?? '').trim();

      final list = <SafetyContact>[];
      if (c1Name.isNotEmpty || c1Phone.isNotEmpty) {
        list.add(SafetyContact(
          initial: c1Name.isNotEmpty
              ? c1Name.characters.first.toUpperCase()
              : '?',
          name: c1Name.isNotEmpty ? c1Name : 'Contact 1',
          detail: c1Rel.isNotEmpty
              ? c1Rel
              : (c1Phone.isNotEmpty ? c1Phone : ''),
          isCrisis: false,
          phone: c1Phone,
        ));
      }
      if (c2Name.isNotEmpty || c2Phone.isNotEmpty) {
        list.add(SafetyContact(
          initial: c2Name.isNotEmpty
              ? c2Name.characters.first.toUpperCase()
              : '?',
          name: c2Name.isNotEmpty ? c2Name : 'Contact 2',
          detail: c2Rel.isNotEmpty
              ? c2Rel
              : (c2Phone.isNotEmpty ? c2Phone : ''),
          isCrisis: false,
          phone: c2Phone,
        ));
      }
      // Always append the universal crisis line so the card never
      // lies-by-omission even when user contacts ARE present.
      list.add(_crisisContact);

      if (mounted) setState(() => _contacts = list);
    } catch (e) {
      debugPrint('[safety_plan_filled] load contacts failed: $e');
      // Keep the crisis-only fallback — never leave the user without 988.
    }
  }

  /// Forward to the widget-supplied edit callback (unchanged API).
  VoidCallback get onEdit => widget.onEdit;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            GQColors.safetyGradStart,
            GQColors.safetyGradMid,
            GQColors.safetyGradEnd,
          ],
          stops: [0.0, 0.6, 1.0],
        ),
        boxShadow: [
          BoxShadow(
            color: GQColors.primary.withValues(alpha: 0.55),
            blurRadius: 44,
            offset: const Offset(0, 22),
            spreadRadius: -18,
          ),
        ],
      ),
      child: Stack(
        children: [
          // Radial highlight
          Positioned(
            top: -30,
            right: -30,
            child: Container(
              width: 170,
              height: 170,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  center: Alignment(-0.4, -0.4),
                  colors: [
                    Color(0x4DFFFFFF),
                    Color(0x00FFFFFF),
                  ],
                  stops: [0.0, 0.6],
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Pills
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    _SafetyPill(label: 'FOR HEAVY DAYS'),
                    _SafetyPill(
                      label: 'ENCRYPTED ON DEVICE',
                      icon: Icons.shield_outlined,
                      iconColor: Colors.white,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                // Headline (copy verbatim from HTML)
                const Text(
                  'When the heavy hits, your plan is here.',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 19,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    letterSpacing: -0.4,
                    height: 1.25,
                  ),
                ),
                const SizedBox(height: 12),
                // Contacts
                SafetyContactsPreview(contacts: _contacts),
                const SizedBox(height: 12),
                // Action buttons
                Row(
                  children: [
                    Expanded(
                      child: _SafetyButton(
                        label: 'Edit plan',
                        onTap: onEdit,
                        style: _SafetyButtonStyle.ghost,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _SafetyButton(
                        label: 'Use now',
                        // "Use now" on the safety-plan card should surface
                        // the USER'S OWN safety plan, not the generic
                        // AI-detected crisis sheet. Until SafetyPlanRecall
                        // ships, fall back to the crisis sheet but flag
                        // the source so the choice is logged separately
                        // for analytics.
                        // FUTURE WORK: replace with
                        //   showSafetyPlanRecallSheet(context, contacts: ..., steps: ...)
                        // once the safety-plan builder actually persists
                        // contacts + plan steps (see _SafetyPlanFilled
                        // hardcoded sample data).
                        onTap: () => showCrisisInterventionSheet(
                          context,
                          source: 'safety_plan_use_now',
                        ),
                        style: _SafetyButtonStyle.solid,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                // Footer copy (verbatim from HTML)
                const Text(
                  'Alex shows this to you fast when you need it most. Never to anyone else.',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 11,
                    color: Colors.white,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SafetyPlanEmpty extends StatelessWidget {
  final VoidCallback onBuild;
  const _SafetyPlanEmpty({required this.onBuild});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            GQColors.safetyGradStart,
            GQColors.safetyGradMid,
            GQColors.safetyGradEnd,
          ],
          stops: [0.0, 0.6, 1.0],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'A plan for the heavy days',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 19,
              fontWeight: FontWeight.w800,
              color: Colors.white,
              letterSpacing: -0.4,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Five light questions. Five minutes. You\'ll be glad it\'s there.',
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 13,
              color: Colors.white,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _SafetyButton(
                  label: 'Build my safety plan',
                  onTap: onBuild,
                  style: _SafetyButtonStyle.solid,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _SafetyButton(
                  label: 'Maybe later',
                  onTap: () => Navigator.of(context).maybePop(),
                  style: _SafetyButtonStyle.ghost,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─── SafetyContactsPreview ────────────────────────────────────────────────────

class SafetyContact {
  final String initial;
  final String name;
  final String detail;
  final bool isCrisis;
  final String phone;

  const SafetyContact({
    required this.initial,
    required this.name,
    required this.detail,
    required this.isCrisis,
    required this.phone,
  });
}

class SafetyContactsPreview extends StatelessWidget {
  final List<SafetyContact> contacts;

  const SafetyContactsPreview({super.key, required this.contacts});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: contacts.map((c) => _ContactRow(contact: c)).toList(),
    );
  }
}

class _ContactRow extends StatelessWidget {
  final SafetyContact contact;
  const _ContactRow({required this.contact});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(9),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          // Avatar
          Container(
            width: 30,
            height: 30,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: Color(0xD9FFFFFF),
            ),
            child: Center(
              child: Text(
                contact.initial,
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: GQColors.safetyCallButtonInk,
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          // Name + detail
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  contact.name,
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                Text(
                  contact.detail,
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10.5,
                    color: Colors.white,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          // Call button
          GestureDetector(
            onTap: () async {
              final phone = contact.phone;
              if (phone.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Add a phone number for ${contact.name} first.')),
                );
                return;
              }
              final uri = Uri.parse('tel:$phone');
              if (await canLaunchUrl(uri)) {
                await launchUrl(uri);
              } else if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Cannot dial ${contact.name} from this device.')),
                );
              }
            },
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
              decoration: BoxDecoration(
                color: contact.isCrisis ? GQColors.coral : Colors.white,
                borderRadius: BorderRadius.circular(9999),
              ),
              child: Text(
                'Call',
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: contact.isCrisis
                      ? Colors.white
                      : GQColors.safetyCallButtonInk,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── View B · Safety plan builder (5 steps, distinct content per step) ─────

class SafetyPlanBuilderStep extends StatefulWidget {
  final int stepIdx;
  final VoidCallback? onClose;
  final VoidCallback? onNext;
  // Fired when the user finishes step 5 (Save & continue on the final step).
  // ProfileScreen uses this to flip the safety_plan_filled_v1 flag refresh
  // and pop back to the home view.
  final VoidCallback? onCompleted;

  const SafetyPlanBuilderStep({
    super.key,
    required this.stepIdx,
    this.onClose,
    this.onNext,
    this.onCompleted,
  });

  @override
  State<SafetyPlanBuilderStep> createState() => _SafetyPlanBuilderStepState();
}

class _SafetyPlanBuilderStepState extends State<SafetyPlanBuilderStep> {
  // Step 0 — Warning signs (3 free-text fields)
  final List<TextEditingController> _warningCtrls =
      List.generate(3, (_) => TextEditingController());

  // Step 1 — Coping strategies (3 free-text fields)
  final List<TextEditingController> _copingCtrls =
      List.generate(3, (_) => TextEditingController());

  // Step 2 — Two people I can call (existing contact cards)
  final _c1NameCtrl = TextEditingController();
  final _c1RelCtrl = TextEditingController();
  final _c1PhoneCtrl = TextEditingController();
  bool _c1Fav = true;
  final _c2NameCtrl = TextEditingController();
  final _c2RelCtrl = TextEditingController();
  final _c2PhoneCtrl = TextEditingController();
  bool _c2Fav = false;

  // Step 3 — Places I feel safe (3 free-text fields)
  final List<TextEditingController> _placeCtrls =
      List.generate(3, (_) => TextEditingController());

  // Step 4 — Why this is worth it (1 large field)
  final TextEditingController _meaningCtrl = TextEditingController();

  // Per-key debouncers for disk writes — keep cadence consistent with profile
  // form (500ms) so quick typing doesn't thrash SharedPreferences.
  final Map<String, Timer> _debouncers = {};

  @override
  void initState() {
    super.initState();
    _loadStepData();
  }

  Future<void> _loadStepData() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      for (var i = 0; i < 3; i++) {
        _warningCtrls[i].text = prefs.getString('safety_plan_step0_warning_${i}_v1') ?? '';
        _copingCtrls[i].text = prefs.getString('safety_plan_step1_coping_${i}_v1') ?? '';
        _placeCtrls[i].text = prefs.getString('safety_plan_step3_place_${i}_v1') ?? '';
      }
      _c1NameCtrl.text = prefs.getString('safety_plan_step2_contact_1_name_v1') ?? '';
      _c1RelCtrl.text = prefs.getString('safety_plan_step2_contact_1_rel_v1') ?? '';
      _c1PhoneCtrl.text = prefs.getString('safety_plan_step2_contact_1_phone_v1') ?? '';
      _c2NameCtrl.text = prefs.getString('safety_plan_step2_contact_2_name_v1') ?? '';
      _c2RelCtrl.text = prefs.getString('safety_plan_step2_contact_2_rel_v1') ?? '';
      _c2PhoneCtrl.text = prefs.getString('safety_plan_step2_contact_2_phone_v1') ?? '';
      _meaningCtrl.text = prefs.getString('safety_plan_step4_meaning_v1') ?? '';
    });
  }

  void _persistString(String key, String value) {
    _debouncers[key]?.cancel();
    _debouncers[key] = Timer(const Duration(milliseconds: 500), () async {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(key, value);
    });
  }

  Future<void> _markPlanFilled() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kSafetyPlanFilled, true);
  }

  @override
  void dispose() {
    for (final t in _debouncers.values) {
      t.cancel();
    }
    _debouncers.clear();
    for (final c in _warningCtrls) {
      c.dispose();
    }
    for (final c in _copingCtrls) {
      c.dispose();
    }
    for (final c in _placeCtrls) {
      c.dispose();
    }
    _c1NameCtrl.dispose();
    _c1RelCtrl.dispose();
    _c1PhoneCtrl.dispose();
    _c2NameCtrl.dispose();
    _c2RelCtrl.dispose();
    _c2PhoneCtrl.dispose();
    _meaningCtrl.dispose();
    super.dispose();
  }

  // Per-step header metadata — eyebrow tag + headline + intro paragraph.
  ({String eyebrow, String title, String intro}) _stepHeader(int idx) {
    switch (idx) {
      case 0:
        return (
          eyebrow: 'STEP 1 OF 5',
          title: 'My warning signs.',
          intro:
              "What's the early signal that the heavy is coming? Naming it helps you catch it sooner.",
        );
      case 1:
        return (
          eyebrow: 'STEP 2 OF 5',
          title: 'Things that actually help me.',
          intro:
              "Small moves that have worked before — even if just a little. We'll surface these when you need them.",
        );
      case 2:
        return (
          eyebrow: 'STEP 3 OF 5',
          title: 'Two people I can call.',
          intro:
              'When the heavy hits, having names ready helps. These stay on your phone — they never leave it.',
        );
      case 3:
        return (
          eyebrow: 'STEP 4 OF 5',
          title: 'Places I feel safe.',
          intro:
              'Spots — physical or in your head — where the volume turns down. List the ones that work.',
        );
      case 4:
        return (
          eyebrow: 'STEP 5 OF 5',
          title: "Why this is worth it.",
          intro:
              'The reason you keep going. Write it for the version of you who needs to hear it later.',
        );
      default:
        return (eyebrow: '', title: '', intro: '');
    }
  }

  // Render the per-step body. Switch keeps the file scrollable without
  // splintering into 5 tiny widgets — each branch is short.
  Widget _buildStepBody(int idx) {
    switch (idx) {
      case 0:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (var i = 0; i < 3; i++) ...[
              if (i > 0) const SizedBox(height: 10),
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Eyebrow('WHEN I NOTICE… ${i + 1}'),
                    const SizedBox(height: 8),
                    _ContactTextField(
                      controller: _warningCtrls[i],
                      hint: i == 0
                          ? 'e.g. I stop replying to friends'
                          : i == 1
                              ? 'e.g. sleep slips past 3am'
                              : 'e.g. I skip meals',
                      onChanged: (v) => _persistString(
                          'safety_plan_step0_warning_${i}_v1', v),
                    ),
                  ],
                ),
              ),
            ],
          ],
        );
      case 1:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (var i = 0; i < 3; i++) ...[
              if (i > 0) const SizedBox(height: 10),
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Eyebrow('WHAT HELPS ME ${i + 1}'),
                    const SizedBox(height: 8),
                    _ContactTextField(
                      controller: _copingCtrls[i],
                      hint: i == 0
                          ? 'e.g. walk to the park'
                          : i == 1
                              ? 'e.g. cold water on my face'
                              : 'e.g. message my sister',
                      onChanged: (v) => _persistString(
                          'safety_plan_step1_coping_${i}_v1', v),
                    ),
                  ],
                ),
              ),
            ],
          ],
        );
      case 2:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ContactCard(
              label: 'PERSON ONE',
              nameCtrl: _c1NameCtrl,
              relCtrl: _c1RelCtrl,
              phoneCtrl: _c1PhoneCtrl,
              favorite: _c1Fav,
              onFavoriteToggled: (v) => setState(() => _c1Fav = v),
              onNameChanged: (v) => _persistString('safety_plan_step2_contact_1_name_v1', v),
              onRelChanged: (v) => _persistString('safety_plan_step2_contact_1_rel_v1', v),
              onPhoneChanged: (v) => _persistString('safety_plan_step2_contact_1_phone_v1', v),
            ),
            const SizedBox(height: 10),
            ContactCard(
              label: 'PERSON TWO',
              nameCtrl: _c2NameCtrl,
              relCtrl: _c2RelCtrl,
              phoneCtrl: _c2PhoneCtrl,
              favorite: _c2Fav,
              onFavoriteToggled: (v) => setState(() => _c2Fav = v),
              onNameChanged: (v) => _persistString('safety_plan_step2_contact_2_name_v1', v),
              onRelChanged: (v) => _persistString('safety_plan_step2_contact_2_rel_v1', v),
              onPhoneChanged: (v) => _persistString('safety_plan_step2_contact_2_phone_v1', v),
            ),
            const SizedBox(height: 14),
            const NoOneSkipBlock(),
          ],
        );
      case 3:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (var i = 0; i < 3; i++) ...[
              if (i > 0) const SizedBox(height: 10),
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Eyebrow('PLACE ${i + 1}'),
                    const SizedBox(height: 8),
                    _ContactTextField(
                      controller: _placeCtrls[i],
                      hint: i == 0
                          ? 'e.g. the bench at Roundwood Park'
                          : i == 1
                              ? 'e.g. my room with the blinds down'
                              : 'e.g. the library on Tuesday afternoons',
                      onChanged: (v) => _persistString(
                          'safety_plan_step3_place_${i}_v1', v),
                    ),
                  ],
                ),
              ),
            ],
          ],
        );
      case 4:
        return _Card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _Eyebrow("THIS IS WHAT I'M HOLDING ON TO…"),
              const SizedBox(height: 8),
              TextField(
                controller: _meaningCtrl,
                minLines: 6,
                maxLines: 10,
                onChanged: (v) => _persistString('safety_plan_step4_meaning_v1', v),
                style: const TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: GQColors.ink,
                  height: 1.5,
                ),
                decoration: InputDecoration(
                  hintText:
                      "Write to a future you who needs to remember. People, projects, small joys — anything.",
                  hintStyle: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: GQColors.ink3,
                  ),
                  filled: true,
                  fillColor: GQColors.softBg,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
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
              ),
            ],
          ),
        );
      default:
        return const SizedBox.shrink();
    }
  }

  @override
  Widget build(BuildContext context) {
    final header = _stepHeader(widget.stepIdx);
    final isFinalStep = widget.stepIdx >= 4;
    return Column(
      children: [
        // Nav bar
        _BuilderNavBar(
          stepIdx: widget.stepIdx,
          total: 5,
          onClose: widget.onClose ?? () => Navigator.maybePop(context),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 30),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Step header
                Text(
                  header.eyebrow,
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink3,
                    letterSpacing: 0.7,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  header.title,
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink,
                    letterSpacing: -0.4,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  header.intro,
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: GQColors.ink2,
                    height: 1.5,
                  ),
                ),

                // Step body (varies by stepIdx)
                const SizedBox(height: 14),
                _buildStepBody(widget.stepIdx),

                // Action row
                const SizedBox(height: 18),
                Row(
                  children: [
                    _OutlineButton(
                      label: 'Back',
                      onTap: widget.onClose ?? () => Navigator.maybePop(context),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _PrimaryButton(
                        label: isFinalStep ? 'Save plan' : 'Save & continue',
                        onTap: () async {
                          if (isFinalStep) {
                            // Final step: persist filled flag + return to home.
                            await _markPlanFilled();
                            if (!context.mounted) return;
                            final completed = widget.onCompleted;
                            if (completed != null) {
                              completed();
                            } else {
                              Navigator.maybePop(context);
                            }
                          } else {
                            (widget.onNext ?? widget.onClose ?? () => Navigator.maybePop(context))();
                          }
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Center(
                  child: GestureDetector(
                    onTap: widget.onClose ?? () => Navigator.maybePop(context),
                    child: Text(
                      'Save & exit · you can come back anytime',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink3,
                        decoration: TextDecoration.underline,
                        decorationColor: GQColors.ink3,
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

// ─── ContactCard ──────────────────────────────────────────────────────────────

class ContactCard extends StatelessWidget {
  final String label;
  final TextEditingController nameCtrl;
  final TextEditingController relCtrl;
  final TextEditingController phoneCtrl;
  final bool favorite;
  final ValueChanged<bool> onFavoriteToggled;
  // Optional onChanged hooks — present in builder mode so each keystroke
  // routes through SharedPreferences debouncer. Stateless display callers
  // can omit them.
  final ValueChanged<String>? onNameChanged;
  final ValueChanged<String>? onRelChanged;
  final ValueChanged<String>? onPhoneChanged;

  const ContactCard({
    super.key,
    required this.label,
    required this.nameCtrl,
    required this.relCtrl,
    required this.phoneCtrl,
    required this.favorite,
    required this.onFavoriteToggled,
    this.onNameChanged,
    this.onRelChanged,
    this.onPhoneChanged,
  });

  @override
  Widget build(BuildContext context) {
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: _Eyebrow(label)),
              if (favorite)
                Text(
                  '★ favorite',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    color: GQColors.primaryDk,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          _ContactTextField(controller: nameCtrl, hint: 'Name', onChanged: onNameChanged),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _ContactTextField(controller: relCtrl, hint: 'Relationship', onChanged: onRelChanged),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _ContactTextField(controller: phoneCtrl, hint: 'Phone', onChanged: onPhoneChanged),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Add to favorites',
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13.5,
                        fontWeight: FontWeight.w700,
                        color: GQColors.ink,
                      ),
                    ),
                    if (favorite) ...[
                      const SizedBox(height: 2),
                      Text(
                        'Tap-to-call shortcut on the crisis screen',
                        style: TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: GQColors.ink3,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              _GQToggle(value: favorite, onChanged: onFavoriteToggled),
            ],
          ),
        ],
      ),
    );
  }
}

// ─── NoOneSkipBlock ───────────────────────────────────────────────────────────

class NoOneSkipBlock extends StatelessWidget {
  const NoOneSkipBlock({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: GQColors.coral.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: GQColors.coral.withValues(alpha: 0.22),
          style: BorderStyle.solid,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "Don't have anyone right now?",
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 12.5,
              fontWeight: FontWeight.w800,
              color: GQColors.ink,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 3),
          RichText(
            text: const TextSpan(
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                color: GQColors.ink2,
                height: 1.45,
              ),
              children: [
                TextSpan(text: "That's not a fail. We'll keep "),
                TextSpan(
                  text: '988',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                TextSpan(
                    text: ' always-on at the top of your crisis screen.'),
              ],
            ),
          ),
          const SizedBox(height: 8),
          GestureDetector(
            onTap: () => Navigator.of(context).maybePop(),
            child: Text(
              'Skip — use 988 only',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
                color: GQColors.ink3,
                decoration: TextDecoration.underline,
                decorationColor: GQColors.ink3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Shared primitives ────────────────────────────────────────────────────────

class _NavBar extends StatelessWidget {
  final String title;
  final bool showBack;
  final bool showClose;
  final VoidCallback? onBack;
  final VoidCallback? onClose;

  const _NavBar({
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
            _IconCircleButton(
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
            _IconCircleButton(
              icon: Icons.close_rounded,
              onTap: onClose ?? () {},
            ),
        ],
      ),
    );
  }
}

class _BuilderNavBar extends StatelessWidget {
  final int stepIdx;
  final int total;
  final VoidCallback onClose;

  const _BuilderNavBar({
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
          _IconCircleButton(
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

class _IconCircleButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final double size;
  final double iconSize;

  const _IconCircleButton({
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

class _Card extends StatelessWidget {
  final Widget child;
  const _Card({required this.child});

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

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

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
          color: GQColors.ink3,
          letterSpacing: 0.7,
        ),
      ),
    );
  }
}

class _Eyebrow extends StatelessWidget {
  final String text;
  const _Eyebrow(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontFamily: GQTypography.bodyFamily,
        fontSize: 10.5,
        fontWeight: FontWeight.w800,
        color: GQColors.ink3,
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

class _GQToggle extends StatelessWidget {
  final bool value;
  final ValueChanged<bool> onChanged;

  const _GQToggle({required this.value, required this.onChanged});

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

class _SafetyPill extends StatelessWidget {
  final String label;
  final IconData? icon;
  final Color? iconColor;

  const _SafetyPill({required this.label, this.icon, this.iconColor});

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

enum _SafetyButtonStyle { ghost, solid }

class _SafetyButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final _SafetyButtonStyle style;

  const _SafetyButton({
    required this.label,
    required this.onTap,
    required this.style,
  });

  @override
  Widget build(BuildContext context) {
    final isGhost = style == _SafetyButtonStyle.ghost;
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

class _ContactTextField extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final ValueChanged<String>? onChanged;

  const _ContactTextField({
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
          color: GQColors.ink3,
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

class _PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _PrimaryButton({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 13),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(9999),
          color: GQColors.primary,
          boxShadow: const [
            BoxShadow(
              color: Color(0x8C667EEA),
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

class _OutlineButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _OutlineButton({required this.label, required this.onTap});

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
