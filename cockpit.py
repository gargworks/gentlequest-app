#!/usr/bin/env python3
"""
Nuclear Cockpit v2 - Complete Redesign
=======================================

A founder-first dashboard for the agentic company.
All controls are clearly labeled and intuitive.

Run: streamlit run cockpit.py
"""

import streamlit as st
import json
import os
import time
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from collections import deque, defaultdict
from typing import Dict, List, Tuple, Optional

try:
    from filelock import FileLock, Timeout
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

# ============================================================================
# PATHS
# ============================================================================

BRAIN_ROOT = Path(__file__).parent / ".brain"
LEDGER_DIR = BRAIN_ROOT / "ledger"
ARTIFACTS_DIR = BRAIN_ROOT / "artifacts"
MEMORY_DIR = BRAIN_ROOT / "memory"

STATE_FILE = LEDGER_DIR / "state.json"
EVENTS_FILE = LEDGER_DIR / "events.jsonl"
DECISIONS_FILE = LEDGER_DIR / "decisions.md"
LEARNINGS_FILE = MEMORY_DIR / "learnings.md"
AGENTS_FILE = Path(__file__).parent / "AGENTS.md"

PID_FILE = BRAIN_ROOT / ".flywheel.pid"
LOCK_FILE = BRAIN_ROOT / ".state.lock"

# ============================================================================
# STYLING
# ============================================================================

GREEN = "#00FF41"
BLACK = "#0D0D0D"
RED = "#FF4444"
YELLOW = "#FFD700"
CYAN = "#00FFFF"
GRAY = "#888888"

CSS = f"""
<style>
    .stApp {{ background: {BLACK}; color: {GREEN}; }}
    [data-testid="stSidebar"] {{ background: #111; border-right: 1px solid {GREEN}; }}
    h1, h2, h3, h4 {{ color: {GREEN} !important; font-family: monospace; }}
    p, span, label, li {{ color: {GREEN}; font-family: monospace; }}
    code {{ color: {CYAN} !important; background: #1a1a1a !important; }}
    
    .stButton > button {{
        background: #1a1a1a; color: {GREEN}; border: 1px solid {GREEN};
        font-family: monospace; transition: all 0.2s;
    }}
    .stButton > button:hover {{ background: {GREEN}; color: {BLACK}; }}
    
    .btn-start {{ border-color: {GREEN} !important; }}
    .btn-stop {{ border-color: {RED} !important; }}
    
    .status-running {{ color: {GREEN}; font-weight: bold; }}
    .status-stopped {{ color: {RED}; font-weight: bold; }}
    
    .card {{
        background: #1a1a1a; border: 1px solid {GREEN};
        border-radius: 8px; padding: 15px; margin: 10px 0;
    }}
    .card-pending {{ border-color: {YELLOW}; }}
    
    .summary-box {{
        background: #0f0f0f; border-left: 3px solid {CYAN};
        padding: 12px; margin: 8px 0; font-size: 13px;
    }}
    
    .help-text {{ color: {GRAY}; font-size: 12px; font-style: italic; }}
    
    .metric-big {{ font-size: 32px; font-weight: bold; text-align: center; }}
    
    .tab-label {{ font-size: 11px; color: {GRAY}; }}
</style>
"""

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def read_state() -> dict:
    """Read state.json with optional locking"""
    try:
        if HAS_FILELOCK:
            lock = FileLock(str(LOCK_FILE))
            with lock.acquire(timeout=2):
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
        else:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except:
        return {}

def write_state(state: dict) -> bool:
    """Write state.json with optional locking"""
    try:
        if HAS_FILELOCK:
            lock = FileLock(str(LOCK_FILE))
            with lock.acquire(timeout=2):
                state['last_updated'] = datetime.now(timezone.utc).isoformat()
                with open(STATE_FILE, 'w') as f:
                    json.dump(state, f, indent=4)
        else:
            state['last_updated'] = datetime.now(timezone.utc).isoformat()
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=4)
        return True
    except:
        return False

def get_events(limit: int = 100) -> List[dict]:
    """Get recent events"""
    if not EVENTS_FILE.exists():
        return []
    events = []
    with open(EVENTS_FILE, 'r') as f:
        for line in deque(f, maxlen=limit):
            try:
                events.append(json.loads(line.strip()))
            except:
                pass
    return events

def get_artifact_content(artifact_path: str) -> Tuple[str, str]:
    """Load artifact content and generate summary"""
    # Handle relative paths from .brain/
    if artifact_path.startswith('.brain/'):
        full_path = Path(__file__).parent / artifact_path
    elif artifact_path.startswith('./'):
        full_path = Path(__file__).parent / artifact_path[2:]
    else:
        full_path = Path(__file__).parent / artifact_path
    
    if not full_path.exists():
        # Try prepending .brain/
        full_path = BRAIN_ROOT / artifact_path.replace('.brain/', '')
        if not full_path.exists():
            return "", f"File not found: {artifact_path}"
    
    try:
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Generate summary from first paragraph after headers
        lines = content.split('\n')
        summary_parts = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('>') and not line.startswith('---'):
                summary_parts.append(line[:150])
                if len(summary_parts) >= 2:
                    break
        summary = ' '.join(summary_parts)[:300] if summary_parts else "No summary available"
        
        return content, summary
    except Exception as e:
        return "", f"Error reading: {str(e)}"

# ============================================================================
# FLYWHEEL CONTROL
# ============================================================================

def flywheel_status() -> Tuple[bool, Optional[int]]:
    """Check if flywheel is running"""
    if not PID_FILE.exists():
        return False, None
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)  # Check if process exists
        return True, pid
    except:
        return False, None

def start_flywheel():
    """Start the flywheel daemon"""
    subprocess.Popen(
        ['python3', 'agent_manager.py', 'start'],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def stop_flywheel():
    """Stop the flywheel daemon"""
    subprocess.run(
        ['python3', 'agent_manager.py', 'stop'],
        cwd=str(Path(__file__).parent),
        capture_output=True
    )

def launch_sprint(goal: str):
    """Launch a new sprint"""
    subprocess.run(
        ['python3', 'agent_manager.py', 'sprint', goal],
        cwd=str(Path(__file__).parent),
        capture_output=True
    )

# ============================================================================
# MAIN UI
# ============================================================================

def main():
    st.set_page_config(
        page_title="☢️ Cockpit",
        page_icon="☢️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown(CSS, unsafe_allow_html=True)
    
    # Session state defaults
    if 'pending_sprint' not in st.session_state:
        st.session_state.pending_sprint = None
    
    # Load data
    state = read_state()
    is_running, pid = flywheel_status()
    events = get_events(50)
    
    # ========== HEADER ==========
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 0;">☢️ NUCLEAR COCKPIT</h1>
    <p style="text-align: center; color: #888; margin-top: 5px;">
        Your Command Center for the Agentic Company
    </p>
    """, unsafe_allow_html=True)
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        # FLYWHEEL CONTROL (Most Important)
        st.markdown("## 🔥 FLYWHEEL")
        
        if is_running:
            st.markdown(f'<p class="status-running">● RUNNING (PID: {pid})</p>', unsafe_allow_html=True)
            st.caption("Agents are actively processing events")
            if st.button("⏹️ STOP FLYWHEEL", use_container_width=True, help="Pause all agent processing"):
                stop_flywheel()
                time.sleep(1)
                st.rerun()
        else:
            st.markdown('<p class="status-stopped">● STOPPED</p>', unsafe_allow_html=True)
            st.caption("No agents running - start to enable automation")
            if st.button("▶️ START FLYWHEEL", use_container_width=True, type="primary", help="Begin agent processing loop"):
                start_flywheel()
                time.sleep(1)
                st.rerun()
        
        st.divider()
        
        # CURRENT STATUS
        st.markdown("## 📊 STATUS")
        sprint = state.get('current_sprint', {})
        st.metric("Sprint", sprint.get('name', 'None')[:25] if sprint else 'None')
        st.metric("Events Today", len(events))
        pending = len(state.get('founder_queue', []))
        if pending > 0:
            st.warning(f"⚠️ {pending} decisions waiting")
        
        st.divider()
        
        # QUICK REFRESH
        if st.button("🔄 REFRESH PAGE", use_container_width=True, help="Reload all data"):
            st.rerun()
    
    # ========== MAIN TABS ==========
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 LAUNCH",           # Start new work
        "📋 DECISIONS",        # Approve pending items
        "📡 ACTIVITY",         # Monitor events
        "⚙️ ADVANCED"          # Ghost, Alignment, Emergency
    ])
    
    # ========== TAB 1: LAUNCH ==========
    with tab1:
        st.markdown("### 🚀 Launch a New Sprint")
        st.markdown('<p class="help-text">Set a goal and agents will work on it automatically</p>', unsafe_allow_html=True)
        
        # How it works
        with st.expander("ℹ️ How does this work?"):
            st.markdown("""
            1. **You write a goal** (e.g., "Build RAG memory layer")
            2. **Synthesizer decomposes** it into tasks for agents
            3. **Researcher, Strategist, Architect** work in parallel
            4. **Developer & Critic** are auto-triggered when needed
            5. **Results appear in DECISIONS** for your approval
            
            Just write the goal - the flywheel handles orchestration!
            """)
        
        # Sprint input
        goal = st.text_area(
            "What do you want to accomplish?",
            placeholder="Examples:\n- Build RAG memory layer with pgvector\n- Research competitor pricing strategies\n- Draft investor update email\n- Implement the Neural Bridge API",
            height=120
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🚀 LAUNCH SPRINT", type="primary", use_container_width=True, 
                        help="Start agents working on this goal"):
                if goal:
                    st.session_state.pending_sprint = goal
        
        # Confirmation
        if st.session_state.pending_sprint:
            st.markdown(f"""
            <div class="card card-pending">
                <strong>⚡ Confirm Launch</strong><br><br>
                <strong>Goal:</strong> {st.session_state.pending_sprint}<br><br>
                <span class="help-text">This will activate Researcher, Strategist, and Architect to work on this goal.</span>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ CONFIRM", type="primary"):
                    launch_sprint(st.session_state.pending_sprint)
                    if not is_running:
                        start_flywheel()
                    st.success("✅ Sprint launched! Agents are now working.")
                    st.session_state.pending_sprint = None
                    time.sleep(1)
                    st.rerun()
            with c2:
                if st.button("❌ CANCEL"):
                    st.session_state.pending_sprint = None
                    st.rerun()
    
    # ========== TAB 2: DECISIONS ==========
    with tab2:
        st.markdown("### 📋 Pending Decisions")
        st.markdown('<p class="help-text">Artifacts that need your approval before proceeding</p>', unsafe_allow_html=True)
        
        founder_queue = state.get('founder_queue', [])
        
        if not founder_queue:
            st.success("✅ No pending decisions - you're all caught up!")
            st.caption("Agents will add items here when they need your approval.")
        else:
            for idx, item in enumerate(founder_queue):
                action = item.get('action', 'Unknown')
                artifact_path = item.get('artifact', '')
                
                st.markdown(f"""
                <div class="card card-pending">
                    <strong>📄 {action}</strong>
                </div>
                """, unsafe_allow_html=True)
                
                # Load artifact
                content, summary = get_artifact_content(artifact_path)
                
                # Summary
                st.markdown(f"""
                <div class="summary-box">
                    <strong>Quick Summary:</strong><br>
                    {summary}
                </div>
                """, unsafe_allow_html=True)
                
                # Full content
                with st.expander(f"📖 Read Full Document ({artifact_path})"):
                    if content:
                        st.markdown(content)
                    else:
                        st.error(summary)  # Show error message
                
                # Comment + Actions
                comment = st.text_input(
                    "Your feedback (optional):",
                    key=f"comment_{idx}",
                    placeholder="e.g., 'Great, but simplify the intro' or 'Pivot to focus on mobile'"
                )
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ APPROVE", key=f"approve_{idx}", type="primary", 
                                help="Accept this artifact and continue"):
                        # Log decision
                        with open(DECISIONS_FILE, 'a') as f:
                            f.write(f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M')} - APPROVED\n")
                            f.write(f"- **Action:** {action}\n")
                            if comment:
                                f.write(f"- **Comment:** {comment}\n")
                        # Remove from queue
                        founder_queue.pop(idx)
                        state['founder_queue'] = founder_queue
                        write_state(state)
                        st.rerun()
                
                with c2:
                    if st.button("🔄 PIVOT", key=f"pivot_{idx}",
                                help="Reject and ask for changes"):
                        with open(DECISIONS_FILE, 'a') as f:
                            f.write(f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M')} - PIVOT\n")
                            f.write(f"- **Action:** {action}\n")
                            f.write(f"- **Feedback:** {comment or 'No feedback provided'}\n")
                        founder_queue.pop(idx)
                        state['founder_queue'] = founder_queue
                        write_state(state)
                        st.rerun()
                
                st.divider()
    
    # ========== TAB 3: ACTIVITY ==========
    with tab3:
        st.markdown("### 📡 Recent Activity")
        st.markdown('<p class="help-text">Real-time log of all agent events</p>', unsafe_allow_html=True)
        
        # Metrics
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Events", len(events))
        with c2:
            active = state.get('active_agents', [])
            st.metric("Active Agents", len(active))
        with c3:
            sprint_status = state.get('current_sprint', {}).get('status', 'N/A')
            st.metric("Sprint Status", sprint_status)
        
        st.divider()
        
        # Event list
        for event in reversed(events[-30:]):
            sev = event.get('severity', 'ROUTINE')
            emoji = {'CRITICAL': '🔴', 'NOTABLE': '🟡', 'ROUTINE': '⚪'}.get(sev, '⚪')
            emitter = event.get('emitter', '?')
            etype = event.get('event_type', '')
            ts = event.get('timestamp', '')[-8:]
            
            st.caption(f"{emoji} `{ts}` **{emitter}** → {etype}")
        
        # Auto-refresh
        if st.checkbox("🔄 Auto-refresh every 3 seconds"):
            time.sleep(3)
            st.rerun()
    
    # ========== TAB 4: ADVANCED ==========
    with tab4:
        st.markdown("### ⚙️ Advanced Controls")
        st.markdown('<p class="help-text">System internals, debugging, and emergency controls</p>', unsafe_allow_html=True)
        
        # Three sections as expanders
        with st.expander("👻 GHOST VIEW - Agent Thinking Traces"):
            st.markdown("""
            **What is this?**
            Shows what agents are "thinking" - the intermediate reasoning before they produce final outputs.
            Useful for debugging why an agent made a certain decision.
            """)
            
            st.markdown("#### Recent Learnings")
            if LEARNINGS_FILE.exists():
                with open(LEARNINGS_FILE, 'r') as f:
                    content = f.read()
                st.code('\n'.join(content.split('\n')[-25:]))
            else:
                st.caption("No learnings recorded yet")
            
            st.markdown("#### Activation Files")
            activations = BRAIN_ROOT / "activations"
            if activations.exists():
                files = sorted(activations.glob("*.md"), reverse=True)[:3]
                for f in files:
                    with st.expander(f.name):
                        st.code(f.read_text()[:2000])
            else:
                st.caption("No activation files")
        
        with st.expander("🎯 ALIGNMENT CHECK - Are Agents Following Rules?"):
            st.markdown("""
            **What is this?**
            Checks if all agents are following the rules defined in AGENTS.md.
            Green = good, Yellow = minor issues, Red = violations detected.
            """)
            
            # Simple alignment check
            violations = []
            
            # Check 1: Are agents writing to correct lanes?
            for e in events[-20:]:
                if e.get('event_type') == 'task_completed':
                    agent = e.get('emitter', '')
                    path = e.get('payload', {}).get('output_path', '')
                    if agent == 'researcher' and path and 'research' not in path:
                        violations.append(f"Researcher wrote to wrong path: {path}")
                    if agent == 'strategist' and path and 'strategy' not in path:
                        violations.append(f"Strategist wrote to wrong path: {path}")
            
            if violations:
                st.error(f"🔴 {len(violations)} violations found")
                for v in violations:
                    st.warning(v)
            else:
                st.success("🟢 All systems aligned with constitution")
            
            if AGENTS_FILE.exists():
                with st.expander("View AGENTS.md Constitution"):
                    st.markdown(AGENTS_FILE.read_text())
        
        with st.expander("🚨 EMERGENCY STOP - Halt All Operations"):
            st.markdown("""
            **What is this?**
            Immediately stops the flywheel and all agent operations.
            Use only if something goes wrong.
            """)
            
            st.warning("⚠️ This will immediately halt ALL running agents.")
            
            if st.button("🛑 EMERGENCY STOP", type="primary"):
                stop_flywheel()
                # Mark emergency in state
                state['emergency_stop'] = {
                    'triggered_at': datetime.now(timezone.utc).isoformat(),
                    'by': 'cockpit'
                }
                state['active_agents'] = []
                write_state(state)
                st.error("🚨 Emergency stop triggered. All operations halted.")
                time.sleep(1)
                st.rerun()
    
    # ========== FOOTER ==========
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; color: #666; font-size: 11px;">
        ☢️ Nuclear Cockpit v2 | {datetime.now().strftime('%H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
