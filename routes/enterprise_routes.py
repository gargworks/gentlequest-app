"""
Enterprise status/metrics endpoints.
Extracted from app.py monolith. Only registers when the `integrations` module
hasn't already provided `enterprise_status` / `enterprise_metrics` view funcs.
"""

import os
from datetime import datetime, timezone

from flask import Flask, jsonify


def register_enterprise_routes(app: Flask) -> None:
    """Register fallback /api/enterprise/* endpoints if not already present."""
    already_registered = (
        "enterprise_status" in app.view_functions
        and "enterprise_metrics" in app.view_functions
    )
    if already_registered:
        return

    @app.route("/api/enterprise/status")
    def enterprise_status():
        """Enterprise status endpoint."""
        return jsonify(
            {
                "status": "active",
                "features": {
                    "ai_optimization": os.getenv(
                        "ENABLE_AI_OPTIMIZATION", "false"
                    ).lower()
                    == "true",
                    "clinical_detection": os.getenv(
                        "ENABLE_CLINICAL_DETECTION", "false"
                    ).lower()
                    == "true",
                    "revenue_system": os.getenv(
                        "ENABLE_REVENUE_SYSTEM", "false"
                    ).lower()
                    == "true",
                    "security_encryption": os.getenv(
                        "ENABLE_SECURITY_ENCRYPTION", "false"
                    ).lower()
                    == "true",
                    "distributed_scale": os.getenv(
                        "ENABLE_DISTRIBUTED_SCALE", "false"
                    ).lower()
                    == "true",
                },
                "version": "2.0.0",
                "environment": os.getenv("ENVIRONMENT", "production"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.route("/api/enterprise/metrics")
    def enterprise_metrics():
        """Enterprise metrics endpoint."""
        return jsonify(
            {
                "status": "active",
                "metrics": {
                    "uptime": True,
                    "health": "healthy",
                    "version": "2.0.0",
                },
            }
        )
