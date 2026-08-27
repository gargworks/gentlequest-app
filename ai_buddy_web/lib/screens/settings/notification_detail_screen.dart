// Settings — D: notification detail screen (daily reminder, gentle nudge,
// reminder time, day-of-week picker) + test-notification button.
// Split from settings_screen.dart (R1D20). WO-5.3 Parts A1/A3/D/F.

import 'package:flutter/material.dart';

import '../../services/notification_service_impl.dart';
import '../../theme/gq_theme.dart';
import '../../theme/gq_tokens.dart';
import '../../widgets/gq/gq.dart';
import 'settings_widgets.dart';

// ─── Notification detail screen (View D) ─────────────────────────────────────

class NotificationDetailScreen extends StatefulWidget {
  const NotificationDetailScreen({super.key});

  @override
  State<NotificationDetailScreen> createState() =>
      _NotificationDetailScreenState();
}

class _NotificationDetailScreenState
    extends State<NotificationDetailScreen> {
  bool _dailyOn = true;
  bool _gentleNudgeOn = false;
  TimeOfDay _reminderTime = const TimeOfDay(hour: 20, minute: 0);

  // Persistent, point-of-failure banner for the test-notification button
  // (WO-5.3 Part D: failures render inline, amber, until dismissed —
  // success is silent, the notification itself is the confirmation).
  String? _testNotifError;

  // M T W T F active by default, S S off
  final List<bool> _days = [true, true, true, true, true, false, false];

  static const _dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _reminderTime,
    );
    if (picked != null && mounted) setState(() => _reminderTime = picked);
  }

  Future<void> _sendTestNotification() async {
    setState(() => _testNotifError = null);
    final granted = await NotificationService.requestPermissions();
    if (!granted) {
      if (!mounted) return;
      setState(() => _testNotifError =
          'Notifications permission denied. Enable in system settings.');
      return;
    }
    await NotificationService.sendTestNotification();
    // Success is silent — the notification arriving is the confirmation.
  }

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Scaffold(
      backgroundColor: t.bg,
      appBar: AppBar(
        backgroundColor: t.bg.withValues(alpha: 0.92),
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new, size: 14,
              color: t.ink),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Notifications',
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: t.ink),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 18, 16, 30),
        children: [
          // DAILY CHECK-IN CARD
          SettingsCard(
            children: [
              SettingsRow(
                iconBg: t.primarySoft,
                iconWidget: const Icon(Icons.notifications_outlined,
                    size: 14, color: GQColors.primaryDk),
                title: 'Daily check-in reminder',
                subtitle: 'A nudge to log your mood',
                trailing: SettingsToggle(
                  value: _dailyOn,
                  onChanged: (v) => setState(() => _dailyOn = v),
                ),
              ),
              if (_dailyOn)
                Padding(
                  padding: const EdgeInsets.fromLTRB(56, 10, 12, 4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Time picker
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 11),
                        decoration: BoxDecoration(
                          color: t.bg,
                          border: Border.all(
                              color: t.hair, width: 1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'REMIND ME AT',
                                    style: TextStyle(
                                        fontFamily: GQTypography.bodyFamily,
                                        fontSize: 10.5,
                                        fontWeight: FontWeight.w800,
                                        color: t.ink2,
                                        letterSpacing: 0.7),
                                  ),
                                  const SizedBox(height: 2),
                                  RichText(
                                    text: TextSpan(
                                      children: [
                                        TextSpan(
                                          text:
                                              '${_reminderTime.hourOfPeriod.toString().padLeft(2, '0')}:${_reminderTime.minute.toString().padLeft(2, '0')} ',
                                          style: TextStyle(
                                              fontFamily:
                                                  GQTypography.bodyFamily,
                                              fontSize: 18,
                                              fontWeight: FontWeight.w800,
                                              color: t.ink,
                                              letterSpacing: -0.5,
                                              height: 1.1),
                                        ),
                                        TextSpan(
                                          text: _reminderTime.period ==
                                                  DayPeriod.pm
                                              ? 'PM'
                                              : 'AM',
                                          style: TextStyle(
                                              fontFamily:
                                                  GQTypography.bodyFamily,
                                              fontSize: 13,
                                              fontWeight: FontWeight.w700,
                                              color: t.ink2),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            GestureDetector(
                              onTap: _pickTime,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 14, vertical: 8),
                                decoration: BoxDecoration(
                                  color: t.surface,
                                  border: Border.all(
                                      color: t.hair, width: 1),
                                  borderRadius:
                                      BorderRadius.circular(999),
                                ),
                                child: Text('Change',
                                    style: TextStyle(
                                        fontFamily:
                                            GQTypography.bodyFamily,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w800,
                                        color: t.ink2)),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      // Day chips
                      Text('ON DAYS',
                          style: TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 10.5,
                              fontWeight: FontWeight.w800,
                              color: t.ink2,
                              letterSpacing: 0.7)),
                      const SizedBox(height: 6),
                      Row(
                        children: List.generate(_dayLabels.length, (i) {
                          final active = _days[i];
                          return Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: GestureDetector(
                              onTap: () =>
                                  setState(() => _days[i] = !_days[i]),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color: active
                                      ? t.primary
                                      : t.surface,
                                  border: Border.all(
                                      color: active
                                          ? t.primary
                                          : t.hair,
                                      width: 1),
                                  borderRadius:
                                      BorderRadius.circular(999),
                                ),
                                child: Text(_dayLabels[i],
                                    style: TextStyle(
                                        fontFamily:
                                            GQTypography.bodyFamily,
                                        fontSize: 11.5,
                                        fontWeight: FontWeight.w800,
                                        // White stays literal — painted
                                        // directly on the primary fill above,
                                        // same fill/foreground discipline as
                                        // the primaryDk CTA.
                                        color: active
                                            ? Colors.white
                                            : t.ink2)),
                              ),
                            ),
                          );
                        }),
                      ),
                    ],
                  ),
                ),
            ],
          ),

          const SizedBox(height: 14),

          // GENTLE NUDGE CARD (WO-5.3 A1 rename — P9, number-first framing
          // is out; this is presence, not a counter).
          SettingsCard(
            children: [
              SettingsRow(
                iconBg: t.warmSoft,
                iconWidget:
                    const Text('🌱', style: TextStyle(fontSize: 14)),
                title: 'Gentle nudge',
                subtitle:
                    "We'll text you after a few good days in a row — never to shame, only to celebrate.",
                trailing: SettingsToggle(
                  value: _gentleNudgeOn,
                  onChanged: (v) => setState(() => _gentleNudgeOn = v),
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),

          // WORRIED CHECK-IN — LOCKED
          SettingsCard(
            children: [
              SettingsRow(
                iconBg: t.primarySoft,
                iconWidget: const Icon(Icons.favorite_outline,
                    size: 14, color: GQColors.primaryDk),
                title: 'Worried check-in',
                subtitle:
                    'Sent within 24h after we detect a heavy moment. Always optional to ignore.',
                trailing: const SettingsToggle(
                  value: true,
                  locked: true,
                  onChanged: null,
                ),
              ),
              Padding(
                padding:
                    const EdgeInsets.fromLTRB(56, 0, 12, 12),
                child: Container(
                  padding: const EdgeInsets.all(9),
                  decoration: BoxDecoration(
                    color: t.primary.withValues(alpha: 0.06),
                    border: Border.all(
                        color: t.primary.withValues(alpha: 0.25),
                        width: 1,
                        style: BorderStyle.solid),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.shield_outlined,
                          size: 13, color: GQColors.primaryDk),
                      const SizedBox(width: 6),
                      Expanded(
                        child: RichText(
                          text: TextSpan(
                            style: TextStyle(
                                fontFamily: GQTypography.bodyFamily,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: t.ink2,
                                height: 1.45),
                            children: [
                              const TextSpan(
                                  text:
                                      'Locked on for the next '),
                              TextSpan(
                                  text: '26 days',
                                  style: TextStyle(
                                      fontWeight: FontWeight.w800,
                                      color: t.ink)),
                              const TextSpan(
                                  text:
                                      ' — last heavy moment was Friday. Resets after 30 quiet days.'),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 18),

          if (_testNotifError != null) ...[
            GQBanner(
              message: _testNotifError!,
              category: GQBannerCategory.amber,
              onDismiss: () => setState(() => _testNotifError = null),
            ),
            const SizedBox(height: GQSpacing.md),
          ],

          // Test notification button — fires a real local notification so
          // the user sees exactly what the OS surface looks like.
          _TestNotificationBtn(onTap: _sendTestNotification),
        ],
      ),
    );
  }
}


/// "Send a test notification" button.
class _TestNotificationBtn extends StatelessWidget {
  final VoidCallback onTap;

  const _TestNotificationBtn({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final t = GQTheme.of(context);
    return Column(
      children: [
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 13),
            decoration: BoxDecoration(
              color: t.surface,
              border: Border.all(color: t.hair, width: 1),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.notifications_outlined,
                    size: 13, color: t.ink2),
                const SizedBox(width: 6),
                Text('Send a test notification',
                    style: TextStyle(
                        fontFamily: GQTypography.bodyFamily,
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: t.ink2)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          "See exactly what you'll get.",
          textAlign: TextAlign.center,
          style: TextStyle(
              fontFamily: GQTypography.bodyFamily,
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: t.ink2),
        ),
      ],
    );
  }
}
