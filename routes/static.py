"""
Static pages: landing, app, clinical dashboard, health check, privacy, terms, assetlinks.
Extracted from app.py monolith.
"""

import os
from datetime import datetime

from flask import (
    Blueprint, jsonify, request, render_template,
    send_from_directory, current_app,
)
from extensions import limiter

static_bp = Blueprint("static", __name__)


def _serve_app_logic():
    """Shared logic to serve the Flutter web app or fallback."""
    current_app.logger.info(
        f"Serving app logic. Environment: {current_app.config.get('ENVIRONMENT')}"
    )
    if os.path.exists(current_app.static_folder) and os.path.exists(
        os.path.join(current_app.static_folder, "index.html")
    ):
        return send_from_directory(current_app.static_folder, "index.html")
    else:
        return jsonify(
            {
                "message": "GentleQuest AI Mental Health Assistant",
                "status": "running",
                "environment": current_app.config.get("ENVIRONMENT", "development"),
            }
        )


@static_bp.route("/clinical")
@static_bp.route("/clinical-dashboard")
def serve_clinical_dashboard():
    """Serve the Clinical Dashboard for university admins."""
    return send_from_directory("static", "clinical-dashboard.html")


@static_bp.route("/health")
def health_check():
    """Simple health check for Render/K8s"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200


@static_bp.route("/")
def landing_page():
    """Serve the 'Quiet Launch' landing page, or the App if strictly on 'app.*' domain."""
    host = request.headers.get("Host", "").lower()
    if host.startswith("app.") or host.startswith("nucleus."):
        return _serve_app_logic()

    return render_template("landing.html")


@static_bp.route("/app", methods=["GET"])
def serve_app():
    """Serve the Flutter web app or fallback page (explicit route)."""
    return _serve_app_logic()


@static_bp.route("/.well-known/assetlinks.json")
@limiter.exempt
def assetlinks():
    """Serve assetlinks.json for Android App Links verification"""
    try:
        return send_from_directory(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), ".well-known"),
            "assetlinks.json",
            mimetype="application/json",
        )
    except FileNotFoundError:
        return jsonify({"error": "Asset links file not found"}), 404


@static_bp.route("/privacy")
@static_bp.route("/privacy/")
@limiter.exempt
def privacy_policy():
    """Serve privacy policy page for app stores"""
    privacy_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - GentleQuest</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }
        h1 { color: #6366f1; }
        h2 { color: #4f46e5; margin-top: 2em; }
        .updated { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Privacy Policy</h1>
    <p class="updated">Last updated: January 2, 2026</p>
    
    <p>We respect your privacy. This Privacy Policy explains what we collect, why we collect it, 
    and how we handle your information when you use GentleQuest ("Service").</p>
    
    <h2>What We Collect</h2>
    <ul>
        <li>Messages you send to the assistant</li>
        <li>Technical metadata (timestamps, device/browser info, approximate location by country for crisis resources)</li>
        <li>Optional wellness/self-assessment inputs</li>
    </ul>
    
    <h2>How We Use Data</h2>
    <ul>
        <li>Provide and improve the Service (e.g., generate responses, show country-specific crisis resources)</li>
        <li>Maintain security and reliability (e.g., rate limiting, abuse prevention)</li>
        <li>Troubleshoot and measure basic usage, in aggregate</li>
    </ul>
    
    <h2>Data Retention</h2>
    <ul>
        <li>Messages: up to 30 days</li>
        <li>Sessions (inactive): up to 14 days</li>
        <li>Error logs: up to 14 days (or provider defaults)</li>
        <li>Aggregated/anonymized analytics: up to 90 days</li>
    </ul>
    <p>We retain data only as long as necessary for the purposes above.</p>
    
    <h2>Data Sharing</h2>
    <ul>
        <li>We do not sell your personal data.</li>
        <li>We may use third-party processors (e.g., AI providers, hosting) subject to confidentiality and data protection obligations.</li>
        <li>We avoid sending PII to providers; please don't include sensitive identifiers in messages.</li>
    </ul>
    
    <h2>Your Choices</h2>
    <ul>
        <li>You may request export or deletion of your data using the in-app Settings > Safety & Legal section.</li>
        <li>You can stop using the Service at any time; retention continues only as described above.</li>
    </ul>
    
    <h2>Safety Notice</h2>
    <p>This Service is not medical care. In an emergency or crisis, contact local emergency services. 
    Crisis resources may be shown based on your country.</p>
    
    <h2>Changes</h2>
    <p>We may update this Policy. Continued use indicates acceptance of the updated Policy.</p>
    
    <h2>Contact</h2>
    <p>For questions or requests, please refer to the in-app Settings > Safety & Legal section, 
    or contact us at <a href="mailto:support@gentlequest.app">support@gentlequest.app</a>.</p>
</body>
</html>
    """
    return privacy_html, 200, {'Content-Type': 'text/html'}


@static_bp.route("/terms")
@static_bp.route("/terms/")
@limiter.exempt
def terms_of_service():
    """Serve terms of service page for app stores"""
    terms_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - GentleQuest</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }
        h1 { color: #6366f1; }
        h2 { color: #4f46e5; margin-top: 2em; }
        .updated { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Terms of Service</h1>
    <p class="updated">Last updated: August 14, 2025</p>
    
    <p>Welcome to GentleQuest ("Service"). By using the Service, you agree to these Terms. If you do not agree, please discontinue use.</p>
    
    <h2>1. Not Medical Advice</h2>
    <p>The Service provides AI-generated wellness support and education only. It is not medical advice, diagnosis, or treatment. In an emergency or crisis, contact your local emergency number or country-specific crisis resources.</p>
    
    <h2>2. Eligibility</h2>
    <p>You must comply with applicable laws and use the Service for lawful purposes. Do not submit illegal, harmful, or personal data you are not authorized to share.</p>
    
    <h2>3. Your Content</h2>
    <p>You are responsible for the content you submit. To operate and improve the Service, you grant us a limited license to process your content.</p>
    
    <h2>4. Privacy</h2>
    <p>See the Privacy Policy for how we collect, use, and retain data.</p>
    
    <h2>5. Data Retention and Deletion</h2>
    <p>We retain data as described in our Privacy Policy. You may request data export or deletion via the in-app settings.</p>
    
    <h2>6. Acceptable Use</h2>
    <p>No misuse, harassment, scraping, reverse engineering, or security testing without permission. Respect rate limits and system integrity.</p>
    
    <h2>7. Third-Party Services</h2>
    <p>We use infrastructure and AI providers. Your use is subject to their terms.</p>
    
    <h2>8. Disclaimers</h2>
    <p>The Service is provided "as is" without warranties. We do not guarantee accuracy, availability, or fitness for a particular purpose.</p>
    
    <h2>9. Limitation of Liability</h2>
    <p>To the maximum extent permitted by law, we are not liable for indirect, incidental, or consequential damages.</p>
    
    <h2>10. Changes</h2>
    <p>We may update these Terms. Continued use means you accept the updated Terms.</p>
    
    <h2>11. Contact</h2>
    <p>For questions or requests, please refer to the in-app Settings > Safety & Legal section, or contact us at <a href="mailto:support@gentlequest.app">support@gentlequest.app</a>.</p>
</body>
</html>
    """
    return terms_html, 200, {'Content-Type': 'text/html'}
