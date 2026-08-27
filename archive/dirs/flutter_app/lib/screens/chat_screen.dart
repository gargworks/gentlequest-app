import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/iip_models.dart';
import '../services/api_service.dart';

class ChatScreen extends ConsumerStatefulWidget {
  final int teamId;
  final String teamName;

  const ChatScreen({Key? key, required this.teamId, required this.teamName}) : super(key: key);

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  
  // Local state
  InterviewSession? _session;
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
      final session = await ref.read(apiServiceProvider).startChatSession(widget.teamId);
      
      // Workaround: Frontend adds a local fake greeting if list is empty.
      final greeting = ChatMessage(
          sessionId: session.sessionId!,
          role: 'assistant',
          content: "Hi! I'm your AI Research Assistant. Tell me about the biggest challenge ${widget.teamName} is facing?",
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
      final aiMsg = await ref.read(apiServiceProvider).sendChatMessage(_session!.sessionId!, text);
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

  Future<void> _finalizeInterview() async {
    if (_session == null) return;
    
    setState(() => _isLoading = true);
    try {
      await ref.read(apiServiceProvider).finalizeChatSession(_session!.sessionId!);
      if (!mounted) return;
      Navigator.pop(context); // Go back to dashboard
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Interview finalized and analyzed!')));
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error finalizing: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Researcher Interview'),
        backgroundColor: Colors.indigo,
        actions: [
          IconButton(
            icon: const Icon(Icons.check_circle),
            tooltip: 'Finalize Interview',
            onPressed: _finalizeInterview,
          )
        ],
      ),
      body: Column(
        children: [
          if (_isLoading) 
            const LinearProgressIndicator(),
            
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
                       child: Text("AI is thinking...", style: TextStyle(fontStyle: FontStyle.italic, color: Colors.grey)),
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
                      color: isUser ? Colors.indigoAccent : Colors.grey[200],
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
                        hintText: 'Type your answer...',
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
                    backgroundColor: Colors.indigo,
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
