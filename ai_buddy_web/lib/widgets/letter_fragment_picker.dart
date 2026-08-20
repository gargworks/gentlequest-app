// letter_fragment_picker.dart — "Keep a line from this" flow.
//
// Shows 2-3 sentences from the weekly letter as tappable cards. The user
// picks one; that sentence becomes a shareable card (reuses the
// shareable_mood_card.dart infrastructure pattern — ScreenshotController +
// share_plus — but renders the chosen sentence instead of mood data).
//
// Card shows: the sentence in Fraunces, week range, companion at stamp size,
// "from a letter to myself". Privacy line: "Only this sentence leaves the
// phone. Never the letter." Buttons: "Share the card" (primary) + "Keep
// private" (secondary).

import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:screenshot/screenshot.dart';
import 'package:share_plus/share_plus.dart';

import '../theme/gq_tokens.dart';

/// Opens the letter fragment picker as a modal bottom sheet.
///
/// [sentences] is the 2-3 candidate sentences from the letter.
/// [weekLabel] is the week range shown on the shareable card.
void showLetterFragmentPicker(
  BuildContext context, {
  required List<String> sentences,
  required String weekLabel,
}) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => _LetterFragmentPickerSheet(
      sentences: sentences,
      weekLabel: weekLabel,
    ),
  );
}

class _LetterFragmentPickerSheet extends StatefulWidget {
  const _LetterFragmentPickerSheet({
    required this.sentences,
    required this.weekLabel,
  });

  final List<String> sentences;
  final String weekLabel;

  @override
  State<_LetterFragmentPickerSheet> createState() =>
      _LetterFragmentPickerSheetState();
}

class _LetterFragmentPickerSheetState
    extends State<_LetterFragmentPickerSheet> {
  int? _selected;

  @override
  Widget build(BuildContext context) {
    final mq = MediaQuery.of(context);
    return Container(
      decoration: const BoxDecoration(
        color: GQColors.softBg,
        borderRadius: BorderRadius.vertical(top: Radius.circular(GQRadii.sheet)),
      ),
      padding: EdgeInsets.only(bottom: mq.viewInsets.bottom),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _grabber(),
              const SizedBox(height: 8),
              _header(),
              const SizedBox(height: 14),
              if (_selected == null) ...[
                _sentenceList(),
              ] else ...[
                _ShareableSentenceCard(
                  sentence: widget.sentences[_selected!],
                  weekLabel: widget.weekLabel,
                ),
                const SizedBox(height: 16),
                _actionButtons(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _grabber() {
    return Container(
      width: 40,
      height: 4,
      decoration: BoxDecoration(
        color: GQColors.hair,
        borderRadius: BorderRadius.circular(999),
      ),
    );
  }

  Widget _header() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text(
          'KEEP A LINE FROM THIS',
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
    );
  }

  Widget _sentenceList() {
    return Column(
      children: [
        for (var i = 0; i < widget.sentences.length; i++) ...[
          _SentenceCard(
            sentence: widget.sentences[i],
            onTap: () => setState(() => _selected = i),
          ),
          if (i < widget.sentences.length - 1) const SizedBox(height: 10),
        ],
        const SizedBox(height: 14),
        const Text(
          'Only this sentence leaves the phone. Never the letter.',
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

  Widget _actionButtons() {
    return Column(
      children: [
        _PickerButton(
          label: 'Share the card',
          primary: true,
          onTap: () => _shareCard(context),
        ),
        const SizedBox(height: 10),
        _PickerButton(
          label: 'Keep private',
          primary: false,
          onTap: () => Navigator.of(context).pop(),
        ),
        const SizedBox(height: 12),
        const Text(
          'Only this sentence leaves the phone. Never the letter.',
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

  Future<void> _shareCard(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final controller = _ShareableSentenceCardController.of(context);
      if (controller == null) {
        messenger.showSnackBar(
          const SnackBar(content: Text('Could not capture the card.')),
        );
        return;
      }
      final Uint8List? png = await controller.capture();
      if (png == null) {
        messenger.showSnackBar(
          const SnackBar(content: Text('Could not capture the card.')),
        );
        return;
      }
      final Directory tmp = await getTemporaryDirectory();
      final String path =
          '${tmp.path}/gentlequest_letter_${DateTime.now().millisecondsSinceEpoch}.png';
      await File(path).writeAsBytes(png);
      await Share.shareXFiles(
        [XFile(path, mimeType: 'image/png')],
        text: 'from a letter to myself — ${widget.weekLabel}',
        subject: 'from a letter to myself',
      );
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('Sharing failed: $e')),
      );
    }
  }
}

// ─── Sentence selection card ─────────────────────────────────────────────────

class _SentenceCard extends StatelessWidget {
  const _SentenceCard({required this.sentence, required this.onTap});
  final String sentence;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(GQRadii.card),
          border: Border.all(color: GQColors.hair),
        ),
        child: Text(
          sentence,
          style: const TextStyle(
            fontFamily: GQTypography.journalSerif,
            fontSize: 15,
            height: 1.6,
            color: GQColors.ink,
          ),
        ),
      ),
    );
  }
}

// ─── Shareable sentence card (the PNG) ───────────────────────────────────────

/// Inherited widget so the parent sheet can capture the card via the
/// ScreenshotController embedded inside [_ShareableSentenceCard].
class _ShareableSentenceCardController extends InheritedWidget {
  const _ShareableSentenceCardController({
    required this.controller,
    required super.child,
  });

  final ScreenshotController controller;

  static ScreenshotController? of(BuildContext context) {
    final w = context
        .dependOnInheritedWidgetOfExactType<_ShareableSentenceCardController>();
    return w?.controller;
  }

  @override
  bool updateShouldNotify(_ShareableSentenceCardController oldWidget) =>
      controller != oldWidget.controller;
}

class _ShareableSentenceCard extends StatelessWidget {
  const _ShareableSentenceCard({
    required this.sentence,
    required this.weekLabel,
  });

  final String sentence;
  final String weekLabel;

  @override
  Widget build(BuildContext context) {
    final controller = ScreenshotController();
    return _ShareableSentenceCardController(
      controller: controller,
      child: Screenshot(
        controller: controller,
        child: Container(
          width: double.infinity,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFFF8F7FF),
                Color(0xFFFBF6F6),
              ],
            ),
            borderRadius: BorderRadius.circular(GQRadii.cardLg),
            border: Border.all(color: GQColors.hair),
          ),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'FROM A LETTER TO MYSELF',
                  style: TextStyle(
                    fontFamily: GQTypography.bodyFamily,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: GQColors.ink2,
                    letterSpacing: 1.4,
                  ),
                ),
                const SizedBox(height: 14),
                Text(
                  sentence,
                  style: const TextStyle(
                    fontFamily: GQTypography.journalSerif,
                    fontSize: 17,
                    height: 1.6,
                    color: GQColors.ink,
                  ),
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    // Companion at stamp size (small simplified form).
                    Text(
                      '🌱',
                      style: TextStyle(fontSize: 22, height: 1.0),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            weekLabel,
                            style: const TextStyle(
                              fontFamily: GQTypography.bodyFamily,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: GQColors.ink2,
                            ),
                          ),
                          const Text(
                            'GentleQuest',
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
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Picker buttons ──────────────────────────────────────────────────────────

class _PickerButton extends StatelessWidget {
  const _PickerButton({
    required this.label,
    required this.primary,
    required this.onTap,
  });

  final String label;
  final bool primary;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        constraints: const BoxConstraints(minHeight: 44),
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 12),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: primary ? GQColors.primary : Colors.white,
          borderRadius: BorderRadius.circular(GQRadii.button),
          border: primary ? null : Border.all(color: GQColors.hair),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: GQTypography.bodyFamily,
            fontSize: 13.5,
            fontWeight: FontWeight.w700,
            color: primary ? Colors.white : GQColors.ink2,
          ),
        ),
      ),
    );
  }
}
