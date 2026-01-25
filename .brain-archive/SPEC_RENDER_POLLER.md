# Render Poller: Detailed Specification (FROZEN)

> **Status:** Ready for implementation  
> **Effort:** 2-4 agentic hours  
> **Priority:** P0 (solves #1 pain point)

---

## Problem Statement

**Current:** User pushes to GitHub → Render deploys → User manually checks dashboard for 10-15 minutes → Momentum lost

**Desired:** User pushes to GitHub → System polls in background → Notifies when live → User continues working

**Impact:** Restores the dopamine loop, eliminates 10-15 min friction

---

## Technical Approach

### Decision: Automatic Polling (Not Manual Tool)

**Why automatic:**
- User shouldn't have to remember to start polling
- Trigger on git push event (observable)
- CEO principle: groundwork happens automatically

**How it works:**
```
1. User (or AI) runs: git push origin main
2. System detects push (via git hook or ledger event)
3. System extracts commit SHA
4. System starts background poll:
   - Get Render service ID (from config or MCP)
   - Poll Render API for deploy status
   - Check every 30 seconds
   - Timeout after 20 minutes
5. When deploy succeeds:
   - Run smoke test (/api/health)
   - Log event to ledger
   - Notify user in conversation
6. User can work on other things while polling happens
```

---

## Integration Points

### 1. Trigger Detection

**Option A: Git Hook (post-push)**
- Create `.git/hooks/post-push` script
- Calls `nucleus brain poll-render`
- Pros: Automatic, reliable
- Cons: Requires hook setup on each clone

**Option B: Ledger Event**
- User (or AI) logs event: `brain_emit_event("git_push", {commit_sha, branch})`
- Synthesizer watches events, triggers poll
- Pros: No git hooks needed
- Cons: Requires manual event logging

**DECISION: Option B (Ledger Event)**
- More flexible
- Aligns with existing Nucleus architecture (event-driven)
- Can be called from anywhere (CLI, MCP tool, automated deploy script)

### 2. Render Service Discovery

**How to get service ID:**
```python
# Method 1: From config file
service_id = brain_state.get("render_service_id_gentlequest")

# Method 2: Query Render MCP
services = mcp_render_list_services()
gentlequest = [s for s in services if "gentlequest" in s["name"].lower()][0]
service_id = gentlequest["id"]

# Method 3: Ask user once, cache in state
if not service_id:
    # List services, ask user to confirm
    # Store in .brain/ledger/state.json
```

**DECISION: Method 1 (config) with Method 2 fallback**
- Check state.json first
- If missing, query Render MCP once, cache result

### 3. Polling Logic

**Render API Flow:**
```python
import time
from render_mcp import get_deploy, list_deploys

async def poll_render_deploy(service_id, commit_sha, timeout_mins=20):
    """Poll Render until deploy completes or times out."""
    start_time = time.time()
    poll_interval = 30  # seconds
    
    while True:
        # Get latest deploy for this service
        deploys = list_deploys(service_id, limit=1)
        latest = deploys[0] if deploys else None
        
        if not latest:
            await asyncio.sleep(poll_interval)
            continue
        
        # Check if it's our commit
        if latest["commit"]["sha"][:7] != commit_sha[:7]:
            # Different commit, keep waiting
            await asyncio.sleep(poll_interval)
            continue
        
        # Check status
        status = latest["status"]
        
        if status == "live":
            return {
                "success": True,
                "url": latest["url"],
                "deployed_at": latest["finishedAt"],
                "duration_seconds": time.time() - start_time
            }
        
        elif status in ["build_failed", "deploy_failed", "canceled"]:
            return {
                "success": False,
                "status": status,
                "error": latest.get("failureReason")
            }
        
        # Still building/deploying
        elif time.time() - start_time > (timeout_mins * 60):
            return {
                "success": False,
                "status": "timeout",
                "error": f"Deploy exceeded {timeout_mins} minute timeout"
            }
        
        # Continue polling
        await asyncio.sleep(poll_interval)
```

### 4. Smoke Testing

**After deploy succeeds, verify health:**
```python
import requests

def run_smoke_test(deploy_url):
    """Quick health check on deployed service."""
    try:
        response = requests.get(f"{deploy_url}/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                return {"passed": True, "latency_ms": response.elapsed.total_seconds() * 1000}
            else:
                return {"passed": False, "reason": f"Status: {data.get('status')}"}
        else:
            return {"passed": False, "reason": f"HTTP {response.status_code}"}
    
    except Exception as e:
        return {"passed": False, "reason": str(e)}
```

### 5. Notification Strategy

**User's Desire:**
> "Ideally when it's complete you should just continue the conversation we were on. That event should get logged. In the meantime we can work on some other parallel thread."

**Implementation:**

**A. Event Logging (Always)**
```python
brain_emit_event("deploy_complete", {
    "service": "gentlequest-backend",
    "commit_sha": commit_sha,
    "url": deploy_url,
    "smoke_test": smoke_result,
    "duration_seconds": duration
})
```

**B. Conversation Continuation (If Same Thread)**
```python
def notify_deploy_complete(deploy_result):
    # Check if we're in the same thread that triggered deploy
    current_thread_id = get_current_thread_id()
    trigger_thread_id = deploy_result.get("triggered_by_thread")
    
    if current_thread_id == trigger_thread_id:
        # Same thread - just continue conversation
        return f"""
## ✅ Deploy Complete

**URL:** {deploy_result['url']}
**Duration:** {deploy_result['duration_seconds']}s
**Smoke Test:** {'✅ Passed' if smoke_result['passed'] else '❌ Failed'}

Ready to test the feature.
"""
    else:
        # Different thread - just log event
        # User can check ledger when they return
        pass
```

**C. OS Notification (Optional Future)**
- macOS: `osascript -e 'display notification "Deploy complete" with title "Nucleus"'`
- Not in v0.4.0 scope

**DECISION: A + B (Event logging + conversation continuation)**

---

## Error Handling

### Failure Scenarios:

1. **Deploy fails on Render**
   - Notify user immediately
   - Show Render error message
   - Suggest rollback command

2. **Smoke test fails**
   - Deploy succeeded but health check failed
   - Notify user with details
   - Don't mark as "complete" in feature map

3. **Timeout (20 min exceeded)**
   - Stop polling
   - Notify user
   - Suggest checking Render dashboard manually

4. **Network error during polling**
   - Retry up to 3 times
   - If still failing, notify user

### Example Error Notification:
```
## ❌ Deploy Failed

**Commit:** abc1234
**Status:** build_failed
**Reason:** npm install failed - missing dependency

**Suggested Action:**
Check Render logs at: https://dashboard.render.com/...

**Rollback:**
```bash
git revert abc1234
git push origin main
```
```

---

## Data Storage

### Where Things Live:

**1. Service Configuration**
```json
// .brain/ledger/state.json
{
  "render": {
    "services": {
      "gentlequest_backend": "srv-abc123",
      "gentlequest_frontend": "srv-def456"
    }
  }
}
```

**2. Deploy Events**
```jsonl
// .brain/ledger/events.jsonl
{"type": "git_push", "commit_sha": "abc1234", "branch": "main", "timestamp": "2025-01-05T01:00:00Z"}
{"type": "deploy_started", "service": "gentlequest-backend", "commit_sha": "abc1234", "timestamp": "2025-01-05T01:00:05Z"}
{"type": "deploy_complete", "service": "gentlequest-backend", "url": "https://...", "duration_seconds": 847, "timestamp": "2025-01-05T01:14:12Z"}
```

**3. Active Polls**
```json
// .brain/ledger/active_polls.json (temporary, cleared on completion)
{
  "polls": [
    {
      "poll_id": "poll_abc123",
      "service_id": "srv-abc123",
      "commit_sha": "abc1234",
      "started_at": "2025-01-05T01:00:05Z",
      "status": "polling"
    }
  ]
}
```

---

## Implementation Checklist

### Phase 1: Core Polling (2 hours)
- [ ] Create `brain_poll_render(service_id, commit_sha)` MCP tool
- [ ] Implement polling loop with 30s interval
- [ ] Handle deploy success/failure/timeout
- [ ] Store service config in state.json
- [ ] Log events to events.jsonl

### Phase 2: Smoke Testing (1 hour)
- [ ] Create `run_smoke_test(deploy_url)` function
- [ ] Auto-run after deploy succeeds
- [ ] Include in deploy_complete event

### Phase 3: Notifications (1 hour)
- [ ] Implement conversation continuation logic
- [ ] Format success/failure messages
- [ ] Test multi-thread scenarios

### Phase 4: Error Handling (30 min)
- [ ] Add retry logic for network errors
- [ ] Timeout handling
- [ ] Failure notifications with rollback suggestions

---

## Testing Plan

### Manual Test Scenario:
1. Make a trivial change to GentleQuest backend (e.g., update version string)
2. Commit and push to GitHub
3. Emit git_push event: `brain_emit_event("git_push", {commit_sha, branch})`
4. Verify polling starts
5. Wait for deploy (should take ~10-15 min)
6. Verify notification appears in conversation
7. Verify smoke test runs
8. Check events.jsonl for complete log

### Automated Tests (Future):
- Mock Render API responses
- Test polling states (live, failed, timeout)
- Test smoke test pass/fail scenarios

---

## Questions Resolved ✅

### Q1: Render API Key
**Answer:** User will add to `.env` file:
```bash
RENDER_API_KEY=rnd_your_key_here
```
The mcp-server-render will auto-detect it. No code changes needed.

### Q2: Multi-Service Support
**Answer:** Build generic tool (can poll any Render service), but test with GentleQuest backend only for v0.4.0. Future services will work automatically.

### Q3: Concurrent Deploy Behavior  
**Answer:** Cancel old poll when new git push happens (same as GitHub behavior). Implementation:
- Detect new `git_push` event for same service
- Cancel active poll if exists
- Start new poll for new commit
- GitHub/Render handles actual deploy cancellation

---

## Success Criteria

**This feature is complete when:**
- [x] Spec frozen (this document)
- [ ] Can push to GitHub and get auto-notification when live
- [ ] Smoke test runs automatically
- [ ] Events logged to ledger
- [ ] Error cases handled gracefully
- [ ] No manual Render dashboard checking needed

**Effort:** 2-4 hours of focused agentic work

---

**FROZEN. Ready for implementation when you say go.**
