import 'package:flutter/material.dart';

import '../../theme/gq_tokens.dart';
import '../../widgets/gq/gq.dart';

/// Design Authority WO-4 acceptance criterion: "component gallery screen
/// (debug route) showing all states; no screen code imports raw Material
/// equivalents after per-screen sweeps begin."
///
/// Dev-only. Not linked from any in-app navigation — reach it by pushing
/// `/debug/gq-gallery` (e.g. from a debugger or a temporary button while
/// working on this file). Shows every GQ widget in every documented state
/// so a change to gq_tokens.dart or a gq_*.dart file is checkable at a
/// glance, without hunting through swept screens for an example.
class GQComponentGalleryScreen extends StatefulWidget {
  const GQComponentGalleryScreen({super.key});

  @override
  State<GQComponentGalleryScreen> createState() => _GQComponentGalleryScreenState();
}

class _GQComponentGalleryScreenState extends State<GQComponentGalleryScreen> {
  bool _chipSelected = false;
  bool _cardSelected = false;
  String? _lastBannerCategory;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GQColors.bg,
      appBar: GQHeader(title: 'GQ Component Gallery'),
      body: ListView(
        padding: const EdgeInsets.all(GQSpacing.lg),
        children: [
          _SectionLabel('GQButton — variants'),
          Wrap(
            spacing: GQSpacing.sm,
            runSpacing: GQSpacing.sm,
            children: [
              GQButton(label: 'Primary', onPressed: () {}, variant: GQButtonVariant.primary, fullWidth: false),
              GQButton(label: 'Crisis', onPressed: () {}, variant: GQButtonVariant.crisis, fullWidth: false),
              GQButton(label: 'Ghost', onPressed: () {}, variant: GQButtonVariant.ghost, fullWidth: false),
              GQButton(label: 'Text', onPressed: () {}, variant: GQButtonVariant.text, fullWidth: false),
              const GQButton(label: 'Disabled', onPressed: null, fullWidth: false),
              GQButton(label: 'Loading', onPressed: () {}, loading: true, fullWidth: false),
            ],
          ),
          _SectionLabel('GQButton — sizes'),
          Wrap(
            spacing: GQSpacing.sm,
            runSpacing: GQSpacing.sm,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              GQButton(label: 'Small', onPressed: () {}, size: GQButtonSize.small, fullWidth: false),
              GQButton(label: 'Medium', onPressed: () {}, size: GQButtonSize.medium, fullWidth: false),
              GQButton(label: 'Large', onPressed: () {}, size: GQButtonSize.large, fullWidth: false),
            ],
          ),
          _SectionLabel('GQCard — plain / large / selectable'),
          Row(
            children: [
              Expanded(
                child: GQCard(
                  onTap: () {},
                  child: const SizedBox(height: 64, child: Center(child: Text('Plain'))),
                ),
              ),
              const SizedBox(width: GQSpacing.md),
              Expanded(
                child: GQCard(
                  large: true,
                  isSelectable: true,
                  selected: _cardSelected,
                  onTap: () => setState(() => _cardSelected = !_cardSelected),
                  child: const SizedBox(height: 64, child: Center(child: Text('Selectable'))),
                ),
              ),
            ],
          ),
          _SectionLabel('GQChip — unselected / selected / with emoji'),
          Wrap(
            spacing: GQSpacing.sm,
            children: [
              GQChip(label: 'Unselected', selected: false, onSelected: (_) {}),
              GQChip(
                label: 'Toggle me',
                selected: _chipSelected,
                onSelected: (v) => setState(() => _chipSelected = v),
              ),
              GQChip(label: 'With emoji', selected: true, emoji: '🌤️', onSelected: (_) {}),
            ],
          ),
          _SectionLabel('GQEmptyState'),
          GQCard(
            child: GQEmptyState(
              illustration: const Icon(Icons.eco_outlined, size: 48, color: GQColors.primaryDk),
              line: 'No entries yet — your first one is one tap away.',
              actionLabel: 'Add an entry',
              onAction: () {},
            ),
          ),
          _SectionLabel('GQBanner — inline, all categories'),
          const GQBanner(message: 'Info: a neutral status update.'),
          const SizedBox(height: GQSpacing.sm),
          const GQBanner(message: 'Warm: a gentle, encouraging note.', category: GQBannerCategory.warm),
          const SizedBox(height: GQSpacing.sm),
          const GQBanner(message: "Amber: you're offline — changes will sync later.", category: GQBannerCategory.amber),
          const SizedBox(height: GQSpacing.sm),
          GQBanner(
            message: 'Danger: please answer all questions before submitting.',
            category: GQBannerCategory.danger,
            onDismiss: () {},
          ),
          _SectionLabel('GQBanner.show — overlay (SnackBar replacement)'),
          Wrap(
            spacing: GQSpacing.sm,
            children: [
              for (final c in GQBannerCategory.values)
                GQButton(
                  label: c.name,
                  fullWidth: false,
                  variant: GQButtonVariant.ghost,
                  onPressed: () {
                    setState(() => _lastBannerCategory = c.name);
                    GQBanner.show(context, message: 'Overlay banner: ${c.name}', category: c);
                  },
                ),
            ],
          ),
          if (_lastBannerCategory != null)
            Padding(
              padding: const EdgeInsets.only(top: GQSpacing.xs),
              child: Text('Last fired: $_lastBannerCategory', style: GQTypography.micro.copyWith(color: GQColors.ink3)),
            ),
          _SectionLabel('GQSheet'),
          GQButton(
            label: 'Open sheet',
            fullWidth: false,
            variant: GQButtonVariant.ghost,
            onPressed: () => GQSheet.show(
              context,
              title: 'Example sheet',
              content: const Text('Sheet content goes here — keyboard-aware padding, 320ms slide-in.'),
            ),
          ),
          const SizedBox(height: GQSpacing.xxxl),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: GQSpacing.xl, bottom: GQSpacing.sm),
      child: Text(text, style: GQTypography.micro.copyWith(color: GQColors.ink3)),
    );
  }
}
