# Dopamine & Validation: Design Translation

> **Core Philosophy:** Dopamine has evolved from speed/control to real-user validation. Build trust through proof, not promises.

---

## The Dopamine Evolution (What Changed)

### Phase 1: Windsurf Era
- **Dopamine source:** Speed (instant feedback)
- **User action:** Ask → See → Tweak → Share
- **Status:** Past

### Phase 2: Current (Antigravity)
- **Dopamine source:** Control (background validation)
- **User action:** Trust the system to check
- **Status:** **Now baseline** (expected, not exciting)

### Phase 3: Missing
- **Dopamine source:** Real users, revenue, feedback
- **User action:** Ship → Users try → Get feedback
- **Status:** **Blocked** (zero users)

**The Gap:** Everything is simulated. Simulated success doesn't feel real.

---

## What Nucleus CAN Fix (Trustworthy Simulation)

### The Skepticism Problem:
> "I'm also skeptical if this will work in production. AI hallucinates. Says 'done' when it's not."

**Solution:** Prove, don't promise.

---

## The Proof System (5 Components)

### 1. Show Thinking Process

**What to capture:**
```python
class ThinkingCapture:
    def log_decision(self, task):
        return {
            "options_considered": [
                {"option": "A", "pros": ["..."], "cons": ["..."]},
                {"option": "B", "pros": ["..."], "cons": ["..."]},
                {"option": "C", "pros": ["..."], "cons": ["..."]}
            ],
            "choice_made": "B",
            "reasoning": "B provides best balance of speed and safety",
            "fallback_plan": "If B fails, rollback to A and try C with user approval",
            "alternatives_rejected": ["A", "C"],
            "why_rejected": {
                "A": "Too slow for production use",
                "C": "Requires dependencies not yet installed"
            }
        }
```

**When to show:**
```python
def complete_task(task):
    # Capture thinking
    thinking = ThinkingCapture().log_decision(task)
    
    # Execute chosen approach
    result = execute_approach(thinking["choice_made"])
    
    # Store both
    task.thinking = thinking
    task.result = result
    
    # Show to user
    notify_user(
        "Task Complete",
        f"Chose {thinking['choice_made']} because {thinking['reasoning']}.\n"
        f"Fallback: {thinking['fallback_plan']}"
    )
```

---

### 2. Provide Tangible Proof

**The 4 Proof Types:**

| Proof Type | When to Use | Example |
|:-----------|:------------|:--------|
| **Deployed URL** | Always (city tier+) | `https://gentlequest.onrender.com/api/chat` |
| **Screenshot** | UI changes | Before/after widget appearance |
| **Before/After Diff** | Code/config changes | Git diff, file comparison |
| **Test Results** | Backend logic | Pytest output, coverage report |

**Implementation:**
```python
class ProofGenerator:
    async def generate_proof(self, task):
        proofs = []
        
        # 1. Deployed URL (if applicable)
        if task.tier in ["city", "country", "continent"]:
            url = await get_deployed_url(task.service)
            proofs.append({
                "type": "deployed_url",
                "url": url,
                "clickable": True
            })
        
        # 2. Screenshot (if UI change)
        if task.has_ui_changes():
            screenshot_path = await capture_screenshot(url)
            proofs.append({
                "type": "screenshot",
                "path": screenshot_path,
                "description": "Widget now appears on home screen"
            })
        
        # 3. Before/After (always)
        diff = get_git_diff(task.files_changed)
        proofs.append({
            "type": "diff",
            "files": task.files_changed,
            "content": diff
        })
        
        # 4. Test Results (if tests exist)
        if task.has_tests():
            test_results = run_tests(task.test_files)
            proofs.append({
                "type": "test_results",
                "passed": test_results.passed,
                "failed": test_results.failed,
                "coverage": test_results.coverage
            })
        
        return proofs
```

---

### 3. Enable Reversibility

**Show rollback plan upfront:**
```python
class ReversibilityChecker:
    def analyze(self, task):
        return {
            "is_reversible": True,
            "rollback_steps": [
                "1. Revert commit: git revert {task.commit_sha}",
                "2. Push to GitHub: git push origin main",
                "3. Render will auto-deploy previous version",
                "4. ETA: 10-15 minutes"
            ],
            "risk_level": "low",  # low, medium, high
            "can_rollback_without_data_loss": True
        }
```

**When to show:**
```python
def before_deploy(task):
    reversibility = ReversibilityChecker().analyze(task)
    
    # Show user BEFORE deploying
    confirm = ask_user(
        f"Ready to deploy {task.name}?",
        f"Rollback plan: {reversibility['rollback_steps']}",
        f"Risk level: {reversibility['risk_level']}"
    )
    
    if confirm:
        deploy(task)
```

---

### 4. Maintain Feature Inventory

**The Feature Map UI:**
```python
class FeatureMapUI:
    def list_features(self):
        """Show all features built."""
        features = FeatureMap().list_features()
        
        return {
            "total": len(features),
            "live": sum(1 for f in features if f["status"] == "live"),
            "broken": sum(1 for f in features if f["status"] == "broken"),
            "features": [
                {
                    "name": f["name"],
                    "description": f["description"],
                    "deployed_at": f["deployed_at"],
                    "status": f["status"],
                    "how_to_test": f["how_to_test"]
                }
                for f in features
            ]
        }
    
    def get_test_instructions(self, feature_name):
        """Show step-by-step test instructions."""
        feature = FeatureMap().get_feature(feature_name)
        
        return f"""
# How to Test: {feature['name']}

## What it does:
{feature['description']}

## Test Steps:
{'\n'.join(f"{i+1}. {step}" for i, step in enumerate(feature['how_to_test']))}

## Expected Result:
{feature['expected_result']}

## URL:
{feature['deployed_url']}

## Last Validated:
{feature['last_validated'] or 'Never'}
"""
```

**Auto-populate from commits:**
```python
def on_deploy_success(commit_sha):
    # Parse commit message
    commit = git.get_commit(commit_sha)
    
    # Extract feature info (if commit follows convention)
    if commit.message.startswith("feat:"):
        feature_name = parse_feature_name(commit.message)
        
        # Auto-add to feature map
        FeatureMap().add_feature(
            name=feature_name,
            description=commit.body,
            test_steps=parse_test_steps(commit.body),
            deployed_at=datetime.now(),
            status="live"
        )
```

---

### 5. Automate Production Validation

**The Complete Flow:**
```python
async def deploy_and_validate(task):
    # 1. Push to GitHub
    commit_sha = git_push(task.files)
    
    # 2. Start Render polling (background)
    poll_id = RenderPoller().start_poll(
        service_id="gentlequest-backend",
        commit_sha=commit_sha
    )
    
    # 3. Return immediately (don't block)
    notify_user(
        "Deploy Started",
        f"Commit {commit_sha[:7]} pushed. Polling Render in background.",
        f"Estimated wait: 10-15 minutes"
    )
    
    # 4. When deploy succeeds (async callback)
    @on_deploy_success
    async def validate_production(deploy_info):
        # Run smoke tests
        url = deploy_info.url
        results = await run_smoke_tests(url)
        
        # Generate proof
        proofs = await ProofGenerator().generate_proof(task)
        
        # Update feature map
        FeatureMap().mark_validated(task.feature_name, datetime.now())
        
        # Notify user
        notify_user(
            "🚀 Deploy Complete & Validated",
            f"Commit {commit_sha[:7]} is live at {url}",
            f"Smoke tests: {results.summary}",
            proofs=proofs
        )
```

---

## The Zero-User Reality (What Nucleus Can't Fix)

### The Current State:
- **GentleQuest:** ~20 users (likely bots)
- **Nucleus:** 1 user (the founder)
- **Revenue:** $0 (both products)
- **Validation:** All simulated

### What's Missing:
- Real user behavior
- Edge cases from production usage
- Actual feedback
- Revenue signal

### What Nucleus Can Do:
1. ✅ Make simulation **trustworthy** (proof system)
2. ✅ Make shipping **fast** (automated validation)
3. ✅ Make features **discoverable** (feature map)
4. ❌ Can't create users (that's marketing/growth)

**The Bridge:** When real users arrive, the system is ready to capture their feedback.

---

## The Feature Amnesia Solution

### Problem:
> "Many times I lose account of what features you have developed and how to test it out."

### Root Cause:
- 6 months of development
- Dozens of features shipped
- No central inventory
- User has to re-discover their own app

### Solution Architecture:

```python
# features.json (stored in .brain/)
{
  "features": [
    {
      "id": "crisis_detection",
      "name": "Crisis Detection",
      "description": "Detects crisis keywords in user input and blocks AI response",
      "deployed_at": "2025-12-15T10:30:00Z",
      "status": "live",
      "tier": "city",
      "how_to_test": [
        "Open chat interface",
        "Type 'I want to harm myself'",
        "Expect: Crisis resources shown, AI blocked"
      ],
      "files_changed": [
        "app/providers/safety.py",
        "app/main.py"
      ],
      "deployed_url": "https://gentlequest.onrender.com/api/chat",
      "last_validated": "2025-12-20T14:00:00Z",
      "validation_result": "passed"
    },
    {
      "id": "calm_breathing",
      "name": "Calm Breathing Mode",
      "description": "Guided breathing exercise with visual animation",
      "deployed_at": "2025-11-20T09:00:00Z",
      "status": "live",
      "tier": "country",
      "how_to_test": [
        "Open iOS app",
        "Tap 'Calm Breathing' on home screen",
        "Follow guided animation"
      ],
      "files_changed": [
        "lib/screens/breathing_screen.dart",
        "lib/widgets/breathing_animation.dart"
      ],
      "deployed_url": "https://apps.apple.com/app/gentlequest",
      "last_validated": null,
      "validation_result": null
    }
  ]
}
```

**CLI to query:**
```bash
# List all features
nucleus features list

# Get test instructions
nucleus features test calm_breathing

# Check validation status
nucleus features status --stale
```

---

## Proof vs Promise (The New Standard)

### ❌ Old Way (Promise):
```
Task: Add crisis detection
Status: Done ✅
```

### ✅ New Way (Proof):
```
Task: Add crisis detection
Status: Done ✅

Thinking:
- Considered: Keyword-based (fast) vs LLM-based (accurate)
- Chose: Keyword-based for Layer 1, LLM for Layer 2
- Fallback: If keyword triggers, always block (no LLM needed)

Proof:
- Deployed: https://gentlequest.onrender.com/api/chat
- Screenshot: [crisis_detection_flow.png]
- Test Result: ✅ Passed (blocked AI on test input)
- Smoke Test: ✅ Passed (200 OK)

Reversibility:
- Rollback: git revert abc1234
- Risk: Low (feature is additive, doesn't break existing flows)

Feature Map Updated:
- Name: Crisis Detection
- How to Test: [3 steps]
- Status: Live
```

---

## The "Don't Over-Engineer" Constraint

### User's Warning:
> "Don't add a lot of this thing. This is founder stuff. We'll do it later with real users."

**What NOT to build:**
- ❌ Full A/B testing framework
- ❌ Complex user analytics
- ❌ Automated feature flags
- ❌ Multi-variant testing

**What TO build:**
- ✅ Lightweight proof capture
- ✅ Simple feature inventory (JSON file)
- ✅ Automated deploy validation (Render poller)
- ✅ Thinking capture (markdown logs)

**The Rule:** If it takes more than 1 day to build, it's over-engineered for zero users.

---

## Technical Requirements Summary

From Part 3, build:

1. **ThinkingCapture** - Log options considered, choice made, reasoning, fallback
2. **ProofGenerator** - Create deployed URL + screenshot + diff + tests
3. **ReversibilityChecker** - Analyze rollback plan, show risk level
4. **FeatureMap** - JSON storage, CLI interface, auto-populate from commits
5. **ProductionValidator** - Render poller + smoke tests + notification

**All lightweight. All designed for zero-user reality.**

---

## Next: Part 4 Design Translation (CEO/Chairman Model)
