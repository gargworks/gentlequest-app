import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/iip_models.dart';
import '../services/api_service.dart';

class ProjectChatScreen extends ConsumerStatefulWidget {
  final int teamId; // Changed from projectId
  final String teamName; // Changed from projectName to match Dashboard usage roughly, or just Display Name

  const ProjectChatScreen({Key? key, required this.teamId, required this.teamName}) : super(key: key);

  @override
  ConsumerState<ProjectChatScreen> createState() => _ProjectChatScreenState();
}

class _ProjectChatScreenState extends ConsumerState<ProjectChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  
  // Local state
  ProjectChatSession? _session; // Changed type
  List<ChatMessage> _messages = [];
  bool _isLoading = true;
  bool _isAiTyping = false;

  @override
  void initState() {
    super.initState();
    _startSession();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _startSession() async {
    try {
      final session = await ref.read(apiServiceProvider).startProjectChat(widget.teamId);
      
      final greeting = ChatMessage(
          sessionId: session.sessionId!,
          role: 'assistant',
          content: "Welcome to the Project War Room. I've analyzed all your research, personas, and plans. How can I help you execute '${widget.teamName}'?",
          timestamp: DateTime.now()
      );

      if (mounted) {
        setState(() {
          _session = session;
          _messages = [greeting];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error starting chat: $e')));
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    
    _controller.clear();
    if (_session == null) return;

    final userMsg = ChatMessage(
      sessionId: _session!.sessionId!,
      role: 'user',
      content: text,
      timestamp: DateTime.now()
    );
    
    setState(() {
      _messages.add(userMsg);
      _isAiTyping = true;
    });
    
    _scrollToBottom();

    try {
      // Use projectId from session
      final aiMsg = await ref.read(apiServiceProvider).sendProjectChatMessage(_session!.projectId, _session!.sessionId!, text);
      if (mounted) {
        setState(() {
          _messages.add(aiMsg);
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to send message')));
      }
    } finally {
      if (mounted) {
        setState(() {
          _isAiTyping = false;
        });
        _scrollToBottom();
      }
    }
  }
  
  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Project Intelligence: ${widget.teamName}'),
        backgroundColor: Colors.teal, // Distinct from Interview Chat
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Clear Chat',
            onPressed: () {
                // simple reload for MVP
                setState(() => _isLoading = true);
                _startSession();
            },
          )
        ],
      ),
      body: Column(
        children: [
          if (_isLoading) 
            const LinearProgressIndicator(color: Colors.tealAccent),
            
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + (_isAiTyping ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == _messages.length && _isAiTyping) {
                   return const Align(
                     alignment: Alignment.centerLeft,
                     child: Padding(
                       padding: EdgeInsets.all(8.0),
                       child: Text("Consulting project files...", style: TextStyle(fontStyle: FontStyle.italic, color: Colors.grey)),
                     ),
                   );
                }
                
                final msg = _messages[index];
                final isUser = msg.role == 'user';
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.all(12),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.teal : Colors.grey[200],
                      borderRadius: BorderRadius.circular(12).copyWith(
                        bottomRight: isUser ? Radius.zero : const Radius.circular(12),
                        bottomLeft: isUser ? const Radius.circular(12) : Radius.zero,
                      ),
                    ),
                    child: Text(
                      msg.content,
                      style: TextStyle(color: isUser ? Colors.white : Colors.black87),
                    ),
                  ),
                );
              },
            ),
          ),
          
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4, offset: const Offset(0, -2))],
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: const InputDecoration(
                        hintText: 'Ask about roadmap, tasks, or interviews...',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                      enabled: !_isLoading,
                    ),
                  ),
                  const SizedBox(width: 8),
                  FloatingActionButton(
                    mini: true,
                    onPressed: _isLoading ? null : _sendMessage,
                    backgroundColor: Colors.teal,
                    child: const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
