#!/usr/bin/env bash
# Easy telemetry control for Lokesh
# Usage:
#   ./telemetry.sh up     # start collector (existing container)
#   ./telemetry.sh down   # stop collector

set -euo pipefail

cd "$(dirname "$0")/.."

CONTAINER_NAME="nucleus-otel-collector"

case "${1:-}" in
  up)
    echo "[telemetry] Starting Docker collector container '$CONTAINER_NAME'..."
    # Try docker compose service first, fall back to plain container start
    if docker compose ps "$CONTAINER_NAME" >/dev/null 2>&1 || docker-compose ps "$CONTAINER_NAME" >/dev/null 2>&1; then
      docker compose up -d "$CONTAINER_NAME" 2>/dev/null || docker-compose up -d "$CONTAINER_NAME" || true
    else
      docker start "$CONTAINER_NAME" || true
    fi
    echo "[telemetry] Reminder: run the drain script in another terminal if not already running:"
    echo "  cd ~/ai-mvp-backend/mcp-server-nucleus && npm run telemetry:drain"
    ;;
  down)
    echo "[telemetry] Stopping Docker collector container '$CONTAINER_NAME'..."
    docker stop "$CONTAINER_NAME" || true
    ;;
  *)
    echo "Usage: $0 {up|down}" >&2
    exit 1
    ;;
esac

