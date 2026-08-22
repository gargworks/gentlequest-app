// shareable_mood_card.dart — Shareable weekly mood summary card.
//
// Renders a self-contained, branded card summarizing a week of mood logs,
// captures it as a PNG via a RepaintBoundary (screenshot package), and shares
// the image + a UTM-tagged deep link through the OS share sheet (share_plus).
//
// Design system: GQColors / GQRadii / GQTypography from lib/theme/gq_tokens.dart.
// Reuses the moodPalette ordering (index 0 low-energy → 4 high-energy) and the
// "coral-not-red / shapes not scores" principles from the weekly review.
//
// The card is presented in a modal sheet; the Share button lives OUTSIDE the
// captured boundary so it never appears in the exported PNG.

import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:screenshot/screenshot.dart';
import 'package:share_plus/share_plus.dart';

import '../screens/weekly_review_screen.dart' show WeeklyReviewData, DayMoodEntry;
import '../theme/gq_tokens.dart';

/// UTM-tagged deep link included on the card and in the shared text.
const String _kShareDeepLink =
    'https://app.gentlequest.app/?ref=shared_card&utm_source=user_share&utm_medium=organic';

/// Emoji used to represent each mood index (0–4), matching the
/// moodPalette ordering (low-energy → high-energy).
const List<String> _kMoodEmoji = [
  '🌙', // 0 — calm / low
  '🌧️', // 1 — heavy
  '🌤️', // 2 — okay / mid
  '☀️', // 3 — good
  '🌈', // 4 — lifted / high
];

/// Opens the shareable mood card as a modal bottom sheet.
void showShareableMoodCard(BuildContext context, WeeklyReviewData data) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => _ShareableMoodCardSheet(data: data),
  );
}

class _ShareableMoodCardSheet extends StatelessWidget {
  const _ShareableMoodCardSheet({required this.data});
  final WeeklyReviewData data;

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    return Container(
      decoration: const BoxDecoration(
        color: GQColors.softBg,
        borderRadius: BorderRadius.vertical(top: Radius.circular(GQRadii.sheet)),
      ),
      padding: EdgeInsets.only(bottom: mediaQuery.viewInsets.bottom),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Grabber
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: GQColors.hair,
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'SHARE YOUR WEEK',
                    style: TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: GQColors.ink2,
                      letterSpacing: 1.2,
                    ),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.of(context).pop(),
                    child: Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                        border: Border.all(color: GQColors.hair),
                      ),
                      child: const Icon(Icons.close, size: 14, color: GQColors.ink),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              _ShareableMoodCardBody(data: data),
            ],
          ),
        ),
      ),
    );
  }
}

/// Owns the ScreenshotController and renders the captured card + Share button.
class _ShareableMoodCardBody extends StatefulWidget {
  const _ShareableMoodCardBody({required this.data});
  final WeeklyReviewData data;

  @override
  State<_ShareableMoodCardBody> createState() => _ShareableMoodCardBodyState();
}

class _ShareableMoodCardBodyState extends State<_ShareableMoodCardBody> {
  final ScreenshotController _screenshotController = ScreenshotController();
  bool _sharing = false;

  // Live week data passed through from the weekly review screen.
  late final WeeklyReviewData _data = widget.data;

  Future<void> _share() async {
    if (_sharing) return;
    setState(() => _sharing = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final Uint8List? png = await _screenshotController.capture();
      if (png == null) {
        messenger.showSnackBar(
          const SnackBar(content: Text('Could not capture the card.')),
        );
        return;
      }
      final Directory tmp = await getTemporaryDirectory();
      final String path =
          '${tmp.path}/gentlequest_week_${DateTime.now().millisecondsSinceEpoch}.png';
      final File file = File(path);
      await file.writeAsBytes(png);

      final String shareText =
          'My week with GentleQuest — ${_data.weekLabel}.\n$_kShareDeepLink';
      await Share.shareXFiles(
        [XFile(path, mimeType: 'image/png')],
        text: shareText,
        subject: 'My GentleQuest week',
      );
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('Sharing failed: $e')),
      );
    } finally {
      if (mounted) setState(() => _sharing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Captured region — this is what becomes the PNG.
        Screenshot(
          controller: _screenshotController,
          child: _ShareableMoodCard(data: _data),
        ),
        const SizedBox(height: 16),
        // Share button — OUTSIDE the captured boundary.
        GestureDetector(
          onTap: _sharing ? null : _share,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: GQColors.primaryDk,
              borderRadius: BorderRadius.circular(GQRadii.button),
              boxShadow: [
                BoxShadow(
                  color: GQColors.primaryDk.withValues(alpha: 0.35),
                  blurRadius: 24,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  _sharing ? Icons.hourglass_top : Icons.share_outlined,
                  size: 14,
                  color: Colors.white,
                ),
                const SizedBox(width: 6),
                Text(
                  _sharing ? 'Preparing…' : 'Share this card',
                  style: const TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Your mood details stay private — only this card is shared.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: GQColors.ink2,
          ),
        ),
      ],
    );
  }
}

/// The visual card itself. Designed to look good as a standalone PNG:
/// gradient header, mood emoji + week label, mini mood-shape row, an
/// encouraging message, and a branded footer with the deep link.
class _ShareableMoodCard extends StatelessWidget {
  const _ShareableMoodCard({required this.data});
  final WeeklyReviewData data;

  @override
  Widget build(BuildContext context) {
    final double avgIndex = _averageMoodIndex(data.days);
    final int emojiIndex = avgIndex.round().clamp(0, _kMoodEmoji.length - 1);
    final String encouragement = _encouragement(data, avgIndex);

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFFEEF4FF),
            Color(0xFFF8F7FF),
          ],
        ),
        borderRadius: BorderRadius.circular(GQRadii.cardLg),
        border: Border.all(color: GQColors.hair),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header: eyebrow + week label ───────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'MY WEEK',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink2,
                    letterSpacing: 1.4,
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: GQColors.primarySoft,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    '${data.logCount} / 7 LOGGED',
                    style: const TextStyle(
                      fontFamily: GQTypography.bodyFamily,
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      color: GQColors.primaryDk,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
          // ── Emoji + week label ─────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 14, 20, 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(
                  _kMoodEmoji[emojiIndex],
                  style: const TextStyle(fontSize: 44, height: 1.0),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        data.weekLabel,
                        style: const TextStyle(
                          fontFamily: GQTypography.bodyFamily,
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: GQColors.ink,
                          height: 1.2,
                        ),
                      ),
                      const SizedBox(height: 2),
                      const Text(
                        'with GentleQuest',
                        style: TextStyle(
                          fontFamily: GQTypography.handwritten,
                          fontSize: 16,
                          color: GQColors.primaryDk,
                          height: 1.2,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // ── Mini mood-shape row ────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 10, 20, 0),
            child: _MiniMoodRow(days: data.days),
          ),
          // ── Encouraging message ────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 14, 20, 0),
            child: Text(
              encouragement,
              style: const TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 13.5,
                fontWeight: FontWeight.w600,
                color: GQColors.ink2,
                height: 1.5,
                fontStyle: FontStyle.italic,
              ),
            ),
          ),
          // ── Branded footer: logo + deep link ───────────────────────────
          const _BrandedFooter(),
        ],
      ),
    );
  }
}

/// Compact 7-day mood-shape row — same low→high palette as MoodShapeChart,
/// sized for the shareable card.
class _MiniMoodRow extends StatelessWidget {
  const _MiniMoodRow({required this.days});
  final List<DayMoodEntry> days;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 60,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: days.map((d) => _MiniBarSlot(entry: d)).toList(),
      ),
    );
  }
}

class _MiniBarSlot extends StatelessWidget {
  const _MiniBarSlot({required this.entry});
  final DayMoodEntry entry;

  @override
  Widget build(BuildContext context) {
    const maxH = 40.0;
    final idx = entry.moodIndex;
    final barH = idx == null ? 0.0 : (0.2 + idx * 0.2) * maxH;
    final color = idx == null
        ? Colors.transparent
        : GQColors.moodPalette[idx.clamp(0, 4)];

    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 2),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            if (idx == null)
              SizedBox(
                height: maxH * 0.28,
                child: Center(
                  child: Container(
                    width: double.infinity,
                    height: 1.5,
                    color: GQColors.hair,
                  ),
                ),
              )
            else
              Container(
                height: barH,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            const SizedBox(height: 4),
            Text(
              entry.label,
              style: TextStyle(
                fontFamily: GQTypography.bodyFamily,
                fontSize: 9,
                fontWeight:
                    entry.isToday ? FontWeight.w800 : FontWeight.w600,
                color:
                    entry.isToday ? GQColors.primaryDk : GQColors.ink2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Branded footer: GentleQuest logo watermark + the UTM deep link.
class _BrandedFooter extends StatelessWidget {
  const _BrandedFooter();

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 18),
      padding: const EdgeInsets.fromLTRB(20, 14, 20, 16),
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: GQColors.hair)),
      ),
      child: Row(
        children: [
          Image.asset(
            'assets/brand/icon_v1/gentlequest_web_192.png',
            width: 28,
            height: 28,
            filterQuality: FilterQuality.medium,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  'GentleQuest',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink,
                  ),
                ),
                Text(
                  'app.gentlequest.app',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w600,
                    color: GQColors.ink2,
                  ),
                ),
              ],
            ),
          ),
          const Text(
            '🌱',
            style: TextStyle(fontSize: 20),
          ),
        ],
      ),
    );
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

double _averageMoodIndex(List<DayMoodEntry> days) {
  final logged = days.where((d) => d.moodIndex != null).toList();
  if (logged.isEmpty) return 2.0; // mid fallback
  final sum = logged.fold<int>(0, (a, d) => a + d.moodIndex!);
  return sum / logged.length;
}

String _encouragement(WeeklyReviewData data, double avgIndex) {
  if (data.observationText != null && data.observationText!.isNotEmpty) {
    return data.observationText!;
  }
  if (data.logCount == 0) {
    return 'A quiet week. Rest counts as a week too.';
  }
  if (avgIndex >= 3) {
    return 'You showed up and the week lifted with you. Quiet wins count.';
  }
  if (avgIndex <= 1) {
    return 'A heavy week, and you stayed with it. That is the work.';
  }
  return 'You showed up ${data.logCount} times this week. Quiet wins count.';
}
