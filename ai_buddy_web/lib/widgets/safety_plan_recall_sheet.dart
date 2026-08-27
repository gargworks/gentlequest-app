// safety_plan_recall_sheet.dart — show the user's OWN safety plan back to
// them when they tap "Use now" on the Profile safety-plan card.
//
// Honesty audit §8: "Use now" was previously wired to the generic crisis
// intervention sheet (showCrisisInterventionSheet) even when the user had
// built and persisted their own plan. The data is sitting in
// SharedPreferences under safety_plan_step{0..4}_*_v1 keys; this sheet
// reads it back, renders it section-by-section, and exposes tap-to-call /
// tap-to-text on the two emergency contacts.
//
// If immediate-danger framing is the right surface, the footer still links
// to the generic crisis resources via [showCrisisInterventionSheet].
//
// Audit reference: .brain/audits/2026-05-24_gq_v1.3.0_honesty_audit.md §8.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../theme/gq_theme.dart';
import '../theme/gq_tokens.dart';
import 'crisis_resources.dart';

/// Convenience entry point — push the bottom sheet over the current route.
Future<void> showSafetyPlanRecallSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    useRootNavigator: true,
    builder: (_) => const SafetyPlanRecallSheet(),
  );
}

class SafetyPlanRecallSheet extends StatefulWidget {
  const SafetyPlanRecallSheet({super.key});

  @override
  State<SafetyPlanRecallSheet> createState() => _SafetyPlanRecallSheetState();
}

class _SafetyPlanRecallSheetState extends State<SafetyPlanRecallSheet> {
  bool _loading = true;

  List<String> _warnings = const [];
  List<String> _copings = const [];
  List<String> _places = const [];
  String _meaning = '';

  _PlanContact? _c1;
  _PlanContact? _c2;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();

    List<String> readNumbered(String prefix, int count) => List.generate(
          count,
          (i) => (prefs.getString('${prefix}_${i}_v1') ?? '').trim(),
        ).where((s) => s.isNotEmpty).toList();

    final warnings = readNumbered('safety_plan_step0_warning', 3);
    final copings = readNumbered('safety_plan_step1_coping', 3);
    final places = readNumbered('safety_plan_step3_place', 3);
    final meaning = (prefs.getString('safety_plan_step4_meaning_v1') ?? '').trim();

    _PlanContact? readContact(int slot) {
      final name = (prefs.getString('safety_plan_step2_contact_${slot}_name_v1') ?? '').trim();
      final rel = (prefs.getString('safety_plan_step2_contact_${slot}_rel_v1') ?? '').trim();
      final phone = (prefs.getString('safety_plan_step2_contact_${slot}_phone_v1') ?? '').trim();
      if (name.isEmpty && phone.isEmpty) return null;
      return _PlanContact(name: name, relation: rel, phone: phone);
    }

    if (!mounted) return;
    setState(() {
      _warnings = warnings;
      _copings = copings;
      _places = places;
      _meaning = meaning;
      _c1 = readContact(1);
      _c2 = readContact(2);
      _loading = false;
    });
  }

  Future<void> _call(String phone) async {
    final cleaned = phone.replaceAll(RegExp(r'[^0-9+]'), '');
    if (cleaned.isEmpty) return;
    final uri = Uri(scheme: 'tel', path: cleaned);
    final messenger = ScaffoldMessenger.of(context);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
        return;
      }
    } catch (_) {}
    await Clipboard.setData(ClipboardData(text: cleaned));
    messenger.showSnackBar(
      const SnackBar(content: Text('Call not supported. Number copied.')),
    );
  }

  Future<void> _sms(String phone) async {
    final cleaned = phone.replaceAll(RegExp(r'[^0-9+]'), '');
    if (cleaned.isEmpty) return;
    final uri = Uri(scheme: 'sms', path: cleaned);
    final messenger = ScaffoldMessenger.of(context);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
        return;
      }
    } catch (_) {}
    await Clipboard.setData(ClipboardData(text: cleaned));
    messenger.showSnackBar(
      const SnackBar(content: Text('SMS not supported. Number copied.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final viewInsets = MediaQuery.of(context).viewInsets.bottom;
    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      expand: false,
      builder: (ctx, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: t.surface,
            borderRadius: BorderRadius.vertical(top: Radius.circular(GQRadii.sheetLg)),
          ),
          padding: EdgeInsets.only(bottom: viewInsets),
          child: _loading
              ? const Center(
                  child: Padding(
                    padding: EdgeInsets.all(40),
                    child: CircularProgressIndicator(),
                  ),
                )
              : ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.fromLTRB(20, 14, 20, 28),
                  children: [
                    Center(
                      child: Container(
                        width: 40,
                        height: 4,
                        decoration: BoxDecoration(
                          color: t.hair,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            'Your safety plan',
                            style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 20,
                              fontWeight: FontWeight.w800,
                              color: t.ink,
                            ),
                          ),
                        ),
                        IconButton(
                          icon: Icon(Icons.close_rounded, color: t.ink2),
                          onPressed: () => Navigator.of(context).maybePop(),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      "You wrote this. It's still here.",
                      style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13,
                        color: t.ink2,
                      ),
                    ),
                    const SizedBox(height: 18),

                    if (_warnings.isNotEmpty)
                      _PlanSection(
                        eyebrow: 'WHEN I MIGHT NOTICE',
                        items: _warnings,
                      ),
                    if (_copings.isNotEmpty)
                      _PlanSection(
                        eyebrow: 'WHAT HELPS',
                        items: _copings,
                      ),
                    if (_c1 != null || _c2 != null) ...[
                      const _EyebrowLabel('PEOPLE I CAN CALL'),
                      const SizedBox(height: 8),
                      if (_c1 != null)
                        _ContactCard(
                          contact: _c1!,
                          onCall: _call,
                          onSms: _sms,
                        ),
                      if (_c1 != null && _c2 != null) const SizedBox(height: 10),
                      if (_c2 != null)
                        _ContactCard(
                          contact: _c2!,
                          onCall: _call,
                          onSms: _sms,
                        ),
                      const SizedBox(height: 14),
                    ],
                    if (_places.isNotEmpty)
                      _PlanSection(
                        eyebrow: 'PLACES I FEEL SAFE',
                        items: _places,
                      ),
                    if (_meaning.isNotEmpty)
                      _PlanSection(
                        eyebrow: 'WHY THIS IS WORTH IT',
                        items: [_meaning],
                      ),

                    const SizedBox(height: 8),
                    // Crisis-line bridge — always reachable.
                    GestureDetector(
                      onTap: () {
                        Navigator.of(context).maybePop();
                        showCrisisInterventionSheet(
                          context,
                          source: 'safety_plan_recall_footer',
                        );
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 14),
                        decoration: BoxDecoration(
                          color: t.coral.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(GQRadii.button),
                          border: Border.all(color: t.coral.withValues(alpha: 0.30)),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.phone_in_talk_outlined, size: 18, color: t.coral),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                'If you need someone right now — crisis lines',
                                style: TextStyle(
                                  fontFamily: GQTypography.bodyFamily,
                                  fontSize: 13.5,
                                  fontWeight: FontWeight.w700,
                                  color: t.coral,
                                ),
                              ),
                            ),
                            Icon(Icons.chevron_right_rounded, color: t.coral),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
        );
      },
    );
  }
}

class _PlanContact {
  const _PlanContact({required this.name, required this.relation, required this.phone});
  final String name;
  final String relation;
  final String phone;
}

class _EyebrowLabel extends StatelessWidget {
  const _EyebrowLabel(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 2),
      child: Text(
        text,
        style: TextStyle(
          fontFamily: GQTypography.bodyFamily,
          fontSize: 11,
          fontWeight: FontWeight.w800,
          letterSpacing: 1.2,
          color: t.ink2,
        ),
      ),
    );
  }
}

class _PlanSection extends StatelessWidget {
  const _PlanSection({required this.eyebrow, required this.items});
  final String eyebrow;
  final List<String> items;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _EyebrowLabel(eyebrow),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            color: t.bg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: t.hair),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < items.length; i++) ...[
                if (i > 0) const SizedBox(height: 8),
                Text(
                  items[i],
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: t.ink,
                    height: 1.45,
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _ContactCard extends StatelessWidget {
  const _ContactCard({
    required this.contact,
    required this.onCall,
    required this.onSms,
  });

  final _PlanContact contact;
  final ValueChanged<String> onCall;
  final ValueChanged<String> onSms;

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    final name = contact.name.isEmpty ? 'Contact' : contact.name;
    final hasPhone = contact.phone.isNotEmpty;
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 14),
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: t.hair),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            name,
            style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: t.ink,
            ),
          ),
          if (contact.relation.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              contact.relation,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 12,
                color: t.ink2,
              ),
            ),
          ],
          if (hasPhone) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => onCall(contact.phone),
                    icon: const Icon(Icons.phone_rounded, size: 18),
                    label: const Text('Call'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: t.primary,
                      side: BorderSide(color: t.primary),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(999),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => onSms(contact.phone),
                    icon: const Icon(Icons.sms_outlined, size: 18),
                    label: const Text('Text'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: t.ink2,
                      side: BorderSide(color: t.hair),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(999),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                  ),
                ),
              ],
            ),
          ] else ...[
            const SizedBox(height: 6),
            Text(
              'No phone saved for this contact.',
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 12,
                color: t.ink2,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
