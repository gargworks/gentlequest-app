import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ai_buddy_web/screens/compliance_guard_screen.dart';

/// One-time welcome screen shown before compliance gate.
/// Shows Alex's personality and value props to reduce first-screen drop-off.
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  static const String _kSeenKey = 'has_seen_welcome_v1';

  /// Check if user has seen the welcome screen before.
  static Future<bool> hasBeenSeen() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kSeenKey) ?? false;
  }

  Future<void> _markSeen(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kSeenKey, true);
    if (context.mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const ComplianceGuardScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F6FF),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(flex: 2),

              // Avatar / illustration
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: const Color(0xFFE8E0FF),
                  borderRadius: BorderRadius.circular(50),
                ),
                child: const Center(
                  child: Text(
                    '\u{1F49C}', // purple heart
                    style: TextStyle(fontSize: 48),
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Heading
              const Text(
                'Meet Alex',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF2D1B69),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Your wellness companion',
                style: TextStyle(
                  fontSize: 16,
                  color: Color(0xFF6B5B95),
                ),
              ),
              const SizedBox(height: 40),

              // Value props
              _buildProp(
                icon: Icons.chat_bubble_outline,
                text: 'Someone to talk to, anytime',
              ),
              const SizedBox(height: 16),
              _buildProp(
                icon: Icons.lock_outline,
                text: 'Your conversations stay private',
              ),
              const SizedBox(height: 16),
              _buildProp(
                icon: Icons.favorite_border,
                text: 'No judgment, just support',
              ),

              const Spacer(flex: 3),

              // CTA
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: () => _markSeen(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF6B5B95),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(26),
                    ),
                    elevation: 0,
                  ),
                  child: const Text(
                    'Get Started',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProp({required IconData icon, required String text}) {
    return Row(
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: const Color(0xFFE8E0FF),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: const Color(0xFF6B5B95), size: 20),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 16,
              color: Color(0xFF2D1B69),
            ),
          ),
        ),
      ],
    );
  }
}
