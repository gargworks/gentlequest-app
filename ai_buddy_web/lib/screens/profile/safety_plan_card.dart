import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/safety_plan_recall_sheet.dart';
import 'profile_widgets.dart';

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
                    SafetyPill(label: 'FOR HEAVY DAYS'),
                    SafetyPill(
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
                      child: SafetyButton(
                        label: 'Edit plan',
                        onTap: onEdit,
                        style: SafetyButtonStyle.ghost,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: SafetyButton(
                        label: 'Use now',
                        // Surfaces the user's OWN persisted safety plan
                        // (warning signs, coping steps, contacts, safe
                        // places, meaning) — not the generic AI crisis
                        // sheet. The crisis sheet remains reachable via
                        // the footer of SafetyPlanRecallSheet for
                        // immediate-danger escalation.
                        // See .brain/audits/2026-05-24_gq_v1.3.0_honesty_audit.md §8.
                        onTap: () => showSafetyPlanRecallSheet(context),
                        style: SafetyButtonStyle.solid,
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
                child: SafetyButton(
                  label: 'Build my safety plan',
                  onTap: onBuild,
                  style: SafetyButtonStyle.solid,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: SafetyButton(
                  label: 'Maybe later',
                  onTap: () => Navigator.of(context).maybePop(),
                  style: SafetyButtonStyle.ghost,
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
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        contact.name.isNotEmpty
                            ? 'Calling ${contact.name}…'
                            : 'Calling…',
                      ),
                      duration: const Duration(seconds: 4),
                    ),
                  );
                }
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
