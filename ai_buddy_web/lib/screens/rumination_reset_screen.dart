import 'dart:async';

import 'package:flutter/material.dart';

import '../models/message.dart';
import '../services/api_service.dart';
import '../services/crisis_keyword_detector.dart';
import '../theme/gq_tokens.dart';
import '../widgets/crisis_resources.dart';
import '../widgets/gq/gq.dart';

enum LoopResetResolution { act, defer, insufficient }

typedef LoopResetReporter = Future<void> Function(
  String outcome,
  int timeSpentSeconds,
);
typedef LoopResetCrisisHandler = Future<void> Function(
  BuildContext context,
  RiskLevel risk,
);

class RuminationResetScreen extends StatefulWidget {
  const RuminationResetScreen({
    super.key,
    this.reportOutcome,
    this.showCrisis,
  });

  final LoopResetReporter? reportOutcome;
  final LoopResetCrisisHandler? showCrisis;

  static Future<void> show(BuildContext context) {
    return Navigator.of(context).push<void>(
      MaterialPageRoute(builder: (_) => const RuminationResetScreen()),
    );
  }

  @override
  State<RuminationResetScreen> createState() => _RuminationResetScreenState();
}

class _RuminationResetScreenState extends State<RuminationResetScreen> {
  final _eventController = TextEditingController();
  final _controlController = TextEditingController();
  final _outcomeController = TextEditingController();
  final _resolutionController = TextEditingController();

  int _step = 0;
  double? _intensity;
  double? _afterIntensity;
  LoopResetResolution? _resolution;
  DateTime? _startedAt;
  bool _finished = false;

  @override
  void dispose() {
    _eventController.dispose();
    _controlController.dispose();
    _outcomeController.dispose();
    _resolutionController.dispose();
    super.dispose();
  }

  Future<void> _report(String outcome) {
    final seconds = _startedAt == null
        ? 0
        : DateTime.now().difference(_startedAt!).inSeconds;
    final reporter = widget.reportOutcome;
    if (reporter != null) return reporter(outcome, seconds);
    return ApiService().reportExerciseOutcome(
      exerciseType: 'rumination_reset',
      outcome: outcome,
      timeSpentSeconds: seconds,
    );
  }

  void _start() {
    _startedAt = DateTime.now();
    unawaited(_report('started'));
    setState(() => _step = 1);
  }

  String get _allConcreteText => [
        _eventController.text,
        _controlController.text,
        _outcomeController.text,
      ].join(' ');

  Future<bool> _preemptForCrisis(String text) async {
    final tier1 = CrisisKeywordDetector.matchTier1(text);
    final tier2 = !tier1 && CrisisKeywordDetector.match(text);
    if (!tier1 && !tier2) return false;

    if (!_finished) {
      _finished = true;
      unawaited(_report('skipped'));
    }
    _clearText();
    if (!mounted) return true;

    final risk = tier1 ? RiskLevel.crisis : RiskLevel.high;
    final handler = widget.showCrisis;
    if (handler != null) {
      await handler(context, risk);
    } else {
      await showCrisisInterventionSheet(
        context,
        risk: risk,
        source: 'rumination_reset',
      );
    }
    if (mounted) Navigator.of(context).maybePop();
    return true;
  }

  Future<void> _continueFromConcrete() async {
    if (_eventController.text.trim().isEmpty ||
        _controlController.text.trim().isEmpty ||
        _outcomeController.text.trim().isEmpty) {
      GQBanner.show(
        context,
        message:
            'Keep each answer short, but fill in all three before moving on.',
        category: GQBannerCategory.info,
      );
      return;
    }
    if (await _preemptForCrisis(_allConcreteText)) return;
    if (mounted) setState(() => _step = 2);
  }

  void _selectResolution(LoopResetResolution resolution) {
    setState(() {
      _resolution = resolution;
      _resolutionController.clear();
    });
  }

  Future<void> _continueFromResolution() async {
    if (_resolution == null || _resolutionController.text.trim().isEmpty) {
      GQBanner.show(
        context,
        message: 'Choose one exit and make it specific before moving on.',
        category: GQBannerCategory.info,
      );
      return;
    }
    if (await _preemptForCrisis(_resolutionController.text)) return;
    if (mounted) setState(() => _step = 3);
  }

  void _complete() {
    if (_finished) return;
    _finished = true;
    unawaited(_report('completed'));
    _clearText();
    if (mounted) Navigator.of(context).maybePop();
  }

  void _skip() {
    if (!_finished) {
      _finished = true;
      unawaited(_report('skipped'));
    }
    _clearText();
    if (mounted) Navigator.of(context).maybePop();
  }

  void _handlePop(bool didPop, Object? result) {
    if (!didPop || _finished) return;
    _finished = true;
    unawaited(_report('skipped'));
    _clearText();
  }

  void _clearText() {
    _eventController.clear();
    _controlController.clear();
    _outcomeController.clear();
    _resolutionController.clear();
  }

  String get _resolutionPrompt {
    return switch (_resolution) {
      LoopResetResolution.act => 'What can you do in five minutes or less?',
      LoopResetResolution.defer =>
        'What exact event tells you to revisit this?',
      LoopResetResolution.insufficient => 'What specific fact is missing?',
      null => '',
    };
  }

  String get _resolutionLabel {
    return switch (_resolution) {
      LoopResetResolution.act => 'Do one small thing',
      LoopResetResolution.defer => 'Revisit on a real trigger',
      LoopResetResolution.insufficient => 'Name what is missing',
      null => '',
    };
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      onPopInvokedWithResult: _handlePop,
      child: Scaffold(
        backgroundColor: GQColors.softBg,
        appBar: GQHeader(
          title: 'Loop reset',
          actions: [
            GQButton(
              label: 'Close',
              variant: GQButtonVariant.text,
              fullWidth: false,
              onPressed: _skip,
            ),
          ],
        ),
        body: SafeArea(
          child: AnimatedSwitcher(
            duration: GQDurations.fade,
            child: switch (_step) {
              0 => _buildNotice(),
              1 => _buildConcrete(),
              2 => _buildResolution(),
              _ => _buildExit(),
            },
          ),
        ),
      ),
    );
  }

  Widget _page({
    required Key key,
    required String eyebrow,
    required String title,
    required String body,
    required List<Widget> children,
  }) {
    return SingleChildScrollView(
      key: key,
      padding: const EdgeInsets.fromLTRB(20, 28, 20, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(eyebrow,
              style: GQTypography.micro.copyWith(color: GQColors.ink2)),
          const SizedBox(height: GQSpacing.sm),
          Text(title, style: GQTypography.title.copyWith(color: GQColors.ink)),
          const SizedBox(height: GQSpacing.sm),
          Text(body, style: GQTypography.body.copyWith(color: GQColors.ink2)),
          const SizedBox(height: GQSpacing.xl),
          ...children,
        ],
      ),
    );
  }

  Widget _buildNotice() {
    return _page(
      key: const ValueKey('notice'),
      eyebrow: 'TWO-MINUTE QUICK WIN',
      title: 'Your mind is looping.',
      body:
          'We will not solve your whole life here. We will get concrete, choose one exit, and stop.',
      children: [
        if (_intensity == null)
          GQButton(
            label: 'Add an optional intensity rating',
            variant: GQButtonVariant.ghost,
            onPressed: () => setState(() => _intensity = 5),
          )
        else ...[
          Text(
            'Intensity right now: ${_intensity!.round()} / 10',
            style: GQTypography.body.copyWith(color: GQColors.ink),
          ),
          Slider(
            value: _intensity!,
            min: 0,
            max: 10,
            divisions: 10,
            activeColor: GQColors.primary,
            onChanged: (value) => setState(() => _intensity = value),
          ),
        ],
        const SizedBox(height: GQSpacing.lg),
        GQButton(label: 'Start the reset', onPressed: _start),
      ],
    );
  }

  Widget _buildConcrete() {
    return _page(
      key: const ValueKey('concrete'),
      eyebrow: 'STEP 1 OF 2 · GET CONCRETE',
      title: 'Only what a camera could record.',
      body:
          'Short facts interrupt the abstract “why” loop. One or two sentences per box is enough.',
      children: [
        _field(
          key: const ValueKey('event_field'),
          controller: _eventController,
          label: 'What happened — where and when?',
          maxLength: 160,
        ),
        const SizedBox(height: GQSpacing.md),
        _field(
          key: const ValueKey('control_field'),
          controller: _controlController,
          label: 'What is controllable in the next few minutes?',
          maxLength: 120,
        ),
        const SizedBox(height: GQSpacing.md),
        _field(
          key: const ValueKey('outcome_field'),
          controller: _outcomeController,
          label: 'What specific outcome matters now?',
          maxLength: 120,
        ),
        const SizedBox(height: GQSpacing.lg),
        GQButton(label: 'Choose one exit', onPressed: _continueFromConcrete),
      ],
    );
  }

  Widget _buildResolution() {
    return _page(
      key: const ValueKey('resolution'),
      eyebrow: 'STEP 2 OF 2 · CHOOSE',
      title: 'One exit. Not another analysis.',
      body: 'Pick the option that returns you to life outside this screen.',
      children: [
        _resolutionCard(
          LoopResetResolution.act,
          Icons.directions_walk_rounded,
          'Do one small thing',
          'A values-consistent action taking five minutes or less.',
        ),
        const SizedBox(height: GQSpacing.sm),
        _resolutionCard(
          LoopResetResolution.defer,
          Icons.event_available_rounded,
          'Revisit on a real trigger',
          'Use an event, person, or appointment — not “later.”',
        ),
        const SizedBox(height: GQSpacing.sm),
        _resolutionCard(
          LoopResetResolution.insufficient,
          Icons.help_outline_rounded,
          'Name what is missing',
          'Stop until the missing fact actually exists.',
        ),
        if (_resolution != null) ...[
          const SizedBox(height: GQSpacing.lg),
          _field(
            key: const ValueKey('resolution_field'),
            controller: _resolutionController,
            label: _resolutionPrompt,
            maxLength: 140,
          ),
          const SizedBox(height: GQSpacing.lg),
          GQButton(label: 'Use this exit', onPressed: _continueFromResolution),
        ],
      ],
    );
  }

  Widget _buildExit() {
    return _page(
      key: const ValueKey('exit'),
      eyebrow: 'RESET COMPLETE',
      title: _resolutionLabel,
      body: _resolutionController.text.trim(),
      children: [
        GQCard(
          child: Text(
            'You do not need to feel completely better before you move. The reset worked when it returned you to a concrete next step.',
            style: GQTypography.body.copyWith(color: GQColors.ink2),
          ),
        ),
        const SizedBox(height: GQSpacing.lg),
        if (_afterIntensity == null)
          GQButton(
            label: 'Add one optional after-rating',
            variant: GQButtonVariant.ghost,
            onPressed: () => setState(() => _afterIntensity = _intensity ?? 5),
          )
        else ...[
          Text(
            'Intensity now: ${_afterIntensity!.round()} / 10',
            style: GQTypography.body.copyWith(color: GQColors.ink),
          ),
          Slider(
            value: _afterIntensity!,
            min: 0,
            max: 10,
            divisions: 10,
            activeColor: GQColors.primary,
            onChanged: (value) => setState(() => _afterIntensity = value),
          ),
        ],
        const SizedBox(height: GQSpacing.lg),
        GQButton(label: 'Leave and do it', onPressed: _complete),
      ],
    );
  }

  Widget _field({
    required Key key,
    required TextEditingController controller,
    required String label,
    required int maxLength,
  }) {
    return TextField(
      key: key,
      controller: controller,
      minLines: 2,
      maxLines: 3,
      maxLength: maxLength,
      style: GQTypography.body.copyWith(color: GQColors.ink),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: GQTypography.body.copyWith(color: GQColors.ink2),
        filled: true,
        fillColor: GQColors.surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(GQRadii.card),
          borderSide: const BorderSide(color: GQColors.hair),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(GQRadii.card),
          borderSide: const BorderSide(color: GQColors.hair),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(GQRadii.card),
          borderSide: const BorderSide(color: GQColors.primary, width: 2),
        ),
      ),
    );
  }

  Widget _resolutionCard(
    LoopResetResolution resolution,
    IconData icon,
    String title,
    String body,
  ) {
    final selected = _resolution == resolution;
    return GQCard(
      onTap: () => _selectResolution(resolution),
      color: selected ? GQColors.primarySoft : GQColors.surface,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: GQColors.primary, size: 24),
          const SizedBox(width: GQSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: GQTypography.body.copyWith(
                        color: GQColors.ink, fontWeight: FontWeight.w700)),
                const SizedBox(height: GQSpacing.xs),
                Text(body,
                    style: GQTypography.caption.copyWith(color: GQColors.ink2)),
              ],
            ),
          ),
          if (selected)
            const Icon(Icons.check_circle_rounded, color: GQColors.primary),
        ],
      ),
    );
  }
}
