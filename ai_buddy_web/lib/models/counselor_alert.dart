class CounselorAlert {
  final int id;
  final String sessionId;
  final String severity; // 'critical', 'high', 'medium', 'low'
  final String triggerMessage;
  final String sentAt;
  final String? acknowledgedAt;
  final String? acknowledgedBy;
  final bool emailSent;
  final bool smsSent;

  CounselorAlert({
    required this.id,
    required this.sessionId,
    required this.severity,
    required this.triggerMessage,
    required this.sentAt,
    this.acknowledgedAt,
    this.acknowledgedBy,
    this.emailSent = false,
    this.smsSent = false,
  });

  factory CounselorAlert.fromJson(Map<String, dynamic> json) {
    return CounselorAlert(
      id: json['id'],
      sessionId: json['session_id'],
      severity: json['severity'],
      triggerMessage: json['trigger_message'],
      sentAt: json['sent_at'],
      acknowledgedAt: json['acknowledged_at'],
      acknowledgedBy: json['acknowledged_by'],
      emailSent: json['email_sent'] ?? false,
      smsSent: json['sms_sent'] ?? false,
    );
  }
}
