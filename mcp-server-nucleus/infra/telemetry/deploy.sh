#!/usr/bin/env bash
# Deploy Nucleus Telemetry Collector to a VPS
#
# Usage:
#   ./deploy.sh                    # Deploy to current machine
#   ./deploy.sh user@vps-ip        # Deploy to remote VPS via SSH
#
# Prerequisites:
#   - Docker + Docker Compose installed on target
#   - DNS: telemetry.nucleusos.dev → target IP
#   - Ports 80, 443, 4317 open

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_DIR="/opt/nucleus-telemetry"

echo "🚀 Nucleus Telemetry Collector Deployment"
echo "==========================================="

if [ "${1:-}" != "" ]; then
    # ── Remote deployment ──
    TARGET="$1"
    echo "📡 Deploying to remote: $TARGET"
    echo ""

    echo "1/4  Creating remote directory..."
    ssh "$TARGET" "mkdir -p $REMOTE_DIR/grafana/provisioning/datasources $REMOTE_DIR/grafana/provisioning/dashboards $REMOTE_DIR/grafana/dashboards"

    echo "2/4  Copying config files..."
    scp "$SCRIPT_DIR/docker-compose.yaml" "$TARGET:$REMOTE_DIR/"
    scp "$SCRIPT_DIR/otel-collector-config.yaml" "$TARGET:$REMOTE_DIR/"
    scp "$SCRIPT_DIR/prometheus.yaml" "$TARGET:$REMOTE_DIR/"
    scp "$SCRIPT_DIR/Caddyfile" "$TARGET:$REMOTE_DIR/"
    scp "$SCRIPT_DIR/grafana/provisioning/datasources/prometheus.yaml" "$TARGET:$REMOTE_DIR/grafana/provisioning/datasources/"
    scp "$SCRIPT_DIR/grafana/provisioning/dashboards/default.yaml" "$TARGET:$REMOTE_DIR/grafana/provisioning/dashboards/"
    scp "$SCRIPT_DIR/grafana/dashboards/nucleus-usage.json" "$TARGET:$REMOTE_DIR/grafana/dashboards/"

    echo "3/4  Starting Docker Compose stack..."
    ssh "$TARGET" "cd $REMOTE_DIR && docker compose pull && docker compose up -d"

    echo "4/4  Verifying health..."
    sleep 5
    ssh "$TARGET" "curl -sf http://localhost:13133 > /dev/null && echo '  ✅ OTel Collector: healthy' || echo '  ❌ OTel Collector: unhealthy'"
    ssh "$TARGET" "curl -sf http://localhost:9090/-/ready > /dev/null && echo '  ✅ Prometheus: healthy' || echo '  ❌ Prometheus: unhealthy'"
    ssh "$TARGET" "curl -sf http://localhost:3000/api/health > /dev/null && echo '  ✅ Grafana: healthy' || echo '  ❌ Grafana: unhealthy'"

else
    # ── Local deployment ──
    echo "📡 Deploying locally"
    echo ""

    echo "1/3  Pulling images..."
    cd "$SCRIPT_DIR"
    docker compose pull

    echo "2/3  Starting stack..."
    docker compose up -d

    echo "3/3  Verifying health..."
    sleep 5
    curl -sf http://localhost:13133 > /dev/null && echo "  ✅ OTel Collector: healthy" || echo "  ❌ OTel Collector: unhealthy"
    curl -sf http://localhost:9090/-/ready > /dev/null && echo "  ✅ Prometheus: healthy" || echo "  ❌ Prometheus: unhealthy"
    curl -sf http://localhost:3000/api/health > /dev/null && echo "  ✅ Grafana: healthy" || echo "  ❌ Grafana: unhealthy"
fi

echo ""
echo "==========================================="
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Verify DNS: dig telemetry.nucleusos.dev"
echo "  2. Test ingest: nucleus morning-brief"
echo "  3. Check Grafana: https://telemetry.nucleusos.dev:3000"
echo "     (Default login: admin / admin — CHANGE ON FIRST LOGIN)"
echo ""
echo "Firewall reminders:"
echo "  ufw allow 4317/tcp    # OTLP gRPC ingest"
echo "  ufw allow 80/tcp      # Caddy HTTP→HTTPS redirect"
echo "  ufw allow 443/tcp     # Caddy TLS"
echo "  ufw allow from <YOUR_IP> to any port 3000  # Grafana (restrict!)"
