import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../services/firebase_service.dart';

class LeopardAccessGate extends StatefulWidget {
  final VoidCallback onGranted;

  const LeopardAccessGate({super.key, required this.onGranted});

  @override
  State<LeopardAccessGate> createState() => _LeopardAccessGateState();
}

class _LeopardAccessGateState extends State<LeopardAccessGate> {
  final TextEditingController _controller = TextEditingController();
  final FirebaseService _firebase = FirebaseService();
  String _statusMessage = "WAITING FOR INPUT...";
  bool _isValidating = false;
  bool _hasError = false;

  // Hardcoded Protocol Codes for MVP
  final List<String> _validCodes = [
    'LEOPARD_2026',
    'ALPHA_STRIKE',
    'OP_LEOPARD_SEAL',
  ];

  Future<void> _validateCode() async {
    final code = _controller.text.trim().toUpperCase();
    if (code.isEmpty) return;

    setState(() {
      _isValidating = true;
      _statusMessage = "VALIDATING CREDENTIALS...";
      _hasError = false;
    });

    // Log the attempt
    _firebase.logEvent('leopard_access_attempt', {'code_entered': code});

    // Artificial delay for "Terminal" vibe
    await Future.delayed(const Duration(milliseconds: 1500));

    if (_validCodes.contains(code)) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('leopard_access_granted', true);

      // Log the success
      _firebase.logEvent('leopard_access_granted', {'code': code});

      if (mounted) {
        setState(() {
          _isValidating = false;
          _statusMessage = "ACCESS GRANTED. INITIALIZING...";
        });

        await Future.delayed(const Duration(milliseconds: 800));
        widget.onGranted();
      }
    } else {
      HapticFeedback.heavyImpact();
      if (mounted) {
        setState(() {
          _isValidating = false;
          _statusMessage = "PROTOCOL DENIED. INVALID CODE.";
          _hasError = true;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 600),
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // HEADER
              const Text(
                "GENTLEQUEST // TERMINAL",
                style: TextStyle(
                  color: Color(0xFF667EEA),
                  fontFamily: 'Courier',
                  fontWeight: FontWeight.bold,
                  fontSize: 24,
                  letterSpacing: 2.0,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                height: 2,
                color: const Color(0xFF667EEA).withOpacity(0.3),
              ),
              const SizedBox(height: 48),

              // ANALYTICS TEXT
              const Text(
                "ENVIRONMENT: PRODUCTION v1.2.1\nSECURITY: ENCRYPTED_TUNNEL\nSTATUS: LOCKED",
                style: TextStyle(
                  color: Colors.white30,
                  fontFamily: 'Courier',
                  fontSize: 12,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 32),

              // INPUT FIELD
              const Text(
                "ENTER PROTOCOL INVITE CODE:",
                style: TextStyle(
                  color: Colors.white70,
                  fontFamily: 'Courier',
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _controller,
                style: const TextStyle(
                  color: Colors.white,
                  fontFamily: 'Courier',
                  fontSize: 18,
                  letterSpacing: 4.0,
                ),
                decoration: InputDecoration(
                  filled: true,
                  fillColor: Colors.white.withOpacity(0.05),
                  border: const OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.white10),
                  ),
                  enabledBorder: const OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.white10),
                  ),
                  focusedBorder: const OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF667EEA)),
                  ),
                  hintText: "********",
                  hintStyle: TextStyle(color: Colors.white.withOpacity(0.1)),
                ),
                onSubmitted: (_) => _validateCode(),
              ),
              const SizedBox(height: 16),

              // STATUS LINE
              Text(
                "> $_statusMessage",
                style: TextStyle(
                  color: _hasError ? Colors.redAccent : const Color(0xFF667EEA),
                  fontFamily: 'Courier',
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 48),

              // EXECUTE BUTTON
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isValidating ? null : _validateCode,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF667EEA),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  child: _isValidating
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : const Text(
                          "EXECUTE PROTOCOL",
                          style: TextStyle(
                            fontFamily: 'Courier',
                            fontWeight: FontWeight.bold,
                            letterSpacing: 2.0,
                          ),
                        ),
                ),
              ),

              const SizedBox(height: 24),
              const Center(
                child: Text(
                  "UNAUTHORIZED ACCESS PROHIBITED",
                  style: TextStyle(
                    color: Colors.white10,
                    fontFamily: 'Courier',
                    fontSize: 10,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
