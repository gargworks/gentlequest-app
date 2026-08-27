import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../services/firebase_service.dart';
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import 'profile_prefs_keys.dart';
import 'profile_widgets.dart';

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
    await prefs.setBool(kSafetyPlanFilled, true);
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
    final t = GQTheme.of(context);
    switch (idx) {
      case 0:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (var i = 0; i < 3; i++) ...[
              if (i > 0) const SizedBox(height: 10),
              ProfileCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Eyebrow('WHEN I NOTICE… ${i + 1}'),
                    const SizedBox(height: 8),
                    ContactTextField(
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
              ProfileCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Eyebrow('WHAT HELPS ME ${i + 1}'),
                    const SizedBox(height: 8),
                    ContactTextField(
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
              ProfileCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Eyebrow('PLACE ${i + 1}'),
                    const SizedBox(height: 8),
                    ContactTextField(
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
        return ProfileCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Eyebrow("THIS IS WHAT I'M HOLDING ON TO…"),
              const SizedBox(height: 8),
              TextField(
                controller: _meaningCtrl,
                minLines: 6,
                maxLines: 10,
                onChanged: (v) => _persistString('safety_plan_step4_meaning_v1', v),
                style: TextStyle(
                  fontFamily: GQTypography.bodyFamily,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: t.ink,
                  height: 1.5,
                ),
                decoration: InputDecoration(
                  hintText:
                      "Write to a future you who needs to remember. People, projects, small joys — anything.",
                  hintStyle: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: t.ink2,
                  ),
                  filled: true,
                  fillColor: t.bg,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
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
            ],
          ),
        );
      default:
        return const SizedBox.shrink();
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final header = _stepHeader(widget.stepIdx);
    final isFinalStep = widget.stepIdx >= 4;
    return Column(
      children: [
        // Nav bar
        BuilderNavBar(
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
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    color: t.ink2,
                    letterSpacing: 0.7,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  header.title,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: t.ink,
                    letterSpacing: -0.4,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  header.intro,
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: t.ink2,
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
                    OutlineButton(
                      label: 'Back',
                      onTap: widget.onClose ?? () => Navigator.maybePop(context),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: PrimaryButton(
                        label: isFinalStep ? 'Save plan' : 'Save & continue',
                        onTap: () async {
                          // Fires once per discrete Save tap (not on rebuild).
                          unawaited(FirebaseService().logEvent(
                            'safety_plan_step_saved',
                            {'step': widget.stepIdx},
                          ));
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
                        color: t.ink2,
                        decoration: TextDecoration.underline,
                        decorationColor: t.ink2,
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
    final t = GQTheme.of(context);
    return ProfileCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Eyebrow(label)),
              if (favorite)
                Text(
                  '★ favorite',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    // primaryDk stays static per the work order — GQTheme has
                    // no slot for it (CTA-fill discipline), even used as text here.
                    color: GQColors.primaryDk,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          ContactTextField(controller: nameCtrl, hint: 'Name', onChanged: onNameChanged),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: ContactTextField(controller: relCtrl, hint: 'Relationship', onChanged: onRelChanged),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ContactTextField(controller: phoneCtrl, hint: 'Phone', onChanged: onPhoneChanged),
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
                        color: t.ink,
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
                          color: t.ink2,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              GQToggle(value: favorite, onChanged: onFavoriteToggled),
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
    final t = GQTheme.of(context);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: t.coral.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: t.coral.withValues(alpha: 0.22),
          style: BorderStyle.solid,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Don't have anyone right now?",
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 12.5,
              fontWeight: FontWeight.w800,
              color: t.ink,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 3),
          RichText(
            text: TextSpan(
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                color: t.ink2,
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
                color: t.ink2,
                decoration: TextDecoration.underline,
                decorationColor: t.ink2,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
