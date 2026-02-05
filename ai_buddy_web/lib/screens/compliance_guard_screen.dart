import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:ai_buddy_web/services/compliance_service.dart';
import 'package:geolocator/geolocator.dart'; // For Permission Enums
import 'package:url_launcher/url_launcher.dart'; // Added for Data Export & App Store links

class ComplianceGuardScreen extends StatefulWidget {
  const ComplianceGuardScreen({super.key});

  @override
  State<ComplianceGuardScreen> createState() => _ComplianceGuardScreenState();
}

class _ComplianceGuardScreenState extends State<ComplianceGuardScreen> {
  final ComplianceService _complianceService = ComplianceService();
  ComplianceStatus _status = ComplianceStatus.loading;
  String? _errorMessage;
  bool _isLoadingAction = false;

  @override
  void initState() {
    super.initState();
    _checkStatus();
  }

  Future<void> _checkStatus() async {
    setState(() => _isLoadingAction = true);
    final status = await _complianceService.checkCompliance();
    if (!mounted) return;

    if (status == ComplianceStatus.allowed) {
      // Navigate to Home/Main
      Navigator.of(context).pushReplacementNamed('/main');
    } else {
      setState(() {
        _status = status;
        _isLoadingAction = false;
      });
    }
  }

  Future<void> _handleAgeVerification(bool isOver18) async {
    if (!isOver18) {
      setState(() {
        _status = ComplianceStatus.blockedAge;
      });
      return;
    }

    await _complianceService.setAgeVerified(true);
    _checkStatus();
  }

  Future<void> _requestLocation() async {
    setState(() => _isLoadingAction = true);
    await _complianceService.requestLocationPermission();
    // After requesting, check again to trigger the full logic (get pos, reverse geocode)
    _checkStatus();
  }

  Future<void> _launchEmail() async {
    final Uri emailLaunchUri = Uri(
      scheme: 'mailto',
      path: 'privacy@gentlequest.app',
      query: _encodeQueryParameters(<String, String>{
        'subject': 'Data Export Request (Blocked Account)',
        'body': 'I am requesting a copy of my data under GDPR/CCPA rights.'
      }),
    );
    if (!await launchUrl(emailLaunchUri)) {
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(content: Text('Could not launch email client')),
         );
      }
    }
  }

  String? _encodeQueryParameters(Map<String, String> params) {
    return params.entries
        .map((e) => '${Uri.encodeComponent(e.key)}=${Uri.encodeComponent(e.value)}')
        .join('&');
  }

  @override
  Widget build(BuildContext context) {
    if (_status == ComplianceStatus.loading || _isLoadingAction) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    switch (_status) {
      case ComplianceStatus.ageVerificationRequired:
        return _buildAgeGate();
      case ComplianceStatus.locationPermissionRequired:
      case ComplianceStatus.locationServicesDisabled:
        return _buildLocationGate();
      case ComplianceStatus.conversionRequired:
        return _buildConversionScreen();
      case ComplianceStatus.blockedAge:
        return _buildBlockedScreen(
          "Age Requirement",
          "GentleQuest is designed for adults (18+). We cannot provide services to minors at this time due to regulatory restrictions.",
        );
      case ComplianceStatus.blockedRegion:
        return _buildBlockedScreen(
          "Region Unavailable",
          "Due to strict local regulations regarding AI implementation (e.g., Illinois WOPR Act, Utah HB 452, EU AI Act), GentleQuest is not available in your jurisdiction.",
        );
      case ComplianceStatus.error:
        return _buildErrorScreen();
      default:
        return const Scaffold(body: SizedBox()); // Should have navigated
    }
  }

  Widget _buildAgeGate() {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.verified_user_outlined, size: 80, color: Color(0xFF667EEA)),
            const SizedBox(height: 24),
            Text(
              "Verify Your Age",
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Text(
              "GentleQuest uses advanced AI. To comply with safety regulations, you must be 18 years or older to use this application.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.black87),
            ),
            const SizedBox(height: 48),
            ElevatedButton(
              onPressed: () => _handleAgeVerification(true),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF667EEA),
                padding: const EdgeInsets.symmetric(vertical: 16),
                foregroundColor: Colors.white,
              ),
              child: const Text("I am 18 or older", style: TextStyle(fontSize: 18)),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => _handleAgeVerification(false),
              child: const Text("I am under 18", style: TextStyle(fontSize: 16, color: Colors.grey)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLocationGate() {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.location_on_outlined, size: 80, color: Color(0xFFFF6B6B)),
            const SizedBox(height: 24),
            Text(
              "Regional Verification",
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Text(
              "Certain jurisdictions (e.g., IL, UT, WA) have restricted AI for mental health. We need to verify you are not physically located in a 'Red Zone'.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 10),
            const Text(
              "We perform a one-time check. We do not track you.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: Colors.grey),
            ),
            const SizedBox(height: 48),
            ElevatedButton(
              onPressed: _requestLocation,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFF6B6B),
                padding: const EdgeInsets.symmetric(vertical: 16),
                foregroundColor: Colors.white,
              ),
              child: const Text("Verify Location", style: TextStyle(fontSize: 18)),
            ),
            if (_status == ComplianceStatus.locationServicesDisabled)
              Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: const Text(
                  "Please enable Location Services in your device settings to proceed.",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.red),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildConversionScreen() {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.mobile_friendly, size: 80, color: Color(0xFF667EEA)),
            const SizedBox(height: 24),
            Text(
              "Mobile App Required",
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Text(
              "To ensure privacy and regulatory compliance, GentleQuest is currently available only on our mobile app.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 48),
            const Text(
              "Please download GentleQuest from the App Store or Google Play Store.",
              textAlign: TextAlign.center,
              style: TextStyle(fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBlockedScreen(String title, String message) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.block, size: 80, color: Colors.red),
            const SizedBox(height: 24),
            Text(
              title,
              style: Theme.of(context).textTheme.headlineMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 48),
            if (title == "Age Requirement") ...[
                const Text("Need Help?", style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                const Text("Dial 988 (USA) for immediate support."),
            ] else ...[
                // Data Export Link for CCPA/GDPR Compliance
                ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 300),
                  child: TextButton.icon(
                    onPressed: _launchEmail,
                    icon: const Icon(Icons.download),
                    label: const Text("Request My Data (Export)"),
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  "Blocked users retain full rights to their data.",
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
            ]
          ],
        ),
      ),
    );
  }

  Widget _buildErrorScreen() {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 60, color: Colors.orange),
            const SizedBox(height: 16),
            const Text("Verification Failed", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text("We couldn't verify your eligibility. Please check your internet/location settings and try again."),
             const SizedBox(height: 24),
            ElevatedButton(onPressed: _checkStatus, child: const Text("Retry"))
          ],
        ),
      ),
    );
  }
}
