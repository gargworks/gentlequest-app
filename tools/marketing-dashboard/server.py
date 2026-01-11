#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import json
import os
import time
from datetime import datetime

# --- FIREBASE ADMIN SETUP ---
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    from google.oauth2 import service_account as google_sa
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase Admin SDK not installed. Auth will be disabled.")

PORT = int(os.environ.get("PORT", 9999))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

# Ensure mcp-server-nucleus is on the path
import sys
MCP_SOURCE = os.path.join(PROJECT_ROOT, "mcp-server-nucleus", "src")
if MCP_SOURCE not in sys.path:
    sys.path.append(MCP_SOURCE)

# PATHS
LOG_PATH = os.path.join(PROJECT_ROOT, "docs/marketing/marketing_log.md")
SERVICE_ACCOUNT_PATH = os.path.join(PROJECT_ROOT, "secret/service_account.json")
EVENTS_PATH = os.path.join(PROJECT_ROOT, ".brain/ledger/events.jsonl")
TASK_PATH = os.path.join(PROJECT_ROOT, ".brain/task.md")

# Initialize Firebase Admin
AUTH_ENABLED = False
if FIREBASE_AVAILABLE:
    try:
        if os.path.exists(SERVICE_ACCOUNT_PATH):
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
            print("🔒 Firebase Admin Initialized with Service Account")
            AUTH_ENABLED = True
        else:
            # Try ADC (Application Default Credentials)
            # Useful if running in Cloud Run or with 'gcloud auth application-default login'
            firebase_admin.initialize_app()
            print("🔒 Firebase Admin Initialized with ADC")
            AUTH_ENABLED = True
    except Exception as e:
        print(f"⚠️ Firebase Admin Init Failed: {e}")
        print("⚠️ server.py running in UNSECURED DEV MODE")

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class MarketingPortalHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()


    def parse_tasks(self):
        """Parses task.md into structured JSON"""
        tasks = []
        current_section = "General"
        
        try:
            if not os.path.exists(TASK_PATH):
                return {"error": "task.md not found"}
                
            with open(TASK_PATH, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line.startswith("###"):
                    current_section = line.strip("# ").strip()
                elif line.startswith("- ["):
                    is_done = line.startswith("- [x]")
                    is_in_progress = line.startswith("- [/]")
                    text = line[5:].strip()
                    
                    status = "pending"
                    if is_done: status = "done"
                    elif is_in_progress: status = "in_progress"
                    
                    tasks.append({
                        "section": current_section,
                        "text": text,
                        "status": status
                    })
            return {"tasks": tasks}
        except Exception as e:
            return {"error": str(e)}
    def list_swarms(self):
        """Lists active swarms from .brain/swarm"""
        swarms = []
        swarm_dir = os.path.join(PROJECT_ROOT, ".brain/swarm")
        
        if not os.path.exists(swarm_dir):
            return {"swarms": []}
            
        try:
            for item in os.listdir(swarm_dir):
                item_path = os.path.join(swarm_dir, item)
                if os.path.isdir(item_path):
                    plan_path = os.path.join(item_path, "plan.json")
                    if os.path.exists(plan_path):
                        try:
                            with open(plan_path, 'r') as f:
                                plan = json.load(f)
                                swarms.append(plan)
                        except:
                            pass
            return {"swarms": swarms}
        except Exception as e:
            return {"error": str(e)}

    def do_GET(self):
        # Serve local files (Dashboard)
        clean_path = self.path.split('?')[0].lstrip('/')
        
        # --- NUCLEUS API ---
        if clean_path == 'api/tasks':
            # Check for JSON format request
            if 'format=json' in self.path:
                self._set_headers(200, 'application/json')
                self.wfile.write(json.dumps(self.parse_tasks()).encode())
                return
            else:
                return self.serve_file(TASK_PATH, 'text/markdown')
            
        elif clean_path == 'api/events':
            return self.stream_events()

        elif clean_path == 'api/swarms':
            self._set_headers(200, 'application/json')
            self.wfile.write(json.dumps(self.list_swarms()).encode())
            return

        elif clean_path == 'api/health':
            self._set_headers(200, 'application/json')
            import time
            from datetime import datetime
            health_data = {
                "status": "green",
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time(), # Placeholder for actual uptime if we tracked it
                "version": "1.0"
            }
            self.wfile.write(json.dumps(health_data).encode())
            return

        elif clean_path == 'api/memory':
            self._set_headers(200, 'application/json')
            brain_path = ".brain" # Relative to CWD
            memory_nodes = []
            
            if os.path.exists(brain_path):
                for root, dirs, files in os.walk(brain_path):
                    for file in files:
                        if file.startswith('.'): continue
                        
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, brain_path)
                        
                        # Determine category/color based on path
                        category = "other"
                        if "agents" in rel_path: category = "agent"
                        elif "memory" in rel_path: category = "memory"
                        elif rel_path.endswith(".md"): category = "strategy"
                        elif rel_path.endswith(".json") or rel_path.endswith(".jsonl"): category = "data"
                        
                        # Get file stats
                        try:
                            stats = os.stat(full_path)
                            size = stats.st_size
                            mtime = stats.st_mtime
                        except:
                            size = 0
                            mtime = 0
                            
                        memory_nodes.append({
                            "id": rel_path,
                            "path": rel_path,
                            "type": category,
                            "size": size,
                            "last_modified": mtime
                        })
            
            self.wfile.write(json.dumps(memory_nodes).encode())
            return
            
        # --- STATIC FILES ---
        if not clean_path or clean_path == 'index.html':
            return self.serve_file(os.path.join(BASE_DIR, 'index.html'), 'text/html')
        elif clean_path == 'firebase_config.js': # Serve Config
            return self.serve_file(os.path.join(BASE_DIR, 'firebase_config.js'), 'application/javascript')
        elif clean_path == 'marketing_log.md':
            return self.serve_file(LOG_PATH, 'text/markdown')
        else:
            # Check for generic file serving within the project root (for protocol links)
            target_path = os.path.abspath(os.path.join(PROJECT_ROOT, clean_path))
            if target_path.startswith(PROJECT_ROOT) and os.path.exists(target_path):
                ext = os.path.splitext(target_path)[1]
                mime = 'text/plain'
                if ext == '.html': mime = 'text/html'
                elif ext == '.md': mime = 'text/markdown'
                return self.serve_file(target_path, mime)
            else:
                self.send_error(404, "File not found")

    def stream_events(self):
        """Streams events.jsonl via SSE"""
        self.send_response(200)
        self.send_header('Content-type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Open file and tail it
        try:
            # Send initial buffer (last 10 events)
            last_lines = []
            if os.path.exists(EVENTS_PATH):
                with open(EVENTS_PATH, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-20:] # Last 20 events
            
            for line in last_lines:
                if line.strip():
                    self.wfile.write(f"data: {line.strip()}\n\n".encode('utf-8'))
                    
            # Follow new events
            # Note: In Cloud Run, file changes might not propagate if not on volume, 
            # but for local hybrid mode, this works.
            # Ideally we'd hook into the Event Bus, but file tailing is robust.
            
            if os.path.exists(EVENTS_PATH):
                f = open(EVENTS_PATH, 'r')
                f.seek(0, 2) # Go to end
                
                while True:
                    line = f.readline()
                    if line:
                        self.wfile.write(f"data: {line.strip()}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    else:
                        time.sleep(0.5)
            else:
                 self.wfile.write(f"data: {json.dumps({'error': 'No event log found'})}\n\n".encode('utf-8'))
                 
        except BrokenPipeError:
            print("Client disconnected from stream.")
            return

    def serve_file(self, full_path, content_type):
        try:
            with open(full_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(404, str(e))

    def verify_token(self):
        """Returns True if authorized, False otherwise"""
        if not AUTH_ENABLED:
            return True # Dev bypass
        
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return False
        
        token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = auth.verify_id_token(token)
            return True
        except Exception as e:
            print(f"❌ Token Verification Failed: {e}")
            return False

    def do_POST(self):
            # ------------------
            
        if self.path == '/api/research':
             content_length = int(self.headers['Content-Length'])
             post_data = self.rfile.read(content_length)
             try:
                data = json.loads(post_data.decode('utf-8'))
                topic = data.get('topic')
                
                if not topic:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "No topic provided"}).encode())
                    return
                    
                # Emit Event for Orchestrator
                from mcp_server_nucleus.runtime.firestore_bridge import get_bridge
                import uuid
                
                event_payload = {
                    "intent": f"Research: {topic}",
                    "source": "hud_research_widget"
                }
                
                evt = {
                    "event_id": f"res-{uuid.uuid4().hex[:8]}",
                    "timestamp": datetime.now().isoformat(),
                    "emitter": "hud",
                    "event_type": "user_intent", # Orchestrator listens for this
                    "severity": "NORMAL",
                    "payload": event_payload
                }
                
                get_bridge().push_event(evt)
                
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "dispatched", "message": f"Researcher dispatched for: {topic}"}).encode())
                return
                
             except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return
        
        elif self.path == '/api/chat':
             content_length = int(self.headers['Content-Length'])
             post_data = self.rfile.read(content_length)
             try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message')
                
                if not message:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "No message provided"}).encode())
                    return
                    
                # Emit Event for Orchestrator
                from mcp_server_nucleus.runtime.firestore_bridge import get_bridge
                import uuid
                
                event_payload = {
                    "message": message,
                    "source": "hud_chat"
                }
                
                evt = {
                    "event_id": f"msg-{uuid.uuid4().hex[:8]}",
                    "timestamp": datetime.now().isoformat(),
                    "emitter": "hud",
                    "event_type": "user_message", # Orchestrator listens for this
                    "severity": "NORMAL",
                    "payload": event_payload
                }
                
                get_bridge().push_event(evt)
                
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "sent", "message": "Message received. Agents notified."}).encode())
                return
                
             except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

        if self.path == '/api/ingest':
            # --- AUTH CHECK ---
            if not self.verify_token():
                self._set_headers(401)
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                print("⛔ Blocked Unauthorized Request")
                return
            # ------------------

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                content = data.get('content', '')
                type_label = data.get('type', 'Trend 📡')
                
                if not content:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "No content provided"}).encode())
                    return

                # Format for Markdown Table
                date_str = datetime.now().strftime("%Y-%m-%d")
                sanitized_content = content.replace("\n", "<br>").replace("|", "\\|")
                platform_label = "Twitter/X" if "Trend" in type_label else "Reddit/Inbox"
                new_row = f"| {date_str} | {platform_label} | {sanitized_content} | New Opportunity | |"
                
                with open(LOG_PATH, "a") as f:
                    f.write("\n" + new_row)
                
                # --- NUCLEUS SENSOR INTEGRATION ---
                try:
                    from mcp_server_nucleus.runtime.event_stream import emit_event, EventSeverity
                    # Use Firestore Bridge
                    from mcp_server_nucleus.runtime.firestore_bridge import get_bridge
                    
                    event_payload = {
                        "source": "marketing_dashboard",
                        "type": type_label,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    import uuid
                    evt = {
                        "event_id": f"mkt-{uuid.uuid4().hex[:8]}",
                        "timestamp": datetime.now().isoformat(),
                        "emitter": "marketing_dashboard",
                        "event_type": "marketing_insight_detected",
                        "severity": "ROUTINE",
                        "payload": event_payload
                    }
                    get_bridge().push_event(evt)
                    print(f"📡 Streamed event to Cloud Brain")
                except Exception as ex:
                    print(f"⚠️ Failed to stream event: {ex}")
                # ----------------------------------

                self.wfile.write(json.dumps({"status": "success", "message": "Logged successfully"}).encode())
                print(f"✅ Ingested {type_label} at {datetime.now()}")

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        
        elif self.path == '/api/autopilot':
             content_length = int(self.headers['Content-Length'])
             post_data = self.rfile.read(content_length)
             try:
                data = json.loads(post_data.decode('utf-8'))
                active = data.get('active', False)
                mode = data.get('mode', 'marketing')
                
                global AUTOPILOT_ACTIVE
                AUTOPILOT_ACTIVE = active
                
                # Emit Event
                from mcp_server_nucleus.runtime.firestore_bridge import get_bridge
                import uuid
                
                status_msg = "ENGAGED" if active else "DISENGAGED"
                
                evt = {
                    "event_id": f"auto-{uuid.uuid4().hex[:8]}",
                    "timestamp": datetime.now().isoformat(),
                    "emitter": "hud",
                    "event_type": "autopilot_status",
                    "severity": "NORMAL",
                    "payload": {"status": status_msg, "mode": mode}
                }
                get_bridge().push_event(evt)
                
                self._set_headers(200, 'application/json')
                self.wfile.write(json.dumps({"status": "success", "active": active}).encode())
                print(f"🤖 Autopilot {status_msg}")
                
             except Exception as e:
                self._set_headers(500, 'application/json')
                self.wfile.write(json.dumps({"error": str(e)}).encode())
             return

        elif self.path == '/api/critique':
             try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                file_path = data.get("file_path")
                if not file_path:
                    raise ValueError("Missing file_path")
                
                print(f"🧐 Critic requested for: {file_path}")
                
                from mcp_server_nucleus import _critique_code
                result = _critique_code(file_path, context="Requested via HUD")
                
                self._set_headers(200, 'application/json')
                self.wfile.write(json.dumps(result).encode())
             except Exception as e:
                print(f"Critic Error: {e}")
                self._set_headers(500, 'application/json')
                self.wfile.write(json.dumps({"error": str(e)}).encode())
             return



# --- NUCLEUS SELF-HEALING AUTOPILOT ---
AUTOPILOT_ACTIVE = False
import threading

def nucleus_autopilot_loop():
    """
    Background loop that scans codebase for low-quality components and Auto-Fixes them.
    Phase 19: The Fixer (Self-Healing Architecture).
    """
    print("🤖 Nucleus Autopilot: Started (Self-Healing Mode)")
    
    # Import Nucleus Core
    from pathlib import Path
    import sys
    sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))
    try:
        from mcp_server_nucleus import _critique_code, brain_fix_code
        from mcp_server_nucleus.runtime.event_stream import emit_event, EventSeverity
    except ImportError as e:
        print(f"⚠️ Autopilot Error: Could not import Nucleus: {e}")
        return

    # Configuration
    WATCH_PATHS = [
        "/Users/lokeshgarg/ai-mvp-backend/tools/nucleus-hud/app/components/clinical",
        "/Users/lokeshgarg/ai-mvp-backend/tools/nucleus-hud/app/components/outcome"
    ]
    MIN_SCORE_THRESHOLD = 80
    
    brain_path = Path(PROJECT_ROOT) / ".brain"
    
    while True:
        if AUTOPILOT_ACTIVE:
            print("🤖 Autopilot: Scanning for pathologies...")
            
            for watch_dir in WATCH_PATHS:
                p = Path(watch_dir)
                if not p.exists(): continue
                
                # Scan .tsx files
                for file_path in p.glob("*.tsx"):
                    # Basic Heuristic: Skip if too big or too small
                    if file_path.stat().st_size < 100: continue
                    
                    try:
                        # 1. Critique
                        print(f"🧐 Auditing: {file_path.name}")
                        critique = _critique_code(str(file_path), context="Autopilot Audit")
                        score = critique.get("score", 100)
                        
                        if score < MIN_SCORE_THRESHOLD:
                            print(f"🚨 Low Score Detected ({score}): {file_path.name}")
                            
                            # Emit "Damage Detected" Event
                            emit_event(
                                brain_path=brain_path,
                                event_type="health_alert",
                                emitter="autopilot",
                                payload={"file": file_path.name, "score": score, "status": "needs_fix"},
                                severity=EventSeverity.WARNING
                            )
                            
                            # 2. Fix (The Fixer)
                            print(f"🔧 Applying Fixer to {file_path.name}...")
                            
                            # Convert issues list to string for Fixer
                            issues_str = json.dumps(critique.get("issues", []))
                            fix_result = brain_fix_code(str(file_path), issues_str)
                            
                            # 3. Report
                            print(f"✅ Fix Applied: {fix_result}")
                            
                            emit_event(
                                brain_path=brain_path,
                                event_type="self_healing_action",
                                emitter="autopilot",
                                payload={
                                    "file": file_path.name,
                                    "initial_score": score,
                                    "action": "patched",
                                    "result": json.loads(fix_result)
                                },
                                severity=EventSeverity.ROUTINE
                            )
                            
                    except Exception as ex:
                        print(f"⚠️ Autopilot Error on {file_path.name}: {ex}")
            
            print("🤖 Autopilot: Scan Complete. Sleeping...")
            time.sleep(30) # Run every 30s (Demo Mode)
            
        else:
            time.sleep(2)

# Start the thread
t = threading.Thread(target=nucleus_autopilot_loop, daemon=True)
t.start()

if __name__ == "__main__":
    print(f"🚀 Nucleus Brain Server running at http://0.0.0.0:{PORT}")
    # Bind to 0.0.0.0 for Docker/Cloud Run
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(('0.0.0.0', PORT), MarketingPortalHandler)
    server.serve_forever()
