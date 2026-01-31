#!/bin/bash

# =============================================================================
# AI MENTAL HEALTH ASSISTANT - LOCAL DEVELOPMENT STARTUP SCRIPT
# =============================================================================
# Usage: ./start_local.sh [option]
# Options: native (default), clean

set -e

# --- CONFIGURATION ---
# Rationalized Ports to match Cloud Run (8080) and distinct Frontend (9200)
export BACKEND_PORT=8080
export FLUTTER_WEB_PORT=9200
export POSTGRES_PORT=5432
export REDIS_PORT=6379

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- HELPER FUNCTIONS ---

check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

kill_port() {
    local port=$1
    if check_port $port; then
        print_warning "Port $port is in use. Killing..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

check_env() {
    if [ ! -f .env ]; then
        if [ -f env.example ]; then
            cp env.example .env
            print_status "Created .env from template"
        else
            print_error "No .env or env.example found!"
            exit 1
        fi
    fi
}

cleanup() {
    print_status "Cleaning up processes..."
    
    # Kill PIDs from files
    if [ -f .backend.pid ]; then
        kill $(cat .backend.pid) 2>/dev/null || true
        rm .backend.pid
    fi
    if [ -f .flutter.pid ]; then
        kill $(cat .flutter.pid) 2>/dev/null || true
        rm .flutter.pid
    fi
    
    # Aggressive port cleanup
    kill_port $BACKEND_PORT
    kill_port $FLUTTER_WEB_PORT
    
    print_success "Cleanup complete."
}

start_native() {
    cleanup # Always start fresh
    check_env
    
    print_status "Starting Backend on port $BACKEND_PORT..."
    
    # Check Python environment
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        print_warning "No .venv found. Assuming global python3..."
    fi

    # Start Backend
    # Pass PORT explicitly to override any defaults
    PORT=$BACKEND_PORT python3 app.py > backend_native.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid
    
    # Wait for backend health check
    print_status "Waiting for Backend to initialize..."
    local retries=0
    while ! curl -s http://localhost:$BACKEND_PORT/api/health >/dev/null; do
        sleep 1
        retries=$((retries+1))
        if [ $retries -gt 15 ]; then
            print_error "Backend failed to start. Check backend_native.log"
            cleanup
            exit 1
        fi
        echo -n "."
    done
    echo ""
    print_success "Backend is UP at http://localhost:$BACKEND_PORT"

    # Start Flutter Web
    if command -v flutter >/dev/null 2>&1; then
        print_status "Starting Flutter Web on port $FLUTTER_WEB_PORT..."
        cd ai_buddy_web
        flutter run -d web-server --web-port=$FLUTTER_WEB_PORT > ../flutter_web.log 2>&1 &
        FLUTTER_PID=$!
        cd ..
        echo $FLUTTER_PID > .flutter.pid
        print_success "Flutter Web launching at http://localhost:$FLUTTER_WEB_PORT"
    else
        print_warning "Flutter not found. Skipping frontend."
    fi

    print_success "Environment Running!"
    print_status "Backend Logs: tail -f backend_native.log"
    print_status "Flutter Logs: tail -f flutter_web.log"
    print_status "Press Ctrl+C to stop (cleanup will run)."
    
    # Keep script running to trap Ctrl+C
    wait $BACKEND_PID
}

# --- MAIN ---

trap cleanup SIGINT SIGTERM

case "${1:-native}" in
    "native")
        start_native
        ;;
    "clean")
        cleanup
        ;;
    *)
        print_error "Usage: $0 {native|clean}"
        exit 1
        ;;
esac 