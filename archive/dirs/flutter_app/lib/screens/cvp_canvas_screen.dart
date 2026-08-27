import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/iip_models.dart';
import '../services/api_service.dart';

class CVPCanvasScreen extends ConsumerStatefulWidget {
  final int teamId;
  final String teamName;

  const CVPCanvasScreen({super.key, required this.teamId, required this.teamName});

  @override
  ConsumerState<CVPCanvasScreen> createState() => _CVPCanvasScreenState();
}

class _CVPCanvasScreenState extends ConsumerState<CVPCanvasScreen> {
  CVPCanvas? _canvas;
  bool _isLoading = true;
  String _loadingMessage = "Loading...";
  Timer? _progressTimer;

  static const List<String> _progressMessages = [
    "Analyzing Interview Notes...",
    "Extracting Key Insights...",
    "Synthesizing Value Propositions...",
    "Defining Customer Pains & Gains...",
    "Drafting Competitive Positioning...",
    "Finalizing Canvas...",
  ];

  @override
  void initState() {
    super.initState();
    _fetchCanvas();
  }

  @override
  void dispose() {
    _progressTimer?.cancel();
    super.dispose();
  }

  void _startProgressSimulation() {
    int index = 0;
    setState(() => _loadingMessage = _progressMessages[0]);
    _progressTimer = Timer.periodic(const Duration(seconds: 4), (timer) {
      if (!mounted) return;
      setState(() {
        index = (index + 1) % _progressMessages.length;
        _loadingMessage = _progressMessages[index];
      });
    });
  }

  void _stopProgressSimulation() {
    _progressTimer?.cancel();
  }

  Future<void> _fetchCanvas() async {
    setState(() {
      _isLoading = true;
      _loadingMessage = "Loading Canvas...";
    });
    try {
      final canvas = await ApiService().getCVPCanvas(widget.teamId);
      if (!mounted) return;
      setState(() {
        _canvas = canvas;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
      });
      // Silent error on fetch; allow empty state
    }
  }

  Future<void> _generateCanvas() async {
    setState(() {
      _isLoading = true;
    });
    _startProgressSimulation();

    try {
      final canvas = await ApiService().generateCVPCanvas(widget.teamId);
      if (!mounted) return;
      
      _stopProgressSimulation();
      setState(() {
        _canvas = canvas;
        _isLoading = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('CVP Canvas Generated Successfully! 🚀'),
          backgroundColor: Colors.green,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _stopProgressSimulation();
      setState(() => _isLoading = false);
      
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text("Generation Failed"),
          content: Text("The AI took too long or encountered an error.\n\nError: $e"),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Close"),
            ),
            FilledButton(
              onPressed: () {
                Navigator.pop(context);
                _generateCanvas(); // Retry
              },
              child: const Text("Retry"),
            ),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.teamName}: CVP Canvas'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          if (_canvas != null && !_isLoading)
            IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: "Regenerate",
              onPressed: _generateCanvas,
            ),
        ],
      ),
      body: Stack(
        children: [
          _canvas == null && !_isLoading
              ? _buildEmptyState()
              : _buildCanvas(),
          if (_isLoading) _buildLoadingOverlay(),
        ],
      ),
      floatingActionButton: _canvas != null && !_isLoading
          ? FloatingActionButton.extended(
              onPressed: _generateCanvas,
              icon: const Icon(Icons.auto_awesome),
              label: const Text('Regenerate AI'),
            )
          : null,
    );
  }

  Widget _buildLoadingOverlay() {
    return Container(
      color: Colors.black.withOpacity(0.7),
      width: double.infinity,
      height: double.infinity,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(color: Colors.white),
            const SizedBox(height: 24),
            Text(
              _loadingMessage,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            const Text(
              "This usually takes about 30-45 seconds.",
              style: TextStyle(
                color: Colors.white70,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.psychology_alt, size: 80, color: Theme.of(context).primaryColor.withOpacity(0.5)),
            const SizedBox(height: 24),
            const Text(
              'No CVP Canvas Generated',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            const Text(
              'Let the AI analyze your Personas to generate a Value Proposition Canvas automatically.',
              style: TextStyle(fontSize: 16, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            FilledButton.icon(
              onPressed: _generateCanvas,
              icon: const Icon(Icons.auto_awesome),
              label: const Text("Generate with AI"),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                textStyle: const TextStyle(fontSize: 18),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCanvas() {
    if (_canvas == null) return const SizedBox.shrink();
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildHeaderSection('Core Proposition', _canvas!.valueProposition, Colors.deepPurple),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(child: _buildSection('Target Segment', [_canvas!.customerSegment], Colors.blue)),
              const SizedBox(width: 16),
              Expanded(child: _buildSection('Jobs To Be Done', _canvas!.jobsToBeDone is List ? (_canvas!.jobsToBeDone as List).map((e)=>e.toString()).toList() : [_canvas!.jobsToBeDone.toString()], Colors.indigo)),
            ],
          ),
          const SizedBox(height: 16),
          _buildGridSection('The Customer Profile', [
            _buildSection('Pains', _canvas!.pains, Colors.red),
            _buildSection('Gains', _canvas!.gains, Colors.green),
          ]),
          const SizedBox(height: 16),
          _buildGridSection('Our Solution Fit', [
            _buildSection('Pain Relievers', _canvas!.painRelievers, Colors.orange),
            _buildSection('Gain Creators', _canvas!.gainCreators, Colors.teal),
          ]),
          const SizedBox(height: 16),
          _buildHeaderSection('Competitive Edge', _canvas!.competitivePositioning, Colors.blueGrey),
          const SizedBox(height: 80), // FAB Space
        ],
      ),
    );
  }

  Widget _buildHeaderSection(String title, String content, Color color) {
    return Card(
      elevation: 4,
      color: color.withOpacity(0.05),
      shape: RoundedRectangleBorder(
        side: BorderSide(color: color, width: 2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text(title.toUpperCase(), style: TextStyle(fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 8),
            Text(content, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18, fontStyle: FontStyle.italic)),
          ],
        ),
      ),
    );
  }

  Widget _buildGridSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
          child: Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        ),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: children.map((w) => Expanded(child: Padding(padding: const EdgeInsets.symmetric(horizontal: 4), child: w))).toList(),
        ),
      ],
    );
  }

  Widget _buildSection(String title, List<String> items, Color color) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(fontWeight: FontWeight.bold, color: color)),
            const Divider(),
            ...items.map((item) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('• ', style: TextStyle(fontWeight: FontWeight.bold)),
                  Expanded(child: Text(item)),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }
}
