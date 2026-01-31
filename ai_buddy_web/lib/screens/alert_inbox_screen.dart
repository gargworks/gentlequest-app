import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/counselor_alert.dart';
import '../widgets/alert_item.dart';

class AlertInboxScreen extends StatefulWidget {
  final String apiBaseUrl;
  final int universityId;

  const AlertInboxScreen({
    super.key,
    required this.apiBaseUrl,
    required this.universityId,
  });

  @override
  _AlertInboxScreenState createState() => _AlertInboxScreenState();
}

class _AlertInboxScreenState extends State<AlertInboxScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<CounselorAlert> _alerts = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(_handleTabChange);
    _fetchAlerts();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _handleTabChange() {
    if (_tabController.indexIsChanging) {
      _fetchAlerts();
    }
  }

  Future<void> _fetchAlerts() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final status = _tabController.index == 0 ? 'pending' : 'acknowledged';
      final url =
          '${widget.apiBaseUrl}/api/alerts/history?university_id=${widget.universityId}&status=$status';

      final response = await http.get(Uri.parse(url));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _alerts = (data['alerts'] as List)
              .map((a) => CounselorAlert.fromJson(a))
              .toList();
          _isLoading = false;
        });
      } else {
        throw Exception("Failed to load alerts: ${response.statusCode}");
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _onAlertTap(CounselorAlert alert) {
    // Navigate to details (placeholder for now)
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Alert Details #${alert.id}"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Trigger: ${alert.triggerMessage}"),
            const SizedBox(height: 10),
            Text("Severity: ${alert.severity}"),
            const SizedBox(height: 10),
            if (alert.acknowledgedAt == null)
              ElevatedButton(
                onPressed: () => _acknowledgeAlert(alert.id),
                child: const Text("Acknowledge Alert"),
              )
            else
              const Text("✅ Already Acknowledged",
                  style: TextStyle(color: Colors.green)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Close"),
          ),
        ],
      ),
    );
  }

  Future<void> _acknowledgeAlert(int alertId) async {
    try {
      final url = '${widget.apiBaseUrl}/api/alerts/$alertId/acknowledge';
      await http.post(Uri.parse(url),
          headers: {"Content-Type": "application/json"},
          body: json.encode({
            "counselor_id": "current_counselor", // Placeholder
            "response_notes": "Acknowledged via dashboard",
            "action_taken": "review_pending"
          }));
      Navigator.pop(context); // Close dialog
      _fetchAlerts(); // Refresh list
    } catch (e) {
      print("Error acknowledging: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Counselor Inbox"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: "Pending", icon: Icon(Icons.mark_email_unread)),
            Tab(text: "Resolved", icon: Icon(Icons.check_circle)),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text("Error: $_error"),
                      ElevatedButton(
                        onPressed: _fetchAlerts,
                        child: const Text("Retry"),
                      )
                    ],
                  ),
                )
              : _alerts.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.inbox,
                              size: 64, color: Colors.grey.shade300),
                          const SizedBox(height: 16),
                          Text(
                            _tabController.index == 0
                                ? "No pending alerts. All clear! 🎉"
                                : "No resolved alerts yet.",
                            style: TextStyle(color: Colors.grey.shade600),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _fetchAlerts,
                      child: ListView.builder(
                        itemCount: _alerts.length,
                        itemBuilder: (context, index) {
                          return AlertItem(
                            alert: _alerts[index],
                            onTap: () => _onAlertTap(_alerts[index]),
                          );
                        },
                      ),
                    ),
    );
  }
}
